#!/usr/bin/env python3
"""
config.py のユニットテスト
==========================

extract_file_number(), extract_number_only(), DigestConfig クラスのテスト

pytestスタイルで実装。conftest.pyのフィクスチャを活用。
"""
import json
import sys
from pathlib import Path

import pytest

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    extract_file_number,
    extract_number_only,
    format_digest_number,
    DigestConfig,
    LEVEL_CONFIG,
    LEVEL_NAMES,
)
from domain.exceptions import ConfigError


# =============================================================================
# テスト用定数
# =============================================================================
# 長い文字列テスト用: ファイルシステムの制限を超えるサイズ
VERY_LONG_STRING_LENGTH = 1000


# =============================================================================
# extract_file_number テスト
# =============================================================================

class TestExtractFileNumber:
    """extract_file_number() のテスト"""

    @pytest.mark.unit
    @pytest.mark.parametrize("filename,expected", [
        ("Loop0001_タイトル.txt", ("Loop", 1)),
        ("Loop0186_xxx.txt", ("Loop", 186)),
        ("W0001_タイトル.txt", ("W", 1)),
        ("W0047_xxx.txt", ("W", 47)),
        ("M001_タイトル.txt", ("M", 1)),
        ("M012_xxx.txt", ("M", 12)),
        ("MD01_タイトル.txt", ("MD", 1)),
        ("MD03_xxx.txt", ("MD", 3)),
        ("Q001_タイトル.txt", ("Q", 1)),
        ("A01_タイトル.txt", ("A", 1)),
        ("T01_タイトル.txt", ("T", 1)),
        ("D01_タイトル.txt", ("D", 1)),
        ("C01_タイトル.txt", ("C", 1)),
    ])
    def test_valid_filenames(self, filename, expected):
        """有効なファイル名からプレフィックスと番号を抽出"""
        assert extract_file_number(filename) == expected

    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_input", [
        "invalid.txt",
        "",
        "no_number.txt",
        None,
        123,
        ['Loop0001'],
        {'name': 'Loop0001'},
    ])
    def test_invalid_input_returns_none(self, invalid_input):
        """無効な入力はNoneを返す"""
        assert extract_file_number(invalid_input) is None


class TestExtractFileNumberEdgeCases:
    """extract_file_number() のエッジケーステスト"""

    @pytest.mark.unit
    def test_unicode_special_chars(self):
        """Unicode特殊文字を含むファイル名"""
        assert extract_file_number("Loop0001_日本語タイトル.txt") == ("Loop", 1)
        assert extract_file_number("W0001_絵文字🎉.txt") == ("W", 1)

    @pytest.mark.unit
    def test_very_long_filename(self):
        """極端に長いファイル名"""
        long_title = "a" * VERY_LONG_STRING_LENGTH
        assert extract_file_number(f"Loop0001_{long_title}.txt") == ("Loop", 1)

    @pytest.mark.unit
    def test_number_overflow(self):
        """大きな番号"""
        assert extract_file_number("Loop99999999.txt") == ("Loop", 99999999)

    @pytest.mark.unit
    @pytest.mark.parametrize("filename,expected", [
        ("Loop0000.txt", ("Loop", 0)),
        ("W00001.txt", ("W", 1)),
    ])
    def test_leading_zeros(self, filename, expected):
        """先頭ゼロのバリエーション"""
        assert extract_file_number(filename) == expected

    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_input", [
        "Loop.txt",
        "W_title.txt",
        "0001.txt",
        "12345.txt",
    ])
    def test_invalid_patterns(self, invalid_input):
        """無効なパターン"""
        assert extract_file_number(invalid_input) is None


# =============================================================================
# extract_number_only テスト
# =============================================================================

class TestExtractNumberOnly:
    """extract_number_only() のテスト"""

    @pytest.mark.unit
    @pytest.mark.parametrize("filename,expected", [
        ("Loop0001_xxx.txt", 1),
        ("MD03_xxx.txt", 3),
        ("Loop0000.txt", 0),
    ])
    def test_returns_number(self, filename, expected):
        """番号のみ返す"""
        assert extract_number_only(filename) == expected

    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_input", [
        "invalid.txt",
        None,
        123,
    ])
    def test_invalid_returns_none(self, invalid_input):
        """無効な形式はNone"""
        assert extract_number_only(invalid_input) is None


