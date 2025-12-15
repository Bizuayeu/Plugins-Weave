#!/usr/bin/env python3
"""
config.py のユニットテスト
==========================

DigestConfig クラスと LEVEL_CONFIG 定数のテスト。

Note:
    extract_file_number(), extract_number_only(), format_digest_number() のテストは
    test_file_naming.py に存在。
    validate_directory_structure() のテストは test_directory_validator.py に存在。

pytestスタイルで実装。conftest.pyのフィクスチャを活用。
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

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

from application.config import DigestConfig
from domain.constants import LEVEL_CONFIG, LEVEL_NAMES
from domain.exceptions import ConfigError

# =============================================================================
# DigestConfig テスト
# =============================================================================


class TestDigestConfig:
    """DigestConfig クラスのテスト"""

    @pytest.fixture
    def config_env(self, temp_plugin_env: "TempPluginEnvironment"):
        """テスト用の設定環境を構築"""
        # config.json 作成（永続化ディレクトリに配置）
        # base_dirは絶対パス必須
        config_data = {
            "base_dir": str(temp_plugin_env.plugin_root),
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None,
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4,
            },
        }
        # 永続化ディレクトリにconfig.jsonを配置（auto-update対象外の場所）
        config_file = temp_plugin_env.persistent_config_dir / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)

        return {
            "env": temp_plugin_env,
            "config_data": config_data,
            "config_file": config_file,
        }

    @pytest.mark.unit
    def test_no_plugin_root_parameter(self) -> None:
        """DigestConfig は plugin_root パラメータを持たない"""
        import inspect

        sig = inspect.signature(DigestConfig.__init__)
        params = list(sig.parameters.keys())

        assert "plugin_root" not in params
        # selfのみ
        assert params == ["self"]

    @pytest.mark.unit
    def test_config_file_uses_persistent_dir(self, config_env) -> None:
        """config_fileは永続化ディレクトリを使用"""
        from infrastructure.config.persistent_path import get_config_path

        config = DigestConfig()
        assert config.config_file == get_config_path()

    @pytest.mark.unit
    def test_load_config_success(self, config_env) -> None:
        """設定ファイルの読み込み成功"""
        config = DigestConfig()
        assert "paths" in config.config
        assert "levels" in config.config

    @pytest.mark.unit
    def test_load_config_not_found(self, config_env) -> None:
        """設定ファイルが見つからない場合"""
        config_env["config_file"].unlink()
        with pytest.raises(ConfigError):
            DigestConfig()

    @pytest.mark.unit
    def test_load_config_invalid_json(self, config_env) -> None:
        """無効なJSONの場合"""
        with open(config_env["config_file"], 'w', encoding='utf-8') as f:
            f.write("invalid json {")
        with pytest.raises(ConfigError):
            DigestConfig()

    @pytest.mark.unit
    def test_base_dir_must_be_absolute(self, config_env) -> None:
        """base_dirは絶対パス必須"""
        config_data = config_env["config_data"]
        config_data["base_dir"] = "."  # 相対パス
        with open(config_env["config_file"], 'w', encoding='utf-8') as f:
            json.dump(config_data, f)

        with pytest.raises(ConfigError) as exc_info:
            DigestConfig()

        assert "base_dir" in str(exc_info.value)

    @pytest.mark.unit
    def test_path_properties(self, config_env) -> None:
        """パスプロパティ（loops_path, digests_path, essences_path）"""
        env = config_env["env"]
        config = DigestConfig()

        assert config.loops_path == (env.plugin_root / "data" / "Loops").resolve()
        assert config.digests_path == (env.plugin_root / "data" / "Digests").resolve()
        assert config.essences_path == (env.plugin_root / "data" / "Essences").resolve()

    @pytest.mark.unit
    def test_resolve_path_missing_key(self, config_env) -> None:
        """存在しないキーの場合"""
        config = DigestConfig()
        with pytest.raises(ConfigError):
            config.resolve_path("nonexistent_key")

    @pytest.mark.unit
    def test_resolve_path_missing_paths_section(self, config_env) -> None:
        """pathsセクションがない場合、初期化時にエラー"""
        config_data = config_env["config_data"]
        del config_data["paths"]
        with open(config_env["config_file"], 'w', encoding='utf-8') as f:
            json.dump(config_data, f)

        # 即時初期化により、DigestConfigコンストラクタでエラーが発生
        with pytest.raises(ConfigError):
            DigestConfig()

    @pytest.mark.unit
    def test_get_level_dir_all_levels(self, config_env) -> None:
        """全レベルのディレクトリ取得"""
        config = DigestConfig()
        for level in LEVEL_NAMES:
            level_dir = config.get_level_dir(level)
            expected_subdir = LEVEL_CONFIG[level]["dir"]
            assert str(level_dir).endswith(expected_subdir)

    @pytest.mark.unit
    def test_get_level_dir_invalid_level(self, config_env) -> None:
        """無効なレベル名の場合"""
        config = DigestConfig()
        with pytest.raises(ConfigError):
            config.get_level_dir("invalid_level")

    @pytest.mark.unit
    def test_get_provisional_dir_all_levels(self, config_env) -> None:
        """全レベルのProvisionalディレクトリ取得"""
        config = DigestConfig()
        for level in LEVEL_NAMES:
            prov_dir = config.get_provisional_dir(level)
            assert str(prov_dir).endswith("Provisional")

    @pytest.mark.unit
    def test_init_handles_permission_error(self, config_env) -> None:
        """PermissionErrorがConfigErrorに変換される"""
        # ConfigLoader.load を PermissionError を発生させるようにモック
        from infrastructure.config import ConfigLoader

        with patch.object(ConfigLoader, "load", side_effect=PermissionError("Access denied")):
            with pytest.raises(ConfigError) as exc_info:
                DigestConfig()

            assert "Failed to initialize configuration" in str(exc_info.value)

    @pytest.mark.unit
    def test_init_handles_os_error(self, config_env) -> None:
        """OSErrorがConfigErrorに変換される"""
        # ConfigLoader.load を OSError を発生させるようにモック
        from infrastructure.config import ConfigLoader

        with patch.object(ConfigLoader, "load", side_effect=OSError("Disk error")):
            with pytest.raises(ConfigError) as exc_info:
                DigestConfig()

            assert "Failed to initialize configuration" in str(exc_info.value)


class TestDigestConfigThresholds:
    """DigestConfig thresholdプロパティのテスト"""

    @pytest.fixture
    def threshold_env(self, temp_plugin_env: "TempPluginEnvironment"):
        """threshold テスト用の設定環境"""
        config_data = {
            "base_dir": str(temp_plugin_env.plugin_root),
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None,
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4,
            },
        }
        # 永続化ディレクトリにconfig.jsonを配置
        config_file = temp_plugin_env.persistent_config_dir / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)

        return {
            "env": temp_plugin_env,
            "config_data": config_data,
            "config_file": config_file,
        }

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "level,expected",
        [
            ("weekly", 5),
            ("monthly", 5),
            ("quarterly", 3),
            ("annual", 4),
            ("triennial", 3),
            ("decadal", 3),
            ("multi_decadal", 3),
            ("centurial", 4),
        ],
    )
    def test_threshold_properties(self, threshold_env, level, expected) -> None:
        """全レベルのthresholdプロパティ"""
        config = DigestConfig()
        assert config.get_threshold(level) == expected

    @pytest.mark.unit
    def test_threshold_properties_default_values(self, threshold_env) -> None:
        """thresholdのデフォルト値"""
        config_data = threshold_env["config_data"]
        del config_data["levels"]
        with open(threshold_env["config_file"], 'w', encoding='utf-8') as f:
            json.dump(config_data, f)

        config = DigestConfig()

        # デフォルト値が返されることを確認
        # ARCHITECTURE: コンポーネント公開パターン
        # config.threshold経由でThresholdProviderに直接アクセス
        assert config.threshold.weekly_threshold == 5
        assert config.threshold.monthly_threshold == 5
        assert config.threshold.quarterly_threshold == 3
        assert config.threshold.annual_threshold == 4

    @pytest.mark.unit
    def test_threshold_custom_values(self, threshold_env) -> None:
        """カスタムthreshold値"""
        config_data = threshold_env["config_data"]
        config_data["levels"]["weekly_threshold"] = 10
        config_data["levels"]["monthly_threshold"] = 8
        with open(threshold_env["config_file"], 'w', encoding='utf-8') as f:
            json.dump(config_data, f)

        config = DigestConfig()
        assert config.threshold.weekly_threshold == 10
        assert config.threshold.monthly_threshold == 8

    @pytest.mark.unit
    def test_get_threshold_invalid_level(self, threshold_env) -> None:
        """get_threshold()が無効なレベルでConfigErrorを発生させる"""
        config = DigestConfig()
        with pytest.raises(ConfigError):
            config.get_threshold("invalid_level")

    @pytest.mark.unit
    def test_get_threshold_matches_properties(self, threshold_env) -> None:
        """get_threshold()とthresholdプロパティが同じ値を返す"""
        config = DigestConfig()

        # config.get_threshold() は後方互換性のため維持
        # 新規コードでは config.threshold.get_threshold() を推奨
        assert config.get_threshold("weekly") == config.threshold.weekly_threshold
        assert config.get_threshold("monthly") == config.threshold.monthly_threshold
        assert config.get_threshold("quarterly") == config.threshold.quarterly_threshold


class TestDigestConfigIdentityFile:
    """DigestConfig identity_file_path のテスト"""

    @pytest.fixture
    def identity_env(self, temp_plugin_env: "TempPluginEnvironment"):
        """identity_file テスト用の設定環境"""
        config_data = {
            "base_dir": str(temp_plugin_env.plugin_root),
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None,
            },
            "levels": {},
        }
        # 永続化ディレクトリにconfig.jsonを配置
        config_file = temp_plugin_env.persistent_config_dir / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)

        return {
            "env": temp_plugin_env,
            "config_data": config_data,
            "config_file": config_file,
        }

    @pytest.mark.unit
    def test_get_identity_file_path_none(self, identity_env) -> None:
        """identity_file_pathがNoneの場合"""
        config = DigestConfig()
        assert config.get_identity_file_path() is None

    @pytest.mark.unit
    def test_get_identity_file_path_configured(self, identity_env) -> None:
        """identity_file_pathが設定されている場合"""
        config_data = identity_env["config_data"]
        config_data["paths"]["identity_file_path"] = "Identity.md"
        with open(identity_env["config_file"], 'w', encoding='utf-8') as f:
            json.dump(config_data, f)

        config = DigestConfig()
        identity_path = config.get_identity_file_path()
        assert identity_path is not None
        assert str(identity_path).endswith("Identity.md")


# =============================================================================
# LEVEL_CONFIG テスト
# =============================================================================


class TestLevelConfig:
    """LEVEL_CONFIG 定数のテスト"""

    @pytest.mark.unit
    def test_all_levels_have_required_keys(self) -> None:
        """全レベルに必要なキーが存在"""
        required_keys = {"prefix", "digits", "dir", "source", "next"}
        for level, config in LEVEL_CONFIG.items():
            for key in required_keys:
                assert key in config, f"Level '{level}' missing key '{key}'"

    @pytest.mark.unit
    def test_level_names_matches_config_keys(self) -> None:
        """LEVEL_NAMESとLEVEL_CONFIGのキーが一致"""
        assert set(LEVEL_NAMES) == set(LEVEL_CONFIG.keys())

    @pytest.mark.unit
    def test_level_chain_is_valid(self) -> None:
        """レベルチェーンが有効（nextが正しく設定されている）"""
        for level, config in LEVEL_CONFIG.items():
            next_level = config["next"]
            if next_level is not None:
                assert next_level in LEVEL_CONFIG, (
                    f"Level '{level}' has invalid next: '{next_level}'"
                )


# =============================================================================
# DigestConfig show_paths テスト
# =============================================================================


class TestDigestConfigShowPaths:
    """DigestConfig.show_paths() のテスト"""

    @pytest.fixture
    def show_paths_env(self, temp_plugin_env: "TempPluginEnvironment"):
        """show_paths テスト用の設定環境"""
        config_data = {
            "base_dir": str(temp_plugin_env.plugin_root),
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None,
            },
            "levels": {},
        }
        # 永続化ディレクトリにconfig.jsonを配置
        config_file = temp_plugin_env.persistent_config_dir / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        return {
            "env": temp_plugin_env,
            "config_data": config_data,
            "config_file": config_file,
        }

    @pytest.mark.unit
    def test_show_paths_logs_all_paths(
        self, show_paths_env, caplog: pytest.LogCaptureFixture
    ) -> None:
        """show_paths()が全パスをログに出力"""
        import logging

        config = DigestConfig()

        with caplog.at_level(logging.INFO, logger="episodic_rag.config"):
            config.show_paths()

        # パス情報がログ出力されている
        assert "Loops" in caplog.text
        assert "Digests" in caplog.text

    @pytest.mark.unit
    def test_show_paths_returns_none(self, show_paths_env) -> None:
        """show_paths()はNoneを返す"""
        config = DigestConfig()

        result = config.show_paths()
        assert result is None


# =============================================================================
# Context Manager テスト
# =============================================================================


class TestDigestConfigContextManager:
    """DigestConfig の Context Manager テスト"""

    @pytest.fixture
    def context_env(self, temp_plugin_env: "TempPluginEnvironment"):
        """Context Manager テスト用の設定環境を構築"""
        config_data = {
            "base_dir": str(temp_plugin_env.plugin_root),
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
        }
        # 永続化ディレクトリにconfig.jsonを配置
        config_file = temp_plugin_env.persistent_config_dir / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)
        return temp_plugin_env

    @pytest.mark.unit
    def test_context_manager_enter_returns_self(self, context_env) -> None:
        """__enter__がselfを返す"""
        config = DigestConfig()

        with config as ctx:
            assert ctx is config

    @pytest.mark.unit
    def test_context_manager_basic_usage(self, context_env) -> None:
        """Context Managerの基本的な使用"""
        with DigestConfig() as config:
            # スコープ内でconfigが使用可能
            assert config.loops_path.name == "Loops"

    @pytest.mark.unit
    def test_context_manager_exit_does_not_suppress_exception(self, context_env) -> None:
        """__exit__が例外を抑制しない"""
        with pytest.raises(ValueError):
            with DigestConfig() as _:
                raise ValueError("Test exception")

    @pytest.mark.unit
    def test_context_manager_nested_usage(self, context_env) -> None:
        """ネストしたContext Managerの使用"""
        with DigestConfig() as outer:
            with DigestConfig() as inner:
                assert outer.base_dir == inner.base_dir
