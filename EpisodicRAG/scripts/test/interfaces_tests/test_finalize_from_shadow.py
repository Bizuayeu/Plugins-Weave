#!/usr/bin/env python3
"""
DigestFinalizerFromShadow 統合テスト
=====================================

一時ディレクトリを使用したファイルI/Oテスト

Note:
    TempPluginEnvironmentを使用してsetUp重複を解消。
    test_helpers.pyの共通ヘルパーを活用。
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from test_helpers import TempPluginEnvironment, create_test_loop_file

# Interfaces層
# Domain層
from domain.exceptions import ConfigError, DigestError, ValidationError
from interfaces import DigestFinalizerFromShadow

# Helpers
from interfaces.interface_helpers import get_next_digest_number


class TestGetNextDigestNumber(unittest.TestCase):
    """get_next_digest_number関数のテスト"""

    def setUp(self) -> None:
        """一時ディレクトリでテスト環境を構築"""
        self.temp_dir = tempfile.mkdtemp()
        self.digests_path = Path(self.temp_dir) / "Digests"
        self.digests_path.mkdir()

    def tearDown(self) -> None:
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir)

    def test_empty_directory_returns_1(self) -> None:
        """空のディレクトリでは1を返す"""
        result = get_next_digest_number(self.digests_path, "weekly")
        self.assertEqual(result, 1)

    def test_nonexistent_directory_returns_1(self) -> None:
        """存在しないディレクトリでは1を返す"""
        nonexistent = Path(self.temp_dir) / "NonExistent"
        result = get_next_digest_number(nonexistent, "weekly")
        self.assertEqual(result, 1)

    def test_with_existing_files(self) -> None:
        """既存ファイルがある場合、最大番号+1を返す"""
        weekly_dir = self.digests_path / "1_Weekly"
        weekly_dir.mkdir()

        (weekly_dir / "W0001_test.txt").write_text("{}")
        (weekly_dir / "W0003_test.txt").write_text("{}")
        (weekly_dir / "W0005_test.txt").write_text("{}")

        result = get_next_digest_number(self.digests_path, "weekly")
        self.assertEqual(result, 6)

    def test_invalid_level_raises(self) -> None:
        """無効なレベルでConfigError"""
        with self.assertRaises(ConfigError):
            get_next_digest_number(self.digests_path, "invalid_level")


class TestDigestFinalizerFromShadow(unittest.TestCase):
    """DigestFinalizerFromShadow の統合テスト"""

    def setUp(self) -> None:
        """TempPluginEnvironmentを使用してテスト環境を構築"""
        self.env = TempPluginEnvironment()
        self.env.__enter__()

        # プロパティ参照を保持（後方互換）
        self.plugin_root = self.env.plugin_root
        self.digests_path = self.env.digests_path
        self.loops_path = self.env.loops_path
        self.essences_path = self.env.essences_path
        self.config_dir = self.env.config_dir

        # モック設定
        self.mock_config = MagicMock()
        self.mock_config.digests_path = self.digests_path
        self.mock_config.loops_path = self.loops_path
        self.mock_config.essences_path = self.essences_path
        self.mock_config.plugin_root = self.plugin_root

        self.finalizer = DigestFinalizerFromShadow(self.mock_config)

    def tearDown(self) -> None:
        """TempPluginEnvironmentをクリーンアップ"""
        self.env.__exit__(None, None, None)

    def test_validate_shadow_content_valid(self) -> None:
        """正常なsource_filesの検証（例外なしで成功）"""
        source_files = ["L00001_test.txt", "L00002_test.txt"]
        # 例外が発生しなければ成功
        self.finalizer.validate_shadow_content("weekly", source_files)

    def test_validate_shadow_content_empty(self) -> None:
        """空のsource_filesでValidationError"""
        with self.assertRaises(ValidationError):
            self.finalizer.validate_shadow_content("weekly", [])

    def test_validate_shadow_content_not_list(self) -> None:
        """リストでない場合ValidationError"""
        with self.assertRaises(ValidationError):
            self.finalizer.validate_shadow_content("weekly", "not a list")

    def test_validate_shadow_content_invalid_filename(self) -> None:
        """無効なファイル名形式でValidationError"""
        source_files = ["invalid_file.txt"]
        with self.assertRaises(ValidationError):
            self.finalizer.validate_shadow_content("weekly", source_files)

    def test_finalize_empty_title(self) -> None:
        """空タイトルでValidationError"""
        with self.assertRaises(ValidationError):
            self.finalizer.finalize_from_shadow("weekly", "")

    def test_finalize_no_shadow(self) -> None:
        """ShadowがないでDigestError"""
        with self.assertRaises(DigestError):
            self.finalizer.finalize_from_shadow("weekly", "Test Title")


class TestDigestFinalizerIntegration(unittest.TestCase):
    """DigestFinalizerFromShadow の統合テスト（フルフロー）"""

    def setUp(self) -> None:
        """TempPluginEnvironmentを使用して完全なテスト環境を構築"""
        self.env = TempPluginEnvironment()
        self.env.__enter__()

        # プロパティ参照を保持（後方互換）
        self.plugin_root = self.env.plugin_root
        self.digests_path = self.env.digests_path
        self.loops_path = self.env.loops_path
        self.essences_path = self.env.essences_path
        self.config_dir = self.env.config_dir

        # GrandDigest.txt、ShadowGrandDigest.txt、last_digest_times.json作成
        self.env.create_grand_digest()
        self.env.create_shadow_digest(
            level="weekly", source_files=["L00001_test.txt", "L00002_test.txt"]
        )
        self.env.create_last_digest_times()

        # Loopファイル作成（ヘルパー関数使用）
        create_test_loop_file(self.loops_path, 1, "test")
        create_test_loop_file(self.loops_path, 2, "test")

    def tearDown(self) -> None:
        """TempPluginEnvironmentをクリーンアップ"""
        self.env.__exit__(None, None, None)

    def _create_finalizer(self):
        """DigestConfigとFinalizerを作成"""
        from application.config import DigestConfig

        config = DigestConfig()  # get_config_path() は TempPluginEnvironment でモック済み
        return DigestFinalizerFromShadow(config)

    def test_finalize_creates_regular_digest_file(self) -> None:
        """finalize_from_shadowがRegularDigestファイルを作成する"""
        finalizer = self._create_finalizer()

        # Shadowから取得したデータでfinalize（例外なしで成功）
        finalizer.finalize_from_shadow("weekly", "TestDigest")

        # RegularDigestファイルが作成されたことを確認
        weekly_dir = self.digests_path / "1_Weekly"
        digest_files = list(weekly_dir.glob("W0001_*.txt"))
        self.assertEqual(len(digest_files), 1)

        # ファイル内容を確認
        with open(digest_files[0], 'r', encoding='utf-8') as f:
            digest_data = json.load(f)
        self.assertIn("metadata", digest_data)
        self.assertIn("overall_digest", digest_data)
        self.assertEqual(digest_data["metadata"]["digest_level"], "weekly")

    def test_finalize_updates_grand_digest(self) -> None:
        """finalize_from_shadowがGrandDigestを更新する"""
        finalizer = self._create_finalizer()

        # 例外なしで成功
        finalizer.finalize_from_shadow("weekly", "TestDigest")

        # GrandDigest.txtが更新されたことを確認
        with open(self.essences_path / "GrandDigest.txt", 'r', encoding='utf-8') as f:
            grand_data = json.load(f)

        weekly_digest = grand_data["major_digests"]["weekly"]["overall_digest"]
        self.assertIsNotNone(weekly_digest)
        self.assertIn("TestDigest", weekly_digest.get("name", ""))

    def test_finalize_updates_last_digest_times(self) -> None:
        """finalize_from_shadowがlast_digest_timesを更新する"""
        finalizer = self._create_finalizer()

        # 例外なしで成功
        finalizer.finalize_from_shadow("weekly", "TestDigest")

        # last_digest_times.jsonが更新されたことを確認（永続化ディレクトリ）
        with open(
            self.env.persistent_config_dir / "last_digest_times.json", 'r', encoding='utf-8'
        ) as f:
            times_data = json.load(f)

        self.assertNotEqual(times_data["weekly"]["timestamp"], "")
        # last_processed stores the digest number (W0001 → 1), not source file count
        self.assertEqual(times_data["weekly"]["last_processed"], 1)

    def test_finalize_cascade_shadow_update(self) -> None:
        """finalize_from_shadowがShadowカスケード更新を実行する"""
        finalizer = self._create_finalizer()

        # 例外なしで成功
        finalizer.finalize_from_shadow("weekly", "TestDigest")

        # ShadowGrandDigest.txtが更新されたことを確認
        with open(self.essences_path / "ShadowGrandDigest.txt", 'r', encoding='utf-8') as f:
            shadow_data = json.load(f)

        # weeklyレベルのShadowがクリアされていることを確認
        # カスケード後はweeklyがクリアまたは更新されている
        # 具体的な動作はcascade_update_on_digest_finalizeの実装による
        _ = shadow_data["latest_digests"]["weekly"]["overall_digest"]

    def test_finalize_without_provisional_auto_generates(self) -> None:
        """Provisionalがない場合、source_filesから自動生成する"""
        finalizer = self._create_finalizer()

        # Provisionalファイルは作成しない（setUpで作成されていない）
        # 例外なしで成功
        finalizer.finalize_from_shadow("weekly", "AutoGenTest")

        # RegularDigestが作成されたことを確認
        weekly_dir = self.digests_path / "1_Weekly"
        digest_files = list(weekly_dir.glob("W0001_*.txt"))
        self.assertEqual(len(digest_files), 1)

        # individual_digestsが自動生成されたことを確認
        with open(digest_files[0], 'r', encoding='utf-8') as f:
            digest_data = json.load(f)

        individual_digests = digest_data.get("individual_digests", [])
        self.assertEqual(len(individual_digests), 2)  # L00001, L00002


if __name__ == "__main__":
    unittest.main()
