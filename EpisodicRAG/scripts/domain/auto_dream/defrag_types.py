#!/usr/bin/env python3
"""
Defrag 型定義
=============

dream-defrag（引く dream＝memory GC）の決定論的「事実」を表す TypedDict 群。
外部依存なし。

設計方針:
    本モジュールは「決定論的に算出できる事実」（件数・閾値超過）と、
    「Claude が後で埋める候補の器」（DefragCandidate）のみを定義する。
    **何を重複/卒業/上位層DRY と見るかの判断ロジックは持たない**
    （判断は Claude=LLM がコマンドフロー内で行う＝archive は LLM タスクの原則）。

    既存 domain/auto_dream/types.py（AutoDreamScanResult 等）と対をなす:
    types.py が「足す dream」（auto_dream_scan の所在通知）、
    本モジュールが「引く dream」（dream-defrag の GC）の型を担う。

Usage:
    from domain.auto_dream.defrag_types import DEFRAG_THRESHOLD, DefragScanResult
"""

from typing import List, Literal, Optional, TypedDict

# =============================================================================
# 閾値
# =============================================================================

DEFRAG_THRESHOLD = 50
"""MEMORY.md の剪定（引く dream）を推奨するメモリ件数の閾値。

commands/digest.md Step 11 が「メモリ件数が 50 件を超えてくる場合、機械的
全件カバー方式への切り替えを再検討する」と名指した変曲点。
file_count がこれを **超える**（> 50）と over_threshold=True。
"""


# =============================================================================
# 剪定候補
# =============================================================================

DefragKind = Literal["dedup", "upper_dry", "graduate"]
"""剪定候補の3種別

dedup     — エントリ間の横断重複（統合対象）
upper_dry — 上位層（WeaveSupplement / CLAUDE.md 等）が定めるルールの再掲（削除対象）
graduate  — 完了プロジェクトの卒業（MEMORY.md live index から降格）
"""

VALID_DEFRAG_KINDS = {"dedup", "upper_dry", "graduate"}
"""DefragKind の検証用セット（VALID_MEMORY_TYPES と同型）"""


class DefragCandidate(TypedDict):
    """剪定候補1件（Claude が判断して埋める器）

    本型は「事実の入れ物」であり、検出ロジックは持たない。
    何を重複/卒業/上位層DRY と見るかの判断は Claude=LLM がコマンドフロー内で行い、
    その結論をこの構造で表現する（CLI/スクリプトは本型を自動生成しない）。

    Example:
        {
            "kind": "dedup",
            "targets": [
                "project_telegram_secretary.md",
                "project_secretary_plugin_port.md",
            ],
            "reason": "TelegramSecretary 関連の重複エントリを1件に統合",
        }
    """

    kind: DefragKind
    targets: List[str]  # 対象 memory ファイル名のリスト
    reason: str  # 候補とした理由（Claude が記述）


# =============================================================================
# スキャン結果
# =============================================================================


class DefragScanResult(TypedDict):
    """dream_defrag scan CLI の出力構造

    決定論的に算出できる「件数と閾値超過の事実」のみを表す。
    剪定候補（DefragCandidate）の検出はここに含めない（Claude の責務）。

    status:
        "ok"        — メモリ発見・件数集計成功
        "no_memory" — メモリディレクトリなし（自動スキップ用）
        "error"     — スキャン中にエラー
    """

    status: str  # "ok" | "no_memory" | "error"
    memory_dir: Optional[str]  # memory/ ディレクトリの絶対パス
    file_count: int  # memory ファイル数（MEMORY.md 自体は除く）
    over_threshold: bool  # file_count > DEFRAG_THRESHOLD
    threshold: int  # 適用された閾値（= DEFRAG_THRESHOLD）
    error: Optional[str]
