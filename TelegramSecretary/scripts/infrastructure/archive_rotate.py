"""管理表の肥大化対策の純関数（エージェントが分割を判断する際に使う道具）。

- `partition_for_archive`: TASKS / INDIVIDUALS の日付 Archive 用（条件を満たすレコードを分離）
- `split_by_category`: KNOWLEDGE / ABILITIES のカテゴリ分割用（category ごとにシャード化、Archive せず蓄積）

いずれも純関数。**「いつ・どの単位で分割/archive するか」はエージェントの判断**（重要度の世界、DESIGN §3.5）——
本モジュールは決定論的な自動実行（subcommand）を持たず、エージェントが判断した分割の「計算」だけを担う。
実ファイルの移動・書き出しはエージェントが `JsonRegistryStore` と組み合わせて行う。
"""
from __future__ import annotations

from typing import Callable, Dict, List, Tuple


def partition_for_archive(
    records: List[dict], should_archive: Callable[[dict], bool]
) -> Tuple[List[dict], List[dict]]:
    """`should_archive` が True のレコードを archive 側へ分離。順序保持。

    返り値は `(keep, archive)`。keep を現役ファイル、archive を `archive/<NAME>_<YYYY-MM>.json` へ。
    """
    keep: List[dict] = []
    archive: List[dict] = []
    for r in records:
        (archive if should_archive(r) else keep).append(r)
    return keep, archive


def split_by_category(
    records: List[dict], category_key: str = "category", default: str = "general"
) -> Dict[str, List[dict]]:
    """`category` ごとに records をグループ化（KNOWLEDGE のシャード分割用）。

    category 欠落・空のレコードは `default`（"general"）に集約。各グループ内の順序は保持。
    """
    out: Dict[str, List[dict]] = {}
    for r in records:
        cat = r.get(category_key) or default
        out.setdefault(cat, []).append(r)
    return out
