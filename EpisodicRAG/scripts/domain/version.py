#!/usr/bin/env python3
"""
EpisodicRAG バージョン定義
=========================

plugin.json からバージョンを動的に読み込む（SSoT）

SSoT (Single Source of Truth):
    バージョンは `.claude-plugin/plugin.json` の `version` フィールドが唯一の定義場所。
    このモジュールはそこから動的に読み込み、後方互換性のため `__version__` として公開。
"""

import json
from pathlib import Path


def _load_version_from_plugin_json() -> str:
    """
    plugin.json からバージョンを読み込む

    Returns:
        str: バージョン文字列（例: "3.0.0"）
             plugin.json が見つからない場合は "0.0.0"
    """
    # version.py → domain/ → scripts/ → EpisodicRAG/ → .claude-plugin/
    plugin_json = Path(__file__).parent.parent.parent / ".claude-plugin" / "plugin.json"

    if not plugin_json.exists():
        return "0.0.0"  # フォールバック

    try:
        data = json.loads(plugin_json.read_text(encoding="utf-8"))
        version = data.get("version", "0.0.0")
        return str(version) if version is not None else "0.0.0"
    except (json.JSONDecodeError, OSError):
        return "0.0.0"


# プラグインバージョン（plugin.json から動的読み込み - SSoT）
__version__ = _load_version_from_plugin_json()

# データフォーマットバージョン (GrandDigest, ShadowGrandDigest, RegularDigest用)
# プラグインバージョンとは独立して管理
DIGEST_FORMAT_VERSION = "1.0"
