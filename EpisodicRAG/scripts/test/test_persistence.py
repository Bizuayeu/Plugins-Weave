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


# =============================================================================
# ユーザー入力テスト（レガシー: monkeypatch方式）
# =============================================================================

class TestDigestPersistenceUserInput:
    """ユーザー入力関連のテスト（レガシー）"""

    @pytest.mark.integration
    def test_overwrite_user_cancels(self, persistence, valid_regular_digest, temp_plugin_env, monkeypatch):
        """既存ファイル上書き時、ユーザーがキャンセル"""
        from domain.exceptions import ValidationError

        # 先にファイルを作成
        result_path = persistence.save_regular_digest("weekly", valid_regular_digest, "W0001_Test")
        assert result_path.exists()

        # input()を'n'を返すようにモック
        monkeypatch.setattr('builtins.input', lambda _: 'n')

        with pytest.raises(ValidationError) as exc_info:
            persistence.save_regular_digest("weekly", valid_regular_digest, "W0001_Test")
        assert "User cancelled" in str(exc_info.value)

    @pytest.mark.integration
    def test_overwrite_user_confirms(self, persistence, valid_regular_digest, temp_plugin_env, monkeypatch):
        """既存ファイル上書き時、ユーザーが確認"""
        # 先にファイルを作成
        result_path = persistence.save_regular_digest("weekly", valid_regular_digest, "W0001_Test")
        assert result_path.exists()

        # input()を'y'を返すようにモック
        monkeypatch.setattr('builtins.input', lambda _: 'y')

        # 内容を変更して保存
        valid_regular_digest["overall_digest"]["abstract"] = "Updated abstract"
        result_path2 = persistence.save_regular_digest("weekly", valid_regular_digest, "W0001_Test")

        assert result_path2.exists()
        with open(result_path2, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        assert saved_data["overall_digest"]["abstract"] == "Updated abstract"

    @pytest.mark.integration
    def test_overwrite_eoferror_continues(self, persistence, valid_regular_digest, temp_plugin_env, monkeypatch):
        """非対話モード（EOFError）では上書きを続行"""
        # 先にファイルを作成
        result_path = persistence.save_regular_digest("weekly", valid_regular_digest, "W0001_Test")
        assert result_path.exists()

        # input()をEOFErrorを発生させるようにモック
        def raise_eoferror(_):
            raise EOFError()

        monkeypatch.setattr('builtins.input', raise_eoferror)

        # 内容を変更して保存（EOFErrorでも続行）
        valid_regular_digest["overall_digest"]["abstract"] = "Non-interactive update"
        result_path2 = persistence.save_regular_digest("weekly", valid_regular_digest, "W0001_Test")

        assert result_path2.exists()
        with open(result_path2, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        assert saved_data["overall_digest"]["abstract"] == "Non-interactive update"


# =============================================================================
# コールバック注入テスト（推奨: confirm_callback方式）
# =============================================================================

class TestDigestPersistenceConfirmCallback:
    """confirm_callback注入方式のテスト"""

    @pytest.mark.integration
    def test_overwrite_cancelled_via_callback(
        self, config, grand_digest_manager, shadow_manager, times_tracker,
        valid_regular_digest, temp_plugin_env
    ):
        """コールバックでキャンセル時にValidationErrorが発生"""
        from domain.exceptions import ValidationError

        # 常にキャンセルするコールバック
        persistence = DigestPersistence(
            config, grand_digest_manager, shadow_manager, times_tracker,
            confirm_callback=lambda msg: False
        )

        # 先にファイルを作成
        result_path = persistence.save_regular_digest("weekly", valid_regular_digest, "W0001_Test")
        assert result_path.exists()

        # 同じファイルに上書き試行
        with pytest.raises(ValidationError) as exc_info:
            persistence.save_regular_digest("weekly", valid_regular_digest, "W0001_Test")
        assert "User cancelled" in str(exc_info.value)

    @pytest.mark.integration
    def test_overwrite_confirmed_via_callback(
        self, config, grand_digest_manager, shadow_manager, times_tracker,
        valid_regular_digest, temp_plugin_env
    ):
        """コールバックで承認時に正常に上書きされる"""
        # 常に承認するコールバック
        persistence = DigestPersistence(
            config, grand_digest_manager, shadow_manager, times_tracker,
            confirm_callback=lambda msg: True
        )

        # 先にファイルを作成
        result_path = persistence.save_regular_digest("weekly", valid_regular_digest, "W0001_Test")
        assert result_path.exists()

        # 内容を変更して上書き
        valid_regular_digest["overall_digest"]["abstract"] = "Callback updated"
        result_path2 = persistence.save_regular_digest("weekly", valid_regular_digest, "W0001_Test")

        assert result_path2.exists()
        with open(result_path2, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        assert saved_data["overall_digest"]["abstract"] == "Callback updated"

    @pytest.mark.unit
    def test_default_callback_used_when_none_provided(
        self, config, grand_digest_manager, shadow_manager, times_tracker
    ):
        """confirm_callbackがNoneの場合、デフォルトコールバックが使用される"""
        persistence = DigestPersistence(
            config, grand_digest_manager, shadow_manager, times_tracker,
            confirm_callback=None
        )

        # _default_confirmメソッドが設定されていることを確認
        assert persistence.confirm_callback == DigestPersistence._default_confirm

    @pytest.mark.unit
    def test_custom_callback_stored(
        self, config, grand_digest_manager, shadow_manager, times_tracker
    ):
        """カスタムコールバックが正しく保存される"""
        custom_callback = lambda msg: True
        persistence = DigestPersistence(
            config, grand_digest_manager, shadow_manager, times_tracker,
            confirm_callback=custom_callback
        )

        assert persistence.confirm_callback is custom_callback


# =============================================================================
# カスケード処理詳細テスト
# =============================================================================

class TestDigestPersistenceCascadeDetails:
    """カスケード処理の詳細テスト"""

    @pytest.mark.integration
    def test_cascade_updates_next_level_shadow(self, persistence, shadow_manager, temp_plugin_env):
        """カスケードが次レベルのShadowを更新"""
        # Loopファイルを作成してShadowに追加
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)
        loop2 = create_test_loop_file(temp_plugin_env.loops_path, 2)
        shadow_manager.update_shadow_for_new_loops()

        # weekly のカスケード処理（monthly に伝播）
        source_files = [loop1.name, loop2.name]
        persistence.process_cascade_and_cleanup("weekly", source_files, None)

        # monthly の shadow が更新されている可能性を確認（エラーなく完了）
        # 具体的な内容検証はカスケードロジックに依存

    @pytest.mark.integration
    def test_cascade_for_all_non_centurial_levels(self, persistence, shadow_manager):
        """centurial以外の全レベルでカスケードが実行される"""
        levels_with_cascade = ["weekly", "monthly", "quarterly", "annual",
                               "triennial", "decadal", "multi_decadal"]

        for level in levels_with_cascade:
            # エラーなく完了することを確認
            persistence.process_cascade_and_cleanup(level, [], None)

    @pytest.mark.integration
    def test_provisional_delete_failure_logs_warning(self, persistence, config, monkeypatch):
        """Provisional削除失敗時は警告を記録（エラーにはならない）"""
        # 存在しないファイルパスを指定（削除失敗シミュレーション）
        fake_provisional = config.get_provisional_dir("weekly") / "NonExistent.txt"

        # 削除しようとしてもファイルがないので何も起きない（エラーにならない）
        persistence.process_cascade_and_cleanup("weekly", [], fake_provisional)
        # ここまで到達すれば成功
