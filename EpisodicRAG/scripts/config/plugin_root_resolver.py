#!/usr/bin/env python3
"""
Plugin Root Resolver
====================

Pluginルートディレクトリの検出
"""

from pathlib import Path


def find_plugin_root(script_path: Path) -> Path:
    """
    Plugin自身のルートディレクトリを検出

    scripts/config/plugin_root_resolver.py から実行された場合:
      このファイルの親（config/）の親（scripts/）の親（EpisodicRAG/）がPluginルート

    Args:
        script_path: 起点となるスクリプトのパス

    Returns:
        PluginルートのPath

    Raises:
        FileNotFoundError: Pluginルートが見つからない場合
    """
    # このファイル（plugin_root_resolver.py）の場所から相対的にPluginルートを検出
    current_file = script_path.resolve()

    # scripts/config/plugin_root_resolver.py なので、3階層上がPluginルート
    plugin_root = current_file.parent.parent.parent

    # .claude-plugin/config.json が存在するか確認
    if (plugin_root / ".claude-plugin" / "config.json").exists():
        return plugin_root

    # 見つからない場合はエラー
    raise FileNotFoundError(
        f"Plugin root not found. Expected .claude-plugin/config.json at: {plugin_root}"
    )
