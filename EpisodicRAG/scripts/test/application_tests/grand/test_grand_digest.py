#!/usr/bin/env python3
"""
GrandDigestManager テスト
=========================

ユニットテストと統合テスト
"""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Application層
from application.grand import GrandDigestManager

# Domain層
from domain.constants import LEVEL_NAMES
from domain.exceptions import DigestError
from domain.version import DIGEST_FORMAT_VERSION


@pytest.fixture
def grand_manager(temp_plugin_env):

    """GrandDigestManagerインスタンスを提供"""
    mock_config = MagicMock()
    mock_config.essences_path = temp_plugin_env.essences_path
    return GrandDigestManager(mock_config)


# =============================================================================
# ユニットテスト
# =============================================================================


class TestGrandDigestManagerUnit:
    """GrandDigestManager のユニットテスト"""

    @pytest.mark.unit
    def test_get_template_returns_valid_structure(self, grand_manager) -> None:

        """get_template() は有効な構造を返す"""
        template = grand_manager.get_template()

        assert isinstance(template, dict)
        assert "metadata" in template
        assert "major_digests" in template

    @pytest.mark.unit
    def test_get_template_has_all_levels(self, grand_manager) -> None:

        """get_template() は全8レベルを含む"""
        template = grand_manager.get_template()

        assert set(template["major_digests"].keys()) == set(LEVEL_NAMES)

    @pytest.mark.unit
    def test_get_template_metadata_has_version(self, grand_manager) -> None:

        """get_template() のmetadataにversionが含まれる"""
        template = grand_manager.get_template()

        assert "version" in template["metadata"]
        assert template["metadata"]["version"] == DIGEST_FORMAT_VERSION

    @pytest.mark.unit
    def test_get_template_metadata_has_last_updated(self, grand_manager) -> None:

        """get_template() のmetadataにlast_updatedが含まれる"""
        template = grand_manager.get_template()

        assert "last_updated" in template["metadata"]
        assert template["metadata"]["last_updated"]  # 空でない

    @pytest.mark.unit
    def test_get_template_levels_have_overall_digest_key(self, grand_manager) -> None:

        """get_template() の各レベルにoverall_digestキーが存在"""
        template = grand_manager.get_template()

        for level in LEVEL_NAMES:
            assert "overall_digest" in template["major_digests"][level]

    @pytest.mark.unit
    def test_get_template_initial_overall_digests_are_none(self, grand_manager) -> None:

        """get_template() の初期状態ではoverall_digestはNone"""
        template = grand_manager.get_template()

        for level in LEVEL_NAMES:
            assert template["major_digests"][level]["overall_digest"] is None

    @pytest.mark.unit
    def test_grand_digest_file_path(self, grand_manager) -> None:

        """grand_digest_fileパスが正しく設定される"""
        assert grand_manager.grand_digest_file.name == "GrandDigest.txt"
        assert grand_manager.grand_digest_file.parent == grand_manager.config.essences_path


# =============================================================================
# 統合テスト
# =============================================================================


