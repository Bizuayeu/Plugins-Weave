#!/usr/bin/env python3
"""
test_level_path_service.py
==========================

config/level_path_service.py のテスト
"""

import pytest

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Dict, List, Tuple
    from test_helpers import TempPluginEnvironment
    from application.config import DigestConfig
    from application.tracking import DigestTimesTracker
    from application.shadow import ShadowTemplate, ShadowIO, FileDetector
    from application.shadow.placeholder_manager import PlaceholderManager
    from application.grand import ShadowGrandDigestManager, GrandDigestManager
    from domain.types.level import LevelHierarchyEntry


from domain.exceptions import ConfigError
from application.config.level_path_service import LevelPathService
from domain.constants import LEVEL_CONFIG, LEVEL_NAMES


class TestLevelPathService:
    """LevelPathServiceクラスのテスト"""

    @pytest.fixture
    def service(self, temp_plugin_env: "TempPluginEnvironment"):

        """LevelPathServiceインスタンス"""
        return LevelPathService(temp_plugin_env.digests_path)

    @pytest.mark.unit
    @pytest.mark.parametrize("level", LEVEL_NAMES)
    def test_get_level_dir_for_each_level(self, service, level) -> None:

        """全8レベルのディレクトリパス取得"""
        result = service.get_level_dir(level)

        assert result.is_absolute()
        expected_dir_name = LEVEL_CONFIG[level]["dir"]
        assert result.name == expected_dir_name

    @pytest.mark.unit
    @pytest.mark.parametrize("level", LEVEL_NAMES)
    def test_get_provisional_dir_for_each_level(self, service, level) -> None:

        """全8レベルのProvisionalディレクトリパス取得"""
        result = service.get_provisional_dir(level)

        assert result.is_absolute()
        assert result.name == "Provisional"
        # 親ディレクトリがレベルディレクトリ
        assert result.parent.name == LEVEL_CONFIG[level]["dir"]

    @pytest.mark.unit
    def test_get_level_dir_weekly(self, service) -> None:

        """weeklyのディレクトリパス"""
        result = service.get_level_dir("weekly")

        assert result.name == "1_Weekly"

    @pytest.mark.unit
    def test_get_level_dir_monthly(self, service) -> None:

        """monthlyのディレクトリパス"""
        result = service.get_level_dir("monthly")

        assert result.name == "2_Monthly"

    @pytest.mark.unit
    def test_get_level_dir_centurial(self, service) -> None:

        """centurialのディレクトリパス"""
        result = service.get_level_dir("centurial")

        assert result.name == "8_Centurial"

    @pytest.mark.unit
    def test_invalid_level_raises_value_error(self, service) -> None:

        """不正レベル名でConfigError"""
        with pytest.raises(ConfigError) as exc_info:
            service.get_level_dir("invalid_level")

        assert "Invalid level" in str(exc_info.value)

    @pytest.mark.unit
    def test_provisional_dir_invalid_level(self, service) -> None:

        """不正レベル名でProvisional取得時もConfigError"""
        with pytest.raises(ConfigError) as exc_info:
            service.get_provisional_dir("invalid_level")

        assert "Invalid level" in str(exc_info.value)

    @pytest.mark.unit
    def test_digests_path_stored(self, temp_plugin_env: "TempPluginEnvironment") -> None:

        """digests_pathが正しく格納される"""
        service = LevelPathService(temp_plugin_env.digests_path)

        assert service.digests_path == temp_plugin_env.digests_path

    @pytest.mark.unit
    def test_level_dir_under_digests_path(self, service, temp_plugin_env: "TempPluginEnvironment") -> None:

        """レベルディレクトリがdigests_path配下"""
        result = service.get_level_dir("weekly")

        assert str(temp_plugin_env.digests_path) in str(result)

    @pytest.mark.unit
    def test_provisional_dir_structure(self, service) -> None:

        """Provisionalディレクトリの構造が正しい"""
        # 正しい構造: Digests/1_Weekly/Provisional
        result = service.get_provisional_dir("weekly")

        parts = result.parts
        # Provisionalの2つ上がDigests
        assert "Provisional" in parts
        assert "1_Weekly" in parts
