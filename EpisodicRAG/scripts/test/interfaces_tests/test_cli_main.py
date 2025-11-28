#!/usr/bin/env python3
"""
CLI main() 関数のテスト
=======================

finalize_from_shadow.main() と save_provisional_digest.main() の
argparse と例外ハンドリングをテスト。
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestFinalizeFromShadowMain(unittest.TestCase):
    """finalize_from_shadow.main() のテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        self._setup_plugin_structure()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_plugin_structure(self):
        """プラグイン構造を作成"""
        # ディレクトリ構造
        (self.plugin_root / "data" / "Digests").mkdir(parents=True)
        (self.plugin_root / "data" / "Loops").mkdir(parents=True)
        (self.plugin_root / "data" / "Essences").mkdir(parents=True)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

        # Digestサブディレクトリ
        for subdir in [
            "1_Weekly",
            "2_Monthly",
            "3_Quarterly",
            "4_Annual",
            "5_Triennial",
            "6_Decadal",
            "7_Multi-decadal",
            "8_Centurial",
        ]:
            (self.plugin_root / "data" / "Digests" / subdir).mkdir()
            (self.plugin_root / "data" / "Digests" / subdir / "Provisional").mkdir()

        # config.json
        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None,
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4,
            },
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    @pytest.mark.unit
    def test_main_invalid_level_exits_with_error(self):
        """無効なレベルでSystemExit"""
        with patch("sys.argv", ["finalize_from_shadow.py", "invalid_level", "TestTitle"]):
            with patch("sys.stderr"):  # argparse エラー出力を抑制
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.finalize_from_shadow import main

                    main()
                # argparse は無効な引数で exit code 2
                assert exc_info.value.code == 2

    @pytest.mark.unit
    def test_main_missing_arguments_exits(self):
        """引数不足でSystemExit"""
        with patch("sys.argv", ["finalize_from_shadow.py"]):
            with patch("sys.stderr"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.finalize_from_shadow import main

                    main()
                assert exc_info.value.code == 2

    @pytest.mark.unit
    def test_main_help_exits_zero(self):
        """--help で exit code 0"""
        with patch("sys.argv", ["finalize_from_shadow.py", "--help"]):
            with patch("sys.stdout"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.finalize_from_shadow import main

                    main()
                assert exc_info.value.code == 0

    @pytest.mark.integration
    def test_main_episodicrag_error_exits_with_1(self):
        """EpisodicRAGError発生時にexit code 1"""
        from domain.exceptions import DigestError

        with patch("sys.argv", ["finalize_from_shadow.py", "weekly", "TestTitle"]):
            with patch(
                "interfaces.finalize_from_shadow.DigestFinalizerFromShadow"
            ) as MockFinalizer:
                mock_instance = MagicMock()
                mock_instance.finalize_from_shadow.side_effect = DigestError("Test error")
                MockFinalizer.return_value = mock_instance

                with patch("infrastructure.logging_config.log_error"):
                    with pytest.raises(SystemExit) as exc_info:
                        from interfaces.finalize_from_shadow import main

                        main()
                    assert exc_info.value.code == 1


class TestSaveProvisionalDigestMain(unittest.TestCase):
    """save_provisional_digest.main() のテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        self._setup_plugin_structure()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_plugin_structure(self):
        """プラグイン構造を作成"""
        (self.plugin_root / "data" / "Digests").mkdir(parents=True)
        (self.plugin_root / "data" / "Loops").mkdir(parents=True)
        (self.plugin_root / "data" / "Essences").mkdir(parents=True)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

        for subdir in [
            "1_Weekly",
            "2_Monthly",
            "3_Quarterly",
            "4_Annual",
            "5_Triennial",
            "6_Decadal",
            "7_Multi-decadal",
            "8_Centurial",
        ]:
            (self.plugin_root / "data" / "Digests" / subdir).mkdir()
            (self.plugin_root / "data" / "Digests" / subdir / "Provisional").mkdir()

        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None,
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4,
            },
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    @pytest.mark.unit
    def test_main_invalid_level_exits_with_error(self):
        """無効なレベルでSystemExit"""
        with patch("sys.argv", ["save_provisional_digest.py", "invalid_level", "[]"]):
            with patch("sys.stderr"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.save_provisional_digest import main

                    main()
                assert exc_info.value.code == 2

    @pytest.mark.unit
    def test_main_missing_arguments_exits(self):
        """引数不足でSystemExit"""
        with patch("sys.argv", ["save_provisional_digest.py"]):
            with patch("sys.stderr"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.save_provisional_digest import main

                    main()
                assert exc_info.value.code == 2

    @pytest.mark.unit
    def test_main_help_exits_zero(self):
        """--help で exit code 0"""
        with patch("sys.argv", ["save_provisional_digest.py", "--help"]):
            with patch("sys.stdout"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.save_provisional_digest import main

                    main()
                assert exc_info.value.code == 0

    @pytest.mark.unit
    def test_main_invalid_json_exits_with_1(self):
        """不正なJSON形式でexit code 1"""
        with patch("sys.argv", ["save_provisional_digest.py", "weekly", "{invalid json"]):
            with patch("infrastructure.logging_config.log_error"):
                # JSONDecodeError は catch されて exit(1)
                # 実際の動作をテスト
                pass  # 実装後に有効化

    @pytest.mark.integration
    def test_main_file_not_found_exits_with_1(self):
        """存在しないファイル指定でexit code 1"""
        with patch("sys.argv", ["save_provisional_digest.py", "weekly", "/nonexistent/file.json"]):
            with patch("infrastructure.logging_config.log_error"):
                # FileNotFoundError は catch されて exit(1)
                pass  # 実装後に有効化

    @pytest.mark.integration
    def test_main_episodicrag_error_exits_with_1(self):
        """EpisodicRAGError発生時にexit code 1"""
        from domain.exceptions import ValidationError

        with patch("sys.argv", ["save_provisional_digest.py", "weekly", "[]"]):
            with patch("interfaces.save_provisional_digest.ProvisionalDigestSaver") as MockSaver:
                mock_instance = MagicMock()
                mock_instance.save_provisional.side_effect = ValidationError("Test error")
                MockSaver.return_value = mock_instance

                with patch("interfaces.save_provisional_digest.InputLoader.load") as mock_load:
                    mock_load.return_value = []

                    with patch("infrastructure.logging_config.log_error"):
                        with patch("infrastructure.logging_config.log_info"):
                            with patch("infrastructure.logging_config.log_warning"):
                                # ValidationError がキャッチされて処理される
                                pass  # 実装後に有効化


class TestMainArgumentParsing(unittest.TestCase):
    """main() の引数パース詳細テスト"""

    @pytest.mark.unit
    def test_finalize_accepts_all_valid_levels(self):
        """全ての有効レベルがargparseで受け入れられる"""
        valid_levels = [
            "weekly",
            "monthly",
            "quarterly",
            "annual",
            "triennial",
            "decadal",
            "multi_decadal",
            "centurial",
        ]

        for level in valid_levels:
            with self.subTest(level=level):
                with patch("sys.argv", ["finalize_from_shadow.py", level, "Title"]):
                    with patch(
                        "interfaces.finalize_from_shadow.DigestFinalizerFromShadow"
                    ) as MockFinalizer:
                        mock_instance = MagicMock()
                        MockFinalizer.return_value = mock_instance

                        from interfaces.finalize_from_shadow import main

                        main()

                        mock_instance.finalize_from_shadow.assert_called_once_with(level, "Title")

    @pytest.mark.unit
    def test_save_provisional_append_flag(self):
        """--append フラグが正しく処理される"""
        with patch("sys.argv", ["save_provisional_digest.py", "weekly", "[]", "--append"]):
            with patch("interfaces.save_provisional_digest.ProvisionalDigestSaver") as MockSaver:
                mock_instance = MagicMock()
                mock_instance.save_provisional.return_value = Path("/tmp/test.txt")
                MockSaver.return_value = mock_instance

                with patch("interfaces.save_provisional_digest.InputLoader.load") as mock_load:
                    mock_load.return_value = []

                    with patch("infrastructure.logging_config.log_info"):
                        with patch("infrastructure.logging_config.log_warning"):
                            from interfaces.save_provisional_digest import main

                            main()

                            mock_instance.save_provisional.assert_called_once()
                            call_args = mock_instance.save_provisional.call_args
                            assert call_args[1]["append"] is True


if __name__ == "__main__":
    unittest.main()
