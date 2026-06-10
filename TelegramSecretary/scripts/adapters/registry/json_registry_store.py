"""管理表（INDIVIDUALS / TASKS / KNOWLEDGE）の JSON ファイル永続化 Adapter。

1 管理表 = 1 JSON ファイル（`{"version": N, "records": [...]}` 形式）。
`UseCase` 層が依存する `RegistryStore` Port（load/save）の実装。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from adapters.atomic_io import load_json_or_default, write_text_atomic


class JsonRegistryStore:
    """管理表 1 ファイルの load/save。

    - load: ファイルが無ければ `[]`、破損していても `[]` にフォールバック
    - save: 親ディレクトリを作成、`ensure_ascii=False` で日本語をそのまま保存。
      `atomic_io.write_text_atomic`（tmp + os.replace）で書く——truncate→write だと
      書込中クラッシュで破損→load() が []→次の add で 1 件だけの表が push され
      リモートへ伝播する silent wipe 経路になるため
    """

    def __init__(self, path: Path, version: int = 1) -> None:
        self._path = Path(path)  # str 渡しでも壊れない防御変換（wal/state store と統一）
        self._version = version

    def load(self) -> List[dict]:
        return load_json_or_default(self._path, parse=self._records_of, default=list)

    @staticmethod
    def _records_of(data: object) -> List[dict]:
        records = data.get("records") if isinstance(data, dict) else None
        return list(records) if isinstance(records, list) else []

    def save(self, records: List[dict]) -> None:
        payload = {"version": self._version, "records": list(records)}
        write_text_atomic(
            self._path, json.dumps(payload, ensure_ascii=False, indent=2)
        )
