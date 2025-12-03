#!/usr/bin/env python3
"""
test_config_repository.py
=========================

config/config_repository.py のテスト
"""

import json
from typing import TYPE_CHECKING

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

from domain.exceptions import ConfigError
from infrastructure.config.config_repository import load_config


class TestLoadConfig:
    """load_config関数のテスト"""

    @pytest.mark.unit
    def test_load_config_success(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """正常なJSONファイル読み込み"""
        config_file = temp_plugin_env.config_dir / "config.json"

        result = load_config(config_file)

        assert isinstance(result, dict)
        assert "paths" in result
        assert "levels" in result

    @pytest.mark.unit
    def test_load_config_file_not_found(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """ファイル不存在時ConfigError"""
        nonexistent_file = temp_plugin_env.config_dir / "nonexistent.json"

        with pytest.raises(ConfigError) as exc_info:
            load_config(nonexistent_file)

        assert "File not found" in str(exc_info.value)

    @pytest.mark.unit
    def test_load_config_invalid_json(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """不正JSON時ConfigError"""
        invalid_json_file = temp_plugin_env.config_dir / "invalid.json"
        invalid_json_file.write_text("{invalid json content", encoding='utf-8')

        with pytest.raises(ConfigError) as exc_info:
            load_config(invalid_json_file)

        assert "Invalid JSON" in str(exc_info.value)

    @pytest.mark.unit
    def test_load_config_returns_config_data_structure(
        self, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """戻り値がConfigData構造を持つ"""
        config_file = temp_plugin_env.config_dir / "config.json"

        result = load_config(config_file)

        # ConfigData型の必須フィールド確認
        assert "paths" in result
        paths = result["paths"]
        assert "loops_dir" in paths
        assert "digests_dir" in paths
        assert "essences_dir" in paths

    @pytest.mark.unit
    def test_load_config_preserves_values(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """設定値が正しく読み込まれる"""
        config_file = temp_plugin_env.config_dir / "config.json"

        # カスタム設定を書き込み
        custom_config = {
            "base_dir": "../custom",
            "paths": {
                "loops_dir": "custom/Loops",
                "digests_dir": "custom/Digests",
                "essences_dir": "custom/Essences",
            },
            "levels": {"weekly_threshold": 10},
        }
        config_file.write_text(json.dumps(custom_config), encoding='utf-8')

        result = load_config(config_file)

        assert result["base_dir"] == "../custom"
        assert result["paths"]["loops_dir"] == "custom/Loops"
        assert result["levels"]["weekly_threshold"] == 10

    @pytest.mark.unit
    def test_load_config_empty_json(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """空のJSONオブジェクトも読み込み可能"""
        empty_json_file = temp_plugin_env.config_dir / "empty.json"
        empty_json_file.write_text("{}", encoding='utf-8')

        result = load_config(empty_json_file)

        assert result == {}

    @pytest.mark.unit
    def test_load_config_unicode_content(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """Unicode文字を含むJSONファイル"""
        unicode_json_file = temp_plugin_env.config_dir / "unicode.json"
        unicode_config = {"description": "日本語テスト 🎉", "paths": {"loops_dir": "データ/ループ"}}
        unicode_json_file.write_text(
            json.dumps(unicode_config, ensure_ascii=False), encoding='utf-8'
        )

        result = load_config(unicode_json_file)

        assert result["description"] == "日本語テスト 🎉"
        assert result["paths"]["loops_dir"] == "データ/ループ"