class TestGrandDigestManagerIntegration:
    """GrandDigestManager の統合テスト"""

    @pytest.mark.integration
    def test_load_or_create_creates_file_when_missing(self, grand_manager) -> None:

        """load_or_create() はファイルがない場合に新規作成する"""
        assert not grand_manager.grand_digest_file.exists()

        data = grand_manager.load_or_create()

        assert grand_manager.grand_digest_file.exists()
        assert "metadata" in data
        assert "major_digests" in data

    @pytest.mark.integration
    def test_load_or_create_loads_existing_file(self, grand_manager) -> None:

        """load_or_create() は既存ファイルを読み込む"""
        # ファイルを作成
        test_data = {"metadata": {"custom": True}, "major_digests": {}}
        grand_manager.grand_digest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(grand_manager.grand_digest_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        data = grand_manager.load_or_create()

        assert data["metadata"]["custom"] is True

    @pytest.mark.integration
    def test_load_or_create_with_corrupted_file(self, grand_manager) -> None:

        """load_or_create() は破損ファイルでFileIOErrorを発生"""
        from domain.exceptions import FileIOError

        grand_manager.grand_digest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(grand_manager.grand_digest_file, 'w', encoding='utf-8') as f:
            f.write("not valid json {{{")

        with pytest.raises(FileIOError):
            grand_manager.load_or_create()

    @pytest.mark.integration
    def test_save_creates_parent_directories(self, temp_plugin_env) -> None:

        """save() は親ディレクトリを自動作成する"""
        import shutil

        mock_config = MagicMock()
        # 存在しないサブディレクトリを指定
        mock_config.essences_path = temp_plugin_env.essences_path / "nested" / "deep"

        manager = GrandDigestManager(mock_config)

        # ディレクトリが存在しないことを確認
        assert not mock_config.essences_path.exists()

        # 保存
        manager.save({"test": "data"})

        # ファイルが作成されることを確認
        assert manager.grand_digest_file.exists()

    @pytest.mark.integration
    def test_save_and_load_roundtrip(self, grand_manager) -> None:

        """保存と読み込みの整合性"""
        test_data = {"test": "data", "number": 123, "nested": {"key": "value"}}
        grand_manager.save(test_data)

        with open(grand_manager.grand_digest_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)

        assert loaded == test_data

    @pytest.mark.integration
    def test_update_digest_success(self, grand_manager) -> None:

        """update_digest() は正常に更新する"""
        overall = {
            "digest_type": "test",
            "keywords": ["a", "b"],
            "abstract": "Test abstract",
            "impression": "Test impression",
        }
        grand_manager.update_digest("weekly", "W0001_Test", overall)

        data = grand_manager.load_or_create()
        assert data["major_digests"]["weekly"]["overall_digest"] == overall

    @pytest.mark.integration
    def test_update_digest_preserves_monthly_when_weekly_updated(self, grand_manager) -> None:

        """update_digest() でweekly更新時にmonthlyが保持される"""
        # まずmonthlyを更新
        monthly_digest = {"type": "monthly"}
        grand_manager.update_digest("monthly", "M0001", monthly_digest)

        # 次にweeklyを更新
        weekly_digest = {"type": "weekly"}
        grand_manager.update_digest("weekly", "W0001", weekly_digest)

        # monthlyが保持されていることを確認
        data = grand_manager.load_or_create()
        assert data["major_digests"]["monthly"]["overall_digest"] == monthly_digest

    @pytest.mark.integration
    def test_update_digest_sets_weekly_correctly(self, grand_manager) -> None:

        """update_digest() でweeklyが正しく設定される"""
        # まずmonthlyを更新
        monthly_digest = {"type": "monthly"}
        grand_manager.update_digest("monthly", "M0001", monthly_digest)

        # 次にweeklyを更新
        weekly_digest = {"type": "weekly"}
        grand_manager.update_digest("weekly", "W0001", weekly_digest)

        # weeklyが正しく設定されていることを確認
        data = grand_manager.load_or_create()
        assert data["major_digests"]["weekly"]["overall_digest"] == weekly_digest

    @pytest.mark.integration
    def test_update_digest_updates_last_updated(self, grand_manager) -> None:

        """update_digest() はlast_updatedを更新する"""
        # 初期作成
        grand_manager.load_or_create()
        data1 = grand_manager.load_or_create()
        ts1 = data1["metadata"]["last_updated"]

        # 少し待ってから更新
        import time

        time.sleep(0.01)

        grand_manager.update_digest("weekly", "W0001", {"test": True})
        data2 = grand_manager.load_or_create()
        ts2 = data2["metadata"]["last_updated"]

        assert ts2 > ts1

    @pytest.mark.integration
    def test_update_digest_invalid_level_raises(self, grand_manager) -> None:

        """update_digest() は無効なレベルでDigestErrorを発生"""
        with pytest.raises(DigestError) as exc_info:
            grand_manager.update_digest("invalid_level", "name", {})

        assert "Unknown level" in str(exc_info.value)

    @pytest.mark.integration
    def test_update_digest_with_missing_major_digests(self, grand_manager) -> None:

        """update_digest() はmajor_digestsがない場合にDigestErrorを発生"""
        # major_digestsがないファイルを作成
        grand_manager.grand_digest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(grand_manager.grand_digest_file, 'w', encoding='utf-8') as f:
            json.dump({"metadata": {}}, f)

        with pytest.raises(DigestError) as exc_info:
            grand_manager.update_digest("weekly", "W0001", {})

        assert "major_digests" in str(exc_info.value)
