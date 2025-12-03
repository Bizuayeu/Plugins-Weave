#!/usr/bin/env python3
"""
EpisodicRAG TypeGuard関数
=========================

型安全な判定関数。
"""

from typing import Any, TypeGuard

from domain.types.config import ConfigData
from domain.types.digest import ShadowDigestData
from domain.types.level import LevelConfigData
from domain.types.text import LongShortText


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

    # trusted_external_pathsキーが存在する場合、listであることを確認
    if "trusted_external_paths" in data and not isinstance(data["trusted_external_paths"], list):
        return False

    return True


def is_level_config_data(data: Any) -> TypeGuard[LevelConfigData]:
    """
    LevelConfigData型かどうかを判定（型ガード）

    Args:
        data: 判定対象のデータ

    Returns:
        LevelConfigData型であればTrue（必須キーがすべて存在）

    Example:
        >>> level_data = LEVEL_CONFIG.get("weekly")
        >>> if is_level_config_data(level_data):
        ...     # level_data は LevelConfigData として型推論される
        ...     print(level_data["prefix"])
    """
    if not isinstance(data, dict):
        return False
    required_keys = {"prefix", "digits", "dir", "source", "next"}
    return required_keys <= data.keys()


def is_shadow_digest_data(data: Any) -> TypeGuard[ShadowDigestData]:
    """
    ShadowDigestData型かどうかを判定（型ガード）

    Args:
        data: 判定対象のデータ

    Returns:
        ShadowDigestData型であればTrue（必須キーがすべて存在）

    Example:
        >>> shadow_data = load_json(shadow_path)
        >>> if is_shadow_digest_data(shadow_data):
        ...     # shadow_data は ShadowDigestData として型推論される
        ...     print(shadow_data["metadata"])
    """
    if not isinstance(data, dict):
        return False
    required_keys = {"metadata", "latest_digests"}
    return required_keys <= data.keys()


def is_long_short_text(value: Any) -> TypeGuard[LongShortText]:
    """
    LongShortText型かどうかを判定（型ガード）

    Args:
        value: 判定対象のデータ

    Returns:
        LongShortText型であればTrue（long, shortキーが存在し、値が文字列）

    Example:
        >>> text = {"long": "詳細な要約...", "short": "簡潔な要約"}
        >>> if is_long_short_text(text):
        ...     # text は LongShortText として型推論される
        ...     print(text["long"])
    """
    if not isinstance(value, dict):
        return False
    if "long" not in value or "short" not in value:
        return False
    return isinstance(value["long"], str) and isinstance(value["short"], str)
