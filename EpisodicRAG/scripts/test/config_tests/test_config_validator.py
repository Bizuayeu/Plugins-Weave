#!/usr/bin/env python3
"""
ConfigValidator ユニットテスト
==============================

config_validator.py のユニットテスト。
ConfigValidatorクラスの動作を検証:
- validate_required_keys: 必須キーの存在検証
- validate_paths: パス設定の型検証
- validate_thresholds: 閾値設定の検証
- validate_directory_structure: ディレクトリ構造の検証
- validate_level_config: レベル設定の検証
- validate_all / is_valid: 統合検証
"""

from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Dict, List, Tuple

    from test_helpers import TempPluginEnvironment

    from application.config import DigestConfig
    from application.grand import GrandDigestManager, ShadowGrandDigestManager
    from application.shadow import FileDetector, ShadowIO, ShadowTemplate
    from application.shadow.placeholder_manager import PlaceholderManager
    from application.tracking import DigestTimesTracker
    from domain.types.level import LevelHierarchyEntry


import pytest

from application.config.config_validator import ConfigValidator, DirectoryValidator
from application.config.level_path_service import LevelPathService
from domain.types import ConfigData

# =============================================================================
# フィクスチャ
# =============================================================================


@pytest.fixture
def valid_config() -> ConfigData:
    """有効な設定データ"""
    return cast(
        ConfigData,
        {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None,
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
            },
            "loops_path": "data/Loops",
            "digests_path": "data/Digests",
            "essences_path": "data/Essences",
        },
    )


@pytest.fixture
def validator_with_env(temp_plugin_env: "TempPluginEnvironment", valid_config):
    """テスト環境付きのConfigValidator"""
    level_path_service = LevelPathService(temp_plugin_env.digests_path)
    return ConfigValidator(
        config=valid_config,
        loops_path=temp_plugin_env.loops_path,
        digests_path=temp_plugin_env.digests_path,
        essences_path=temp_plugin_env.essences_path,
        level_path_service=level_path_service,
    )


@pytest.fixture
def validator_without_level_service(temp_plugin_env: "TempPluginEnvironment", valid_config):
    """LevelPathServiceなしのConfigValidator"""
    return ConfigValidator(
        config=valid_config,
        loops_path=temp_plugin_env.loops_path,
        digests_path=temp_plugin_env.digests_path,
        essences_path=temp_plugin_env.essences_path,
        level_path_service=None,
    )


# =============================================================================
# TestConfigValidatorInit - 初期化テスト
# =============================================================================


class TestConfigValidatorInit:
    """ConfigValidatorの初期化テスト"""

    @pytest.mark.unit
    def test_init_with_all_parameters(
        self, temp_plugin_env: "TempPluginEnvironment", valid_config
    ) -> None:
        """全パラメータで初期化できる"""
        level_path_service = LevelPathService(temp_plugin_env.digests_path)
        validator = ConfigValidator(
            config=valid_config,
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
            level_path_service=level_path_service,
        )
        assert validator.config == valid_config
        assert validator.loops_path == temp_plugin_env.loops_path
        assert validator.digests_path == temp_plugin_env.digests_path
        assert validator.essences_path == temp_plugin_env.essences_path
        assert validator.level_path_service == level_path_service

    @pytest.mark.unit
    def test_init_without_level_path_service(
        self, temp_plugin_env: "TempPluginEnvironment", valid_config
    ) -> None:
        """LevelPathServiceなしで初期化できる"""
        validator = ConfigValidator(
            config=valid_config,
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
        )
        assert validator.level_path_service is None


# =============================================================================
# TestValidateRequiredKeys - 必須キー検証テスト
# =============================================================================


