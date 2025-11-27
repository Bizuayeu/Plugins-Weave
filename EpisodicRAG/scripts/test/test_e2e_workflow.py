#!/usr/bin/env python3
"""
E2E Workflow Tests
==================

エンドツーエンドの統合テスト。
実際のワークフローに近い形でシステム全体の動作を検証。

テストシナリオ:
1. 新規Loopファイル検出 → Shadow更新
2. Shadow → Regular → Grand の昇格フロー
3. カスケード処理の検証
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# Application層
# テストヘルパー
from test_helpers import create_test_loop_file

from application.grand import GrandDigestManager, ShadowGrandDigestManager
from application.tracking import DigestTimesTracker

# 設定
from config import DigestConfig

# Domain層
from domain.constants import LEVEL_NAMES

# Interfaces層
from interfaces import DigestFinalizerFromShadow

# =============================================================================
# E2E: Loop検出からShadow更新
# =============================================================================


class TestE2ELoopDetectionToShadow:
    """新規Loopファイル検出 → Shadow更新のE2Eテスト"""

    @pytest.fixture
    def e2e_env(self, temp_plugin_env):
        """E2Eテスト用の環境を構築"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        # last_digest_times.json を初期化
        times_file = temp_plugin_env.config_dir / "last_digest_times.json"
        times_file.write_text("{}")

        return {
            "env": temp_plugin_env,
            "config": config,
        }

    @pytest.mark.integration
    def test_new_loops_detected_and_added_to_shadow(self, e2e_env):
        """新規Loopファイルが検出されShadowに追加される"""
        env = e2e_env["env"]
        config = e2e_env["config"]

        # Loopファイルを作成
        for i in range(1, 4):
            create_test_loop_file(env.loops_path, i, f"test_loop_{i}")

        # ShadowGrandDigestManagerを初期化
        shadow_manager = ShadowGrandDigestManager(config)

        # 新しいLoopを検出
        new_files = shadow_manager._detector.find_new_files("weekly")

        # 3つのファイルが検出される
        assert len(new_files) == 3

        # Shadowに追加
        shadow_manager.add_files_to_shadow("weekly", new_files)

        # Shadow内容を確認
        shadow_digest = shadow_manager.get_shadow_digest_for_level("weekly")
        assert shadow_digest is not None
        assert len(shadow_digest["source_files"]) == 3

    @pytest.mark.integration
    def test_incremental_loop_detection(self, e2e_env):
        """増分検出：既存ファイルは再検出されない"""
        env = e2e_env["env"]
        config = e2e_env["config"]

        # 初回: 3つのLoopファイルを作成
        for i in range(1, 4):
            create_test_loop_file(env.loops_path, i, f"test_loop_{i}")

        shadow_manager = ShadowGrandDigestManager(config)
        times_tracker = DigestTimesTracker(config)

        # 初回検出
        new_files = shadow_manager._detector.find_new_files("weekly")
        assert len(new_files) == 3

        # last_processedを更新
        file_names = [f.name for f in new_files]
        times_tracker.save("weekly", file_names)

        # 追加: 2つのLoopファイルを作成
        for i in range(4, 6):
            create_test_loop_file(env.loops_path, i, f"test_loop_{i}")

        # 再検出（新しいファイルのみ）
        # DigestTimesTrackerを再読み込み
        shadow_manager2 = ShadowGrandDigestManager(config)
        new_files2 = shadow_manager2._detector.find_new_files("weekly")

        # 2つの新しいファイルのみ検出
        assert len(new_files2) == 2
        filenames = [f.name for f in new_files2]
        assert any("Loop0004" in name for name in filenames)
        assert any("Loop0005" in name for name in filenames)


# =============================================================================
# E2E: Shadow → Regular → Grand 昇格フロー
# =============================================================================


