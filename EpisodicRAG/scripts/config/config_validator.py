#!/usr/bin/env python3
"""
Config Validator
================

設定とディレクトリ構造の検証を担当するクラス。
DirectoryValidator の機能を包含し、さらに設定検証機能を追加。

Usage:
    from config.config_validator import ConfigValidator

    validator = ConfigValidator(config, loops_path, digests_path, essences_path, level_path_service)
    errors = validator.validate_all()
    if errors:
        print("Validation errors:", errors)
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from domain.constants import LEVEL_CONFIG, LEVEL_NAMES
from domain.types import ConfigData

from .level_path_service import LevelPathService


class ConfigValidator:
    """
    設定とディレクトリ構造の検証を担当

    Single Responsibility: 設定値とディレクトリ構造の検証のみを担当。
    DirectoryValidator の機能を包含し、設定スキーマ検証を追加。

    Attributes:
        config: 検証対象の設定データ
        loops_path: Loopsディレクトリのパス
        digests_path: Digestsディレクトリのパス
        essences_path: Essencesディレクトリのパス
        level_path_service: レベルパスサービス
    """

    # 必須の設定キー
    REQUIRED_KEYS = ["loops_path", "digests_path", "essences_path"]

    # オプションの設定キー（型チェック用）
    OPTIONAL_KEYS_WITH_TYPES: Dict[str, type] = {
        "base_dir": str,
        "identity_file": str,
    }

    # 閾値キーと型
    THRESHOLD_KEYS = [
        "weekly_threshold",
        "monthly_threshold",
        "quarterly_threshold",
        "annual_threshold",
        "triennial_threshold",
        "decadal_threshold",
        "multi_decadal_threshold",
        "centurial_threshold",
    ]

    def __init__(
        self,
        config: ConfigData,
        loops_path: Path,
        digests_path: Path,
        essences_path: Path,
        level_path_service: Optional[LevelPathService] = None,
    ):
        """
        初期化

        Args:
            config: 検証対象の設定データ
            loops_path: Loopsディレクトリのパス
            digests_path: Digestsディレクトリのパス
            essences_path: Essencesディレクトリのパス
            level_path_service: レベルパスサービス（ディレクトリ検証用、省略可）
        """
        self.config = config
        self.loops_path = loops_path
        self.digests_path = digests_path
        self.essences_path = essences_path
        self.level_path_service = level_path_service

    def validate_all(self) -> List[str]:
        """
        全ての検証を実行

        Returns:
            エラーメッセージのリスト（問題がなければ空リスト）
        """
        errors: List[str] = []
        errors.extend(self.validate_required_keys())
        errors.extend(self.validate_paths())
        errors.extend(self.validate_thresholds())
        errors.extend(self.validate_directory_structure())
        return errors

    def validate_required_keys(self) -> List[str]:
        """
        必須キーの存在を検証

        Returns:
            エラーメッセージのリスト
        """
        errors: List[str] = []
        for key in self.REQUIRED_KEYS:
            if key not in self.config:
                errors.append(f"Required configuration key missing: '{key}'")
        return errors

    def validate_paths(self) -> List[str]:
        """
        パス設定の検証

        Returns:
            エラーメッセージのリスト
        """
        errors: List[str] = []

        # パス値が文字列であることを検証
        path_keys = ["loops_path", "digests_path", "essences_path", "base_dir", "identity_file"]
        for key in path_keys:
            if key in self.config:
                value = self.config[key]
                if not isinstance(value, str):
                    errors.append(
                        f"Invalid configuration value for '{key}': "
                        f"expected str, got {type(value).__name__}"
                    )

        return errors

    def validate_thresholds(self) -> List[str]:
        """
        閾値設定の検証

        Returns:
            エラーメッセージのリスト
        """
        errors: List[str] = []

        for key in self.THRESHOLD_KEYS:
            if key in self.config:
                value = self.config[key]
                if not isinstance(value, int):
                    errors.append(
                        f"Invalid configuration value for '{key}': "
                        f"expected int, got {type(value).__name__}"
                    )
                elif value < 1:
                    errors.append(
                        f"Invalid configuration value for '{key}': "
                        f"must be positive integer, got {value}"
                    )

        return errors

    def validate_directory_structure(self) -> List[str]:
        """
        ディレクトリ構造の検証

        期待される構造:
          - loops_path が存在
          - digests_path が存在
          - essences_path が存在
          - 各レベルディレクトリ (1_Weekly, 2_Monthly, ...) が存在
          - 各レベルディレクトリ内にProvisionalが存在

        Returns:
            エラーメッセージのリスト（問題がなければ空リスト）
        """
        errors: List[str] = []

        # 基本ディレクトリのチェック
        for path, name in [
            (self.loops_path, "Loops"),
            (self.digests_path, "Digests"),
            (self.essences_path, "Essences"),
        ]:
            if not path.exists():
                errors.append(f"{name} directory missing: {path}")

        # レベルディレクトリのチェック（level_path_service が提供された場合のみ）
        if self.level_path_service is not None:
            for level in LEVEL_NAMES:
                level_dir = self.level_path_service.get_level_dir(level)
                prov_dir = self.level_path_service.get_provisional_dir(level)

                if not level_dir.exists():
                    errors.append(f"{level} directory missing: {level_dir}")
                elif not prov_dir.exists():
                    # レベルディレクトリがある場合のみProvisionalをチェック
                    errors.append(f"{level} Provisional missing: {prov_dir}")

        return errors

    def validate_level_config(self, level: str) -> List[str]:
        """
        特定レベルの設定を検証

        Args:
            level: 検証対象のレベル名

        Returns:
            エラーメッセージのリスト
        """
        errors: List[str] = []

        if level not in LEVEL_CONFIG:
            errors.append(f"Unknown level: '{level}'")
            return errors

        level_config = LEVEL_CONFIG[level]

        # 必須フィールドの存在チェック
        required_fields = ["prefix", "digits", "dir", "source", "next"]
        for field in required_fields:
            if field not in level_config:
                errors.append(f"Level '{level}' missing required field: '{field}'")

        return errors

    def is_valid(self) -> bool:
        """
        設定が有効かどうかを簡易チェック

        Returns:
            全ての検証をパスした場合True
        """
        return len(self.validate_all()) == 0


# =============================================================================
# 後方互換性のためのエイリアス
# =============================================================================

# DirectoryValidator は ConfigValidator に統合されたが、
# 既存コードとの互換性のため DirectoryValidator としてもアクセス可能
DirectoryValidator = ConfigValidator
