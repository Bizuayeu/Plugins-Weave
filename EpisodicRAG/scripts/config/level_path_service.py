#!/usr/bin/env python3
"""
Level Path Service
==================

レベル固有パス（level_dir, provisional_dir）
"""

from pathlib import Path

from domain.constants import LEVEL_CONFIG, LEVEL_NAMES
from domain.exceptions import ConfigError


class LevelPathService:
    """レベル固有パスサービス"""

    def __init__(self, digests_path: Path):
        """
        初期化

        Args:
            digests_path: Digestsディレクトリのパス
        """
        self.digests_path = digests_path

    def get_level_dir(self, level: str) -> Path:
        """
        指定レベルのRegularDigest格納ディレクトリを取得

        Args:
            level: 階層名（weekly, monthly, ...）

        Returns:
            RegularDigest格納ディレクトリの絶対Path

        Raises:
            ConfigError: 不正なレベル名の場合
        """
        if level not in LEVEL_CONFIG:
            raise ConfigError(f"Invalid level: {level}. Valid levels: {LEVEL_NAMES}")
        return self.digests_path / str(LEVEL_CONFIG[level]["dir"])

    def get_provisional_dir(self, level: str) -> Path:
        """
        指定レベルのProvisionalDigest格納ディレクトリを取得

        Args:
            level: 階層名（weekly, monthly, ...）

        Returns:
            ProvisionalDigest格納ディレクトリの絶対Path
            例: digests_path/1_Weekly/Provisional

        Raises:
            ValueError: 不正なレベル名の場合
        """
        return self.get_level_dir(level) / "Provisional"