class TestE2EDigestPromotion:
    """ダイジェスト昇格フロー（Shadow → Regular → Grand）のE2Eテスト"""

    @pytest.fixture
    def promotion_env(self, temp_plugin_env):
        """昇格テスト用の環境を構築"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        # 必要なディレクトリを作成
        weekly_dir = temp_plugin_env.digests_path / "1_Weekly"
        weekly_dir.mkdir(parents=True, exist_ok=True)
        provisional_dir = weekly_dir / "Provisional"
        provisional_dir.mkdir(parents=True, exist_ok=True)

        # last_digest_times.json を初期化
        times_file = temp_plugin_env.config_dir / "last_digest_times.json"
        times_file.write_text("{}")

        # GrandDigest.txt を初期化
        grand_file = temp_plugin_env.essences_path / "GrandDigest.txt"
        grand_template = {
            "metadata": {"version": "test"},
            "major_digests": {level: {"overall_digest": None} for level in LEVEL_NAMES},
        }
        with open(grand_file, 'w', encoding='utf-8') as f:
            json.dump(grand_template, f, ensure_ascii=False, indent=2)

        return {
            "env": temp_plugin_env,
            "config": config,
            "weekly_dir": weekly_dir,
            "provisional_dir": provisional_dir,
        }

    @pytest.mark.integration
    def test_shadow_to_regular_promotion(self, promotion_env):
        """ShadowからRegularへの昇格が正しく行われる"""
        env = promotion_env["env"]
        config = promotion_env["config"]
        weekly_dir = promotion_env["weekly_dir"]

        # Loopファイルを作成
        for i in range(1, 4):
            create_test_loop_file(env.loops_path, i, f"test_loop_{i}")

        # ShadowGrandDigestを初期化・更新
        shadow_manager = ShadowGrandDigestManager(config)
        new_files = shadow_manager._detector.find_new_files("weekly")
        shadow_manager.add_files_to_shadow("weekly", new_files)

        # Shadowにテストデータを設定
        shadow_data = shadow_manager._io.load_or_create()
        shadow_data["latest_digests"]["weekly"]["overall_digest"] = {
            "digest_type": "weekly",
            "source_files": ["Loop0001_test.txt", "Loop0002_test.txt", "Loop0003_test.txt"],
            "abstract": "Test abstract",
            "keywords": ["test", "e2e"],
            "key_insights": ["insight1"],
            "learning_points": ["point1"],
            "emotional_context": {"primary": "neutral"},
            "connections": {"technical": []},
        }
        shadow_manager._io.save(shadow_data)

        # GrandDigestManagerを初期化
        grand_manager = GrandDigestManager(config)

        # DigestFinalizerを初期化（依存注入）
        finalizer = DigestFinalizerFromShadow(
            config=config,
            grand_digest_manager=grand_manager,
            shadow_manager=shadow_manager,
        )

        # 昇格実行
        finalizer.finalize_from_shadow("weekly", "E2E Test Digest")

        # RegularDigestファイルが作成されたことを確認
        regular_files = list(weekly_dir.glob("W0001_*.txt"))
        assert len(regular_files) == 1
        assert "E2E_Test_Digest" in regular_files[0].name

        # GrandDigestが更新されたことを確認
        grand_data = grand_manager.load_or_create()
        assert grand_data["major_digests"]["weekly"]["overall_digest"] is not None


# =============================================================================
# E2E: カスケード処理
# =============================================================================


class TestE2ECascadeProcessing:
    """カスケード処理のE2Eテスト"""

    @pytest.fixture
    def cascade_env(self, temp_plugin_env):
        """カスケードテスト用の環境を構築"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        # 必要なディレクトリを作成
        for i, name in enumerate(["1_Weekly", "2_Monthly"], start=1):
            dir_path = temp_plugin_env.digests_path / name
            dir_path.mkdir(parents=True, exist_ok=True)

        # last_digest_times.json を初期化
        times_file = temp_plugin_env.config_dir / "last_digest_times.json"
        times_file.write_text("{}")

        return {
            "env": temp_plugin_env,
            "config": config,
        }

    @pytest.mark.integration
    def test_weekly_finalize_triggers_monthly_shadow_update(self, cascade_env):
        """Weekly確定時にMonthlyShadowが更新される"""
        env = cascade_env["env"]
        config = cascade_env["config"]

        # Weeklyディレクトリにファイルを作成（Monthlyのソース）
        weekly_dir = env.digests_path / "1_Weekly"
        for i in range(1, 3):
            filename = f"W{i:04d}_test.txt"
            filepath = weekly_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({"test": f"weekly{i}"}, f)

        # ShadowGrandDigestManagerを初期化
        shadow_manager = ShadowGrandDigestManager(config)

        # Weeklyレベルのカスケード処理をシミュレート
        # （実際のカスケードは次レベルのShadowを更新する）
        monthly_new_files = shadow_manager._detector.find_new_files("monthly")

        # Weeklyファイルが検出される
        assert len(monthly_new_files) == 2


