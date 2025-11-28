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

    起点パスから祖先ディレクトリを順に検索し、
    .claude-plugin/config.json が存在するディレクトリを返す。

    Args:
        script_path: 起点となるスクリプトのパス

    Returns:
        PluginルートのPath

    Raises:
        FileNotFoundError: Pluginルートが見つからない場合
    """
    current = script_path.resolve()

    # 祖先ディレクトリを順に検索
    for ancestor in [current] + list(current.parents):
        plugin_marker = ancestor / ".claude-plugin" / "config.json"
        if plugin_marker.exists():
            return ancestor

    # 見つからない場合はエラー
    raise FileNotFoundError(
        f"Plugin root not found. No .claude-plugin/config.json in ancestors of: {script_path}"
    )
