"""管理表（INDIVIDUALS / TASKS / KNOWLEDGE）の JSON ファイル永続化 Adapter。

1 管理表 = 1 JSON ファイル（`{"version": N, "records": [...]}` 形式）。
`UseCase` 層が依存する `RegistryStore` Port（load/save）の実装。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List


class JsonRegistryStore:
    """管理表 1 ファイルの load/save。

    - load: ファイルが無ければ `[]`、破損していても `[]` にフォールバック
    - save: 親ディレクトリを作成、`ensure_ascii=False` で日本語をそのまま保存
    """

    def __init__(self, path: Path, version: int = 1) -> None:
        self._path = path
        self._version = version

    def load(self) -> List[dict]:
        if not self._path.exists():
            return []
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, ValueError):
            return []
        records = data.get("records") if isinstance(data, dict) else None
        return list(records) if isinstance(records, list) else []

    def save(self, records: List[dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": self._version, "records": list(records)}
        self._path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
