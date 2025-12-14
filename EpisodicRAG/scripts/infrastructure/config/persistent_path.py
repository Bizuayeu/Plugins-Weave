#!/usr/bin/env python3
"""
永続化パス解決ユーティリティ
============================

Claude Codeのプラグイン自動更新に影響されない永続化ディレクトリを提供。

## 背景

Claude Codeはプラグイン更新時に`~/.claude/plugins/marketplaces/`を
削除→再cloneするため、`.gitignore`に含まれるファイル（config.json等）が消失する。

## 解決策

永続化ファイルを`~/.claude/plugins/.episodicrag/`に保存。
このディレクトリはmarketplaces/外にあるため、auto-updateの影響を受けない。

Usage:
    from infrastructure.config.persistent_path import get_persistent_config_dir

    config_dir = get_persistent_config_dir()
    config_file = config_dir / "config.json"

    # テスト時は環境変数で上書き可能
    # EPISODICRAG_CONFIG_DIR=/path/to/test/config pytest ...
"""

import os
from pathlib import Path

from domain.file_constants import PERSISTENT_CONFIG_DIR_NAME

# テスト用環境変数名
PERSISTENT_CONFIG_ENV_VAR = "EPISODICRAG_CONFIG_DIR"


def get_persistent_config_dir() -> Path:
    """
    永続化設定ディレクトリを取得（なければ作成）

    Returns:
        Path: ~/.claude/plugins/.episodicrag のパス

    Note:
        - ディレクトリが存在しない場合は自動的に作成される
        - このディレクトリはClaude Codeのauto-update対象外
        - 環境変数EPISODICRAG_CONFIG_DIRで上書き可能（テスト用）
    """
    # 環境変数で上書き可能（テスト用）
    env_override = os.environ.get(PERSISTENT_CONFIG_ENV_VAR)
    if env_override:
        persistent_dir = Path(env_override)
        persistent_dir.mkdir(parents=True, exist_ok=True)
        return persistent_dir

    home = Path.home()
    persistent_dir = home / ".claude" / "plugins" / PERSISTENT_CONFIG_DIR_NAME
    persistent_dir.mkdir(parents=True, exist_ok=True)
    return persistent_dir
