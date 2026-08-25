#!/usr/bin/env python3
"""
ConfigLoader ユニットテスト
===========================

config_loader.py のユニットテスト。
ConfigLoaderクラスの動作を検証:
- load/reload: 設定ファイルの読み込み・再読み込み
- get/get_required/has_key: 設定値へのアクセス
- validate_required_keys: 必須キーの検証
- キャッシュ動作の確認
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from test_helpers import TempPluginEnvironment

    from application.config import DigestConfig
    from application.grand import GrandDigestManager, ShadowGrandDigestManager
    from application.shadow import FileDetector, ShadowIO, ShadowTemplate
    from application.shadow.placeholder_manager import PlaceholderManager
    from application.tracking import DigestTimesTracker
    from domain.types.level import LevelHierarchyEntry


import pytest

from domain.exceptions import ConfigError
from infrastructure.config.config_loader import ConfigLoader

# =============================================================================
# フィクスチャ
# =============================================================================


@pytest.fixture
def config_file(temp_plugin_env: "TempPluginEnvironment"):
    """テスト用config.jsonファイルパスを提供"""
    return temp_plugin_env.config_dir / "config.json"


@pytest.fixture
def valid_config_data():
    """有効な設定データ"""
    return {
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
    }


@pytest.fixture
def config_loader(config_file, valid_config_data):
    """テスト用ConfigLoaderインスタンス"""
    with config_file.open("w", encoding="utf-8") as f:
        json.dump(valid_config_data, f)
    return ConfigLoader(config_file)


# =============================================================================
# TestConfigLoaderInit - 初期化テスト
# =============================================================================


class TestConfigLoaderInit:
    """ConfigLoaderの初期化テスト"""

    @pytest.mark.unit
    def test_init_with_valid_path(self, config_file) -> None:
        """有効なパスで初期化できる"""
        loader = ConfigLoader(config_file)
        assert loader.config_file == config_file
        assert loader._config is None  # 初期状態ではキャッシュなし

    @pytest.mark.unit
    def test_init_with_path_object(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """Pathオブジェクトで初期化できる"""
        config_path = temp_plugin_env.config_dir / "config.json"
        loader = ConfigLoader(config_path)
        assert isinstance(loader.config_file, Path)

    @pytest.mark.unit
    def test_is_loaded_initially_false(self, config_file) -> None:
        """初期化直後はis_loadedがFalse"""
        loader = ConfigLoader(config_file)
        assert loader.is_loaded is False


# =============================================================================
# TestConfigLoaderLoad - load/reloadテスト
# =============================================================================


class TestConfigLoaderLoad:
    """load/reloadメソッドのテスト"""

    @pytest.mark.unit
    def test_load_valid_config(self, config_loader) -> None:
        """有効な設定ファイルを読み込める"""
        config = config_loader.load()
        assert config is not None
        assert "base_dir" in config
        assert config["base_dir"] == "."

    @pytest.mark.unit
    def test_load_sets_is_loaded_true(self, config_loader) -> None:
        """load後はis_loadedがTrue"""
        config_loader.load()
        assert config_loader.is_loaded is True

    @pytest.mark.unit
    def test_load_file_not_found(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """ファイルが存在しない場合ConfigError"""
        nonexistent = temp_plugin_env.config_dir / "nonexistent.json"
        loader = ConfigLoader(nonexistent)

        with pytest.raises(ConfigError) as exc_info:
            loader.load()

        assert "File not found" in str(exc_info.value)

    @pytest.mark.unit
    def test_load_invalid_json(self, config_file) -> None:
        """無効なJSONの場合ConfigError"""
        with config_file.open("w", encoding="utf-8") as f:
            f.write("{ invalid json }")

        loader = ConfigLoader(config_file)

        with pytest.raises(ConfigError) as exc_info:
            loader.load()

        assert "Invalid JSON" in str(exc_info.value)

    @pytest.mark.unit
    def test_reload_clears_cache(self, config_loader, config_file, valid_config_data) -> None:
        """reloadでキャッシュがクリアされる"""
        # 最初のload
        config1 = config_loader.load()
        assert config1["base_dir"] == "."

        # ファイルを変更
        valid_config_data["base_dir"] = "new_base"
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(valid_config_data, f)

        # reloadで新しい値を取得
        config2 = config_loader.reload()
        assert config2["base_dir"] == "new_base"

    @pytest.mark.unit
    def test_get_config_is_load_alias(self, config_loader) -> None:
        """get_configはloadのエイリアス"""
        config1 = config_loader.load()
        config2 = config_loader.get_config()
        assert config1 is config2  # 同じオブジェクト


# =============================================================================
# TestConfigLoaderGet - get/get_required/has_keyテスト
# =============================================================================


class TestConfigLoaderGet:
    """get/get_required/has_keyメソッドのテスト"""

    @pytest.mark.unit
    def test_get_existing_key(self, config_loader) -> None:
        """存在するキーの値を取得"""
        value = config_loader.get("base_dir")
        assert value == "."

    @pytest.mark.unit
    def test_get_missing_key_returns_default(self, config_loader) -> None:
        """存在しないキーはデフォルト値を返す"""
        value = config_loader.get("nonexistent_key", default="default_value")
        assert value == "default_value"

    @pytest.mark.unit
    def test_get_missing_key_returns_none_without_default(self, config_loader) -> None:
        """デフォルトなしで存在しないキーはNone"""
        value = config_loader.get("nonexistent_key")
        assert value is None

    @pytest.mark.unit
    def test_get_nested_key_returns_dict(self, config_loader) -> None:
        """ネストされたキーのdict取得"""
        paths = config_loader.get("paths")
        assert isinstance(paths, dict)
        assert "loops_dir" in paths

    @pytest.mark.unit
    def test_get_required_existing_key(self, config_loader) -> None:
        """get_required: 存在するキーの値を取得"""
        value = config_loader.get_required("base_dir")
        assert value == "."

    @pytest.mark.unit
    def test_get_required_missing_key_raises(self, config_loader) -> None:
        """get_required: 存在しないキーでConfigError"""
        with pytest.raises(ConfigError) as exc_info:
            config_loader.get_required("nonexistent_key")

        assert "Required configuration key missing" in str(exc_info.value)
        assert "nonexistent_key" in str(exc_info.value)

    @pytest.mark.unit
    def test_has_key_returns_true_for_existing(self, config_loader) -> None:
        """has_key: 存在するキーでTrue"""
        assert config_loader.has_key("base_dir") is True
        assert config_loader.has_key("paths") is True

    @pytest.mark.unit
    def test_has_key_returns_false_for_missing(self, config_loader) -> None:
        """has_key: 存在しないキーでFalse"""
        assert config_loader.has_key("nonexistent_key") is False


# =============================================================================
# TestConfigLoaderValidation - validate_required_keysテスト
# =============================================================================


class TestConfigLoaderValidation:
    """validate_required_keysメソッドのテスト"""

    @pytest.mark.unit
    def test_validate_all_required_keys_present(self, config_loader) -> None:
        """全必須キーが存在する場合、空リストを返す"""
        errors = config_loader.validate_required_keys()
        assert errors == []

    @pytest.mark.unit
    def test_validate_missing_required_key(self, config_file) -> None:
        """必須キーが欠けている場合、エラーリストを返す"""
        # 必須キーの一部が欠けた設定
        incomplete_config = {
            "base_dir": ".",
            "paths": {},
            # loops_path, digests_path, essences_path が欠けている
        }
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(incomplete_config, f)

        loader = ConfigLoader(config_file)
        errors = loader.validate_required_keys()

        # REQUIRED_KEYS = ["loops_path", "digests_path", "essences_path"]
        assert len(errors) == 3
        assert any("loops_path" in err for err in errors)
        assert any("digests_path" in err for err in errors)
        assert any("essences_path" in err for err in errors)

    @pytest.mark.unit
    def test_validate_partial_missing_keys(self, config_file) -> None:
        """一部の必須キーのみ欠けている場合"""
        partial_config = {
            "base_dir": ".",
            "paths": {},
            "loops_path": "data/Loops",
            # digests_path, essences_path が欠けている
        }
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(partial_config, f)

        loader = ConfigLoader(config_file)
        errors = loader.validate_required_keys()

        assert len(errors) == 2
        assert any("digests_path" in err for err in errors)
        assert any("essences_path" in err for err in errors)


# =============================================================================
# TestConfigLoaderCaching - キャッシュ動作テスト
# =============================================================================


class TestConfigLoaderCaching:
    """キャッシュ動作のテスト"""

    @pytest.mark.unit
    def test_load_returns_cached_config(self, config_loader) -> None:
        """2回目のloadはキャッシュを返す"""
        config1 = config_loader.load()
        config2 = config_loader.load()

        # 同一オブジェクトであることを確認
        assert config1 is config2

    @pytest.mark.unit
    def test_load_does_not_reread_file(self, config_loader, config_file, valid_config_data) -> None:
        """キャッシュがある場合、ファイルを再読み込みしない"""
        # 最初のload（キャッシュを作成）
        _ = config_loader.load()

        # ファイルを変更（キャッシュには影響しない）
        valid_config_data["base_dir"] = "changed_value"
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(valid_config_data, f)

        # 2回目のloadはキャッシュを返す
        config2 = config_loader.load()
        assert config2["base_dir"] == "."  # 変更前の値

    @pytest.mark.unit
    def test_reload_rereads_file(self, config_loader, config_file, valid_config_data) -> None:
        """reloadはファイルを再読み込みする"""
        # 最初のload
        config1 = config_loader.load()
        assert config1["base_dir"] == "."

        # ファイルを変更
        valid_config_data["base_dir"] = "reloaded_value"
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(valid_config_data, f)

        # reloadで新しい値を取得
        config2 = config_loader.reload()
        assert config2["base_dir"] == "reloaded_value"

        # 以降のloadは新しい値
        config3 = config_loader.load()
        assert config3["base_dir"] == "reloaded_value"

    @pytest.mark.unit
    def test_reload_clears_is_loaded_temporarily(self, config_loader) -> None:
        """reloadはキャッシュをクリアしてから再読み込み"""
        config_loader.load()
        assert config_loader.is_loaded is True

        # reload内部で_config = Noneが設定される
        config_loader.reload()
        # reload完了後はTrueに戻る
        assert config_loader.is_loaded is True


# =============================================================================
# TestConfigLoaderEdgeCases - エッジケーステスト
# =============================================================================


class TestConfigLoaderEdgeCases:
    """エッジケースのテスト"""

    @pytest.mark.unit
    def test_empty_config_file(self, config_file) -> None:
        """空のJSON設定ファイル"""
        with config_file.open("w", encoding="utf-8") as f:
            json.dump({}, f)

        loader = ConfigLoader(config_file)
        config = loader.load()

        assert config == {}
        assert loader.get("any_key") is None

    @pytest.mark.unit
    def test_config_with_unicode(self, config_file) -> None:
        """Unicode文字を含む設定"""
        unicode_config = {
            "title": "日本語タイトル",
            "description": "説明文 with émojis 🎉",
        }
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(unicode_config, f, ensure_ascii=False)

        loader = ConfigLoader(config_file)
        config = loader.load()

        assert config["title"] == "日本語タイトル"
        assert "🎉" in config["description"]

    @pytest.mark.unit
    def test_config_with_deeply_nested_structure(self, config_file) -> None:
        """深くネストされた設定"""
        nested_config = {"level1": {"level2": {"level3": {"value": "deep_value"}}}}
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(nested_config, f)

        loader = ConfigLoader(config_file)
        config = loader.load()

        assert config["level1"]["level2"]["level3"]["value"] == "deep_value"

    @pytest.mark.unit
    def test_config_with_array_values(self, config_file) -> None:
        """配列を含む設定"""
        array_config = {
            "items": ["item1", "item2", "item3"],
            "numbers": [1, 2, 3],
        }
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(array_config, f)

        loader = ConfigLoader(config_file)
        config = loader.load()

        assert len(config["items"]) == 3
        assert config["numbers"][1] == 2

    @pytest.mark.unit
    def test_config_with_null_values(self, config_file) -> None:
        """null値を含む設定"""
        null_config = {
            "nullable_field": None,
            "empty_string": "",
            "zero": 0,
        }
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(null_config, f)

        loader = ConfigLoader(config_file)
        config = loader.load()

        assert config["nullable_field"] is None
        assert config["empty_string"] == ""
        assert config["zero"] == 0

    @pytest.mark.unit
    def test_get_with_none_as_stored_value(self, config_file) -> None:
        """None値が保存されている場合とキーが存在しない場合の区別"""
        config_data = {
            "stored_none": None,
        }
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(config_data, f)

        loader = ConfigLoader(config_file)

        # キーは存在するがNone値
        assert loader.has_key("stored_none") is True
        assert loader.get("stored_none") is None
        assert loader.get("stored_none", default="default") is None  # デフォルト無視

        # キーが存在しない
        assert loader.has_key("nonexistent") is False
        assert loader.get("nonexistent", default="default") == "default"


# =============================================================================
# TestConfigLoaderStructureValidation - 構造検証テスト
# =============================================================================


class TestConfigLoaderStructureValidation:
    """config_loaderの構造検証テスト（Phase 4で追加したTypeGuard検証）"""

    @pytest.mark.unit
    def test_load_invalid_paths_structure_raises_config_error(self, config_file) -> None:
        """pathsが無効な構造の場合ConfigError"""
        invalid_config = {"paths": "not_a_dict"}
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(invalid_config, f)

        loader = ConfigLoader(config_file)

        with pytest.raises(ConfigError) as exc_info:
            loader.load()

        assert "Invalid config structure" in str(exc_info.value)

    @pytest.mark.unit
    def test_load_invalid_levels_structure_raises_config_error(self, config_file) -> None:
        """levelsが無効な構造の場合ConfigError"""
        invalid_config = {"levels": [1, 2, 3]}
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(invalid_config, f)

        loader = ConfigLoader(config_file)

        with pytest.raises(ConfigError) as exc_info:
            loader.load()

        assert "Invalid config structure" in str(exc_info.value)

    @pytest.mark.unit
    def test_load_valid_paths_and_levels_succeeds(self, config_file) -> None:
        """有効なpathsとlevelsの場合は成功"""
        valid_config = {"paths": {"loops_dir": "data"}, "levels": {"threshold": 5}}
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(valid_config, f)

        loader = ConfigLoader(config_file)
        config = loader.load()

        assert config["paths"]["loops_dir"] == "data"
        assert config["levels"]["threshold"] == 5

    @pytest.mark.unit
    def test_error_message_includes_file_path(self, config_file) -> None:
        """エラーメッセージにファイルパスが含まれる"""
        invalid_config = {"paths": "invalid"}
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(invalid_config, f)

        loader = ConfigLoader(config_file)

        with pytest.raises(ConfigError) as exc_info:
            loader.load()

        # ファイルパスがエラーメッセージに含まれる
        assert str(config_file) in str(exc_info.value)

    @pytest.mark.unit
    def test_error_message_includes_structure_hint(self, config_file) -> None:
        """エラーメッセージに構造ヒントが含まれる"""
        invalid_config = {"levels": None}
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(invalid_config, f)

        loader = ConfigLoader(config_file)

        with pytest.raises(ConfigError) as exc_info:
            loader.load()

        # 構造ヒントがエラーメッセージに含まれる
        assert "'paths' and 'levels' must be dict" in str(exc_info.value)

    @pytest.mark.unit
    def test_load_paths_none_raises_config_error(self, config_file) -> None:
        """pathsがNoneの場合ConfigError"""
        invalid_config = {"paths": None}
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(invalid_config, f)

        loader = ConfigLoader(config_file)

        with pytest.raises(ConfigError) as exc_info:
            loader.load()

        assert "Invalid config structure" in str(exc_info.value)

    @pytest.mark.unit
    def test_load_both_invalid_raises_config_error(self, config_file) -> None:
        """pathsとlevels両方が無効な場合ConfigError"""
        invalid_config = {"paths": "string", "levels": [1, 2, 3]}
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(invalid_config, f)

        loader = ConfigLoader(config_file)

        with pytest.raises(ConfigError) as exc_info:
            loader.load()

        assert "Invalid config structure" in str(exc_info.value)
