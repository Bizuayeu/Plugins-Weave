# domain/constants.py
"""
定数定義

曜日マッピングなど、複数モジュールで使用される定数を一元管理する。
Clean Architecture の domain 層に配置し、外部依存なし。
"""
from __future__ import annotations

from typing import Final


# =============================================================================
# 曜日定数
# =============================================================================

# 有効な曜日の省略形セット（バリデーション用）
VALID_WEEKDAYS: Final[frozenset[str]] = frozenset({
    "mon", "tue", "wed", "thu", "fri", "sat", "sun"
})

# 曜日フルネームのリスト（順序保証用）
WEEKDAYS_FULL: Final[tuple[str, ...]] = (
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
)

# 曜日省略形のリスト（順序保証用）
WEEKDAYS_ABBR: Final[tuple[str, ...]] = (
    "mon", "tue", "wed", "thu", "fri", "sat", "sun"
)

# =============================================================================
# 曜日マッピング（Python weekday → 文字列）
# =============================================================================

# Python weekday番号 → 曜日省略形（0=月曜, 6=日曜）
WEEKDAY_NUM_TO_ABBR: Final[dict[int, str]] = {
    0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"
}

# 曜日省略形 → Python weekday番号
ABBR_TO_WEEKDAY_NUM: Final[dict[str, int]] = {
    "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6
}

# 曜日フルネーム → Python weekday番号
FULL_TO_WEEKDAY_NUM: Final[dict[str, int]] = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6
}

# =============================================================================
# Windows Task Scheduler 用マッピング
# =============================================================================

# 曜日省略形 → schtasks形式（大文字3文字）
ABBR_TO_SCHTASKS: Final[dict[str, str]] = {
    "mon": "MON", "tue": "TUE", "wed": "WED",
    "thu": "THU", "fri": "FRI", "sat": "SAT", "sun": "SUN"
}

# 曜日フルネーム → schtasks形式
FULL_TO_SCHTASKS: Final[dict[str, str]] = {
    "monday": "MON", "tuesday": "TUE", "wednesday": "WED",
    "thursday": "THU", "friday": "FRI", "saturday": "SAT", "sunday": "SUN"
}

# 序数 → schtasks週指定
ORDINAL_TO_SCHTASKS: Final[dict[int, str]] = {
    1: "FIRST", 2: "SECOND", 3: "THIRD", 4: "FOURTH"
}

# =============================================================================
# Unix cron 用マッピング
# =============================================================================

# 曜日省略形 → cron番号（0=日曜, 1=月曜, ...）
ABBR_TO_CRON: Final[dict[str, int]] = {
    "sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6
}

# 曜日フルネーム → cron番号
FULL_TO_CRON: Final[dict[str, int]] = {
    "sunday": 0, "monday": 1, "tuesday": 2, "wednesday": 3,
    "thursday": 4, "friday": 5, "saturday": 6
}


# =============================================================================
# ヘルパー関数
# =============================================================================

def weekday_to_python_num(weekday: str) -> int:
    """
    曜日文字列をPython weekday番号に変換する。

    Args:
        weekday: 曜日（省略形または完全形）

    Returns:
        Python weekday番号（0=月曜, 6=日曜）

    Raises:
        ValueError: 無効な曜日の場合
    """
    weekday_lower = weekday.lower()
    if weekday_lower in ABBR_TO_WEEKDAY_NUM:
        return ABBR_TO_WEEKDAY_NUM[weekday_lower]
    if weekday_lower in FULL_TO_WEEKDAY_NUM:
        return FULL_TO_WEEKDAY_NUM[weekday_lower]
    raise ValueError(f"Invalid weekday: {weekday}")


def weekday_to_schtasks(weekday: str) -> str:
    """
    曜日文字列をschtasks形式に変換する。

    Args:
        weekday: 曜日（省略形または完全形）

    Returns:
        schtasks形式（大文字3文字: MON, TUE, ...）

    Raises:
        ValueError: 無効な曜日の場合
    """
    weekday_lower = weekday.lower()
    if weekday_lower in ABBR_TO_SCHTASKS:
        return ABBR_TO_SCHTASKS[weekday_lower]
    if weekday_lower in FULL_TO_SCHTASKS:
        return FULL_TO_SCHTASKS[weekday_lower]
    raise ValueError(f"Invalid weekday: {weekday}")


def weekday_to_cron(weekday: str) -> int:
    """
    曜日文字列をcron番号に変換する。

    Args:
        weekday: 曜日（省略形または完全形）

    Returns:
        cron番号（0=日曜, 6=土曜）

    Raises:
        ValueError: 無効な曜日の場合
    """
    weekday_lower = weekday.lower()
    if weekday_lower in ABBR_TO_CRON:
        return ABBR_TO_CRON[weekday_lower]
    if weekday_lower in FULL_TO_CRON:
        return FULL_TO_CRON[weekday_lower]
    raise ValueError(f"Invalid weekday: {weekday}")


def ordinal_to_schtasks(ordinal: int) -> str:
    """
    序数をschtasks週指定に変換する。

    Args:
        ordinal: 序数（1-4）

    Returns:
        schtasks週指定（FIRST, SECOND, THIRD, FOURTH）

    Raises:
        ValueError: 無効な序数の場合
    """
    if ordinal not in ORDINAL_TO_SCHTASKS:
        raise ValueError(f"Invalid ordinal: {ordinal}. Must be 1-4.")
    return ORDINAL_TO_SCHTASKS[ordinal]
