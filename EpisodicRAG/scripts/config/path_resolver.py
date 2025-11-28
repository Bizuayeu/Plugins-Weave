#!/usr/bin/env python3
"""
Path Resolver
=============

base_dir基準のパス解決
"""

from pathlib import Path
from typing import Any, Dict, Optional, cast

from domain.exceptions import ConfigError
from domain.types import ConfigData, as_dict

__all__ = ["PathResolver"]


class PathResolver:
    """パス解決クラス"""

    def __init__(self, plugin_root: Path, config: ConfigData):
        """
        初期化

        Args:
            plugin_root: Pluginルート
            config: 設定辞書（ConfigData型）
        """
        self.plugin_root = plugin_root
        self.config = config
        self.base_dir = self._resolve_base_dir()

    def _resolve_base_dir(self) -> Path:
        """
        base_dir設定を解釈して基準ディレクトリを返す

        base_dir設定値（相対パスのみ）:
          - ".": プラグインルート自身（デフォルト）
          - "../../..": プラグインルートから3階層上
          - 任意の相対パス: プラグインルートからの相対パス

        Returns:
            解決された基準ディレクトリのPath

        Note:
            絶対パスは使用しない（Git公開時の可搬性のため）
        """
        base_dir_setting = self.config.get("base_dir", ".")
        return (self.plugin_root / base_dir_setting).resolve()

    def resolve_path(self, key: str) -> Path:
        """
        相対パスを絶対パスに解決（base_dir基準）

        Args:
            key: paths以下のキー（loops_dir, digests_dir, essences_dir）

        Returns:
            解決された絶対Path

        Raises:
            ConfigError: pathsセクションまたはキーが存在しない場合
        """
        if "paths" not in self.config:
            raise ConfigError("'paths' section missing in config.json")
        paths = as_dict(self.config["paths"])
        if key not in paths:
            raise ConfigError(f"Path key '{key}' not found in config.json")
        rel_path = str(paths[key])
        return (self.base_dir / rel_path).resolve()

    @property
    def loops_path(self) -> Path:
        """Loopファイル配置先"""
        return self.resolve_path("loops_dir")

    @property
    def digests_path(self) -> Path:
        """Digest出力先"""
        return self.resolve_path("digests_dir")

    @property
    def essences_path(self) -> Path:
        """GrandDigest配置先"""
        return self.resolve_path("essences_dir")

    def get_identity_file_path(self) -> Optional[Path]:
        """
        外部identityファイルのパス（設定されている場合のみ）

        Returns:
            identityファイルの絶対Path（設定されていない場合はNone）
        """
        identity_file = self.config.get("paths", {}).get("identity_file_path")

        if identity_file is None:
            return None

        return (self.base_dir / identity_file).resolve()
