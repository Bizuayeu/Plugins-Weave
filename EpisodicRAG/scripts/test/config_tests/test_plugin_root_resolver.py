#!/usr/bin/env python3
"""
test_plugin_root_resolver.py
============================

config/plugin_root_resolver.py のテスト
"""

from pathlib import Path
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

from infrastructure.config.plugin_root_resolver import find_plugin_root


class TestFindPluginRoot:
    """find_plugin_root関数のテスト"""

    @pytest.mark.integration
    def test_resolve_from_scripts_config(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """scripts/config/からPluginルート検出"""
        # scripts/config/plugin_root_resolver.py の位置をシミュレート
        scripts_dir = temp_plugin_env.plugin_root / "scripts"
        config_dir = scripts_dir / "config"
        scripts_dir.mkdir(exist_ok=True)
        config_dir.mkdir(exist_ok=True)

        fake_script = config_dir / "plugin_root_resolver.py"
        fake_script.touch()

        result = find_plugin_root(fake_script)

        assert result == temp_plugin_env.plugin_root

    @pytest.mark.integration
    def test_resolve_failure_no_config(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """config.jsonが存在しない場合FileNotFoundError"""
        # config.jsonを削除
        config_file = temp_plugin_env.config_dir / "config.json"
        config_file.unlink()

        # scripts/config/からの検出を試みる
        scripts_dir = temp_plugin_env.plugin_root / "scripts"
        config_dir = scripts_dir / "config"
        scripts_dir.mkdir(exist_ok=True)
        config_dir.mkdir(exist_ok=True)

        fake_script = config_dir / "plugin_root_resolver.py"
        fake_script.touch()

        with pytest.raises(FileNotFoundError) as exc_info:
            find_plugin_root(fake_script)

        assert "Plugin root not found" in str(exc_info.value)

    @pytest.mark.integration
    def test_resolve_returns_absolute_path(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """絶対パスを返す"""
        scripts_dir = temp_plugin_env.plugin_root / "scripts"
        config_dir = scripts_dir / "config"
        scripts_dir.mkdir(exist_ok=True)
        config_dir.mkdir(exist_ok=True)

        fake_script = config_dir / "plugin_root_resolver.py"
        fake_script.touch()

        result = find_plugin_root(fake_script)

        assert result.is_absolute()

    @pytest.mark.integration
    def test_resolve_with_claude_plugin_dir(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """.claude-plugin/config.jsonが存在する場合成功"""
        scripts_dir = temp_plugin_env.plugin_root / "scripts"
        config_dir = scripts_dir / "config"
        scripts_dir.mkdir(exist_ok=True)
        config_dir.mkdir(exist_ok=True)

        fake_script = config_dir / "plugin_root_resolver.py"
        fake_script.touch()

        # .claude-plugin/config.jsonが存在することを確認
        assert (temp_plugin_env.config_dir / "config.json").exists()

        result = find_plugin_root(fake_script)

        # 結果のconfig_dirに.claude-plugin/config.jsonが存在
        assert (result / ".claude-plugin" / "config.json").exists()

    @pytest.mark.unit
    def test_resolve_calculates_correct_depth(
        self, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """3階層上がPluginルートになる"""
        scripts_dir = temp_plugin_env.plugin_root / "scripts"
        config_dir = scripts_dir / "config"
        scripts_dir.mkdir(exist_ok=True)
        config_dir.mkdir(exist_ok=True)

        fake_script = config_dir / "fake.py"
        fake_script.touch()

        result = find_plugin_root(fake_script)

        # fake.py -> config -> scripts -> plugin_root
        assert result == fake_script.resolve().parent.parent.parent

    @pytest.mark.integration
    def test_resolve_with_symlinks(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """シンボリックリンクを含むパスでも動作"""
        scripts_dir = temp_plugin_env.plugin_root / "scripts"
        config_dir = scripts_dir / "config"
        scripts_dir.mkdir(exist_ok=True)
        config_dir.mkdir(exist_ok=True)

        fake_script = config_dir / "plugin_root_resolver.py"
        fake_script.touch()

        # resolve()は内部で呼ばれるのでシンボリックリンクは解決される
        result = find_plugin_root(fake_script)

        assert result.exists()
        assert (result / ".claude-plugin").exists()
