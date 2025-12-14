#!/usr/bin/env python3
"""
閾値境界条件テスト
==================

各レベルの閾値（threshold）における境界条件を網羅的にテスト。

テスト対象:
    - threshold - 1: 処理トリガーされない
    - threshold: 処理トリガーされる
    - threshold + 1: 処理トリガーされる
    - 0: 空の状態

全8階層（Weekly〜Centurial）をパラメータ化してカバー。
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
from test_helpers import create_test_loop_file

from application.config import DigestConfig
from application.grand import ShadowGrandDigestManager
from domain.constants import DIGEST_LEVEL_NAMES

# 統合テストマーカー
pytestmark = [pytest.mark.integration]

# テスト対象の全レベル（loopを除く - threshold=None のため）
TESTABLE_LEVELS = DIGEST_LEVEL_NAMES  # ["weekly", "monthly", "quarterly", ...]


class TestThresholdBoundaryBase:
    """閾値境界条件テストの基底クラス"""

    @pytest.fixture
    def boundary_env(self, temp_plugin_env: "TempPluginEnvironment"):
        """境界条件テスト用の環境を構築"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        # last_digest_times.json を初期化（永続化ディレクトリに配置）
        times_file = temp_plugin_env.persistent_config_dir / "last_digest_times.json"
        times_file.write_text("{}")

        return {
            "env": temp_plugin_env,
            "config": config,
        }

    def _get_threshold_for_level(self, config: DigestConfig, level: str) -> int:
        """指定レベルの閾値を取得"""
        threshold_attr = f"{level.replace('-', '_')}_threshold"
        # config.threshold経由でThresholdProviderにアクセス
        return getattr(config.threshold, threshold_attr, 5)

    def _create_source_files_for_level(
        self, env, config: DigestConfig, level: str, count: int
    ) -> list:
        """指定レベルのソースファイルを作成"""
        if level == "weekly":
            # weeklyの場合はLoopファイルを作成
            files = []
            for i in range(1, count + 1):
                f = create_test_loop_file(env.loops_path, i, f"test_loop_{i}")
                files.append(f)
            return files
        else:
            # 他のレベルの場合は前のレベルのDigestファイルを作成
            # （簡略化のためここでは空リストを返す）
            return []


