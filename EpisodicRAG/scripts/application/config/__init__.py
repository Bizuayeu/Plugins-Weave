#!/usr/bin/env python3
"""
Application Config パッケージ
=============================

設定管理ユースケースを提供。DigestConfigがFacadeとして機能。

Usage:
    from application.config import DigestConfig

    config = DigestConfig()
    config.loops_path  # Path to loops directory
    config.threshold.weekly_threshold  # Weekly threshold value
"""

import logging
from pathlib import Path
from typing import List, Literal, Optional

from application.config.config_builder import DigestConfigBuilder
from application.config.config_validator import (
    ConfigValidator,
    DirectoryValidator,  # 後方互換
)
from application.config.level_path_service import LevelPathService
from application.config.source_path_resolver import SourcePathResolver
from application.config.threshold_provider import ThresholdProvider
from domain.exceptions import ConfigError
from domain.types import ConfigData
from infrastructure.config import ConfigLoader, PathResolver, find_plugin_root
from infrastructure.config.error_messages import initialization_failed_message

# Application Config専用logger
_logger = logging.getLogger("episodic_rag.config")

__all__ = [
    "DigestConfig",
    "DigestConfigBuilder",
    "ConfigValidator",
    "DirectoryValidator",
    "LevelPathService",
    "SourcePathResolver",
    "ThresholdProvider",
]


class DigestConfig:
    """
    設定管理クラス（Plugin自己完結版）- Facade

    薄い Facade として機能し、各コンポーネントに責任を委譲。
    後方互換性を維持しつつ、内部実装を分離。

    Design Pattern: Facade
        複雑なサブシステム（PathResolver, ThresholdProvider等）を
        単純なインターフェースで隠蔽。

    Components:
        - _config_loader: ConfigLoader - 設定ファイルの読み込み
        - _path_resolver: PathResolver - パス解決
        - _threshold_provider: ThresholdProvider - 閾値管理
        - _level_path_service: LevelPathService - レベル別パス管理
        - _source_path_resolver: SourcePathResolver - ソースパス解決
        - _config_validator: ConfigValidator - 設定とディレクトリ構造の検証
    """

    def __init__(self, plugin_root: Optional[Path] = None):
        """
        初期化

        Args:
            plugin_root: Pluginルート（省略時は自動検出）

        Raises:
            ConfigError: 設定の読み込みまたは初期化に失敗した場合
        """
        try:
            # Pluginルート検出
            if plugin_root is None:
                plugin_root = self._find_plugin_root()

            self.plugin_root = plugin_root
            self.config_file = self.plugin_root / ".claude-plugin" / "config.json"

            # ConfigLoader を使用して設定を読み込み
            self._config_loader = ConfigLoader(self.config_file)
            self.config = self._config_loader.load()

            # 各コンポーネントを即時初期化（軽量オブジェクトのため遅延不要）
            self._path_resolver = PathResolver(self.plugin_root, self.config)
            self._threshold_provider = ThresholdProvider(self.config)
            self._level_path_service = LevelPathService(self._path_resolver.digests_path)
            self._source_path_resolver = SourcePathResolver(
                self._path_resolver.loops_path, self._level_path_service
            )

            # ConfigValidator を使用（DirectoryValidator を統合）
            self._config_validator = ConfigValidator(
                self.config,
                self._path_resolver.loops_path,
                self._path_resolver.digests_path,
                self._path_resolver.essences_path,
                self._level_path_service,
            )

            # 後方互換性のためbase_dirを公開
            self.base_dir = self._path_resolver.base_dir

            # 後方互換性のため _directory_validator も公開（_config_validator へのエイリアス）
            self._directory_validator = self._config_validator

        except (PermissionError, OSError) as e:
            raise ConfigError(initialization_failed_message("configuration", e)) from e

    # =========================================================================
    # Context Manager Support
    # =========================================================================

    def __enter__(self) -> "DigestConfig":
        """Context Manager開始"""
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> Literal[False]:
        """Context Manager終了"""
        return False

    def _find_plugin_root(self) -> Path:
        """
        Plugin自身のルートディレクトリを検出

        Returns:
            PluginルートのPath

        Raises:
            FileNotFoundError: __file__が定義されていない場合、またはPluginルートが見つからない場合
        """
        try:
            current_file = Path(__file__).resolve()
        except NameError:
            raise FileNotFoundError("Cannot determine script location (__file__ not defined)")

        return find_plugin_root(current_file)

    def load_config(self) -> ConfigData:
        """設定読み込み"""
        return self._config_loader.load()

    def resolve_path(self, key: str) -> Path:
        """相対パスを絶対パスに解決（base_dir基準）"""
        return self._path_resolver.resolve_path(key)

    @property
    def loops_path(self) -> Path:
        """Loopファイル配置先"""
        return self._path_resolver.loops_path

    @property
    def digests_path(self) -> Path:
        """Digest出力先"""
        return self._path_resolver.digests_path

    @property
    def essences_path(self) -> Path:
        """GrandDigest配置先"""
        return self._path_resolver.essences_path

    def get_identity_file_path(self) -> Optional[Path]:
        """外部identityファイルのパス"""
        return self._path_resolver.get_identity_file_path()

    def get_level_dir(self, level: str) -> Path:
        """指定レベルのRegularDigest格納ディレクトリを取得"""
        return self._level_path_service.get_level_dir(level)

    def get_provisional_dir(self, level: str) -> Path:
        """指定レベルのProvisionalDigest格納ディレクトリを取得"""
        return self._level_path_service.get_provisional_dir(level)

    def get_source_dir(self, level: str) -> Path:
        """指定レベルのソースファイルディレクトリを取得"""
        return self._source_path_resolver.get_source_dir(level)

    def get_source_pattern(self, level: str) -> str:
        """指定レベルのソースファイルパターンを取得"""
        return self._source_path_resolver.get_source_pattern(level)

    def validate_directory_structure(self) -> List[str]:
        """ディレクトリ構造の検証"""
        return self._directory_validator.validate_directory_structure()

    # =========================================================================
    # コンポーネント公開プロパティ
    # =========================================================================

    @property
    def threshold(self) -> ThresholdProvider:
        """閾値プロバイダーへのアクセス"""
        return self._threshold_provider

    def get_threshold(self, level: str) -> int:
        """指定レベルのthresholdを動的に取得（後方互換性）"""
        return self._threshold_provider.get_threshold(level)

    def show_paths(self) -> None:
        """パス設定を表示（デバッグ用）"""
        _logger.info(f"プラグインルート: {self.plugin_root}")
        _logger.info(f"設定ファイル: {self.config_file}")
        _logger.info(f"ベースディレクトリ (設定値): {self.config.get('base_dir', '.')}")
        _logger.info(f"ベースディレクトリ (解決後): {self.base_dir}")
        _logger.info(f"Loopsパス: {self.loops_path}")
        _logger.info(f"Digestsパス: {self.digests_path}")
        _logger.info(f"Essencesパス: {self.essences_path}")

        identity_file = self.get_identity_file_path()
        if identity_file:
            _logger.info(f"Identityファイル: {identity_file}")
