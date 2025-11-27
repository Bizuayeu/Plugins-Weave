#!/usr/bin/env python3
"""
Digest Plugin Configuration Manager
====================================

Plugin自己完結版：Plugin内の.claude-plugin/config.jsonから設定を読み込む

Usage:
    # 推奨（新しいインポートパス）
    from domain.file_naming import extract_file_number, format_digest_number

    # 後方互換（従来のインポートパス）
    from config import extract_file_number, format_digest_number
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Domain層から定数をインポート（Single Source of Truth）
# 明示的な再エクスポート（ruff F401対応）
from domain.constants import DEFAULT_THRESHOLDS as DEFAULT_THRESHOLDS
from domain.constants import LEVEL_CONFIG as LEVEL_CONFIG
from domain.constants import LEVEL_NAMES as LEVEL_NAMES
from domain.constants import PLACEHOLDER_END as PLACEHOLDER_END
from domain.constants import PLACEHOLDER_LIMITS as PLACEHOLDER_LIMITS
from domain.constants import PLACEHOLDER_MARKER as PLACEHOLDER_MARKER
from domain.constants import PLACEHOLDER_SIMPLE as PLACEHOLDER_SIMPLE
from domain.constants import SOURCE_TYPE_LOOPS as SOURCE_TYPE_LOOPS
from domain.exceptions import ConfigError

# Domain層からファイル命名関数を再エクスポート（後方互換性）
# 明示的な再エクスポート（ruff F401対応）
from domain.file_naming import extract_file_number as extract_file_number
from domain.file_naming import extract_number_only as extract_number_only
from domain.file_naming import format_digest_number as format_digest_number
from domain.types import ConfigData as ConfigData
from domain.types import LevelConfigData as LevelConfigData

from .config_repository import load_config
from .directory_validator import DirectoryValidator
from .level_path_service import LevelPathService
from .path_resolver import PathResolver

# 分割されたモジュールをインポート
from .plugin_root_resolver import find_plugin_root
from .threshold_provider import ThresholdProvider

# =============================================================================
# DigestConfig クラス（Facade）
# =============================================================================


class DigestConfig:
    """設定管理クラス（Plugin自己完結版）- Facade"""

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
            self.config = self.load_config()

            # 各コンポーネントを初期化（遅延初期化用のキャッシュ）
            self._path_resolver = PathResolver(self.plugin_root, self.config)
            self._threshold_provider = ThresholdProvider(self.config)
            self._level_path_service_cache: Optional[LevelPathService] = None
            self._directory_validator_cache: Optional[DirectoryValidator] = None

            # 後方互換性のためbase_dirを公開
            self.base_dir = self._path_resolver.base_dir

        except (PermissionError, OSError) as e:
            raise ConfigError(f"Failed to initialize configuration: {e}") from e

    @property
    def _level_path_service(self) -> LevelPathService:
        """LevelPathServiceの遅延初期化"""
        if self._level_path_service_cache is None:
            self._level_path_service_cache = LevelPathService(self._path_resolver.digests_path)
        return self._level_path_service_cache

    @property
    def _directory_validator(self) -> DirectoryValidator:
        """DirectoryValidatorの遅延初期化"""
        if self._directory_validator_cache is None:
            self._directory_validator_cache = DirectoryValidator(
                self._path_resolver.loops_path,
                self._path_resolver.digests_path,
                self._path_resolver.essences_path,
                self._level_path_service,
            )
        return self._directory_validator_cache

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

    def load_config(self) -> Dict[str, Any]:
        """設定読み込み"""
        return load_config(self.config_file)

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

        source_type = LEVEL_CONFIG[level]["source"]

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
            ファイル検索パターン (例: "Loop*.txt", "W*.txt")

        Raises:
            ConfigError: 無効なlevelが指定された場合
        """
        if level not in LEVEL_CONFIG:
            raise ConfigError(f"Invalid level: {level}")

        source_type = LEVEL_CONFIG[level]["source"]

        if source_type == SOURCE_TYPE_LOOPS:
            return "Loop*.txt"
        else:
            source_prefix = LEVEL_CONFIG[source_type]["prefix"]
            return f"{source_prefix}*.txt"

    def validate_directory_structure(self) -> List[str]:
        """ディレクトリ構造の検証"""
        return self._directory_validator.validate_directory_structure()

    def get_threshold(self, level: str) -> int:
        """指定レベルのthresholdを動的に取得"""
        return self._threshold_provider.get_threshold(level)

    @property
    def weekly_threshold(self) -> int:
        """Weekly生成に必要なLoop数"""
        return self._threshold_provider.weekly_threshold

    @property
    def monthly_threshold(self) -> int:
        """Monthly生成に必要なWeekly数"""
        return self._threshold_provider.monthly_threshold

    @property
    def quarterly_threshold(self) -> int:
        """Quarterly生成に必要なMonthly数"""
        return self._threshold_provider.quarterly_threshold

    @property
    def annual_threshold(self) -> int:
        """Annual生成に必要なQuarterly数"""
        return self._threshold_provider.annual_threshold

    @property
    def triennial_threshold(self) -> int:
        """Triennial生成に必要なAnnual数"""
        return self._threshold_provider.triennial_threshold

    @property
    def decadal_threshold(self) -> int:
        """Decadal生成に必要なTriennial数"""
        return self._threshold_provider.decadal_threshold

    @property
    def multi_decadal_threshold(self) -> int:
        """Multi-decadal生成に必要なDecadal数"""
        return self._threshold_provider.multi_decadal_threshold

    @property
    def centurial_threshold(self) -> int:
        """Centurial生成に必要なMulti-decadal数"""
        return self._threshold_provider.centurial_threshold

    def show_paths(self):
        """パス設定を表示（デバッグ用）"""
        from infrastructure import log_info

        log_info(f"Plugin Root: {self.plugin_root}")
        log_info(f"Config File: {self.config_file}")
        log_info(f"Base Dir (setting): {self.config.get('base_dir', '.')}")
        log_info(f"Base Dir (resolved): {self.base_dir}")
        log_info(f"Loops Path: {self.loops_path}")
        log_info(f"Digests Path: {self.digests_path}")
        log_info(f"Essences Path: {self.essences_path}")

        identity_file = self.get_identity_file_path()
        if identity_file:
            log_info(f"Identity File: {identity_file}")


def main():
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
