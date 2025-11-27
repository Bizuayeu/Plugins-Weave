#!/usr/bin/env python3
"""
GrandDigestManager 統合テスト
==============================

一時ディレクトリを使用したファイルI/Oテスト
"""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# Application層
from application.grand import GrandDigestManager

# Domain層
from domain.constants import LEVEL_NAMES
from domain.exceptions import DigestError


@pytest.fixture
def grand_manager(temp_plugin_env):
    """GrandDigestManagerインスタンスを提供"""
    mock_config = MagicMock()
    mock_config.essences_path = temp_plugin_env.essences_path
    return GrandDigestManager(mock_config)


class TestGrandDigestManager:
    """GrandDigestManager の統合テスト"""

    @pytest.mark.integration
    def test_get_template_structure(self, grand_manager):
        """テンプレートの構造確認"""
        template = grand_manager.get_template()

        assert "metadata" in template
        assert "major_digests" in template
        assert set(template["major_digests"].keys()) == set(LEVEL_NAMES)

    @pytest.mark.integration
    def test_load_or_create_new(self, grand_manager):
        """新規作成時の動作"""
        data = grand_manager.load_or_create()

        assert grand_manager.grand_digest_file.exists()
        assert "metadata" in data

    @pytest.mark.integration
    def test_save_and_load(self, grand_manager):
        """保存と読み込みの整合性"""
        test_data = {"test": "data", "number": 123}
        grand_manager.save(test_data)

        with open(grand_manager.grand_digest_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)

        assert loaded == test_data

    @pytest.mark.integration
    def test_update_digest(self, grand_manager):
        """ダイジェスト更新（例外なしで成功）"""
        overall = {"digest_type": "test", "keywords": ["a", "b"]}
        # 例外が発生しなければ成功
        grand_manager.update_digest("weekly", "W0001_Test", overall)

        data = grand_manager.load_or_create()
        assert data["major_digests"]["weekly"]["overall_digest"] == overall

    @pytest.mark.integration
    def test_update_digest_invalid_level(self, grand_manager):
        """無効なレベルへの更新でDigestError"""
        with pytest.raises(DigestError):
            grand_manager.update_digest("invalid", "name", {})
