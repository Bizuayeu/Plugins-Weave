#!/usr/bin/env python3
"""
File Naming Utilities
=====================

ファイル名のパース・フォーマットに関するドメインロジック

Usage:
    from domain.file_naming import extract_file_number, format_digest_number
    from domain.file_naming import find_max_number, filter_files_after

Note:
    このモジュールはLevelRegistryProtocolを使用してOCP (Open/Closed Principle) を実現。
    新しいレベル追加時にこのファイルの修正は不要。
    Protocol経由の依存関係逆転により、循環インポートを解消。
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple, Union

from domain.protocols import LevelRegistryProtocol

# Registry インスタンス（set_registry()で設定、未設定時は遅延インポートでフォールバック）
_registry_instance: Optional[LevelRegistryProtocol] = None


def set_registry(registry: LevelRegistryProtocol) -> None:
    """
    Registryを設定（アプリケーション起動時に呼び出し）

    Args:
        registry: LevelRegistryProtocolを満たすインスタンス

    Note:
        この関数を呼び出すことで、遅延インポートを回避できる。
        テスト時にモックを注入する際にも使用可能。
    """
    global _registry_instance
    _registry_instance = registry


def reset_registry() -> None:
    """
    Registryをリセット（テスト用）

    テスト間でRegistryの状態をクリアするために使用。
    """
    global _registry_instance
    _registry_instance = None


def _get_registry() -> LevelRegistryProtocol:
    """
    LevelRegistryProtocolを取得

    set_registry()で設定されたインスタンスを返す。
    未設定の場合は後方互換性のため遅延インポートでフォールバック。

    Returns:
        LevelRegistryProtocolインスタンス
    """
    global _registry_instance
    if _registry_instance is not None:
        return _registry_instance

    # フォールバック: 遅延インポート（後方互換性）
    from domain.level_registry import get_level_registry

    return get_level_registry()


def extract_file_number(
    filename: str,
    registry: Optional[LevelRegistryProtocol] = None,
) -> Optional[Tuple[str, int]]:
    """
    ファイル名からプレフィックスと番号を抽出

    Registry経由で動的にプレフィックスパターンを生成（OCP準拠）。

    Args:
        filename: ファイル名（例: "Loop0186_xxx.txt", "MD01_xxx.txt"）
        registry: オプショナルなLevelRegistryProtocol（DIによるテスト容易化）
                  未指定時はグローバルシングルトンを使用

    Returns:
        (prefix, number) のタプル、またはNone

    Examples:
        >>> extract_file_number("Loop0186_test.txt")
        ('Loop', 186)
        >>> extract_file_number("W0001_weekly.txt")
        ('W', 1)
        >>> extract_file_number("MD03_decadal.txt")
        ('MD', 3)
    """
    # 型チェック
    if not isinstance(filename, str):
        return None

    # Registry経由で動的にプレフィックスパターンを取得
    reg = registry if registry is not None else _get_registry()
    pattern = reg.build_prefix_pattern()

    match = re.search(rf"({pattern})(\d+)", filename)
    if match:
        return (match.group(1), int(match.group(2)))

    return None


def extract_number_only(filename: str) -> Optional[int]:
    """
    ファイル名から番号のみを抽出（後方互換性用）

    Args:
        filename: ファイル名

    Returns:
        番号、またはNone

    Examples:
        >>> extract_number_only("Loop0186_test.txt")
        186
    """
    result = extract_file_number(filename)
    return result[1] if result else None


def format_digest_number(
    level: str,
    number: int,
    registry: Optional[LevelRegistryProtocol] = None,
) -> str:
    """
    レベルと番号から統一されたフォーマットの文字列を生成

    Registry経由でStrategy patternを使用（OCP準拠）。

    Args:
        level: 階層名（"loop", "weekly", "monthly", ...）
        number: 番号
        registry: オプショナルなLevelRegistryProtocol（DIによるテスト容易化）
                  未指定時はグローバルシングルトンを使用

    Returns:
        ゼロ埋めされた文字列（例: "Loop0186", "W0001", "MD01"）

    Raises:
        ValueError: 不正なレベル名の場合

    Examples:
        >>> format_digest_number("loop", 186)
        'Loop0186'
        >>> format_digest_number("weekly", 1)
        'W0001'
        >>> format_digest_number("multi_decadal", 3)
        'MD03'
    """
    reg = registry if registry is not None else _get_registry()
    behavior = reg.get_behavior(level)
    return behavior.format_number(number)


def find_max_number(
    files: List[Union[Path, str]],
    prefix: str,
    registry: Optional[LevelRegistryProtocol] = None,
) -> Optional[int]:
    """
    ファイルリストから指定プレフィックスの最大番号を取得

    Args:
        files: ファイルパス（PathまたはStr）のリスト
        prefix: 検索するプレフィックス（例: "W", "Loop", "MD"）
        registry: オプショナルなLevelRegistryProtocol（DIによるテスト容易化）
                  未指定時はグローバルシングルトンを使用

    Returns:
        最大番号、またはマッチするファイルがない場合はNone

    Examples:
        >>> find_max_number(["W0001_a.txt", "W0003_b.txt"], "W")
        3
        >>> find_max_number(["M001_a.txt"], "W")
        None
    """
    if not files:
        return None

    max_num: Optional[int] = None

    for file in files:
        # PathオブジェクトまたはStringからファイル名を取得
        if isinstance(file, Path):
            filename = file.name
        elif isinstance(file, str):
            filename = Path(file).name if "/" in file or "\\" in file else file
        else:
            continue

        result = extract_file_number(filename, registry=registry)
        if result and result[0] == prefix:
            num = result[1]
            if max_num is None or num > max_num:
                max_num = num

    return max_num


def filter_files_after(files: List[Path], threshold: int) -> List[Path]:
    """
    閾値より大きい番号のファイルをフィルタ

    Args:
        files: ファイルパス（Path）のリスト
        threshold: この番号より大きいファイルを返す

    Returns:
        閾値より大きい番号のファイルリスト

    Examples:
        >>> filter_files_after([Path("Loop0001.txt"), Path("Loop0005.txt")], 2)
        [Path("Loop0005.txt")]
    """
    if not files:
        return []

    result = []
    for file in files:
        file_num = extract_number_only(file.name)
        if file_num is not None and file_num > threshold:
            result.append(file)

    return result


def extract_numbers_formatted(
    files: List[Union[str, None]],
    registry: Optional[LevelRegistryProtocol] = None,
) -> List[str]:
    """
    ファイル名リストからフォーマット済み番号リストを抽出

    各ファイル名からプレフィックスと番号を抽出し、
    Registry経由で統一フォーマットに変換（OCP準拠）。
    結果はソートされて返される。

    Args:
        files: ファイル名のリスト
        registry: オプショナルなLevelRegistryProtocol（DIによるテスト容易化）
                  未指定時はグローバルシングルトンを使用

    Returns:
        フォーマット済み番号のソート済みリスト（例: ["Loop0001", "Loop0002"]）

    Examples:
        >>> extract_numbers_formatted(["Loop0003_c.txt", "Loop0001_a.txt"])
        ["Loop0001", "Loop0003"]
    """
    if not files:
        return []

    reg = registry if registry is not None else _get_registry()

    numbers = []
    for file in files:
        # 型チェック
        if not isinstance(file, str):
            continue

        result = extract_file_number(file, registry=reg)
        if result:
            prefix, num = result
            # Registry経由でプレフィックスからレベルを逆引き
            level = reg.get_level_by_prefix(prefix)
            if level:
                behavior = reg.get_behavior(level)
                numbers.append(behavior.format_number(num))
            else:
                # 未知のプレフィックス: 元の形式を維持（フォールバック）
                numbers.append(f"{prefix}{num:04d}")

    return sorted(numbers)


__all__ = [
    "extract_file_number",
    "extract_number_only",
    "format_digest_number",
    "find_max_number",
    "filter_files_after",
    "extract_numbers_formatted",
    "set_registry",
    "reset_registry",
]
