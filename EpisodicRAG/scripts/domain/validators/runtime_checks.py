#!/usr/bin/env python3
"""
Runtime Checks
==============

実行時チェック関数。assertの代替として使用。

Python の assert 文は -O フラグで無効化されるため、
本番コードでの制御フローには適さない。
この関数群は -O フラグの影響を受けず、常に実行される。

Usage:
    from domain.validators import ensure_not_none

    # Before (unsafe with -O flag):
    # assert value is not None

    # After (always safe):
    value = ensure_not_none(value, "config.base_dir")
"""

from typing import TypeVar

from domain.exceptions import ValidationError

T = TypeVar("T")


def ensure_not_none(value: T | None, context: str) -> T:
    """
    値がNoneでないことを保証（型ナローイング付き）

    assertの代替として使用。Python -O フラグでも無効化されない。
    バリデーション通過後の「契約」チェックに使用する。

    Args:
        value: チェック対象の値
        context: エラーメッセージに含める文脈情報

    Returns:
        Noneでないことが保証されたvalue（型がTにナローイング）

    Raises:
        ValidationError: valueがNoneの場合

    Examples:
        >>> ensure_not_none("hello", "greeting")
        'hello'
        >>> ensure_not_none(None, "config.base_dir")
        ValidationError: config.base_dir: expected non-None value

    Note:
        このエラーが発生する場合、通常はバグを示す。
        上流のバリデーションが正しく行われていれば、
        この関数でエラーになることはない。
    """
    if value is None:
        raise ValidationError(f"{context}: expected non-None value")
    return value
