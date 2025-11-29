#!/usr/bin/env python3
"""
Config Repository
=================

config.json の読み書き
"""

import json
from pathlib import Path

from .error_messages import file_not_found_message, invalid_json_message
from .exceptions import ConfigError
from .types import ConfigData


def load_config(config_file: Path) -> ConfigData:
    """
    設定読み込み

    Args:
        config_file: 設定ファイルのパス

    Returns:
        設定辞書（ConfigData型）

    Raises:
        ConfigError: 設定ファイルが見つからない、またはJSONパースに失敗した場合
    """
    if not config_file.exists():
        raise ConfigError(
            f"{file_not_found_message(config_file)}\n"
            "Run setup first: bash scripts/setup.sh"
        )

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(invalid_json_message(config_file, e)) from e
