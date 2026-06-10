"""WalLogStore の JSONL 実装。1 行 1 intent、append は O(1) 追記、破損行はスキップ。

`adapters/state/json_state_store.py` の単一ファイル + 親 mkdir + 破損フォールバックを
JSONL 用に踏襲する。git push は既存 `GitCliAdapter` を再利用（本 Adapter は I/O のみ）。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from adapters.atomic_io import load_jsonl, write_text_atomic
from domain.wal import WalEntry


class JsonlWalLogStore:
    """WAL ログを JSONL（1 行 1 WalEntry）で永続化する。

    - append: "a" モードで 1 行追記（ファイル全読込しない＝O(1)、追記は元来 atomic 寄りで
      クラッシュしても破損は末尾 1 行に閉じ、load の破損行スキップで吸収される）
    - load: 全行をパースし破損行はスキップ（`atomic_io.load_jsonl` に集約）
    - rewrite: checkpoint 後の entry 列でファイルを全置換（done 掃除の反映）。
      must-succeed 装置の全書換ゆえ `atomic_io.write_text_atomic`（tmp + os.replace）で
      書込中クラッシュの WAL 全損を構造的に排除する
    """

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def append(self, entry: WalEntry) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry.to_dict(), ensure_ascii=False)
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def load(self) -> List[WalEntry]:
        return load_jsonl(self._path, parse_line=WalEntry.from_dict)

    def rewrite(self, entries: List[WalEntry]) -> None:
        text = "".join(
            json.dumps(e.to_dict(), ensure_ascii=False) + "\n" for e in entries
        )
        write_text_atomic(self._path, text)
