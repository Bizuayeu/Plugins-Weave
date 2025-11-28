#!/usr/bin/env python3
"""
Digest Plugin Configuration Manager
====================================

Plugin自己完結版：Plugin内の.claude-plugin/config.jsonから設定を読み込む

Architecture:
    DigestConfig は薄い Facade として機能し、以下のコンポーネントに委譲:
    - ConfigLoader: 設定ファイルの読み込み
    - PathResolver: パス解決
    - ThresholdProvider: 閾値管理
    - LevelPathService: レベル別パス管理
    - ConfigValidator: 設定とディレクトリ構造の検証

Usage:
    from config import DigestConfig
    from domain.file_naming import extract_file_number, format_digest_number
    from domain.types import ConfigData
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, List, Optional

# Config層専用logger（Infrastructure層に依存しない）
_logger = logging.getLogger("episodic_rag.config")

# Domain層からインポート
from domain.constants import (
    LEVEL_CONFIG,
    SOURCE_TYPE_LOOPS,
)
from domain.exceptions import ConfigError
from domain.types import ConfigData

# 内部コンポーネント
from .config_loader import ConfigLoader

# 後方互換性のため DirectoryValidator も公開（ConfigValidatorへのエイリアス）
from .config_validator import ConfigValidator
from .config_validator import DirectoryValidator as DirectoryValidator  # noqa: PLC0414
from .level_path_service import LevelPathService
from .path_resolver import PathResolver
from .plugin_root_resolver import find_plugin_root
from .threshold_provider import ThresholdProvider

# =============================================================================
# DigestConfig クラス（Facade）
# =============================================================================


class DigestConfig:
    """
    設定管理クラス（Plugin自己完結版）- Facade

    薄い Facade として機能し、各コンポーネントに責任を委譲。
    後方互換性を維持しつつ、内部実装を分離。

    Components:
        - _config_loader: ConfigLoader - 設定ファイルの読み込み
        - _path_resolver: PathResolver - パス解決
        - _threshold_provider: ThresholdProvider - 閾値管理
        - _level_path_service: LevelPathService - レベル別パス管理
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
            raise ConfigError(f"Failed to initialize configuration: {e}") from e

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
        """
        設定読み込み

        Returns:
            設定データ辞書

        Note:
            内部では ConfigLoader に委譲。reload が必要な場合は
            _config_loader.reload() を直接呼び出す。
        """
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
            raise ConfigError(f"Invalid level: {level}")

        source_type = str(LEVEL_CONFIG[level]["source"])

        if source_type == SOURCE_TYPE_LOOPS:
            return self.loops_path
        else:
            return self.get_level_dir(source_type)

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
            raise ConfigError(f"Invalid level: {level}")

        source_type = str(LEVEL_CONFIG[level]["source"])

        if source_type == SOURCE_TYPE_LOOPS:
            return "L*.txt"
        else:
            source_prefix = str(LEVEL_CONFIG[source_type]["prefix"])
            return f"{source_prefix}*.txt"

    def validate_directory_structure(self) -> List[str]:
        """ディレクトリ構造の検証"""
        return self._directory_validator.validate_directory_structure()

    def get_threshold(self, level: str) -> int:
        """指定レベルのthresholdを動的に取得"""
        return self._threshold_provider.get_threshold(level)

    def __getattr__(self, name: str) -> Any:
        """
        動的なthresholdプロパティアクセス

        例: config.weekly_threshold -> _threshold_provider.weekly_threshold

        サポートするプロパティ:
            - weekly_threshold, monthly_threshold, quarterly_threshold
            - annual_threshold, triennial_threshold, decadal_threshold
            - multi_decadal_threshold, centurial_threshold

        Args:
            name: アトリビュート名

        Returns:
            threshold値

        Raises:
            AttributeError: 無効なアトリビュート名の場合
        """
        if name.endswith("_threshold"):
            # ThresholdProviderに委譲
            return getattr(self._threshold_provider, name)
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

    def show_paths(self) -> None:
        """パス設定を表示（デバッグ用）"""
        _logger.info(f"Plugin Root: {self.plugin_root}")
        _logger.info(f"Config File: {self.config_file}")
        _logger.info(f"Base Dir (setting): {self.config.get('base_dir', '.')}")
        _logger.info(f"Base Dir (resolved): {self.base_dir}")
        _logger.info(f"Loops Path: {self.loops_path}")
        _logger.info(f"Digests Path: {self.digests_path}")
        _logger.info(f"Essences Path: {self.essences_path}")

        identity_file = self.get_identity_file_path()
        if identity_file:
            _logger.info(f"Identity File: {identity_file}")


def main() -> None:
    """CLI エントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="Digest Plugin Configuration Manager")
    parser.add_argument("--show-paths", action="store_true", help="Show all configured paths")
    parser.add_argument("--plugin-root", type=Path, help="Override plugin root")

    args = parser.parse_args()

    try:
        config = DigestConfig(plugin_root=args.plugin_root)

        if args.show_paths:
            config.show_paths()
        else:
            # デフォルト: JSON出力
            print(json.dumps(config.config, indent=2, ensure_ascii=False))

    except FileNotFoundError as e:
        # 循環インポートを避けるため直接出力
        sys.stderr.write(f"[ERROR] {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
