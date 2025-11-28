#!/usr/bin/env python3
"""
Config Loader
=============

設定ファイルの読み込みと管理を担当するクラス。
config.json の読み込み、キャッシュ、アクセスを一元管理。

Usage:
    from config.config_loader import ConfigLoader

    loader = ConfigLoader(config_file)
    config = loader.load()
    value = loader.get("key", default="default_value")
"""

import json
from pathlib import Path
from typing import Any, List, Optional

from domain.error_formatter import get_error_formatter
from domain.exceptions import ConfigError
from domain.types import ConfigData, as_dict, is_config_data

from .config_constants import REQUIRED_CONFIG_KEYS


class ConfigLoader:
    """
    設定ファイルの読み込みと管理を担当

    Single Responsibility: 設定ファイルの読み込みとアクセスのみを担当。
    パス解決や検証は他のクラスに委譲。

    Attributes:
        config_file: 設定ファイルのパス
        _config: 読み込んだ設定データ（キャッシュ）
    """

    def __init__(self, config_file: Path):
        """
        初期化

        Args:
            config_file: 設定ファイルのパス
        """
        self.config_file = config_file
        self._config: Optional[ConfigData] = None

    def load(self) -> ConfigData:
        """
        設定ファイルを読み込む

        既に読み込み済みの場合はキャッシュを返す。
        強制再読み込みが必要な場合は reload() を使用。

        Returns:
            設定データ辞書

        Raises:
            ConfigError: 設定ファイルが見つからない、またはJSONパースに失敗した場合
        """
        if self._config is not None:
            return self._config

        self._config = self._load_from_file()
        return self._config

    def reload(self) -> ConfigData:
        """
        設定ファイルを強制的に再読み込み

        キャッシュをクリアして再読み込みを行う。

        Returns:
            設定データ辞書

        Raises:
            ConfigError: 設定ファイルが見つからない、またはJSONパースに失敗した場合
        """
        self._config = None
        return self.load()

    def _load_from_file(self) -> ConfigData:
        """
        ファイルから設定を読み込む（内部メソッド）

        Returns:
            設定データ辞書

        Raises:
            ConfigError: 設定ファイルが見つからない、またはJSONパースに失敗した場合
        """
        formatter = get_error_formatter()
        if not self.config_file.exists():
            raise ConfigError(
                f"{formatter.file.file_not_found(self.config_file)}\n"
                "Run setup first: bash scripts/setup.sh"
            )

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(formatter.file.invalid_json(self.config_file, e)) from e

        # 構造検証（TypeGuard）
        if not is_config_data(data):
            raise ConfigError(
                f"Invalid config structure in {self.config_file}: "
                "'paths' and 'levels' must be dict if present"
            )

        return data

    def get_config(self) -> ConfigData:
        """
        設定データを取得（load()のエイリアス）

        Returns:
            設定データ辞書
        """
        return self.load()

    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得

        Args:
            key: 設定キー
            default: キーが存在しない場合のデフォルト値

        Returns:
            設定値、またはデフォルト値
        """
        config = self.load()
        return config.get(key, default)

    def has_key(self, key: str) -> bool:
        """
        設定キーが存在するかチェック

        Args:
            key: 設定キー

        Returns:
            キーが存在する場合True
        """
        config = self.load()
        return key in config

    def get_required(self, key: str) -> Any:
        """
        必須の設定値を取得

        Args:
            key: 設定キー

        Returns:
            設定値

        Raises:
            ConfigError: キーが存在しない場合
        """
        config = self.load()
        # Use dict view for dynamic key access
        config_dict = as_dict(config)
        if key not in config_dict:
            formatter = get_error_formatter()
            raise ConfigError(formatter.config.config_key_missing(key))
        return config_dict[key]

    @property
    def is_loaded(self) -> bool:
        """
        設定が読み込み済みかどうか

        Returns:
            読み込み済みの場合True
        """
        return self._config is not None

    # 必須の設定キー（共通定数を参照）
    REQUIRED_KEYS = REQUIRED_CONFIG_KEYS

    def validate_required_keys(self) -> List[str]:
        """
        設定の必須キーを検証

        ConfigValidatorの包括的な検証とは別に、最低限の必須キー検証を提供。
        設定読み込み直後の軽量チェックに使用。

        Returns:
            エラーメッセージのリスト（問題がなければ空リスト）

        Example:
            errors = loader.validate_required_keys()
            if errors:
                raise ConfigError(f"Configuration errors: {errors}")
        """
        config = self.load()
        config_dict = as_dict(config)
        errors: List[str] = []
        for key in self.REQUIRED_KEYS:
            if key not in config_dict:
                errors.append(f"Required key missing: '{key}'")
        return errors
