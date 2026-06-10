"""offset と lease の JSON ファイル永続化。破損時は安全フォールバック。

save は `atomic_io.write_text_atomic`（tmp + os.replace）——書込中クラッシュで
offset/lease を全損させない（破損 offset は initial へ巻き戻り重複再取得、破損 lease は
排他喪失につながるため、そもそも破損ファイルを作らない側に倒す）。
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from adapters.atomic_io import load_json_or_default, write_text_atomic
from domain.lease import SessionLease
from domain.offset import UpdateOffset


class JsonOffsetStore:
    """update offset を `offset.json` に永続化。破損時は initial に戻して再書き込み可能。"""

    FILENAME = "offset.json"

    def __init__(self, state_dir: Path) -> None:
        self._dir = Path(state_dir)
        self._path = self._dir / self.FILENAME

    def load(self) -> UpdateOffset:
        return load_json_or_default(
            self._path,
            parse=lambda data: UpdateOffset(value=int(data["value"])),
            default=UpdateOffset.initial,
        )

    def save(self, offset: UpdateOffset) -> None:
        write_text_atomic(
            self._path, json.dumps({"value": offset.value}, ensure_ascii=False)
        )


class JsonLeaseStore:
    """セッションリースを `lease.json` に永続化。"""

    FILENAME = "lease.json"

    def __init__(self, state_dir: Path) -> None:
        self._dir = Path(state_dir)
        self._path = self._dir / self.FILENAME

    def load(self) -> Optional[SessionLease]:
        return load_json_or_default(self._path, parse=self._parse, default=lambda: None)

    @staticmethod
    def _parse(data: object) -> SessionLease:
        return SessionLease(
            owner=str(data["owner"]),
            heartbeat=datetime.fromisoformat(data["heartbeat"]),
            ttl_seconds=int(data["ttl_seconds"]),
        )

    def save(self, lease: SessionLease) -> None:
        write_text_atomic(
            self._path, json.dumps(self._payload(lease), ensure_ascii=False)
        )

    def try_create(self, lease: SessionLease) -> bool:
        """lease ファイル不在時のみ O_CREAT|O_EXCL で atomic に新規作成する。

        並走プロセスとの新規取得レース（load→check→save の TOCTOU）を OS の
        排他作成で塞ぐ——同時 cron 起動の 2 コンテナで勝者は必ず 1 つ。
        既存ファイルがあれば False（呼び出し側が再 load して held_by_other 判定へ戻る）。
        """
        self._dir.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self._payload(lease), ensure_ascii=False)
        try:
            fd = os.open(str(self._path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return False
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
        return True

    @staticmethod
    def _payload(lease: SessionLease) -> dict:
        return {
            "owner": lease.owner,
            "heartbeat": lease.heartbeat.isoformat(),
            "ttl_seconds": lease.ttl_seconds,
        }

    def clear(self) -> None:
        if self._path.exists():
            try:
                self._path.unlink()
            except OSError:
                pass
