#!/usr/bin/env python3
"""
finalize/persistence.py のユニットテスト
========================================

DigestPersistenceクラスの動作を検証。
- save_regular_digest: RegularDigestの保存
- update_grand_digest: GrandDigest更新
- process_cascade_and_cleanup: カスケード処理とクリーンアップ
"""
import json
import pytest
from pathlib import Path

# Application層
from application.finalize import DigestPersistence
from application.grand import GrandDigestManager, ShadowGrandDigestManager
from application.tracking import DigestTimesTracker

# Domain層
from domain.exceptions import DigestError

# 設定
from config import DigestConfig
from test_helpers import create_test_loop_file


# =============================================================================
# フィクスチャ
# =============================================================================

@pytest.fixture
def config(temp_plugin_env):
    """テスト用DigestConfig"""
    return DigestConfig(plugin_root=temp_plugin_env.plugin_root)


@pytest.fixture
def grand_digest_manager(config):
    """テスト用GrandDigestManager"""
    return GrandDigestManager(config)


@pytest.fixture
def shadow_manager(config):
    """テスト用ShadowGrandDigestManager"""
    return ShadowGrandDigestManager(config)


@pytest.fixture
def times_tracker(config):
    """テスト用DigestTimesTracker"""
    return DigestTimesTracker(config)


@pytest.fixture
def persistence(config, grand_digest_manager, shadow_manager, times_tracker):
    """テスト用DigestPersistence"""
    return DigestPersistence(config, grand_digest_manager, shadow_manager, times_tracker)


@pytest.fixture
def valid_regular_digest():
    """有効なRegularDigest"""
    return {
        "metadata": {
            "digest_level": "weekly",
            "digest_number": "W0001",
            "last_updated": "2025-01-01T00:00:00",
            "version": "1.0"
        },
        "overall_digest": {
            "name": "W0001_Test",
            "timestamp": "2025-01-01T00:00:00",
            "source_files": ["Loop0001_test.txt"],
            "digest_type": "週次統合",
            "keywords": ["test"],
            "abstract": "Test abstract",
            "impression": "Test impression"
        },
        "individual_digests": []
    }


# =============================================================================
# DigestPersistence.save_regular_digest テスト
# =============================================================================