# =============================================================================
# format_digest_number テスト
# =============================================================================

class TestFormatDigestNumber:
    """format_digest_number() のテスト"""

    @pytest.mark.unit
    @pytest.mark.parametrize("level,number,expected", [
        ("loop", 1, "Loop0001"),
        ("weekly", 1, "W0001"),
        ("monthly", 1, "M001"),
        ("quarterly", 1, "Q001"),
        ("annual", 1, "A01"),
        ("triennial", 1, "T01"),
        ("decadal", 1, "D01"),
        ("multi_decadal", 1, "MD01"),
        ("centurial", 1, "C01"),
    ])
    def test_all_valid_levels(self, level, number, expected):
        """すべての有効なレベルで正しく動作"""
        assert format_digest_number(level, number) == expected

    @pytest.mark.unit
    @pytest.mark.parametrize("level,number,expected", [
        ("loop", 0, "Loop0000"),
        ("weekly", 0, "W0000"),
    ])
    def test_zero_number(self, level, number, expected):
        """番号0の処理"""
        assert format_digest_number(level, number) == expected

    @pytest.mark.unit
    def test_very_large_number(self):
        """桁数を超える大きな番号"""
        result = format_digest_number("weekly", 99999)
        assert result == "W99999"

    @pytest.mark.unit
    def test_invalid_level_raises_valueerror(self):
        """無効なレベル名でValueError"""
        with pytest.raises(ValueError):
            format_digest_number("invalid_level", 1)


# =============================================================================
# DigestConfig テスト
# =============================================================================

class TestDigestConfig:
    """DigestConfig クラスのテスト"""

    @pytest.fixture
    def config_env(self, temp_plugin_env):
        """テスト用の設定環境を構築"""
        # config.json 作成
        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4
            }
        }
        config_file = temp_plugin_env.config_dir / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)

        return {
            "env": temp_plugin_env,
            "config_data": config_data,
            "config_file": config_file,
        }

    @pytest.mark.unit
    def test_init_with_explicit_plugin_root(self, config_env):
        """明示的なplugin_rootで初期化"""
        env = config_env["env"]
        config = DigestConfig(plugin_root=env.plugin_root)
        assert config.plugin_root == env.plugin_root
        assert config.config_file == config_env["config_file"]

    @pytest.mark.unit
    def test_load_config_success(self, config_env):
        """設定ファイルの読み込み成功"""
        env = config_env["env"]
        config = DigestConfig(plugin_root=env.plugin_root)
        assert config.config["base_dir"] == "."
        assert "paths" in config.config
        assert "levels" in config.config

    @pytest.mark.unit
    def test_load_config_not_found(self, config_env):
        """設定ファイルが見つからない場合"""
        config_env["config_file"].unlink()
        with pytest.raises(ConfigError):
            DigestConfig(plugin_root=config_env["env"].plugin_root)

    @pytest.mark.unit
    def test_load_config_invalid_json(self, config_env):
        """無効なJSONの場合"""
        with open(config_env["config_file"], 'w', encoding='utf-8') as f:
            f.write("invalid json {")
        with pytest.raises(ConfigError):
            DigestConfig(plugin_root=config_env["env"].plugin_root)

    @pytest.mark.unit
    def test_resolve_base_dir_dot(self, config_env):
        """base_dir="." の場合はplugin_rootと同じ"""
        env = config_env["env"]
        config = DigestConfig(plugin_root=env.plugin_root)
        assert config.base_dir == env.plugin_root.resolve()

    @pytest.mark.unit
    def test_resolve_base_dir_relative(self, config_env):
        """相対パスのbase_dir"""
        config_data = config_env["config_data"]
        config_data["base_dir"] = "data"
        with open(config_env["config_file"], 'w', encoding='utf-8') as f:
            json.dump(config_data, f)

        env = config_env["env"]
        config = DigestConfig(plugin_root=env.plugin_root)
        assert config.base_dir == (env.plugin_root / "data").resolve()

    @pytest.mark.unit
    def test_path_properties(self, config_env):
        """パスプロパティ（loops_path, digests_path, essences_path）"""
        env = config_env["env"]
        config = DigestConfig(plugin_root=env.plugin_root)

        assert config.loops_path == (env.plugin_root / "data" / "Loops").resolve()
        assert config.digests_path == (env.plugin_root / "data" / "Digests").resolve()
        assert config.essences_path == (env.plugin_root / "data" / "Essences").resolve()

    @pytest.mark.unit
    def test_resolve_path_missing_key(self, config_env):
        """存在しないキーの場合"""
        env = config_env["env"]
        config = DigestConfig(plugin_root=env.plugin_root)
        with pytest.raises(ConfigError):
            config.resolve_path("nonexistent_key")

    @pytest.mark.unit
    def test_resolve_path_missing_paths_section(self, config_env):
        """pathsセクションがない場合"""
        config_data = config_env["config_data"]
        del config_data["paths"]
        with open(config_env["config_file"], 'w', encoding='utf-8') as f:
            json.dump(config_data, f)

        env = config_env["env"]
        config = DigestConfig(plugin_root=env.plugin_root)
        with pytest.raises(ConfigError):
            config.resolve_path("loops_dir")

    @pytest.mark.unit
    def test_get_level_dir_all_levels(self, config_env):
        """全レベルのディレクトリ取得"""
        env = config_env["env"]
        config = DigestConfig(plugin_root=env.plugin_root)
        for level in LEVEL_NAMES:
            level_dir = config.get_level_dir(level)
            expected_subdir = LEVEL_CONFIG[level]["dir"]
            assert str(level_dir).endswith(expected_subdir)

    @pytest.mark.unit
    def test_get_level_dir_invalid_level(self, config_env):
        """無効なレベル名の場合"""
        env = config_env["env"]
        config = DigestConfig(plugin_root=env.plugin_root)
        with pytest.raises(ValueError):
            config.get_level_dir("invalid_level")

    @pytest.mark.unit
    def test_get_provisional_dir_all_levels(self, config_env):
        """全レベルのProvisionalディレクトリ取得"""
        env = config_env["env"]
        config = DigestConfig(plugin_root=env.plugin_root)
        for level in LEVEL_NAMES:
            prov_dir = config.get_provisional_dir(level)
            assert str(prov_dir).endswith("Provisional")


