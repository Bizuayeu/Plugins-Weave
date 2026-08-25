#!/usr/bin/env python3
"""
interfaces/interface_helpers.py のユニットテスト
================================================

sanitize_filename(), get_next_digest_number() のテスト
"""

import unittest
from pathlib import Path

from domain.exceptions import ConfigError, ValidationError
from interfaces.interface_helpers import get_next_digest_number, sanitize_filename

# =============================================================================
# テスト用定数
# =============================================================================
# 長い文字列テスト用: max_length を超えるサイズ
LONG_TITLE_LENGTH = 100
DEFAULT_MAX_LENGTH = 50


class TestSanitizeFilename(unittest.TestCase):
    """sanitize_filename() のテスト"""

    def test_basic(self) -> None:
        """基本的な変換"""
        self.assertEqual(sanitize_filename("テスト"), "テスト")
        self.assertEqual(sanitize_filename("Hello World"), "Hello_World")

    def test_dangerous_chars(self) -> None:
        """危険な文字の削除"""
        self.assertEqual(sanitize_filename('test<>:"/\\|?*'), "test")
        self.assertEqual(sanitize_filename("file:name"), "filename")

    def test_spaces_to_underscore(self) -> None:
        """空白をアンダースコアに変換"""
        self.assertEqual(sanitize_filename("a b c"), "a_b_c")
        self.assertEqual(sanitize_filename("a  b"), "a_b")  # 連続空白

    def test_strip_underscores(self) -> None:
        """先頭・末尾のアンダースコア削除"""
        self.assertEqual(sanitize_filename(" test "), "test")
        self.assertEqual(sanitize_filename("_test_"), "test")

    def test_max_length(self) -> None:
        """長さ制限"""
        long_title = "a" * LONG_TITLE_LENGTH
        result = sanitize_filename(long_title, max_length=DEFAULT_MAX_LENGTH)
        self.assertEqual(len(result), DEFAULT_MAX_LENGTH)

    def test_max_length_no_trailing_underscore(self) -> None:
        """長さ制限後に末尾アンダースコアなし"""
        # 50文字目がアンダースコアになるケース (49文字 + 空白 + "b")
        result = sanitize_filename(
            "a" * (DEFAULT_MAX_LENGTH - 1) + " b", max_length=DEFAULT_MAX_LENGTH
        )
        self.assertFalse(result.endswith("_"))

    def test_japanese(self) -> None:
        """日本語タイトル"""
        self.assertEqual(sanitize_filename("AIとの対話"), "AIとの対話")
        self.assertEqual(sanitize_filename("テスト 2025"), "テスト_2025")


# =============================================================================
# エッジケーステスト（Phase 0で追加）
# =============================================================================


class TestSanitizeFilenameEdgeCases(unittest.TestCase):
    """sanitize_filename() のエッジケーステスト"""

    def test_none_input_raises_typeerror(self) -> None:
        """None入力でValidationError"""
        with self.assertRaises(ValidationError):
            sanitize_filename(None)

    def test_non_string_input_raises_typeerror(self) -> None:
        """非文字列型入力でValidationError"""
        with self.assertRaises(ValidationError):
            sanitize_filename(123)
        with self.assertRaises(ValidationError):
            sanitize_filename(["test"])

    def test_zero_max_length_raises_valueerror(self) -> None:
        """max_length=0でValidationError"""
        with self.assertRaises(ValidationError):
            sanitize_filename("test", max_length=0)

    def test_negative_max_length_raises_valueerror(self) -> None:
        """負のmax_lengthでValidationError"""
        with self.assertRaises(ValidationError):
            sanitize_filename("test", max_length=-1)

    def test_only_dangerous_chars(self) -> None:
        """危険文字のみの入力"""
        self.assertEqual(sanitize_filename('<>:"/\\|?*'), "untitled")

    def test_empty_string(self) -> None:
        """空文字列入力"""
        self.assertEqual(sanitize_filename(""), "untitled")

    def test_only_spaces(self) -> None:
        """空白のみの入力"""
        self.assertEqual(sanitize_filename("   "), "untitled")

    def test_only_underscores(self) -> None:
        """アンダースコアのみの入力"""
        self.assertEqual(sanitize_filename("___"), "untitled")

    def test_mixed_dangerous_and_valid(self) -> None:
        """危険文字と有効文字の混合"""
        self.assertEqual(sanitize_filename("test<file>name"), "testfilename")
        self.assertEqual(sanitize_filename("a:b:c"), "abc")

    def test_max_length_boundary(self) -> None:
        """max_length境界値テスト"""
        # max_length=1の場合
        self.assertEqual(len(sanitize_filename("abcde", max_length=1)), 1)
        # max_length=2の場合
        self.assertEqual(len(sanitize_filename("abcde", max_length=2)), 2)

    def test_unicode_normalization(self) -> None:
        """Unicode文字の正常処理"""
        # 絵文字を含む入力
        result = sanitize_filename("テスト🎉ファイル")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_consecutive_dangerous_chars(self) -> None:
        """連続した危険文字"""
        self.assertEqual(sanitize_filename("test<<<>>>name"), "testname")


class TestGetNextDigestNumber(unittest.TestCase):
    """get_next_digest_number() のテスト"""

    def setUp(self) -> None:
        """テスト用の一時ディレクトリを作成"""
        import shutil
        import tempfile

        self.temp_dir = tempfile.mkdtemp()
        self.digests_path = Path(self.temp_dir) / "Digests"
        self.digests_path.mkdir()
        # 各レベルのディレクトリを作成
        for level_dir in ["1_Weekly", "2_Monthly", "3_Quarterly"]:
            (self.digests_path / level_dir).mkdir()

    def tearDown(self) -> None:
        """一時ディレクトリを削除"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_empty_directory_returns_one(self) -> None:
        """空ディレクトリでは1を返す"""
        result = get_next_digest_number(self.digests_path, "weekly")
        self.assertEqual(result, 1)

    def test_with_existing_files(self) -> None:
        """既存ファイルがある場合は最大番号+1を返す"""
        # テストファイルを作成
        weekly_dir = self.digests_path / "1_Weekly"
        (weekly_dir / "W0001_test.txt").touch()
        (weekly_dir / "W0003_test.txt").touch()

        result = get_next_digest_number(self.digests_path, "weekly")
        self.assertEqual(result, 4)

    def test_invalid_level_raises_valueerror(self) -> None:
        """無効なレベル名でConfigError"""
        with self.assertRaises(ConfigError):
            get_next_digest_number(self.digests_path, "invalid_level")

    def test_nonexistent_level_directory_returns_one(self) -> None:
        """レベルディレクトリが存在しない場合は1を返す"""
        # 存在しないディレクトリを削除
        import shutil

        shutil.rmtree(self.digests_path / "1_Weekly")

        result = get_next_digest_number(self.digests_path, "weekly")
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
