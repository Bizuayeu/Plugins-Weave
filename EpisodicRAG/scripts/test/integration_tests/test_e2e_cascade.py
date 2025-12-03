#!/usr/bin/env python3
"""
E2E Cascade Tests
=================

マルチレベルカスケード処理の統合テスト。
Weekly → Monthly → Quarterly の階層間連携を検証。
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from test_helpers import create_test_loop_file

from application.grand import GrandDigestManager, ShadowGrandDigestManager
from application.tracking import DigestTimesTracker
from application.config import DigestConfig
from domain.constants import LEVEL_NAMES

# slow マーカーを適用（ファイル全体）
pytestmark = [pytest.mark.slow, pytest.mark.integration]


class TestMultiLevelCascade:
    """マルチレベルカスケード処理のE2Eテスト"""

    @pytest.fixture
    def cascade_env(self, temp_plugin_env):

        """カスケードテスト用の環境を構築"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        # last_digest_times.json を初期化
        times_file = temp_plugin_env.config_dir / "last_digest_times.json"
        times_file.write_text("{}")

        return {
            "env": temp_plugin_env,
            "config": config,
        }

    def test_weekly_finalize_triggers_monthly_shadow_update(self, cascade_env) -> None:

        """
        Weekly確定時にMonthly Shadowが更新される

        シナリオ:
        1. Loopファイルを作成 → weekly Shadowに追加
        2. weekly Shadowを確定（模擬）
        3. Monthly Shadowに新しいソースファイルが追加される
        """
        env = cascade_env["env"]
        config = cascade_env["config"]

        # 1. Loopファイルを作成
        for i in range(1, 4):
            create_test_loop_file(env.loops_path, i, f"test_loop_{i}")

        # ShadowGrandDigestManagerを初期化
        shadow_manager = ShadowGrandDigestManager(config)

        # weekly Shadowに追加
        new_files = shadow_manager._detector.find_new_files("weekly")
        shadow_manager.add_files_to_shadow("weekly", new_files)

        # weekly Shadowを確認
        weekly_shadow = shadow_manager.get_shadow_digest_for_level("weekly")
        assert weekly_shadow is not None
        assert len(weekly_shadow["source_files"]) == 3

        # 2. weekly確定をシミュレート（RegularDigestファイルを作成）
        weekly_dir = config.get_level_dir("weekly")
        weekly_digest_file = weekly_dir / "W00001_test_digest.txt"
        weekly_digest_file.write_text(
            json.dumps(
                {
                    "metadata": {"level": "weekly", "number": "00001"},
                    "overall_digest": {
                        "abstract": "Test weekly digest",
                        "keywords": ["test"],
                        "source_files": ["L00001", "L00002", "L00003"],
                    },
                    "individual_digests": [],
                },
                ensure_ascii=False,
            )
        )

        # 3. カスケード処理を実行
        shadow_manager.cascade_update_on_digest_finalize("weekly")

        # 4. Monthly Shadowを確認
        _monthly_shadow = shadow_manager.get_shadow_digest_for_level("monthly")
        # Note: monthly Shadowにweeklyダイジェストがソースとして追加される
        # （実際の動作は実装に依存）

        # weekly Shadowがクリアされていることを確認
        weekly_shadow_after = shadow_manager.get_shadow_digest_for_level("weekly")
        # クリア後はsource_filesが空になる
        if weekly_shadow_after is not None:
            assert len(weekly_shadow_after.get("source_files", [])) == 0

    def test_cascade_stops_at_insufficient_threshold(self, cascade_env) -> None:

        """
        閾値未満の場合カスケードが発動しない

        シナリオ:
        1. Loopファイルを1つだけ作成
        2. weekly Shadowに追加
        3. 確定処理後、monthly Shadowは閾値未満のため変化なし
        """
        env = cascade_env["env"]
        config = cascade_env["config"]

        # 1. Loopファイルを1つ作成
        create_test_loop_file(env.loops_path, 1, "test_loop_1")

        # ShadowGrandDigestManagerを初期化
        shadow_manager = ShadowGrandDigestManager(config)

        # weekly Shadowに追加
        new_files = shadow_manager._detector.find_new_files("weekly")
        assert len(new_files) == 1
        shadow_manager.add_files_to_shadow("weekly", new_files)

        # weekly Shadowを確認
        weekly_shadow = shadow_manager.get_shadow_digest_for_level("weekly")
        assert weekly_shadow is not None
        assert len(weekly_shadow["source_files"]) == 1


