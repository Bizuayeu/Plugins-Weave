#!/usr/bin/env python3
"""
Path Resolver
=============

base_dir基準のパス解決
"""

from pathlib import Path
from typing import List, Optional

from domain.exceptions import ConfigError
from domain.types import ConfigData, as_dict
from infrastructure.config.error_messages import (
    config_invalid_value_message,
    config_key_missing_message,
    config_section_missing_message,
)

__all__ = ["PathResolver"]


class PathResolver:
    """パス解決クラス"""

    def __init__(self, config: ConfigData):
        """
        初期化

        Args:
            config: 設定辞書（ConfigData型）。base_dirは絶対パス必須。

        Raises:
            ConfigError: base_dirが絶対パスでない場合
        """
        self.config = config
        self._trusted_external_paths = self._parse_trusted_paths()
        self.base_dir = self._resolve_base_dir()

    def _parse_trusted_paths(self) -> List[Path]:
        """
        trusted_external_paths設定をパースして正規化

        Returns:
            正規化された信頼済み外部パスのリスト

        Raises:
            ConfigError: 相対パスが含まれている場合

        Note:
            - 空配列がデフォルト（セキュア）
            - チルダ展開（~）をサポート
            - 相対パスは禁止（絶対パスのみ）
        """
        raw_paths = self.config.get("trusted_external_paths", [])
        trusted: List[Path] = []

        for path_str in raw_paths:
            # チルダ展開
            expanded = Path(path_str).expanduser()

            # 相対パスは禁止
            if not expanded.is_absolute():
                raise ConfigError(
                    config_invalid_value_message(
                        "trusted_external_paths",
                        "absolute path",
                        f"'{path_str}' (relative paths not allowed)",
                    )
                )

            trusted.append(expanded.resolve())

        return trusted

    def _is_within_trusted_paths(self, resolved: Path) -> bool:
        """
        パスが信頼済み外部パス内にあるかチェック

        Args:
            resolved: チェック対象の解決済みパス

        Returns:
            信頼済みパス内であればTrue
        """
        for trusted_path in self._trusted_external_paths:
            try:
                resolved.relative_to(trusted_path)
                return True
            except ValueError:
                continue
        return False

    def _resolve_base_dir(self) -> Path:
        """
        base_dir設定を解釈して基準ディレクトリを返す

        base_dir設定値:
          - "~/path": ホームディレクトリからの絶対パス（チルダ展開）
          - "C:/path": 絶対パス（trusted_external_pathsで許可が必要）

        Returns:
            解決された基準ディレクトリのPath

        Raises:
            ConfigError: base_dirが絶対パスでない場合、
                         またはtrusted_external_paths外を指す場合

        Note:
            - 相対パスは禁止（絶対パスのみ）
            - チルダ展開（~）をサポート
            - trusted_external_pathsで明示的な許可が必要
        """
        base_dir_setting = self.config.get("base_dir", "")

        if not base_dir_setting:
            raise ConfigError(
                config_key_missing_message("base_dir")
            )

        # チルダ展開
        base_path = Path(base_dir_setting).expanduser()

        # 絶対パスチェック（チルダ展開後）
        if not base_path.is_absolute():
            raise ConfigError(
                config_invalid_value_message(
                    "base_dir",
                    "absolute path (e.g., '~/.claude/plugins/.episodicrag' or 'C:/path')",
                    f"'{base_dir_setting}' (relative paths not allowed)",
                )
            )

        resolved = base_path.resolve()

        # trusted_external_paths内かチェック（設定されている場合のみ）
        if self._trusted_external_paths and not self._is_within_trusted_paths(resolved):
            raise ConfigError(
                config_invalid_value_message(
                    "base_dir",
                    "path within trusted_external_paths",
                    f"'{base_dir_setting}' (resolves outside allowed paths)",
                )
            )

        return resolved

    def resolve_path(self, key: str) -> Path:
        """
        相対パスを絶対パスに解決（base_dir基準）

        Args:
            key: paths以下のキー（loops_dir, digests_dir, essences_dir）

        Returns:
            解決された絶対Path

        Raises:
            ConfigError: pathsセクションまたはキーが存在しない場合

        Example:
            >>> resolver = PathResolver(plugin_root, config)
            >>> resolver.resolve_path("loops_dir")
            Path("/data/Loops")
        """
        if "paths" not in self.config:
            raise ConfigError(config_section_missing_message("paths"))
        paths = as_dict(self.config["paths"])
        if key not in paths:
            raise ConfigError(config_key_missing_message(f"paths.{key}"))
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

        Example:
            >>> resolver.get_identity_file_path()
            Path("/data/identity.json")
        """
        identity_file = self.config.get("paths", {}).get("identity_file_path")

        if identity_file is None:
            return None

        return (self.base_dir / identity_file).resolve()