class TestDigestConfigThresholds:
    """DigestConfig thresholdプロパティのテスト"""

    @pytest.fixture
    def threshold_env(self, temp_plugin_env):
        """threshold テスト用の設定環境"""
        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4
            }
        }
        config_file = temp_plugin_env.config_dir / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)

        return {
            "env": temp_plugin_env,
            "config_data": config_data,
            "config_file": config_file,
        }

    @pytest.mark.unit
    @pytest.mark.parametrize("level,expected", [
        ("weekly", 5),
        ("monthly", 5),
        ("quarterly", 3),
        ("annual", 4),
        ("triennial", 3),
        ("decadal", 3),
        ("multi_decadal", 3),
        ("centurial", 4),
    ])
    def test_threshold_properties(self, threshold_env, level, expected):
        """全レベルのthresholdプロパティ"""
        env = threshold_env["env"]
        config = DigestConfig(plugin_root=env.plugin_root)
        assert config.get_threshold(level) == expected

    @pytest.mark.unit
    def test_threshold_properties_default_values(self, threshold_env):
        """thresholdのデフォルト値"""
        config_data = threshold_env["config_data"]
        del config_data["levels"]
        with open(threshold_env["config_file"], 'w', encoding='utf-8') as f:
            json.dump(config_data, f)

        env = threshold_env["env"]
        config = DigestConfig(plugin_root=env.plugin_root)

        # デフォルト値が返されることを確認
        assert config.weekly_threshold == 5
        assert config.monthly_threshold == 5
        assert config.quarterly_threshold == 3
        assert config.annual_threshold == 4

    @pytest.mark.unit
    def test_threshold_custom_values(self, threshold_env):
        """カスタムthreshold値"""
        config_data = threshold_env["config_data"]
        config_data["levels"]["weekly_threshold"] = 10
        config_data["levels"]["monthly_threshold"] = 8
        with open(threshold_env["config_file"], 'w', encoding='utf-8') as f:
            json.dump(config_data, f)

        env = threshold_env["env"]
        config = DigestConfig(plugin_root=env.plugin_root)
        assert config.weekly_threshold == 10
        assert config.monthly_threshold == 8

    @pytest.mark.unit
    def test_get_threshold_invalid_level(self, threshold_env):
        """get_threshold()が無効なレベルでConfigErrorを発生させる"""
        env = threshold_env["env"]
        config = DigestConfig(plugin_root=env.plugin_root)
        with pytest.raises(ConfigError):
            config.get_threshold("invalid_level")

    @pytest.mark.unit
    def test_get_threshold_matches_properties(self, threshold_env):
        """get_threshold()と既存プロパティが同じ値を返す"""
        env = threshold_env["env"]
        config = DigestConfig(plugin_root=env.plugin_root)

        assert config.get_threshold("weekly") == config.weekly_threshold
        assert config.get_threshold("monthly") == config.monthly_threshold
        assert config.get_threshold("quarterly") == config.quarterly_threshold