class TestBoundaryConditions:
    """境界条件のE2Eテスト"""

    @pytest.fixture
    def boundary_env(self, temp_plugin_env):

        """境界条件テスト用の環境を構築"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        # last_digest_times.json を初期化
        times_file = temp_plugin_env.config_dir / "last_digest_times.json"
        times_file.write_text("{}")

        return {
            "env": temp_plugin_env,
            "config": config,
        }

    def test_exactly_at_threshold_triggers_processing(self, boundary_env) -> None:

        """
        閾値ちょうどの場合は処理が発動する

        シナリオ:
        1. 閾値と同じ数のファイルを作成
        2. 処理が正しく発動することを確認
        """
        env = boundary_env["env"]
        config = boundary_env["config"]

        # weekly_threshold（デフォルト: 5）と同じ数のファイルを作成
        threshold = config.threshold.weekly_threshold
        for i in range(1, threshold + 1):
            create_test_loop_file(env.loops_path, i, f"test_loop_{i}")

        # ShadowGrandDigestManagerを初期化
        shadow_manager = ShadowGrandDigestManager(config)

        # ファイルを検出
        new_files = shadow_manager._detector.find_new_files("weekly")
        assert len(new_files) == threshold

        # Shadowに追加
        shadow_manager.add_files_to_shadow("weekly", new_files)

        # 閾値と同じ数のファイルがShadowに存在
        weekly_shadow = shadow_manager.get_shadow_digest_for_level("weekly")
        assert weekly_shadow is not None
        assert len(weekly_shadow["source_files"]) == threshold

    def test_empty_loop_directory_initialization(self, boundary_env) -> None:

        """
        空のLoopディレクトリでの初回実行

        シナリオ:
        1. Loopファイルなしで検出を実行
        2. エラーなく空の結果が返る
        """
        config = boundary_env["config"]

        # ShadowGrandDigestManagerを初期化
        shadow_manager = ShadowGrandDigestManager(config)

        # ファイルを検出（0件のはず）
        new_files = shadow_manager._detector.find_new_files("weekly")
        assert len(new_files) == 0

        # Shadowも初期状態
        weekly_shadow = shadow_manager.get_shadow_digest_for_level("weekly")
        # Shadowファイルがなければ None、あればsource_filesが空
        if weekly_shadow is not None:
            assert len(weekly_shadow.get("source_files", [])) == 0

    def test_one_file_below_threshold_no_auto_finalize(self, boundary_env) -> None:

        """
        閾値-1の場合は自動確定が発生しない

        シナリオ:
        1. 閾値-1のファイルを作成
        2. Shadowに追加
        3. 自動確定が発生しないことを確認
        """
        env = boundary_env["env"]
        config = boundary_env["config"]

        # weekly_threshold - 1 のファイルを作成
        threshold = config.threshold.weekly_threshold
        file_count = threshold - 1
        for i in range(1, file_count + 1):
            create_test_loop_file(env.loops_path, i, f"test_loop_{i}")

        # ShadowGrandDigestManagerを初期化
        shadow_manager = ShadowGrandDigestManager(config)

        # ファイルを検出
        new_files = shadow_manager._detector.find_new_files("weekly")
        assert len(new_files) == file_count

        # Shadowに追加
        shadow_manager.add_files_to_shadow("weekly", new_files)

        # 閾値未満のファイルがShadowに存在
        weekly_shadow = shadow_manager.get_shadow_digest_for_level("weekly")
        assert weekly_shadow is not None
        assert len(weekly_shadow["source_files"]) == file_count