# =============================================================================
# E2E: フルワークフロー
# =============================================================================


class TestE2EFullWorkflow:
    """完全なワークフローのE2Eテスト"""

    @pytest.fixture
    def full_env(self, temp_plugin_env):
        """フルワークフローテスト用の環境を構築"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        # 必要なディレクトリを作成
        for name in ["1_Weekly", "2_Monthly"]:
            dir_path = temp_plugin_env.digests_path / name
            dir_path.mkdir(parents=True, exist_ok=True)
            provisional = dir_path / "Provisional"
            provisional.mkdir(exist_ok=True)

        # last_digest_times.json を初期化
        times_file = temp_plugin_env.config_dir / "last_digest_times.json"
        times_file.write_text("{}")

        # GrandDigest.txt を初期化
        grand_file = temp_plugin_env.essences_path / "GrandDigest.txt"
        grand_template = {
            "metadata": {"version": "test"},
            "major_digests": {level: {"overall_digest": None} for level in LEVEL_NAMES},
        }
        with open(grand_file, 'w', encoding='utf-8') as f:
            json.dump(grand_template, f, ensure_ascii=False, indent=2)

        return {
            "env": temp_plugin_env,
            "config": config,
        }

    @pytest.mark.integration
    def test_complete_workflow_loop_to_grand(self, full_env):
        """Loop作成からGrand更新までの完全なワークフロー"""
        env = full_env["env"]
        config = full_env["config"]

        # Step 1: Loopファイルを作成
        for i in range(1, 6):
            create_test_loop_file(env.loops_path, i, f"workflow_loop_{i}")

        # Step 2: Shadowを更新
        shadow_manager = ShadowGrandDigestManager(config)
        new_files = shadow_manager._detector.find_new_files("weekly")
        assert len(new_files) == 5

        shadow_manager.add_files_to_shadow("weekly", new_files)

        # Step 3: Shadow内容を確認
        shadow_digest = shadow_manager.get_shadow_digest_for_level("weekly")
        assert shadow_digest is not None
        assert len(shadow_digest["source_files"]) == 5

        # Step 4: Shadowデータを完成させる（Claude分析をシミュレート）
        shadow_data = shadow_manager._io.load_or_create()
        shadow_data["latest_digests"]["weekly"]["overall_digest"].update(
            {
                "abstract": "Complete workflow test abstract",
                "keywords": ["workflow", "e2e", "complete"],
                "key_insights": ["Full workflow works"],
                "learning_points": ["E2E testing is valuable"],
                "emotional_context": {"primary": "confident"},
                "connections": {"technical": ["testing"]},
            }
        )
        shadow_manager._io.save(shadow_data)

        # Step 5: Grandを更新
        grand_manager = GrandDigestManager(config)
        times_tracker = DigestTimesTracker(config)

        finalizer = DigestFinalizerFromShadow(
            config=config,
            grand_digest_manager=grand_manager,
            shadow_manager=shadow_manager,
            times_tracker=times_tracker,
        )

        finalizer.finalize_from_shadow("weekly", "Complete Workflow Test")

        # Step 6: 結果を検証
        # RegularDigestが作成された
        weekly_dir = env.digests_path / "1_Weekly"
        regular_files = list(weekly_dir.glob("W0001_*.txt"))
        assert len(regular_files) == 1

        # GrandDigestが更新された
        grand_data = grand_manager.load_or_create()
        assert grand_data["major_digests"]["weekly"]["overall_digest"] is not None

        # last_digest_timesが更新された
        times_data = times_tracker.load_or_create()
        assert times_data["weekly"]["last_processed"] is not None

    @pytest.mark.integration
    def test_multiple_weekly_cycles(self, full_env):
        """複数回のWeeklyサイクルが正しく処理される"""
        env = full_env["env"]
        config = full_env["config"]

        shadow_manager = ShadowGrandDigestManager(config)
        grand_manager = GrandDigestManager(config)
        times_tracker = DigestTimesTracker(config)

        # サイクル1: Loop 1-3
        for i in range(1, 4):
            create_test_loop_file(env.loops_path, i, f"cycle1_loop_{i}")

        new_files = shadow_manager._detector.find_new_files("weekly")
        shadow_manager.add_files_to_shadow("weekly", new_files)

        # Shadowを完成させる
        shadow_data = shadow_manager._io.load_or_create()
        shadow_data["latest_digests"]["weekly"]["overall_digest"].update(
            {
                "abstract": "Cycle 1 abstract",
                "keywords": ["cycle1"],
                "key_insights": ["insight1"],
                "learning_points": ["point1"],
                "emotional_context": {"primary": "neutral"},
                "connections": {"technical": []},
            }
        )
        shadow_manager._io.save(shadow_data)

        # サイクル1を確定
        finalizer = DigestFinalizerFromShadow(
            config=config,
            grand_digest_manager=grand_manager,
            shadow_manager=shadow_manager,
            times_tracker=times_tracker,
        )
        finalizer.finalize_from_shadow("weekly", "Cycle 1 Digest")

        # サイクル2: Loop 4-6
        for i in range(4, 7):
            create_test_loop_file(env.loops_path, i, f"cycle2_loop_{i}")

        # 新しいShadowManagerインスタンスで検出
        shadow_manager2 = ShadowGrandDigestManager(config)
        new_files2 = shadow_manager2._detector.find_new_files("weekly")

        # 3つの新しいファイルのみ検出
        assert len(new_files2) == 3
        filenames = [f.name for f in new_files2]
        assert not any("Loop0001" in name for name in filenames)
        assert any("Loop0004" in name for name in filenames)

        # サイクル2をShadowに追加
        shadow_manager2.add_files_to_shadow("weekly", new_files2)

        # Shadowを完成させる
        shadow_data2 = shadow_manager2._io.load_or_create()
        shadow_data2["latest_digests"]["weekly"]["overall_digest"].update(
            {
                "abstract": "Cycle 2 abstract",
                "keywords": ["cycle2"],
                "key_insights": ["insight2"],
                "learning_points": ["point2"],
                "emotional_context": {"primary": "curious"},
                "connections": {"technical": []},
            }
        )
        shadow_manager2._io.save(shadow_data2)

        # サイクル2を確定
        finalizer2 = DigestFinalizerFromShadow(
            config=config,
            grand_digest_manager=grand_manager,
            shadow_manager=shadow_manager2,
            times_tracker=times_tracker,
        )
        finalizer2.finalize_from_shadow("weekly", "Cycle 2 Digest")

        # 結果を検証: 2つのRegularDigestが存在
        weekly_dir = env.digests_path / "1_Weekly"
        regular_files = list(weekly_dir.glob("W*.txt"))
        # Provisionalディレクトリ内のファイルを除外
        regular_files = [f for f in regular_files if "Provisional" not in str(f)]
        assert len(regular_files) == 2