class TestValidateRequiredKeys:
    """必須キー検証のテスト"""

    @pytest.mark.unit
    def test_valid_config_has_no_errors(self, validator_with_env) -> None:
        """有効な設定では必須キーエラーなし"""
        errors = validator_with_env.validate_required_keys()
        assert len(errors) == 0

    @pytest.mark.unit
    def test_missing_loops_path_key(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """loops_pathキーがない場合エラー"""
        config = cast(
            ConfigData,
            {
                "base_dir": ".",
                # "loops_path" is missing
                "digests_path": "data/Digests",
                "essences_path": "data/Essences",
            },
        )
        validator = ConfigValidator(
            config=config,
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
        )
        errors = validator.validate_required_keys()
        assert any("loops_path" in e for e in errors)

    @pytest.mark.unit
    def test_missing_digests_path_key(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """digests_pathキーがない場合エラー"""
        config = cast(
            ConfigData,
            {
                "base_dir": ".",
                "loops_path": "data/Loops",
                # "digests_path" is missing
                "essences_path": "data/Essences",
            },
        )
        validator = ConfigValidator(
            config=config,
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
        )
        errors = validator.validate_required_keys()
        assert any("digests_path" in e for e in errors)

    @pytest.mark.unit
    def test_empty_config_has_multiple_errors(
        self, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """空の設定では複数のエラー"""
        config = cast(ConfigData, {})
        validator = ConfigValidator(
            config=config,
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
        )
        errors = validator.validate_required_keys()
        assert len(errors) >= 2  # paths, levels が必要


# =============================================================================
# TestValidatePaths - パス検証テスト
# =============================================================================


class TestValidatePaths:
    """パス設定検証のテスト"""

    @pytest.mark.unit
    def test_valid_paths_no_errors(self, validator_with_env) -> None:
        """有効なパス設定ではエラーなし"""
        errors = validator_with_env.validate_paths()
        assert len(errors) == 0

    @pytest.mark.unit
    def test_invalid_path_type_int(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """パスが整数の場合エラー"""
        config = cast(
            ConfigData,
            {
                "paths": {"loops_dir": "data/Loops"},
                "levels": {"weekly_threshold": 5},
                "loops_path": 123,  # Invalid type
                "digests_path": "data/Digests",
                "essences_path": "data/Essences",
            },
        )
        validator = ConfigValidator(
            config=config,
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
        )
        errors = validator.validate_paths()
        assert any("loops_path" in e for e in errors)

    @pytest.mark.unit
    def test_invalid_path_type_list(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """パスがリストの場合エラー"""
        config = cast(
            ConfigData,
            {
                "paths": {"loops_dir": "data/Loops"},
                "levels": {"weekly_threshold": 5},
                "loops_path": "data/Loops",
                "digests_path": ["invalid", "list"],  # Invalid type
                "essences_path": "data/Essences",
            },
        )
        validator = ConfigValidator(
            config=config,
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
        )
        errors = validator.validate_paths()
        assert any("digests_path" in e for e in errors)


# =============================================================================
# TestValidateThresholds - 閾値検証テスト
# =============================================================================


class TestValidateThresholds:
    """閾値設定検証のテスト"""

    @pytest.mark.unit
    def test_valid_thresholds_no_errors(self, validator_with_env) -> None:
        """有効な閾値設定ではエラーなし"""
        errors = validator_with_env.validate_thresholds()
        assert len(errors) == 0

    @pytest.mark.unit
    def test_threshold_zero_is_invalid(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """閾値0は無効"""
        config = cast(
            ConfigData,
            {
                "paths": {"loops_dir": "data/Loops"},
                "levels": {"weekly_threshold": 5},
                "weekly_threshold": 0,  # Invalid: must be positive
            },
        )
        validator = ConfigValidator(
            config=config,
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
        )
        errors = validator.validate_thresholds()
        assert any("weekly_threshold" in e and "positive" in e for e in errors)

    @pytest.mark.unit
    def test_threshold_negative_is_invalid(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """負の閾値は無効"""
        config = cast(
            ConfigData,
            {
                "paths": {"loops_dir": "data/Loops"},
                "levels": {"weekly_threshold": 5},
                "monthly_threshold": -5,  # Invalid: negative
            },
        )
        validator = ConfigValidator(
            config=config,
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
        )
        errors = validator.validate_thresholds()
        assert any("monthly_threshold" in e for e in errors)

    @pytest.mark.unit
    def test_threshold_string_is_invalid(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """文字列の閾値は無効"""
        config = cast(
            ConfigData,
            {
                "paths": {"loops_dir": "data/Loops"},
                "levels": {"weekly_threshold": 5},
                "quarterly_threshold": "five",  # Invalid: string
            },
        )
        validator = ConfigValidator(
            config=config,
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
        )
        errors = validator.validate_thresholds()
        assert any("quarterly_threshold" in e for e in errors)


# =============================================================================
# TestValidateDirectoryStructure - ディレクトリ構造検証テスト
# =============================================================================


class TestValidateDirectoryStructure:
    """ディレクトリ構造検証のテスト"""

    @pytest.mark.unit
    def test_valid_structure_no_errors(self, validator_with_env) -> None:
        """有効なディレクトリ構造ではエラーなし"""
        errors = validator_with_env.validate_directory_structure()
        assert len(errors) == 0

    @pytest.mark.unit
    def test_missing_loops_directory(
        self, temp_plugin_env: "TempPluginEnvironment", valid_config
    ) -> None:
        """Loopsディレクトリがない場合エラー"""
        # 存在しないパスを指定
        missing_path = temp_plugin_env.plugin_root / "nonexistent_loops"
        validator = ConfigValidator(
            config=valid_config,
            loops_path=missing_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
        )
        errors = validator.validate_directory_structure()
        assert any("Loops directory missing" in e for e in errors)

    @pytest.mark.unit
    def test_missing_digests_directory(
        self, temp_plugin_env: "TempPluginEnvironment", valid_config
    ) -> None:
        """Digestsディレクトリがない場合エラー"""
        missing_path = temp_plugin_env.plugin_root / "nonexistent_digests"
        validator = ConfigValidator(
            config=valid_config,
            loops_path=temp_plugin_env.loops_path,
            digests_path=missing_path,
            essences_path=temp_plugin_env.essences_path,
        )
        errors = validator.validate_directory_structure()
        assert any("Digests directory missing" in e for e in errors)

    @pytest.mark.unit
    def test_missing_essences_directory(
        self, temp_plugin_env: "TempPluginEnvironment", valid_config
    ) -> None:
        """Essencesディレクトリがない場合エラー"""
        missing_path = temp_plugin_env.plugin_root / "nonexistent_essences"
        validator = ConfigValidator(
            config=valid_config,
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=missing_path,
        )
        errors = validator.validate_directory_structure()
        assert any("Essences directory missing" in e for e in errors)

    @pytest.mark.unit
    def test_skips_level_check_without_service(self, validator_without_level_service) -> None:
        """LevelPathServiceがない場合、レベルディレクトリチェックをスキップ"""
        errors = validator_without_level_service.validate_directory_structure()
        # 基本ディレクトリのみチェック、レベルディレクトリはスキップ
        level_errors = [e for e in errors if "weekly" in e.lower() or "monthly" in e.lower()]
        assert len(level_errors) == 0


# =============================================================================
# TestValidateLevelConfig - レベル設定検証テスト
# =============================================================================


class TestValidateLevelConfig:
    """レベル設定検証のテスト"""

    @pytest.mark.unit
    def test_valid_level_no_errors(self, validator_with_env) -> None:
        """有効なレベルではエラーなし"""
        errors = validator_with_env.validate_level_config("weekly")
        assert len(errors) == 0

    @pytest.mark.unit
    def test_unknown_level_returns_error(self, validator_with_env) -> None:
        """不明なレベルはエラー"""
        errors = validator_with_env.validate_level_config("unknown_level")
        assert any("Unknown level" in e for e in errors)

    @pytest.mark.unit
    def test_all_standard_levels_valid(self, validator_with_env) -> None:
        """全ての標準レベルが有効"""
        levels = ["weekly", "monthly", "quarterly", "annual", "triennial", "decadal", "centurial"]
        for level in levels:
            errors = validator_with_env.validate_level_config(level)
            assert len(errors) == 0, f"Level {level} should be valid"


# =============================================================================
# TestValidateAll - 統合検証テスト
# =============================================================================


class TestValidateAll:
    """統合検証のテスト"""

    @pytest.mark.unit
    def test_valid_config_passes_all_validation(self, validator_with_env) -> None:
        """有効な設定は全検証をパス"""
        errors = validator_with_env.validate_all()
        assert len(errors) == 0

    @pytest.mark.unit
    def test_is_valid_returns_true_for_valid_config(self, validator_with_env) -> None:
        """有効な設定でis_validがTrue"""
        assert validator_with_env.is_valid() is True

    @pytest.mark.unit
    def test_is_valid_returns_false_for_invalid_config(
        self, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """無効な設定でis_validがFalse"""
        config = cast(ConfigData, {})  # Empty config
        validator = ConfigValidator(
            config=config,
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
        )
        assert validator.is_valid() is False


# =============================================================================
# TestDirectoryValidatorAlias - 後方互換性エイリアステスト
# =============================================================================


class TestDirectoryValidatorAlias:
    """DirectoryValidatorエイリアスのテスト"""

    @pytest.mark.unit
    def test_directory_validator_is_config_validator(self) -> None:
        """DirectoryValidatorはConfigValidatorのエイリアス"""
        assert DirectoryValidator is ConfigValidator

    @pytest.mark.unit
    def test_directory_validator_instantiation(
        self, temp_plugin_env: "TempPluginEnvironment", valid_config
    ) -> None:
        """DirectoryValidatorとしてインスタンス化可能"""
        validator = DirectoryValidator(
            config=valid_config,
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
        )
        assert isinstance(validator, ConfigValidator)