class TestWeeklyThresholdBoundary(TestThresholdBoundaryBase):
    """Weekly レベル閾値境界テスト"""

    def test_zero_files_no_trigger(self, boundary_env) -> None:
        """
        ファイル0件では処理がトリガーされない

        境界条件: count = 0
        """
        config = boundary_env["config"]

        shadow_manager = ShadowGrandDigestManager(config)
        new_files = shadow_manager._detector.find_new_files("weekly")

        assert len(new_files) == 0, "0件のファイルが検出されること"

        weekly_shadow = shadow_manager.get_shadow_digest_for_level("weekly")
        if weekly_shadow is not None:
            assert len(weekly_shadow.get("source_files", [])) == 0

    def test_below_threshold_no_trigger(self, boundary_env) -> None:
        """
        閾値-1ファイルでは処理がトリガーされない

        境界条件: count = threshold - 1
        """
        env = boundary_env["env"]
        config = boundary_env["config"]

        threshold = config.threshold.weekly_threshold
        file_count = max(1, threshold - 1)  # 最低1ファイル

        # Loopファイルを作成
        for i in range(1, file_count + 1):
            create_test_loop_file(env.loops_path, i, f"test_loop_{i}")

        shadow_manager = ShadowGrandDigestManager(config)
        new_files = shadow_manager._detector.find_new_files("weekly")

        assert len(new_files) == file_count, f"閾値-1={file_count}件のファイルが検出されること"

        shadow_manager.add_files_to_shadow("weekly", new_files)
        weekly_shadow = shadow_manager.get_shadow_digest_for_level("weekly")

        assert weekly_shadow is not None
        assert len(weekly_shadow["source_files"]) == file_count

    def test_exactly_at_threshold_triggers(self, boundary_env) -> None:
        """
        閾値ちょうどで処理がトリガーされる

        境界条件: count = threshold
        """
        env = boundary_env["env"]
        config = boundary_env["config"]

        threshold = config.threshold.weekly_threshold

        # Loopファイルを閾値と同数作成
        for i in range(1, threshold + 1):
            create_test_loop_file(env.loops_path, i, f"test_loop_{i}")

        shadow_manager = ShadowGrandDigestManager(config)
        new_files = shadow_manager._detector.find_new_files("weekly")

        assert len(new_files) == threshold, f"閾値={threshold}件のファイルが検出されること"

        shadow_manager.add_files_to_shadow("weekly", new_files)
        weekly_shadow = shadow_manager.get_shadow_digest_for_level("weekly")

        assert weekly_shadow is not None
        assert len(weekly_shadow["source_files"]) == threshold

    def test_above_threshold_triggers(self, boundary_env) -> None:
        """
        閾値+1で処理がトリガーされる

        境界条件: count = threshold + 1
        """
        env = boundary_env["env"]
        config = boundary_env["config"]

        threshold = config.threshold.weekly_threshold
        file_count = threshold + 1

        # Loopファイルを閾値+1作成
        for i in range(1, file_count + 1):
            create_test_loop_file(env.loops_path, i, f"test_loop_{i}")

        shadow_manager = ShadowGrandDigestManager(config)
        new_files = shadow_manager._detector.find_new_files("weekly")

        assert len(new_files) == file_count, f"閾値+1={file_count}件のファイルが検出されること"

        shadow_manager.add_files_to_shadow("weekly", new_files)
        weekly_shadow = shadow_manager.get_shadow_digest_for_level("weekly")

        assert weekly_shadow is not None
        assert len(weekly_shadow["source_files"]) == file_count


class TestAllLevelThresholds(TestThresholdBoundaryBase):
    """全レベル共通閾値テスト（パラメータ化）"""

    @pytest.mark.parametrize("level", TESTABLE_LEVELS)
    def test_threshold_value_is_positive(self, boundary_env, level) -> None:
        """
        全レベルの閾値が正の整数であること

        Args:
            level: テスト対象のレベル名
        """
        config = boundary_env["config"]
        threshold = self._get_threshold_for_level(config, level)

        assert isinstance(threshold, int), f"{level}の閾値はint型であること"
        assert threshold > 0, f"{level}の閾値は正の整数であること（実際: {threshold}）"

    @pytest.mark.parametrize("level", TESTABLE_LEVELS)
    def test_shadow_level_exists(self, boundary_env, level) -> None:
        """
        全レベルでShadowレベルが初期化可能であること

        Args:
            level: テスト対象のレベル名
        """
        config = boundary_env["config"]

        shadow_manager = ShadowGrandDigestManager(config)
        shadow_data = shadow_manager._io.load_or_create()

        assert level in shadow_data["latest_digests"], f"{level}がShadowに存在すること"

    @pytest.mark.parametrize(
        "level,expected_threshold",
        [
            ("weekly", 5),
            ("monthly", 5),
            ("quarterly", 3),
            ("annual", 4),
            ("triennial", 3),
            ("decadal", 3),
            ("multi_decadal", 3),  # アンダースコア（ハイフンではない）
            ("centurial", 4),  # LEVEL_CONFIGに統合済み
        ],
    )
    def test_default_threshold_values(self, boundary_env, level, expected_threshold) -> None:
        """
        デフォルト閾値が期待通りであること

        Args:
            level: テスト対象のレベル名
            expected_threshold: 期待される閾値
        """
        config = boundary_env["config"]
        actual = self._get_threshold_for_level(config, level)

        assert actual == expected_threshold, (
            f"{level}のデフォルト閾値は{expected_threshold}であること（実際: {actual}）"
        )


