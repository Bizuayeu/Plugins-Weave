"""WAL の UseCase: intent 追記 / ログ push（must-succeed） / 起動時 redo。

registry の永続化（`registry_sync.py` の best-effort push）と対照的に、WAL ログ push は
redo のソースゆえ **must-succeed**（push 失敗は raise で伝播＝秘書は送信前ゲートで止まる）。
Domain（`domain/wal.py` の reconcile/settle/checkpoint）を Port 越しに駆動する。
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable, Mapping, Set, Tuple

from domain.exceptions import PushRejectedError
from domain.lease import utc_now
from domain.wal import WalEntry, checkpoint, reconcile, settle
from usecases.manage_registry import RegistryService
from usecases.ports import GitSyncPort, WalLogStore


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


class RedoPendingIntents:
    """起動時の redo: WAL ログを読み、registry に無い pending を upsert して整合させる。

    load → registry_keys 収集 → reconcile（やり残し抽出）→ registry へ upsert
    → settle（registry にある pending を done 化）→ checkpoint（pending 保持・done を
    retention 掃除）→ rewrite。**返信は再送しない**（送信前クラッシュ分は offset 再取得が
    再処理を担う＝役割分担。WAL redo は送信後の registry 漏れ専任）。
    """

    def __init__(
        self,
        log_store: WalLogStore,
        services: Mapping[str, RegistryService],
        now_fn: Callable[[], datetime] = utc_now,
        retention_h: int = 24,
    ) -> None:
        self._log = log_store
        self._services = services
        self._now_fn = now_fn
        self._retention_h = retention_h

    def execute(self) -> dict:
        entries = self._log.load()
        todo = reconcile(entries, self._collect_keys())
        for e in todo:
            svc = self._services.get(e.kind)
            if svc is not None:
                svc.add_or_update(e.payload)
        # upsert 後の registry_keys で settle（今 redo した分＋既反映分を done 化）
        settled = settle(entries, self._collect_keys())
        kept = checkpoint(settled, self._now_fn(), self._retention_h)
        self._log.rewrite(kept)
        return {"redone": len(todo), "kept": len(kept)}

    def _collect_keys(self) -> Set[Tuple[str, str]]:
        keys: Set[Tuple[str, str]] = set()
        for kind, svc in self._services.items():
            for rec in svc.list():
                k = rec.get(svc.key_field)
                if k is not None:
                    keys.add((kind, k))
        return keys
