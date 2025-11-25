#!/usr/bin/env python3
"""
Digest Plugin Configuration Manager
====================================

Plugin自己完結版：Plugin内の.claude-plugin/config.jsonから設定を読み込む
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class DigestConfig:
    """設定管理クラス（Plugin自己完結版）"""

    def __init__(self, plugin_root: Optional[Path] = None):
        """
        初期化

        Args:
            plugin_root: Pluginルート（省略時は自動検出）
        """
        # Pluginルート検出
        if plugin_root is None:
            plugin_root = self._find_plugin_root()

        self.plugin_root = plugin_root
        self.config_file = self.plugin_root / ".claude-plugin" / "config.json"
        self.config = self.load_config()
        self.base_dir = self._resolve_base_dir()

    def _find_plugin_root(self) -> Path:
        """
        Plugin自身のルートディレクトリを検出

        scripts/config.py から実行された場合:
          scripts/config.py の親（scripts/）の親（EpisodicRAG/）がPluginルート

        Returns:
            PluginルートのPath
        """
        # このファイル（config.py）の場所から相対的にPluginルートを検出
        current_file = Path(__file__).resolve()

        # scripts/config.py なので、2階層上がPluginルート
        plugin_root = current_file.parent.parent

        # .claude-plugin/config.json が存在するか確認
        if (plugin_root / ".claude-plugin" / "config.json").exists():
            return plugin_root

        # 見つからない場合はエラー
        raise FileNotFoundError(
            f"Plugin root not found. Expected .claude-plugin/config.json at: {plugin_root}"
        )

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

    def load_config(self) -> Dict[str, Any]:
        """
        設定読み込み

        Returns:
            設定辞書

        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
        """
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        raise FileNotFoundError(
            f"Config file not found: {self.config_file}\n"
            f"Run setup first: bash {self.plugin_root}/scripts/setup.sh"
        )

    def resolve_path(self, key: str) -> Path:
        """
        相対パスを絶対パスに解決（base_dir基準）

        Args:
            key: paths以下のキー（loops_dir, digests_dir, essences_dir）

        Returns:
            解決された絶対Path
        """
        rel_path = self.config["paths"][key]
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


    @property
    def weekly_threshold(self) -> int:
        """Weekly生成に必要なLoop数"""
        return self.config.get("levels", {}).get("weekly_threshold", 5)

    @property
    def monthly_threshold(self) -> int:
        """Monthly生成に必要なWeekly数"""
        return self.config.get("levels", {}).get("monthly_threshold", 5)

    @property
    def quarterly_threshold(self) -> int:
        """Quarterly生成に必要なMonthly数"""
        return self.config.get("levels", {}).get("quarterly_threshold", 3)

    @property
    def annual_threshold(self) -> int:
        """Annual生成に必要なQuarterly数"""
        return self.config.get("levels", {}).get("annual_threshold", 4)

    @property
    def triennial_threshold(self) -> int:
        """Triennial生成に必要なAnnual数"""
        return self.config.get("levels", {}).get("triennial_threshold", 3)

    @property
    def decadal_threshold(self) -> int:
        """Decadal生成に必要なTriennial数"""
        return self.config.get("levels", {}).get("decadal_threshold", 3)

    @property
    def multi_decadal_threshold(self) -> int:
        """Multi-decadal生成に必要なDecadal数"""
        return self.config.get("levels", {}).get("multi_decadal_threshold", 3)

    @property
    def centurial_threshold(self) -> int:
        """Centurial生成に必要なMulti-decadal数"""
        return self.config.get("levels", {}).get("centurial_threshold", 4)

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

    def show_paths(self):
        """パス設定を表示（デバッグ用）"""
        print(f"Plugin Root: {self.plugin_root}")
        print(f"Config File: {self.config_file}")
        print(f"Base Dir (setting): {self.config.get('base_dir', '.')}")
        print(f"Base Dir (resolved): {self.base_dir}")
        print(f"Loops Path: {self.loops_path}")
        print(f"Digests Path: {self.digests_path}")
        print(f"Essences Path: {self.essences_path}")

        identity_file = self.get_identity_file_path()
        if identity_file:
            print(f"Identity File: {identity_file}")


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
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
