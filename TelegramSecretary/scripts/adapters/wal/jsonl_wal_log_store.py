"""WalLogStore の JSONL 実装。1 行 1 intent、append は O(1) 追記、破損行はスキップ。

`adapters/state/json_state_store.py` の単一ファイル + 親 mkdir + 破損フォールバックを
JSONL 用に踏襲する。git push は既存 `GitCliAdapter` を再利用（本 Adapter は I/O のみ）。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from domain.wal import WalEntry


class JsonlWalLogStore:
    """WAL ログを JSONL（1 行 1 WalEntry）で永続化する。

    - append: "a" モードで 1 行追記（ファイル全読込しない＝O(1)）
    - load: 全行をパースし破損行はスキップ（`JsonOffsetStore` の破損フォールバックと同型）
    - rewrite: checkpoint 後の entry 列でファイルを全置換（done 掃除の反映）
    """

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def append(self, entry: WalEntry) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry.to_dict(), ensure_ascii=False)
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def load(self) -> List[WalEntry]:
        if not self._path.exists():
            return []
        entries: List[WalEntry] = []
        for raw in self._path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line:
                continue
            try:
                entries.append(WalEntry.from_dict(json.loads(line)))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue  # 破損行はスキップ（他行は読む＝JsonOffsetStore 同型の安全側）
        return entries

    def rewrite(self, entries: List[WalEntry]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        text = "".join(
            json.dumps(e.to_dict(), ensure_ascii=False) + "\n" for e in entries
        )
        self._path.write_text(text, encoding="utf-8")
