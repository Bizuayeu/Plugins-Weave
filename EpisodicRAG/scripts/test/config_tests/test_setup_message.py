#!/usr/bin/env python3
"""
test_setup_message.py
=====================

setup.sh廃止に伴うエラーメッセージテスト

TDD Red-Green-Refactor:
- Red: このテストは最初に失敗する（setup.sh参照が残っている）
- Green: エラーメッセージを更新して成功させる
- Refactor: 全テストがパスすることを確認
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from test_helpers import TempPluginEnvironment

import pytest

from domain.exceptions import ConfigError
from infrastructure.config.config_loader import ConfigLoader
from infrastructure.config.config_repository import load_config


class TestSetupMessageRemoved:
    """setup.sh参照がエラーメッセージから削除されていることを確認"""

    @pytest.mark.unit
    def test_config_repository_no_setup_sh_reference(
        self, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """config_repository: setup.sh参照がないこと"""
        nonexistent = temp_plugin_env.config_dir / "nonexistent.json"

        with pytest.raises(ConfigError) as exc_info:
            load_config(nonexistent)

        error_msg = str(exc_info.value)
        assert "setup.sh" not in error_msg, f"Error message still contains 'setup.sh': {error_msg}"
        assert "@digest-setup" in error_msg, (
            f"Error message should mention '@digest-setup': {error_msg}"
        )

    @pytest.mark.unit
    def test_config_loader_no_setup_sh_reference(
        self, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """config_loader: setup.sh参照がないこと"""
        nonexistent = temp_plugin_env.config_dir / "nonexistent.json"
        loader = ConfigLoader(nonexistent)

        with pytest.raises(ConfigError) as exc_info:
            loader.load()

        error_msg = str(exc_info.value)
        assert "setup.sh" not in error_msg, f"Error message still contains 'setup.sh': {error_msg}"
        assert "@digest-setup" in error_msg, (
            f"Error message should mention '@digest-setup': {error_msg}"
        )