class TestDigestConfigIdentityFile:
    """DigestConfig identity_file_path のテスト"""

    @pytest.fixture
    def identity_env(self, temp_plugin_env):
        """identity_file テスト用の設定環境"""
        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None
            },
            "levels": {}
        }
        config_file = temp_plugin_env.config_dir / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)

        return {
            "env": temp_plugin_env,
            "config_data": config_data,
            "config_file": config_file,
        }

    @pytest.mark.unit
    def test_get_identity_file_path_none(self, identity_env):
        """identity_file_pathがNoneの場合"""
        env = identity_env["env"]
        config = DigestConfig(plugin_root=env.plugin_root)
        assert config.get_identity_file_path() is None

    @pytest.mark.unit
    def test_get_identity_file_path_configured(self, identity_env):
        """identity_file_pathが設定されている場合"""
        config_data = identity_env["config_data"]
        config_data["paths"]["identity_file_path"] = "Identity.md"
        with open(identity_env["config_file"], 'w', encoding='utf-8') as f:
            json.dump(config_data, f)

        env = identity_env["env"]
        config = DigestConfig(plugin_root=env.plugin_root)
        identity_path = config.get_identity_file_path()
        assert identity_path is not None
        assert str(identity_path).endswith("Identity.md")


# =============================================================================
# LEVEL_CONFIG テスト
# =============================================================================

class TestLevelConfig:
    """LEVEL_CONFIG 定数のテスト"""

    @pytest.mark.unit
    def test_all_levels_have_required_keys(self):
        """全レベルに必要なキーが存在"""
        required_keys = {"prefix", "digits", "dir", "source", "next"}
        for level, config in LEVEL_CONFIG.items():
            for key in required_keys:
                assert key in config, f"Level '{level}' missing key '{key}'"

    @pytest.mark.unit
    def test_level_names_matches_config_keys(self):
        """LEVEL_NAMESとLEVEL_CONFIGのキーが一致"""
        assert set(LEVEL_NAMES) == set(LEVEL_CONFIG.keys())

    @pytest.mark.unit
    def test_level_chain_is_valid(self):
        """レベルチェーンが有効（nextが正しく設定されている）"""
        for level, config in LEVEL_CONFIG.items():
            next_level = config["next"]
            if next_level is not None:
                assert next_level in LEVEL_CONFIG, \
                    f"Level '{level}' has invalid next: '{next_level}'"


# =============================================================================
# validate_directory_structure テスト
# =============================================================================