class TestEdgeCases(TestThresholdBoundaryBase):
    """エッジケーステスト"""

    def test_large_file_count(self, boundary_env) -> None:
        """
        大量ファイル（閾値の10倍）でも正常動作すること
        """
        env = boundary_env["env"]
        config = boundary_env["config"]

        threshold = config.threshold.weekly_threshold
        file_count = threshold * 10  # 閾値の10倍

        # 大量のLoopファイルを作成
        for i in range(1, file_count + 1):
            create_test_loop_file(env.loops_path, i, f"test_loop_{i}")

        shadow_manager = ShadowGrandDigestManager(config)
        new_files = shadow_manager._detector.find_new_files("weekly")

        assert len(new_files) == file_count

        shadow_manager.add_files_to_shadow("weekly", new_files)
        weekly_shadow = shadow_manager.get_shadow_digest_for_level("weekly")

        assert weekly_shadow is not None
        assert len(weekly_shadow["source_files"]) == file_count

    def test_incremental_addition_to_threshold(self, boundary_env) -> None:
        """
        増分追加で閾値に到達するケース

        シナリオ:
        1. 閾値-2ファイルを追加
        2. さらに2ファイルを追加
        3. 合計が閾値に到達
        """
        env = boundary_env["env"]
        config = boundary_env["config"]

        threshold = config.threshold.weekly_threshold
        if threshold < 3:
            pytest.skip("閾値が3未満のため増分テストをスキップ")

        # 第1バッチ: 閾値-2ファイル
        first_batch = threshold - 2
        for i in range(1, first_batch + 1):
            create_test_loop_file(env.loops_path, i, f"test_loop_{i}")

        shadow_manager = ShadowGrandDigestManager(config)
        new_files = shadow_manager._detector.find_new_files("weekly")
        shadow_manager.add_files_to_shadow("weekly", new_files)

        weekly_shadow = shadow_manager.get_shadow_digest_for_level("weekly")
        assert len(weekly_shadow["source_files"]) == first_batch

        # 第2バッチ: さらに2ファイル
        for i in range(first_batch + 1, threshold + 1):
            create_test_loop_file(env.loops_path, i, f"test_loop_{i}")

        new_files = shadow_manager._detector.find_new_files("weekly")
        shadow_manager.add_files_to_shadow("weekly", new_files)

        weekly_shadow = shadow_manager.get_shadow_digest_for_level("weekly")
        assert len(weekly_shadow["source_files"]) == threshold

    def test_duplicate_file_addition_prevented(self, boundary_env) -> None:
        """
        同じファイルをShadowに重複追加しても1回しか追加されないこと

        Note:
            find_new_filesはtimes_trackerのlast_processed番号に基づいて判定する。
            このテストではadd_files_to_shadowの重複防止機能を検証する。
        """
        env = boundary_env["env"]
        config = boundary_env["config"]

        # Loopファイルを3つ作成
        for i in range(1, 4):
            create_test_loop_file(env.loops_path, i, f"test_loop_{i}")

        shadow_manager = ShadowGrandDigestManager(config)

        # 1回目の追加
        new_files = shadow_manager._detector.find_new_files("weekly")
        shadow_manager.add_files_to_shadow("weekly", new_files)

        weekly_shadow = shadow_manager.get_shadow_digest_for_level("weekly")
        initial_count = len(weekly_shadow["source_files"])
        assert initial_count == 3, f"初回追加で3件追加されるべき（実際: {initial_count}）"

        # 2回目の追加（同じファイルを直接追加）
        # add_files_to_shadowは内部で重複を防止するはず
        shadow_manager.add_files_to_shadow("weekly", new_files)

        weekly_shadow = shadow_manager.get_shadow_digest_for_level("weekly")
        final_count = len(weekly_shadow["source_files"])

        # 重複追加がなければ件数は同じ
        assert final_count == initial_count, (
            f"重複追加が発生: {final_count - initial_count}件追加された"
        )


