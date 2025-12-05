#!/usr/bin/env python3
"""
Digest Validators
=================

ダイジェストデータのバリデーション関数。

cascade_processor.py と file_appender.py で重複していた
_is_valid_overall_digest を統合し、Single Source of Truth を実現。

Usage:
    from domain.validators import is_valid_overall_digest

    if is_valid_overall_digest(digest):
        # digest は OverallDigestData として型推論される
        digest["source_files"]  # List[str] - type narrowed by TypeGuard
"""

from typing import Any, TypeGuard

from domain.types import OverallDigestData


def is_valid_overall_digest(
    digest: Any,
    require_non_empty: bool = True,
) -> TypeGuard[OverallDigestData]:
    """
    overall_digestの有効性を検証（TypeGuard付き）

    cascade_processor.py と file_appender.py で重複していたロジックを統合。
    以前の実装の違い:
    - cascade_processor: dictかつsource_filesが存在かつ空でない
    - file_appender: dictかつsource_filesキーが存在

    統合後はrequire_non_emptyパラメータで動作を選択可能。
    デフォルトは True（より厳格な cascade_processor 相当の動作）。

    Args:
        digest: 検証対象のダイジェスト
        require_non_empty: Trueの場合、source_filesが空でないことも検証

    Returns:
        有効な場合True（TypeGuardによりOverallDigestData型として推論）

    Examples:
        >>> is_valid_overall_digest({"source_files": ["file1.txt"]})
        True
        >>> is_valid_overall_digest({"source_files": []})
        False  # require_non_empty=True (default)
        >>> is_valid_overall_digest({"source_files": []}, require_non_empty=False)
        True
        >>> is_valid_overall_digest(None)
        False
        >>> is_valid_overall_digest("not a dict")
        False
    """
    # dict型チェック
    if not isinstance(digest, dict):
        return False

    # source_filesキーの存在チェック
    if "source_files" not in digest:
        return False

    # 空でないことのチェック（オプション）
    if require_non_empty:
        source_files = digest.get("source_files", [])
        if not source_files:
            return False

    return True
