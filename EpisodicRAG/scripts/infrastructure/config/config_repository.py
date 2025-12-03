#!/usr/bin/env python3
"""
Config Repository
=================

config.json の読み書き
"""

import json
from pathlib import Path

from domain.exceptions import ConfigError
from domain.types import ConfigData
from infrastructure.config.error_messages import file_not_found_message, invalid_json_message


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
            f"{file_not_found_message(config_file)}\nRun setup first: bash scripts/setup.sh"
        )

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            data: ConfigData = json.load(f)
            return data
    except json.JSONDecodeError as e:
        raise ConfigError(invalid_json_message(config_file, e)) from e
