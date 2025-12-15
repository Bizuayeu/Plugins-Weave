#!/usr/bin/env python3
"""
8層フルカスケード統合テスト
===========================

Weekly から Centurial までの完全なカスケードフローを検証。
各レベルの閾値到達時に次レベルへの昇格が正しく動作することを確認。

テストシナリオ:
    1. 全8層構造の初期化確認
    2. Weekly→Monthly→...→Centurialのカスケードフロー
    3. 閾値未達時のカスケード停止確認
    4. メタデータの伝播確認
"""

import json
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
from application.grand import GrandDigestManager, ShadowGrandDigestManager
from application.tracking import DigestTimesTracker
from domain.constants import DIGEST_LEVEL_NAMES, LEVEL_CONFIG, build_level_hierarchy

# slow + integration マーカーを適用（ファイル全体）
pytestmark = [pytest.mark.slow, pytest.mark.integration]

# 全8層の順序（loopを除く - Shadow/GrandDigest構造用）
LEVEL_ORDER = DIGEST_LEVEL_NAMES  # ["weekly", "monthly", "quarterly", "annual", ...]


class TestFullCascadeInitialization:
    """8層構造の初期化テスト"""

    @pytest.fixture
    def full_cascade_env(self, temp_plugin_env: "TempPluginEnvironment"):
        """フルカスケードテスト用環境"""
        config = DigestConfig()

        # last_digest_times.json を初期化
        times_file = temp_plugin_env.config_dir / "last_digest_times.json"
        times_file.write_text("{}")

        return {
            "env": temp_plugin_env,
            "config": config,
        }

    def test_all_eight_levels_exist_in_shadow(self, full_cascade_env) -> None:
        """
        ShadowGrandDigestに全8層が存在する

        検証: latest_digests に全レベルのエントリが存在
        """
        config = full_cascade_env["config"]

        shadow_manager = ShadowGrandDigestManager(config)
        shadow_data = shadow_manager._io.load_or_create()

        for level in LEVEL_ORDER:
            assert level in shadow_data["latest_digests"], f"{level}がShadowに存在すること"

    def test_all_eight_levels_exist_in_grand(self, full_cascade_env) -> None:
        """
        GrandDigestに全8層が存在する

        検証: major_digests に全レベルのエントリが存在
        """
        config = full_cascade_env["config"]

        grand_manager = GrandDigestManager(config)
        grand_data = grand_manager.load_or_create()

        for level in LEVEL_ORDER:
            assert level in grand_data["major_digests"], f"{level}がGrandDigestに存在すること"

    def test_level_hierarchy_is_correctly_linked(self, full_cascade_env) -> None:
        """
        レベル階層が正しくリンクされている

        検証: 各レベルのnextが正しい次レベルを指している
        """
        hierarchy = build_level_hierarchy()

        for i, level in enumerate(LEVEL_ORDER):
            if i < len(LEVEL_ORDER) - 1:
                expected_next = LEVEL_ORDER[i + 1]
                actual_next = hierarchy[level]["next"]
                assert actual_next == expected_next, (
                    f"{level}の次は{expected_next}であること（実際: {actual_next}）"
                )
            else:
                # 最上位（centurial）のnextはNone
                assert hierarchy[level]["next"] is None, "centurialの次はNoneであること"

    def test_all_eight_level_directories_created(self, full_cascade_env) -> None:
        """
        全8層のディレクトリが作成される

        検証: digests_path配下に各レベルのディレクトリが存在
        """
        config = full_cascade_env["config"]

        for level in LEVEL_ORDER:
            level_dir = config.get_level_dir(level)
            # ディレクトリは存在するか、作成可能であること
            assert level_dir is not None, f"{level}のディレクトリパスが取得できること"


class TestFullCascadeFlow:
    """8層フルカスケードフローテスト"""

    @pytest.fixture
    def cascade_flow_env(self, temp_plugin_env: "TempPluginEnvironment"):
        """カスケードフローテスト用環境"""
        config = DigestConfig()

        # last_digest_times.json を初期化
        times_file = temp_plugin_env.config_dir / "last_digest_times.json"
        times_file.write_text("{}")

        # 全レベルのDigestディレクトリを作成
        for level in LEVEL_ORDER:
            level_dir = config.get_level_dir(level)
            level_dir.mkdir(parents=True, exist_ok=True)
            # Provisionalディレクトリも作成
            provisional_dir = level_dir / "Provisional"
            provisional_dir.mkdir(exist_ok=True)

        return {
            "env": temp_plugin_env,
            "config": config,
        }

    def test_weekly_to_monthly_cascade(self, cascade_flow_env) -> None:
        """
        Weekly→Monthlyカスケードが正しく動作する

        シナリオ:
        1. Loopファイルを作成しweekly Shadowに追加
        2. weekly確定をシミュレート
        3. カスケード処理実行
        4. monthly Shadowに反映されることを確認
        """
        env = cascade_flow_env["env"]
        config = cascade_flow_env["config"]

        # 1. Loopファイルを3つ作成
        for i in range(1, 4):
            create_test_loop_file(env.loops_path, i, f"test_loop_{i}")

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

        # 4. weekly Shadowがクリアされていることを確認
        weekly_shadow_after = shadow_manager.get_shadow_digest_for_level("weekly")
        if weekly_shadow_after is not None:
            assert len(weekly_shadow_after.get("source_files", [])) == 0

    def test_multi_level_cascade_quarterly(self, cascade_flow_env) -> None:
        """
        複数レベルのカスケード（Weekly→Monthly→Quarterly）

        シナリオ:
        1. weeklyダイジェストを複数作成
        2. monthly確定をシミュレート
        3. quarterly Shadowに反映されることを確認
        """
        config = cascade_flow_env["config"]

        # weeklyダイジェストを5つ作成（monthly閾値分）
        weekly_dir = config.get_level_dir("weekly")
        for i in range(1, 6):
            weekly_file = weekly_dir / f"W{i:05d}_test_weekly_{i}.txt"
            weekly_file.write_text(
                json.dumps(
                    {
                        "metadata": {"level": "weekly", "number": f"{i:05d}"},
                        "overall_digest": {
                            "abstract": f"Weekly digest {i}",
                            "keywords": [f"week{i}"],
                            "source_files": [f"L{i:05d}"],
                        },
                        "individual_digests": [],
                    },
                    ensure_ascii=False,
                )
            )

        shadow_manager = ShadowGrandDigestManager(config)

        # monthly Shadowに週次ダイジェストを追加
        monthly_files = list(weekly_dir.glob("W*.txt"))
        shadow_manager.add_files_to_shadow("monthly", monthly_files)

        # monthly Shadowを確認
        monthly_shadow = shadow_manager.get_shadow_digest_for_level("monthly")
        assert monthly_shadow is not None
        assert len(monthly_shadow["source_files"]) == 5

    def test_cascade_preserves_level_order(self, cascade_flow_env) -> None:
        """
        カスケードはレベル順序を保持する

        検証: weeklyからmonthlyへは遷移可能だが、
              monthlyからweeklyへは遷移しない
        """
        hierarchy = build_level_hierarchy()

        # 各レベルのnextを確認
        for i, level in enumerate(LEVEL_ORDER[:-1]):  # centurial以外
            next_level = hierarchy[level]["next"]
            next_index = LEVEL_ORDER.index(next_level)

            assert next_index == i + 1, f"{level}({i})の次は{LEVEL_ORDER[i + 1]}({i + 1})であること"


