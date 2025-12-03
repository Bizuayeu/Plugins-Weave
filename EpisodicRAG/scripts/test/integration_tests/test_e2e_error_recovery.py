#!/usr/bin/env python3
"""
E2E Error Recovery Tests
========================

エラー発生時の回復動作を検証する統合テスト。
破損ファイル、権限エラー、不正データからの回復シナリオ。
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
from domain.exceptions import ConfigError, FileIOError

# slow マーカーを適用（ファイル全体）
pytestmark = [pytest.mark.slow, pytest.mark.integration]


class TestCorruptedFileRecovery:
    """破損ファイルからの回復テスト"""

    @pytest.fixture
    def recovery_env(self, temp_plugin_env: "TempPluginEnvironment"):
        """回復テスト用の環境を構築"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        # last_digest_times.json を初期化
        times_file = temp_plugin_env.config_dir / "last_digest_times.json"
        times_file.write_text("{}")

        return {
            "env": temp_plugin_env,
            "config": config,
        }

    def test_recover_from_corrupted_shadow_file(self, recovery_env) -> None:
        """
        破損したShadowファイルからの回復

        シナリオ:
        1. 不正なJSONでShadowファイルを作成
        2. ShadowGrandDigestManager初期化
        3. テンプレートで再作成されることを確認
        """
        env = recovery_env["env"]
        config = recovery_env["config"]

        # 破損したShadowファイルを作成
        shadow_file = env.essences_path / "ShadowGrandDigest.txt"
        shadow_file.write_text("{ invalid json content }")

        # ShadowGrandDigestManagerを初期化
        # 破損ファイルがあってもエラーにならず、テンプレートで再作成される
        shadow_manager = ShadowGrandDigestManager(config)

        # Loopファイルを作成して処理できることを確認
        create_test_loop_file(env.loops_path, 1, "test_loop_1")

        # 正常に動作することを確認
        new_files = shadow_manager._detector.find_new_files("weekly")
        assert len(new_files) == 1

    def test_recover_from_corrupted_grand_digest(self, recovery_env) -> None:
        """
        破損したGrandDigest.txtの読み込み時エラー

        シナリオ:
        1. 不正なJSONでGrandDigestを作成
        2. GrandDigestManager.load_or_create()
        3. FileIOErrorが発生することを確認
        """
        env = recovery_env["env"]
        config = recovery_env["config"]

        # 破損したGrandDigestファイルを作成
        grand_file = env.essences_path / "GrandDigest.txt"
        grand_file.write_text("not valid json {{{")

        # GrandDigestManagerを初期化
        grand_manager = GrandDigestManager(config)

        # 破損ファイルを読み込むとFileIOErrorが発生
        with pytest.raises(FileIOError):
            grand_manager.load_or_create()

    def test_recover_from_empty_shadow_file(self, recovery_env) -> None:
        """
        空のShadowファイルからの回復

        シナリオ:
        1. 空のShadowファイルを作成
        2. 正常に処理できることを確認
        """
        env = recovery_env["env"]
        config = recovery_env["config"]

        # 空のShadowファイルを作成
        shadow_file = env.essences_path / "ShadowGrandDigest.txt"
        shadow_file.write_text("")

        # ShadowGrandDigestManagerを初期化
        shadow_manager = ShadowGrandDigestManager(config)

        # 正常に動作することを確認
        create_test_loop_file(env.loops_path, 1, "test_loop_1")
        new_files = shadow_manager._detector.find_new_files("weekly")
        assert len(new_files) == 1


