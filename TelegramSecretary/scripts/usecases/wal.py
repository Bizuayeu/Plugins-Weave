"""WAL の UseCase: intent 追記 / ログ push（must-succeed） / 起動時 redo。

registry の永続化（`registry_sync.py` の best-effort push）と対照的に、WAL ログ push は
redo のソースゆえ **must-succeed**（push 失敗は raise で伝播＝秘書は送信前ゲートで止まる）。
Domain（`domain/wal.py` の reconcile/settle/checkpoint）を Port 越しに駆動する。
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable, Mapping, Optional, Set, Tuple

from domain.exceptions import PushRejectedError
from domain.lease import utc_now
from domain.models import OutboundMessage
from domain.outbound import OutboundAttachment
from domain.wal import WalEntry, checkpoint, reconcile, settle, settle_outbound
from usecases.manage_registry import RegistryService
from usecases.ports import GitSyncPort, MessageSink, WalLogStore


class AppendWalIntent:
    """1 intent を pending で WAL ログに追記する（対外コミット〔返信送信〕の前段）。"""

    def __init__(self, log_store: WalLogStore) -> None:
        self._log = log_store

    def execute(self, key: str, kind: str, payload: dict, created_at: str) -> WalEntry:
        entry = WalEntry(
            key=key, kind=kind, status="pending", payload=payload, created_at=created_at
        )
        self._log.append(entry)
        return entry


class SettleOutboundIntent:
    """送信成功した outbound intent を done 化する（happy-path settle）。

    `proactive-send` が送信成功直後に呼ぶ。outbound は registry のような外部真実源を
    持たないため、**送信者自身が key（created_at）直指定で done 化**する。これにより
    `RedoPendingIntents` の outbound 再送が「成功送信まで巻き込んで偽謝罪付きで複製する」
    のを断つ（DESIGN §3.9 が前提とする happy-path settle の実装）。送信成功と done 記録の
    間でクラッシュした分だけが pending として残り、次回 redo の at-least-once 再送が拾う。
    """

    def __init__(self, log_store: WalLogStore) -> None:
        self._log = log_store

    def execute(self, key: str) -> None:
        entries = self._log.load()
        self._log.rewrite(settle_outbound(entries, key))


class PushWalLog:
    """WAL ログを commit & push。**must-succeed**＝push 失敗は raise で伝播（送信前ゲート）。

    `RegistrySyncService` は push 失敗を握る（best-effort）が、WAL ログは redo のソースゆえ
    「push 成功まで送信しない」。non-ff のみ `pull_rebase`→再 push を 1 枚挟み、なお失敗
    （PushRejectedError / GitSyncError）なら raise してターンを止める（秘書が send-reply を打たない）。
    """

    def __init__(self, git: GitSyncPort, log_path: Path) -> None:
        self._git = git
        self._log_path = log_path

    def execute(self, message: str) -> bool:
        committed = self._git.commit([self._log_path], message)
        if not committed:
            return False  # 変更なし（no-op）、push しない
        try:
            self._git.push()
        except PushRejectedError:
            self._git.pull_rebase()
            self._git.push()  # 再失敗は raise を伝播（best-effort と異なり握らない）
        return True


_OUTBOUND_RESEND_PREFIX = (
    "[{created_at}] にお送りしようとした内容を、念のためお届けします（既に届いていたらご容赦ください）"
)


def _rebuild_outbound(entry: WalEntry) -> OutboundMessage:
    """WAL outbound intent の payload から OutboundMessage を復元し、再送プレフィックスを付す。

    元の送信予定時刻（created_at）を本文頭に埋め込み、鮮度判定は人間に委ねる（policy をコードに
    持たない＝v4 設計）。重複は exactly-once を技術で追わず「受け手の混乱」を社会レイヤで無害化する。
    """
    p = entry.payload
    prefix = _OUTBOUND_RESEND_PREFIX.format(created_at=entry.created_at)
    body = p.get("text", "")
    text = f"{prefix}\n\n{body}" if body else prefix
    attachments = [OutboundAttachment(path=Path(x)) for x in p.get("attachments", [])]
    return OutboundMessage(
        chat_id=p["chat_id"],
        text=text,
        reply_to_message_id=p.get("reply_to_message_id"),
        attachments=attachments,
    )


class RedoPendingIntents:
    """起動時の redo: registry の pending を upsert し、outbound の pending を1回だけ再送する。

    **registry kind**（individuals/tasks/knowledge/abilities）: load → reconcile（やり残し抽出）→
    registry へ upsert → settle（registry にある pending を done 化）→ checkpoint → rewrite。
    送信前クラッシュ分は offset 再取得が再処理を担うため **返信は再送しない**（WAL redo は送信後の
    registry 漏れ専任）。

    **outbound kind**（proactive-send、DESIGN §3.9）: inbound に紐づかず offset の安全網が無いため
    WAL 再送が唯一の冪等性保証になる。pending を **1回だけ再送**（元時刻＋謝罪プレフィックス）して即
    mark_done する。registry_keys を持たないので reconcile/settle の照合経路には乗せず独立ループで
    処理する（混ぜると未送信判定が壊れる）。再送→即 done で無限再送ループを防ぐ（v4、TTL 不要）。
    """

    def __init__(
        self,
        log_store: WalLogStore,
        services: Mapping[str, RegistryService],
        sink: Optional[MessageSink] = None,
        now_fn: Callable[[], datetime] = utc_now,
        retention_h: int = 24,
    ) -> None:
        self._log = log_store
        self._services = services
        self._sink = sink
        self._now_fn = now_fn
        self._retention_h = retention_h

    def execute(self) -> dict:
        entries = self._log.load()
        registry_entries = [e for e in entries if e.kind != "outbound"]
        outbound_entries = [e for e in entries if e.kind == "outbound"]

        # registry kind: reconcile（やり残し抽出）→ upsert → settle（done 化）
        todo = reconcile(registry_entries, self._collect_keys())
        for e in todo:
            svc = self._services.get(e.kind)
            if svc is not None:
                svc.add_or_update(e.payload)
        # upsert 後の registry_keys で settle（今 redo した分＋既反映分を done 化）
        settled_registry = settle(registry_entries, self._collect_keys())

        # outbound kind: pending を1回だけ再送 → mark_done（registry_keys 非依存の独立経路）
        settled_outbound = []
        resent = 0
        for e in outbound_entries:
            if e.status == "pending" and self._sink is not None:
                self._sink.send(_rebuild_outbound(e))
                settled_outbound.append(e.mark_done())
                resent += 1
            else:
                settled_outbound.append(e)

        kept = checkpoint(
            settled_registry + settled_outbound, self._now_fn(), self._retention_h
        )
        self._log.rewrite(kept)
        return {"redone": len(todo), "resent": resent, "kept": len(kept)}

    def _collect_keys(self) -> Set[Tuple[str, str]]:
        keys: Set[Tuple[str, str]] = set()
        for kind, svc in self._services.items():
            for rec in svc.list():
                k = rec.get(svc.key_field)
                if k is not None:
                    keys.add((kind, k))
        return keys