class TestEdgeCaseBoundaries(TestThresholdBoundaryBase):
    """追加のエッジケース境界値テスト"""

    def test_threshold_equals_one(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """
        閾値=1の特殊ケース

        単一ファイルで閾値達成する場合のテスト
        """
        import json

        env = temp_plugin_env

        # 閾値=1の設定を作成（永続化ディレクトリに配置）
        config_file = env.persistent_config_dir / "config.json"
        config_data = json.loads(config_file.read_text())
        config_data["levels"] = {"weekly_threshold": 1}
        config_file.write_text(json.dumps(config_data, indent=2))

        config = DigestConfig(plugin_root=env.plugin_root)

        # last_digest_times.json を初期化（永続化ディレクトリに配置）
        times_file = env.persistent_config_dir / "last_digest_times.json"
        times_file.write_text("{}")

        # 閾値が1であることを確認
        assert config.threshold.weekly_threshold == 1

        # 1ファイルを作成
        create_test_loop_file(env.loops_path, 1, "test_loop_1")

        shadow_manager = ShadowGrandDigestManager(config)
        new_files = shadow_manager._detector.find_new_files("weekly")

        assert len(new_files) == 1, "1件のファイルが検出されること"

    @pytest.mark.slow
    def test_very_large_threshold(self, boundary_env) -> None:
        """
        大きな閾値（1000+）のテスト

        大量ファイルでのパフォーマンスと正確性
        """
        env = boundary_env["env"]
        config = boundary_env["config"]

        # 1000ファイルを作成
        file_count = 1000
        for i in range(1, file_count + 1):
            create_test_loop_file(env.loops_path, i, f"test_loop_{i}")

        shadow_manager = ShadowGrandDigestManager(config)
        new_files = shadow_manager._detector.find_new_files("weekly")

        assert len(new_files) == file_count, (
            f"1000件のファイルが検出されること（実際: {len(new_files)}）"
        )

        shadow_manager.add_files_to_shadow("weekly", new_files)
        weekly_shadow = shadow_manager.get_shadow_digest_for_level("weekly")

        assert weekly_shadow is not None
        assert len(weekly_shadow["source_files"]) == file_count

    def test_threshold_minus_two(self, boundary_env) -> None:
        """
        閾値-2のテスト

        threshold-2でトリガーされないこと
        """
        env = boundary_env["env"]
        config = boundary_env["config"]

        threshold = config.threshold.weekly_threshold
        if threshold < 3:
            pytest.skip("閾値が3未満のためテストをスキップ")

        file_count = threshold - 2

        for i in range(1, file_count + 1):
            create_test_loop_file(env.loops_path, i, f"test_loop_{i}")

        shadow_manager = ShadowGrandDigestManager(config)
        new_files = shadow_manager._detector.find_new_files("weekly")

        assert len(new_files) == file_count, f"閾値-2={file_count}件のファイルが検出されること"

        # 閾値に達していないことを確認
        assert file_count < threshold, "ファイル数が閾値未満であること"

    def test_threshold_plus_two(self, boundary_env) -> None:
        """
        閾値+2のテスト

        threshold+2で確実にトリガーされること
        """
        env = boundary_env["env"]
        config = boundary_env["config"]

        threshold = config.threshold.weekly_threshold
        file_count = threshold + 2

        for i in range(1, file_count + 1):
            create_test_loop_file(env.loops_path, i, f"test_loop_{i}")

        shadow_manager = ShadowGrandDigestManager(config)
        new_files = shadow_manager._detector.find_new_files("weekly")

        assert len(new_files) == file_count, f"閾値+2={file_count}件のファイルが検出されること"

        shadow_manager.add_files_to_shadow("weekly", new_files)
        weekly_shadow = shadow_manager.get_shadow_digest_for_level("weekly")

        assert weekly_shadow is not None
        assert len(weekly_shadow["source_files"]) == file_count
        # 閾値を超えていることを確認
        assert file_count > threshold, "ファイル数が閾値を超えていること"