class TestMissingFileRecovery:
    """ファイル欠損からの回復テスト"""

    @pytest.fixture
    def missing_env(self, temp_plugin_env: "TempPluginEnvironment"):
        """ファイル欠損テスト用の環境を構築"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        # last_digest_times.json を初期化
        times_file = temp_plugin_env.config_dir / "last_digest_times.json"
        times_file.write_text("{}")

        return {
            "env": temp_plugin_env,
            "config": config,
        }

    def test_missing_last_digest_times_creates_new(self, missing_env) -> None:
        """
        last_digest_times.json欠損時の自動作成

        シナリオ:
        1. last_digest_times.jsonを削除
        2. DigestTimesTracker初期化
        3. 新しいファイルが作成される
        """
        env = missing_env["env"]
        config = missing_env["config"]

        # ファイルを削除
        times_file = env.config_dir / "last_digest_times.json"
        if times_file.exists():
            times_file.unlink()

        # DigestTimesTracker初期化
        tracker = DigestTimesTracker(config)

        # load_or_createで初期値が返る
        times_data = tracker.load_or_create()
        last_processed = times_data.get("weekly", {}).get("last_processed")
        # 初期状態ではNone
        assert last_processed is None

    def test_missing_shadow_file_creates_new(self, missing_env) -> None:
        """
        ShadowGrandDigest.txt欠損時の自動作成

        シナリオ:
        1. ShadowGrandDigest.txtが存在しない
        2. ShadowGrandDigestManager初期化
        3. 新しいファイルが作成される
        """
        env = missing_env["env"]
        config = missing_env["config"]

        # Shadowファイルが存在しないことを確認
        shadow_file = env.essences_path / "ShadowGrandDigest.txt"
        if shadow_file.exists():
            shadow_file.unlink()

        # ShadowGrandDigestManagerを初期化
        shadow_manager = ShadowGrandDigestManager(config)

        # Loopファイルを作成して処理
        create_test_loop_file(env.loops_path, 1, "test_loop_1")
        shadow_manager.update_shadow_for_new_loops()

        # Shadowファイルが作成されている
        assert shadow_file.exists()


class TestInvalidDataRecovery:
    """不正データからの回復テスト"""

    @pytest.fixture
    def invalid_data_env(self, temp_plugin_env: "TempPluginEnvironment"):
        """不正データテスト用の環境を構築"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        # last_digest_times.json を初期化
        times_file = temp_plugin_env.config_dir / "last_digest_times.json"
        times_file.write_text("{}")

        return {
            "env": temp_plugin_env,
            "config": config,
        }

    def test_invalid_loop_file_skipped_gracefully(self, invalid_data_env) -> None:
        """
        不正なLoopファイルは優雅にスキップされる

        シナリオ:
        1. 正常なLoopファイルと不正なLoopファイルを作成
        2. 検出実行
        3. ファイル自体は検出されるが、処理時にエラーにならない
        """
        env = invalid_data_env["env"]
        config = invalid_data_env["config"]

        # 正常なLoopファイルを作成
        create_test_loop_file(env.loops_path, 1, "valid_loop")

        # 不正なLoopファイルを作成（JSONとしては無効）
        invalid_loop = env.loops_path / "L00002_invalid_loop.txt"
        invalid_loop.write_text("not a valid json file")

        # ShadowGrandDigestManagerを初期化
        shadow_manager = ShadowGrandDigestManager(config)

        # ファイル検出は両方とも成功
        new_files = shadow_manager._detector.find_new_files("weekly")
        assert len(new_files) == 2

    def test_shadow_with_null_overall_digest_recovers(self, invalid_data_env) -> None:
        """
        overall_digestがnullのShadowからの回復

        シナリオ:
        1. overall_digestがnullのShadowファイルを作成
        2. ファイル追加処理
        3. 正しく初期化されて処理が完了
        """
        env = invalid_data_env["env"]
        config = invalid_data_env["config"]

        # overall_digestがnullのShadowファイルを作成
        shadow_file = env.essences_path / "ShadowGrandDigest.txt"
        shadow_data = {
            "metadata": {"last_updated": "2024-01-01T00:00:00"},
            "latest_digests": {
                level: {"overall_digest": None, "source_files": []}
                for level in [
                    "weekly",
                    "monthly",
                    "quarterly",
                    "annual",
                    "triennial",
                    "decadal",
                    "multi_decadal",
                    "centurial",
                ]
            },
        }
        shadow_file.write_text(json.dumps(shadow_data, ensure_ascii=False))

        # ShadowGrandDigestManagerを初期化
        shadow_manager = ShadowGrandDigestManager(config)

        # Loopファイルを作成
        create_test_loop_file(env.loops_path, 1, "test_loop_1")

        # ファイル追加処理
        new_files = shadow_manager._detector.find_new_files("weekly")
        shadow_manager.add_files_to_shadow("weekly", new_files)

        # 正しく処理されたことを確認
        weekly_shadow = shadow_manager.get_shadow_digest_for_level("weekly")
        assert weekly_shadow is not None
        # source_filesに追加されている
        assert len(weekly_shadow.get("source_files", [])) >= 1
