#!/usr/bin/env python3
"""
Config Repository
=================

config.json の読み書き
"""

import json
from pathlib import Path

from domain.error_formatter import get_error_formatter
from domain.exceptions import ConfigError
from domain.types import ConfigData


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
    formatter = get_error_formatter()
    if not config_file.exists():
        raise ConfigError(
            f"{formatter.file.file_not_found(config_file)}\n"
            "Run setup first: bash scripts/setup.sh"
        )

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(formatter.file.invalid_json(config_file, e)) from e