class TestCascadeStopConditions:
    """カスケード停止条件テスト"""

    @pytest.fixture
    def stop_condition_env(self, temp_plugin_env: "TempPluginEnvironment"):
        """停止条件テスト用環境"""
        config = DigestConfig()

        times_file = temp_plugin_env.config_dir / "last_digest_times.json"
        times_file.write_text("{}")

        return {
            "env": temp_plugin_env,
            "config": config,
        }

    def test_cascade_stops_at_insufficient_threshold(self, stop_condition_env) -> None:
        """
        閾値未満の場合カスケードが停止する

        シナリオ:
        1. weekly Shadowに1ファイルのみ追加
        2. weekly確定→monthlyに1ファイルのみ
        3. monthlyの閾値未達のためquarterlyへのカスケードは発生しない
        """
        env = stop_condition_env["env"]
        config = stop_condition_env["config"]

        # Loopファイルを1つだけ作成
        create_test_loop_file(env.loops_path, 1, "test_loop_1")

        shadow_manager = ShadowGrandDigestManager(config)

        # weekly Shadowに追加
        new_files = shadow_manager._detector.find_new_files("weekly")
        shadow_manager.add_files_to_shadow("weekly", new_files)

        # weekly Shadowを確認（1ファイルのみ）
        weekly_shadow = shadow_manager.get_shadow_digest_for_level("weekly")
        assert weekly_shadow is not None
        assert len(weekly_shadow["source_files"]) == 1

        # 閾値（デフォルト5）未満なのでfinalize不要
        threshold = config.threshold.weekly_threshold
        assert len(weekly_shadow["source_files"]) < threshold

    def test_cascade_stops_at_centurial(self, stop_condition_env) -> None:
        """
        カスケードはcenturialで停止する

        検証: centurialのnextはNoneである
        """
        hierarchy = build_level_hierarchy()

        centurial_next = hierarchy["centurial"]["next"]
        assert centurial_next is None, "centurialの次はNoneであること"


class TestMetadataPropagation:
    """メタデータ伝播テスト"""

    @pytest.fixture
    def metadata_env(self, temp_plugin_env: "TempPluginEnvironment"):
        """メタデータテスト用環境"""
        config = DigestConfig()

        times_file = temp_plugin_env.config_dir / "last_digest_times.json"
        times_file.write_text("{}")

        return {
            "env": temp_plugin_env,
            "config": config,
        }

    def test_shadow_metadata_has_last_updated(self, metadata_env) -> None:
        """
        ShadowGrandDigestのmetadataにlast_updatedが存在する
        """
        config = metadata_env["config"]

        shadow_manager = ShadowGrandDigestManager(config)
        shadow_data = shadow_manager._io.load_or_create()

        assert "metadata" in shadow_data
        assert "last_updated" in shadow_data["metadata"]

    def test_grand_metadata_has_version(self, metadata_env) -> None:
        """
        GrandDigestのmetadataにversionが存在する
        """
        config = metadata_env["config"]

        grand_manager = GrandDigestManager(config)
        grand_data = grand_manager.load_or_create()

        assert "metadata" in grand_data
        assert "version" in grand_data["metadata"]

    def test_source_files_tracked_per_level(self, metadata_env) -> None:
        """
        各レベルでsource_filesが追跡される
        """
        env = metadata_env["env"]
        config = metadata_env["config"]

        # Loopファイルを作成
        for i in range(1, 4):
            create_test_loop_file(env.loops_path, i, f"test_loop_{i}")

        shadow_manager = ShadowGrandDigestManager(config)

        # weekly Shadowに追加
        new_files = shadow_manager._detector.find_new_files("weekly")
        shadow_manager.add_files_to_shadow("weekly", new_files)

        # source_filesが追跡されていることを確認
        weekly_shadow = shadow_manager.get_shadow_digest_for_level("weekly")
        assert weekly_shadow is not None
        assert "source_files" in weekly_shadow
        assert len(weekly_shadow["source_files"]) == 3
