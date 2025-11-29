#!/usr/bin/env python3
"""
Source Path Resolver
====================

レベル別ソースファイルディレクトリとパターンの解決を担当。

Usage:
    from config.source_path_resolver import SourcePathResolver

    resolver = SourcePathResolver(loops_path, level_path_service)
    source_dir = resolver.get_source_dir("weekly")
    pattern = resolver.get_source_pattern("weekly")
"""

from pathlib import Path

from .constants import LEVEL_CONFIG, LEVEL_NAMES, SOURCE_TYPE_LOOPS
from .exceptions import ConfigError

from .level_path_service import LevelPathService


class SourcePathResolver:
    """
    レベル別ソースパス解決クラス

    各レベルのダイジェスト生成に必要なソースファイルの
    ディレクトリとファイルパターンを解決する。

    Attributes:
        loops_path: Loopファイル配置ディレクトリ
        level_path_service: レベル別パスサービス
    """

    def __init__(self, loops_path: Path, level_path_service: LevelPathService):
        """
        初期化

        Args:
            loops_path: Loopファイル配置ディレクトリ
            level_path_service: レベル別パスサービス
        """
        self.loops_path = loops_path
        self.level_path_service = level_path_service

    def get_source_dir(self, level: str) -> Path:
        """
        指定レベルのソースファイルディレクトリを取得

        Args:
            level: ダイジェストレベル (weekly, monthly, quarterly, etc.)

        Returns:
            ソースファイルのディレクトリパス
            - weeklyの場合: loops_path
            - その他: 下位レベルのDigestディレクトリ

        Raises:
            ConfigError: 無効なlevelが指定された場合
        """
        if level not in LEVEL_CONFIG:
            raise ConfigError(
                f"Invalid level: '{level}'. Valid levels: {', '.join(LEVEL_NAMES)}"
            )

        source_type = str(LEVEL_CONFIG[level]["source"])

        if source_type == SOURCE_TYPE_LOOPS:
            return self.loops_path
        else:
            return self.level_path_service.get_level_dir(source_type)

    def get_source_pattern(self, level: str) -> str:
        """
        指定レベルのソースファイルパターンを取得

        Args:
            level: ダイジェストレベル (weekly, monthly, quarterly, etc.)

        Returns:
            ファイル検索パターン (例: "L*.txt", "W*.txt")

        Raises:
            ConfigError: 無効なlevelが指定された場合
        """
        if level not in LEVEL_CONFIG:
            raise ConfigError(
                f"Invalid level: '{level}'. Valid levels: {', '.join(LEVEL_NAMES)}"
            )

        source_type = str(LEVEL_CONFIG[level]["source"])

        if source_type == SOURCE_TYPE_LOOPS:
            return "L*.txt"
        else:
            source_prefix = str(LEVEL_CONFIG[source_type]["prefix"])
            return f"{source_prefix}*.txt"
