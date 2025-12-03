#!/usr/bin/env python3
"""
DigestConfigBuilder - Builder Pattern for DigestConfig
=======================================================

DigestConfigのオプショナルなコンポーネント注入をサポートするBuilder。

## 使用デザインパターン

### Builder Pattern
複雑なオブジェクト（DigestConfig）の構築を段階的に行い、
オプショナルな依存性注入をサポートする。

### Fluent Interface
メソッドチェーンで読みやすいコードを実現。

## SOLID原則の実践

### OCP (Open/Closed Principle)
- 新しいコンポーネントを追加しても既存コードに影響なし
- with_*メソッドで拡張可能

### DIP (Dependency Inversion Principle)
- 具象クラスへの依存をBuilderに集約
- テスト時にモックを注入可能

Usage:
    # 標準的な使い方
    config = DigestConfigBuilder.build_default()

    # カスタムコンポーネント注入
    config = (
        DigestConfigBuilder()
        .with_plugin_root(Path("/custom/root"))
        .with_custom_loader(my_loader)
        .build()
    )
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from domain.exceptions import ConfigError
from infrastructure.config import ConfigLoader, PathResolver, find_plugin_root
from infrastructure.config.error_messages import initialization_failed_message

if TYPE_CHECKING:
    from application.config import DigestConfig


class DigestConfigBuilder:
    """
    DigestConfig のBuilder

    オプショナルな依存性注入と段階的な構築をサポート。

    Attributes:
        _plugin_root: カスタムPluginルート
        _config_loader: カスタムConfigLoader
        _path_resolver: カスタムPathResolver

    Example:
        # シンプルな使用法
        config = DigestConfigBuilder.build_default()

        # カスタム設定
        config = (
            DigestConfigBuilder()
            .with_plugin_root(Path("/my/plugin"))
            .build()
        )

        # テスト用モック注入
        config = (
            DigestConfigBuilder()
            .with_plugin_root(Path("/test"))
            .with_custom_loader(mock_loader)
            .build()
        )
    """

    def __init__(self) -> None:
        """Initialize builder with no configuration"""
        self._plugin_root: Optional[Path] = None
        self._config_loader: Optional[ConfigLoader] = None
        self._path_resolver: Optional[PathResolver] = None

    def with_plugin_root(self, path: Path) -> "DigestConfigBuilder":
        """
        Pluginルートを設定

        Args:
            path: Pluginルートパス

        Returns:
            self (fluent interface)
        """
        self._plugin_root = path
        return self

    def with_custom_loader(self, loader: ConfigLoader) -> "DigestConfigBuilder":
        """
        カスタムConfigLoaderを設定

        テスト時のモック注入に使用。

        Args:
            loader: カスタムConfigLoader

        Returns:
            self (fluent interface)
        """
        self._config_loader = loader
        return self

    def with_custom_path_resolver(self, resolver: PathResolver) -> "DigestConfigBuilder":
        """
        カスタムPathResolverを設定

        テスト時のモック注入に使用。

        Args:
            resolver: カスタムPathResolver

        Returns:
            self (fluent interface)
        """
        self._path_resolver = resolver
        return self

    def build(self) -> "DigestConfig":
        """
        DigestConfigを構築

        注入されたコンポーネントがあればそれを使用し、
        なければデフォルトを生成。

        Returns:
            構築されたDigestConfig

        Raises:
            ConfigError: 構築に失敗した場合
        """
        # 遅延インポート（循環参照回避）
        from application.config.config_validator import ConfigValidator
        from application.config.level_path_service import LevelPathService
        from application.config.source_path_resolver import SourcePathResolver
        from application.config.threshold_provider import ThresholdProvider

        try:
            # Plugin root 決定
            plugin_root = self._plugin_root
            if plugin_root is None:
                plugin_root = self._detect_plugin_root()

            config_file = plugin_root / ".claude-plugin" / "config.json"

            # ConfigLoader（カスタムまたはデフォルト）
            config_loader = self._config_loader
            if config_loader is None:
                config_loader = ConfigLoader(config_file)

            config = config_loader.load()

            # PathResolver（カスタムまたはデフォルト）
            path_resolver = self._path_resolver
            if path_resolver is None:
                path_resolver = PathResolver(plugin_root, config)

            # 他のコンポーネント構築
            threshold_provider = ThresholdProvider(config)
            level_path_service = LevelPathService(path_resolver.digests_path)
            source_path_resolver = SourcePathResolver(path_resolver.loops_path, level_path_service)
            config_validator = ConfigValidator(
                config,
                path_resolver.loops_path,
                path_resolver.digests_path,
                path_resolver.essences_path,
                level_path_service,
            )

            # DigestConfig インスタンス構築（内部構築）
            return self._create_digest_config(
                plugin_root=plugin_root,
                config_file=config_file,
                config_loader=config_loader,
                config=config,
                path_resolver=path_resolver,
                threshold_provider=threshold_provider,
                level_path_service=level_path_service,
                source_path_resolver=source_path_resolver,
                config_validator=config_validator,
            )

        except (PermissionError, OSError) as e:
            raise ConfigError(initialization_failed_message("configuration", e)) from e

    def _detect_plugin_root(self) -> Path:
        """Plugin root を自動検出"""
        try:
            current_file = Path(__file__).resolve()
        except NameError:
            raise FileNotFoundError("Cannot determine script location (__file__ not defined)")
        return find_plugin_root(current_file)

    def _create_digest_config(
        self,
        plugin_root: Path,
        config_file: Path,
        config_loader: ConfigLoader,
        config,
        path_resolver: PathResolver,
        threshold_provider,
        level_path_service,
        source_path_resolver,
        config_validator,
    ) -> "DigestConfig":
        """
        DigestConfigインスタンスを直接構築（コンストラクタをバイパス）

        Builder経由でのみ使用される内部メソッド。
        """
        from application.config import DigestConfig

        # object.__new__ で __init__ をスキップしてインスタンス作成
        instance = object.__new__(DigestConfig)

        # 属性を直接設定
        instance.plugin_root = plugin_root
        instance.config_file = config_file
        instance._config_loader = config_loader
        instance.config = config
        instance._path_resolver = path_resolver
        instance._threshold_provider = threshold_provider
        instance._level_path_service = level_path_service
        instance._source_path_resolver = source_path_resolver
        instance._config_validator = config_validator
        instance.base_dir = path_resolver.base_dir
        instance._directory_validator = config_validator  # 後方互換性

        return instance

    @classmethod
    def build_default(cls, plugin_root: Optional[Path] = None) -> "DigestConfig":
        """
        デフォルト設定でDigestConfigを構築

        標準的な使用法のための便利メソッド。

        Args:
            plugin_root: オプションのPluginルート（省略時は自動検出）

        Returns:
            構築されたDigestConfig

        Example:
            config = DigestConfigBuilder.build_default()
            config = DigestConfigBuilder.build_default(Path("/my/plugin"))
        """
        builder = cls()
        if plugin_root is not None:
            builder.with_plugin_root(plugin_root)
        return builder.build()