class TestDigestPersistenceSaveRegularDigest:
    """save_regular_digest メソッドのテスト"""

    @pytest.mark.integration
    def test_saves_new_digest(self, persistence, valid_regular_digest, temp_plugin_env):
        """新しいdigestを保存"""
        result_path = persistence.save_regular_digest("weekly", valid_regular_digest, "W0001_Test")

        assert result_path.exists()
        assert result_path.name == "W0001_Test.txt"

        # 内容を検証
        with open(result_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        assert saved_data["overall_digest"]["name"] == "W0001_Test"

    @pytest.mark.integration
    def test_creates_directory_if_not_exists(self, persistence, valid_regular_digest, temp_plugin_env):
        """ディレクトリがなければ作成"""
        # 1_Weeklyディレクトリを削除
        import shutil
        weekly_dir = temp_plugin_env.digests_path / "1_Weekly"
        shutil.rmtree(weekly_dir)

        result_path = persistence.save_regular_digest("weekly", valid_regular_digest, "W0001_Test")

        assert result_path.exists()
        assert weekly_dir.exists()

    @pytest.mark.integration
    def test_saves_to_correct_level_directory(self, persistence, valid_regular_digest, temp_plugin_env):
        """正しいレベルディレクトリに保存"""
        # monthlyに保存
        valid_regular_digest["metadata"]["digest_level"] = "monthly"
        result_path = persistence.save_regular_digest("monthly", valid_regular_digest, "M001_Test")

        expected_dir = temp_plugin_env.digests_path / "2_Monthly"
        assert result_path.parent == expected_dir


# =============================================================================
# DigestPersistence.update_grand_digest テスト
# =============================================================================

class TestDigestPersistenceUpdateGrandDigest:
    """update_grand_digest メソッドのテスト"""

    @pytest.mark.integration
    def test_updates_grand_digest(self, persistence, valid_regular_digest, grand_digest_manager):
        """GrandDigestが更新される"""
        persistence.update_grand_digest("weekly", valid_regular_digest, "W0001_Test")

        # GrandDigestを読み込んで確認
        grand_data = grand_digest_manager.load_or_create()
        weekly_digest = grand_data["major_digests"]["weekly"]["overall_digest"]
        assert weekly_digest is not None
        assert weekly_digest["name"] == "W0001_Test"

    @pytest.mark.integration
    def test_raises_on_invalid_overall_digest(self, persistence):
        """overall_digestが無効な場合はDigestError"""
        invalid_digest = {
            "metadata": {},
            "overall_digest": None,  # 無効
            "individual_digests": []
        }

        with pytest.raises(DigestError) as exc_info:
            persistence.update_grand_digest("weekly", invalid_digest, "W0001_Test")
        assert "no valid overall_digest" in str(exc_info.value)

    @pytest.mark.integration
    def test_raises_on_missing_overall_digest(self, persistence):
        """overall_digestがない場合はDigestError"""
        invalid_digest = {
            "metadata": {},
            # overall_digestがない
            "individual_digests": []
        }

        with pytest.raises(DigestError) as exc_info:
            persistence.update_grand_digest("weekly", invalid_digest, "W0001_Test")
        assert "no valid overall_digest" in str(exc_info.value)


# =============================================================================
# DigestPersistence.process_cascade_and_cleanup テスト
# =============================================================================

class TestDigestPersistenceProcessCascadeAndCleanup:
    """process_cascade_and_cleanup メソッドのテスト"""

    @pytest.mark.integration
    def test_updates_times_tracker(self, persistence, times_tracker, temp_plugin_env):
        """times_trackerが更新される"""
        source_files = ["Loop0001_test.txt", "Loop0002_test.txt"]
        persistence.process_cascade_and_cleanup("weekly", source_files, None)

        # times_trackerを確認
        times_data = times_tracker.load_or_create()
        assert times_data["weekly"]["last_processed"] is not None

    @pytest.mark.integration
    def test_removes_provisional_file(self, persistence, config):
        """Provisionalファイルが削除される"""
        # Provisionalファイルを作成
        provisional_dir = config.get_provisional_dir("weekly")
        provisional_path = provisional_dir / "W0001_Individual.txt"
        with open(provisional_path, 'w', encoding='utf-8') as f:
            json.dump({"test": "data"}, f)

        assert provisional_path.exists()

        persistence.process_cascade_and_cleanup("weekly", ["Loop0001.txt"], provisional_path)

        assert not provisional_path.exists()

    @pytest.mark.integration
    def test_handles_none_provisional_file(self, persistence):
        """Provisionalファイルがない場合も正常に動作"""
        # エラーなく完了すればOK
        persistence.process_cascade_and_cleanup("weekly", ["Loop0001.txt"], None)

    @pytest.mark.integration
    def test_skips_cascade_for_centurial(self, persistence, shadow_manager, temp_plugin_env):
        """centurialではカスケードがスキップされる"""
        # エラーなく完了すればOK（centurialにはnext=Noneなので）
        persistence.process_cascade_and_cleanup("centurial", [], None)


# =============================================================================
# DigestPersistence 初期化テスト
# =============================================================================

class TestDigestPersistenceInit:
    """DigestPersistence 初期化のテスト"""

    @pytest.mark.unit
    def test_stores_dependencies(self, config, grand_digest_manager, shadow_manager, times_tracker):
        """依存関係が正しく保存される"""
        persistence = DigestPersistence(config, grand_digest_manager, shadow_manager, times_tracker)

        assert persistence.config is config
        assert persistence.grand_digest_manager is grand_digest_manager
        assert persistence.shadow_manager is shadow_manager
        assert persistence.times_tracker is times_tracker

    @pytest.mark.unit
    def test_sets_digests_path(self, config, grand_digest_manager, shadow_manager, times_tracker):
        """digests_pathが設定される"""
        persistence = DigestPersistence(config, grand_digest_manager, shadow_manager, times_tracker)

        assert persistence.digests_path == config.digests_path
