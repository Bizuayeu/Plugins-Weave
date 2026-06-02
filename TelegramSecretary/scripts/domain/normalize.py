"""入力正規化と prompt injection フラグ（ブロックせず記録）。"""
from __future__ import annotations

import re
import unicodedata
from typing import List, Tuple


def normalize_input(text: str) -> str:
    """全角/半角・Unicode 異体字を NFKC 正規化し、サロゲートペアを安全化する。

    - NFKC: 全角英数→半角、合字分解、互換文字統一
    - サロゲート安全化: lone surrogate を 'replace' でフォールバック（JSON 経由の壊れた入力対策）
    """
    if not text:
        return text
    normalized = unicodedata.normalize("NFKC", text)
    # lone surrogate を UTF-8 round-trip で潰す。errors="replace" で破壊的だが安全
    safe = normalized.encode("utf-8", errors="replace").decode("utf-8")
    return safe


# Injection フラグ用パターン（フラグするだけでブロックしない）。
# OPS.md §7「フラグのみ・偽陽性回避」に従い、シグナル弱めにとどめる。
_INJECTION_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ("role_override", re.compile(r"(?i)\b(ignore|disregard|forget)\s+(previous|prior|all|the\s+above)")),
    ("system_prompt_request", re.compile(r"(?i)\bsystem\s+prompt\b")),
    ("role_assertion", re.compile(r"(?i)\byou\s+are\s+now\b|\b(role|act)\s+as\b")),
    ("credentials_request", re.compile(r"(?i)\b(api[\s_-]*key|access[\s_-]*token|password|secret)\b")),
]


def flag_injection(text: str) -> List[str]:
    """検知したパターン名のリストを返す。偽陽性は許容、フラグのみで処理側がブロック判断する。"""
    if not text:
        return []
    flags = []
    for name, pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            flags.append(name)
    return flags
