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

    def __init__(self, plugin_root: Path, config: ConfigData):
        """
        初期化

        Args:
            plugin_root: Pluginルート
            config: 設定辞書（ConfigData型）
        """
        self.plugin_root = plugin_root
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
          - ".": プラグインルート自身（デフォルト）
          - "subdir": プラグインルート配下のサブディレクトリ
          - "~/path": ホームディレクトリからの絶対パス（チルダ展開）
          - "C:/path": 絶対パス（trusted_external_pathsで許可が必要）

        Returns:
            解決された基準ディレクトリのPath

        Raises:
            ConfigError: base_dirがplugin_rootまたはtrusted_external_paths外を指す場合

        Note:
            - plugin_root内は常に許可
            - plugin_root外はtrusted_external_pathsで明示的な許可が必要
            - チルダ展開（~）をサポート
        """
        base_dir_setting = self.config.get("base_dir", ".")

        # チルダ展開または絶対パスの処理
        base_path = Path(base_dir_setting).expanduser()
        if base_path.is_absolute():
            resolved = base_path.resolve()
        else:
            resolved = (self.plugin_root / base_dir_setting).resolve()

        plugin_root_resolved = self.plugin_root.resolve()

        # 1. まずplugin_root内かチェック
        try:
            resolved.relative_to(plugin_root_resolved)
            return resolved  # plugin_root内なのでOK
        except ValueError:
            pass  # plugin_root外 - 次のチェックへ

        # 2. trusted_external_paths内かチェック
        if self._is_within_trusted_paths(resolved):
            return resolved  # 信頼済み外部パス内なのでOK

        # 3. どちらにも該当しない場合はエラー
        raise ConfigError(
            config_invalid_value_message(
                "base_dir",
                "path within plugin root or trusted_external_paths",
                f"'{base_dir_setting}' (resolves outside allowed paths)",
            )
        )

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
        """
        identity_file = self.config.get("paths", {}).get("identity_file_path")

        if identity_file is None:
            return None

        return (self.base_dir / identity_file).resolve()
