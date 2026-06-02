"""offset と lease の JSON ファイル永続化。破損時は安全フォールバック。"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from domain.lease import SessionLease
from domain.offset import UpdateOffset


class JsonOffsetStore:
    """update offset を `offset.json` に永続化。破損時は initial に戻して再書き込み可能。"""

    FILENAME = "offset.json"

    def __init__(self, state_dir: Path) -> None:
        self._dir = Path(state_dir)
        self._path = self._dir / self.FILENAME

    def load(self) -> UpdateOffset:
        if not self._path.exists():
            return UpdateOffset.initial()
        try:
            raw = self._path.read_text(encoding="utf-8")
            data = json.loads(raw)
            return UpdateOffset(value=int(data["value"]))
        except (json.JSONDecodeError, KeyError, ValueError, OSError):
            return UpdateOffset.initial()

    def save(self, offset: UpdateOffset) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps({"value": offset.value}, ensure_ascii=False),
            encoding="utf-8",
        )


class JsonLeaseStore:
    """セッションリースを `lease.json` に永続化。"""

    FILENAME = "lease.json"

    def __init__(self, state_dir: Path) -> None:
        self._dir = Path(state_dir)
        self._path = self._dir / self.FILENAME

    def load(self) -> Optional[SessionLease]:
        if not self._path.exists():
            return None
        try:
            raw = self._path.read_text(encoding="utf-8")
            data = json.loads(raw)
            return SessionLease(
                owner=str(data["owner"]),
                heartbeat=datetime.fromisoformat(data["heartbeat"]),
                ttl_seconds=int(data["ttl_seconds"]),
            )
        except (json.JSONDecodeError, KeyError, ValueError, OSError):
            return None

    def save(self, lease: SessionLease) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "owner": lease.owner,
            "heartbeat": lease.heartbeat.isoformat(),
            "ttl_seconds": lease.ttl_seconds,
        }
        self._path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def clear(self) -> None:
        if self._path.exists():
            try:
                self._path.unlink()
            except OSError:
                pass