class TestValidateDirectoryStructure:
    """validate_directory_structure() のテスト"""

    @pytest.fixture
    def validate_env(self, temp_plugin_env):
        """validate_directory_structure テスト用の設定環境"""
        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None
            },
            "levels": {}
        }
        config_file = temp_plugin_env.config_dir / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)

        return {
            "env": temp_plugin_env,
            "config_file": config_file,
        }

    def _create_full_directory_structure(self, plugin_root):
        """完全なディレクトリ構造を作成"""
        data_dir = plugin_root / "data"
        (data_dir / "Loops").mkdir(parents=True, exist_ok=True)
        (data_dir / "Digests").mkdir(parents=True, exist_ok=True)
        (data_dir / "Essences").mkdir(parents=True, exist_ok=True)

        for level in LEVEL_NAMES:
            level_subdir = LEVEL_CONFIG[level]["dir"]
            level_dir = data_dir / "Digests" / level_subdir
            level_dir.mkdir(parents=True, exist_ok=True)
            (level_dir / "Provisional").mkdir(exist_ok=True)

    @pytest.mark.integration
    def test_validate_directory_structure_all_present(self, validate_env):
        """全ディレクトリ存在時はエラーなし"""
        env = validate_env["env"]
        self._create_full_directory_structure(env.plugin_root)
        config = DigestConfig(plugin_root=env.plugin_root)
        errors = config.validate_directory_structure()
        assert errors == []

    @pytest.mark.integration
    def test_validate_directory_structure_missing_loops(self, validate_env):
        """Loopsディレクトリ欠落"""
        import shutil
        env = validate_env["env"]
        self._create_full_directory_structure(env.plugin_root)
        shutil.rmtree(env.plugin_root / "data" / "Loops")

        config = DigestConfig(plugin_root=env.plugin_root)
        errors = config.validate_directory_structure()

        assert len(errors) == 1
        assert "Loops" in errors[0]

    @pytest.mark.integration
    def test_validate_directory_structure_missing_digests(self, validate_env):
        """Digestsディレクトリ欠落"""
        import shutil
        env = validate_env["env"]
        # temp_plugin_envが既にDigestsを作成しているので削除する
        shutil.rmtree(env.plugin_root / "data" / "Digests")

        config = DigestConfig(plugin_root=env.plugin_root)
        errors = config.validate_directory_structure()

        assert len(errors) > 0
        assert any("Digests" in e for e in errors)

    @pytest.mark.integration
    def test_validate_directory_structure_missing_essences(self, validate_env):
        """Essencesディレクトリ欠落"""
        import shutil
        env = validate_env["env"]
        self._create_full_directory_structure(env.plugin_root)
        shutil.rmtree(env.plugin_root / "data" / "Essences")

        config = DigestConfig(plugin_root=env.plugin_root)
        errors = config.validate_directory_structure()

        assert len(errors) == 1
        assert "Essences" in errors[0]

    @pytest.mark.integration
    def test_validate_directory_structure_missing_level_dir(self, validate_env):
        """レベルディレクトリ（1_Weekly等）欠落"""
        import shutil
        env = validate_env["env"]
        self._create_full_directory_structure(env.plugin_root)
        weekly_dir = env.plugin_root / "data" / "Digests" / "1_Weekly"
        shutil.rmtree(weekly_dir)

        config = DigestConfig(plugin_root=env.plugin_root)
        errors = config.validate_directory_structure()

        assert len(errors) == 1
        assert "weekly" in errors[0].lower()

    @pytest.mark.integration
    def test_validate_directory_structure_missing_provisional(self, validate_env):
        """Provisionalディレクトリ欠落"""
        import shutil
        env = validate_env["env"]
        self._create_full_directory_structure(env.plugin_root)
        prov_dir = env.plugin_root / "data" / "Digests" / "1_Weekly" / "Provisional"
        shutil.rmtree(prov_dir)

        config = DigestConfig(plugin_root=env.plugin_root)
        errors = config.validate_directory_structure()

        assert len(errors) == 1
        assert "Provisional" in errors[0]

    @pytest.mark.integration
    def test_validate_directory_structure_multiple_errors(self, validate_env):
        """複数エラーの集約"""
        import shutil
        env = validate_env["env"]
        # temp_plugin_envが既に全ディレクトリを作成しているので削除する
        shutil.rmtree(env.plugin_root / "data" / "Digests")
        shutil.rmtree(env.plugin_root / "data" / "Essences")

        config = DigestConfig(plugin_root=env.plugin_root)
        errors = config.validate_directory_structure()

        assert len(errors) > 2
        assert any("Digests" in e for e in errors)
        assert any("Essences" in e for e in errors)
