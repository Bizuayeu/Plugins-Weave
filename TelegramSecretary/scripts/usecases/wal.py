"""WAL の UseCase: intent 追記 / ログ push（must-succeed） / 起動時 redo。

registry の永続化（`registry_sync.py` の best-effort push）と対照的に、WAL ログ push は
redo のソースゆえ **must-succeed**（push 失敗は raise で伝播＝秘書は送信前ゲートで止まる）。
Domain（`domain/wal.py` の reconcile/quarantine/settle/checkpoint）を Port 越しに駆動する。
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path

from domain.exceptions import PushRejectedError
from domain.lease import utc_now
from domain.models import OutboundMessage
from domain.outbound import OutboundAttachment
from domain.wal import (
    WalEntry,
    checkpoint,
    quarantine,
    reconcile,
    settle,
    settle_outbound,
)
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


class DropDeadIntent:
    """dead 化した intent を操作者の明示指示で WAL から落とす（`wal-drop` の実体）。

    dead の出口は二つだけ——同 key の再登録（`settle` による自己治癒）と、この明示的な
    drop。**pending は落とせない**（果たされていない約束を黙って捨てる口を作らない）ので、
    dead 以外は `ValueError` で拒む。同 (kind, key) の dead が重複していれば全て落とし、
    並んでいる pending / done の行は残す。`SettleOutboundIntent` と同型（load → 判定 → rewrite）。
    """

    def __init__(self, log_store: WalLogStore) -> None:
        self._log = log_store

    def execute(self, kind: str, key: str) -> None:
        entries = self._log.load()
        matched = [e for e in entries if e.kind == kind and e.key == key]
        if not matched:
            raise ValueError(f"wal intent not found: {kind} key={key}")
        if not any(e.status == "dead" for e in matched):
            raise ValueError(
                f"wal intent is not dead: {kind} key={key} status={matched[0].status}"
            )
        self._log.rewrite(
            [
                e
                for e in entries
                if not (e.kind == kind and e.key == key and e.status == "dead")
            ]
        )


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


_OUTBOUND_RESEND_PREFIX = "[{created_at}] にお送りしようとした内容を、念のためお届けします（既に届いていたらご容赦ください）"


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

    **registry kind**（REGISTRY_SPEC の各表）: load → reconcile（やり残し抽出）→
    **validate**（正準化・検証）→ registry へ upsert → quarantine（落ちた分を dead 化）→
    settle（registry にある pending / dead を done 化）→ checkpoint → rewrite。
    `validate` は**必須引数**——省略可にすると注入し忘れが素通りし、「WAL 経由なら未検証の
    レコードが registry へ入る」という穴が UseCase 内に再生する。1 件の不正は dead へ隔離
    され、他の pending の redo を道連れにしない。
    **返信は再送しない**（WAL redo は送信後の registry 漏れ専任。送信前クラッシュ分の再処理は
    Telegram サーバ側の unconfirmed 再配送＝新コンテナの fresh state_dir での再取得が担う）。

    **outbound kind**（proactive-send、DESIGN §3.9）: inbound に紐づかず offset の安全網が無いため
    WAL 再送が唯一の冪等性保証になる。pending を **1回だけ再送**（元時刻＋謝罪プレフィックス）して即
    mark_done する。registry_keys を持たないので reconcile/settle の照合経路には乗せず独立ループで
    処理する（混ぜると未送信判定が壊れる）。再送→即 done で無限再送ループを防ぐ（v4、TTL 不要）。
    """

    def __init__(
        self,
        log_store: WalLogStore,
        services: Mapping[str, RegistryService],
        validate: Callable[[str, dict], dict],
        sink: MessageSink | None = None,
        now_fn: Callable[[], datetime] = utc_now,
        retention_h: int = 24,
    ) -> None:
        self._log = log_store
        self._services = services
        self._validate = validate
        self._sink = sink
        self._now_fn = now_fn
        self._retention_h = retention_h

    def execute(self) -> dict:
        entries = self._log.load()
        registry_entries = [e for e in entries if e.kind != "outbound"]
        outbound_entries = [e for e in entries if e.kind == "outbound"]

        # registry kind: reconcile（やり残し抽出）→ validate → upsert → quarantine → settle
        todo = reconcile(registry_entries, self._collect_keys())
        failures: dict[tuple[str, str], str] = {}
        redone = 0
        for e in todo:
            svc = self._services.get(e.kind)
            if svc is None:
                continue  # 未知の kind は書き込み先が無い（検証しても行き場がない）
            try:
                record = self._validate(e.kind, e.payload)
            except (ValueError, OSError, TypeError, KeyError) as exc:
                # registry_cli の add と同一の捕捉タプル（入力不正の扱いを一箇所に揃える）。
                # 切り詰めは validator 組み立て側の責務、UseCase は str(exc) をそのまま残す
                failures[(e.kind, e.key)] = str(exc)
                continue
            svc.add_or_update(record)  # 生 payload ではなく正準 record を書く
            redone += 1
        # settle の**前**に quarantine（今回 dead にしたものは registry に無いので done にならない）
        quarantined = quarantine(registry_entries, failures)
        # upsert 後の registry_keys で settle（今 redo した分＋既反映分＋治癒した dead を done 化）
        settled_registry = settle(quarantined, self._collect_keys())

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

        # kind 別の settle 結果を元 entries の並びへ書き戻す（WAL の時系列＝interleave 順を
        # 保持。連結だと registry が前・outbound が後ろへ寄り、短期記憶の読み出し順が崩れる）。
        # 分離リストは各 kind 内の元順序を保つため、kind 判定で交互に消費すれば復元できる。
        registry_iter = iter(settled_registry)
        outbound_iter = iter(settled_outbound)
        settled = [
            next(outbound_iter) if e.kind == "outbound" else next(registry_iter)
            for e in entries
        ]

        kept = checkpoint(settled, self._now_fn(), self._retention_h)
        self._log.rewrite(kept)
        # dead は「今回隔離した件数」でなくログに残る総数——未履行の約束が毎起動で見える
        dead = sum(1 for e in kept if e.status == "dead")
        return {
            "redone": redone,
            "resent": resent,
            "kept": len(kept),
            "dead": dead,
        }

    def _collect_keys(self) -> set[tuple[str, str]]:
        keys: set[tuple[str, str]] = set()
        for kind, svc in self._services.items():
            for rec in svc.list():
                k = rec.get(svc.key_field)
                if k is not None:
                    keys.add((kind, k))
        return keys
