#!/usr/bin/env python3
"""
Config層専用の型定義
====================

Config層をDomain層から独立させるための型定義。
Domain層のtypes.pyからConfig関連の型のみを抽出。

Usage:
    from config.types import ConfigData, PathsConfigData, LevelsConfigData
    from config.types import as_dict, is_config_data
"""

from typing import Any, Dict, Optional, TypedDict, TypeGuard, cast

# =============================================================================
# 設定ファイルの型定義
# =============================================================================


class PathsConfigData(TypedDict, total=False):
    """
    config.json の paths セクション
    """

    loops_dir: str
    digests_dir: str
    essences_dir: str
    identity_file_path: Optional[str]


class LevelsConfigData(TypedDict, total=False):
    """
    config.json の levels セクション（threshold設定）
    """

    weekly_threshold: int
    monthly_threshold: int
    quarterly_threshold: int
    annual_threshold: int
    triennial_threshold: int
    decadal_threshold: int
    multi_decadal_threshold: int
    centurial_threshold: int


class ConfigData(TypedDict, total=False):
    """
    config.json の全体構造
    """

    base_dir: str
    paths: PathsConfigData
    levels: LevelsConfigData


# =============================================================================
# 型ユーティリティ関数
# =============================================================================


def as_dict(typed_dict: Any) -> Dict[str, Any]:
    """
    TypedDictを動的キーアクセス用にDict[str, Any]にキャスト。

    TypedDictは静的型チェックには優れるが、動的キーアクセス
    （例: data[level_name]）時にmypyが警告を出す。
    このヘルパーで意図を明確化する。

    Args:
        typed_dict: キャストするTypedDictインスタンス

    Returns:
        Dict[str, Any]としてキャストされた同じオブジェクト

    Example:
        >>> config: ConfigData = load_config()
        >>> levels = as_dict(config).get("levels", {})  # 動的アクセスOK
    """
    return cast(Dict[str, Any], typed_dict)


# =============================================================================
# TypeGuard関数（型安全な判定）
# =============================================================================


def is_config_data(data: Any) -> TypeGuard[ConfigData]:
    """
    ConfigData型かどうかを判定（型ガード）

    構造検証を行い、ネストされた型も確認する。

    Args:
        data: 判定対象のデータ

    Returns:
        ConfigData型であればTrue

    Example:
        >>> data = load_json(path)
        >>> if is_config_data(data):
        ...     # data は ConfigData として型推論される
        ...     print(data.get("base_dir"))
    """
    if not isinstance(data, dict):
        return False

    # pathsキーが存在する場合、dictであることを確認
    if "paths" in data and not isinstance(data["paths"], dict):
        return False

    # levelsキーが存在する場合、dictであることを確認
    if "levels" in data and not isinstance(data["levels"], dict):
        return False

    return True
