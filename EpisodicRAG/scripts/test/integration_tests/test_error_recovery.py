#!/usr/bin/env python3
"""
エラーリカバリーのユニットテスト
================================

ファイル権限エラー、ディスク容量不足、JSON破損などの
エラーリカバリーシナリオをテスト。
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from domain.exceptions import FileIOError
from infrastructure import load_json, save_json

# slow マーカーを適用（ファイル全体）
pytestmark = pytest.mark.slow

# =============================================================================
# ファイル権限エラーテスト
# =============================================================================


class TestFilePermissionErrors:
    """ファイル権限エラーのテスト"""

    @pytest.mark.unit
    @pytest.mark.skipif(sys.platform == "win32", reason="Windows has different permission model")
    def test_save_json_permission_denied(self, tmp_path: Path) -> None:
        """save_jsonが権限エラーを適切に処理"""
        test_file = tmp_path / "readonly.json"
        test_file.write_text("{}")
        test_file.chmod(0o444)  # Read-only

        try:
            with pytest.raises((FileIOError, PermissionError, OSError)):
                save_json(test_file, {"key": "value"})
        finally:
            test_file.chmod(0o644)  # Restore for cleanup

    @pytest.mark.unit
    @pytest.mark.skipif(sys.platform == "win32", reason="Windows has different permission model")
    def test_load_json_permission_denied(self, tmp_path: Path) -> None:
        """load_jsonが権限エラーを適切に処理"""
        test_file = tmp_path / "noaccess.json"
        test_file.write_text('{"key": "value"}')
        test_file.chmod(0o000)

        try:
            with pytest.raises((FileIOError, PermissionError, OSError)):
                load_json(test_file)
        finally:
            test_file.chmod(0o644)

    @pytest.mark.unit
    @pytest.mark.skipif(sys.platform == "win32", reason="Windows has different permission model")
    def test_save_json_directory_not_writable(self, tmp_path: Path) -> None:
        """ディレクトリが書き込み不可の場合"""
        readonly_dir = tmp_path / "readonly_dir"
        readonly_dir.mkdir()
        test_file = readonly_dir / "test.json"
        readonly_dir.chmod(0o555)  # Read + execute only

        try:
            with pytest.raises((FileIOError, PermissionError, OSError)):
                save_json(test_file, {"key": "value"})
        finally:
            readonly_dir.chmod(0o755)


# =============================================================================
# ディスク容量エラーテスト
# =============================================================================


class TestDiskSpaceErrors:
    """ディスク容量エラーのテスト"""

    @pytest.mark.unit
    def test_save_json_disk_full_simulation(self, tmp_path: Path) -> None:
        """ディスク容量不足のシミュレーション（モック）"""
        test_file = tmp_path / "test.json"

        # OSError 28 = ENOSPC (No space left on device)
        with patch("builtins.open", side_effect=OSError(28, "No space left on device")):
            with pytest.raises((FileIOError, OSError)):
                save_json(test_file, {"large": "data"})

    @pytest.mark.unit
    def test_save_json_io_error_simulation(self, tmp_path: Path) -> None:
        """I/Oエラーのシミュレーション（モック）"""
        test_file = tmp_path / "test.json"

        # 一般的なI/Oエラー
        with patch("builtins.open", side_effect=IOError("Disk I/O error")):
            with pytest.raises((FileIOError, IOError)):
                save_json(test_file, {"key": "value"})


# =============================================================================
# JSON破損・フォーマットエラーテスト
# =============================================================================


class TestJsonCorruptionErrors:
    """JSON破損エラーのテスト"""

    @pytest.mark.unit
    def test_load_json_invalid_json(self, tmp_path: Path) -> None:
        """不正なJSONの読み込み"""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("{ invalid json }")

        with pytest.raises((FileIOError, json.JSONDecodeError)):
            load_json(test_file)

    @pytest.mark.unit
    def test_load_json_empty_file(self, tmp_path: Path) -> None:
        """空ファイルの読み込み"""
        test_file = tmp_path / "empty.json"
        test_file.write_text("")

        with pytest.raises((FileIOError, json.JSONDecodeError)):
            load_json(test_file)

    @pytest.mark.unit
    def test_load_json_truncated(self, tmp_path: Path) -> None:
        """途中で切れたJSONの読み込み"""
        test_file = tmp_path / "truncated.json"
        test_file.write_text('{"key": "value", "nested": {"incomplete":')

        with pytest.raises((FileIOError, json.JSONDecodeError)):
            load_json(test_file)

    @pytest.mark.unit
    def test_load_json_binary_content(self, tmp_path: Path) -> None:
        """バイナリコンテンツの読み込み"""
        test_file = tmp_path / "binary.json"
        test_file.write_bytes(b"\x00\x01\x02\x03\x04\x05")

        with pytest.raises((FileIOError, json.JSONDecodeError, UnicodeDecodeError)):
            load_json(test_file)


# =============================================================================
# ファイル存在エラーテスト
# =============================================================================


class TestFileNotFoundErrors:
    """ファイルが見つからないエラーのテスト"""

    @pytest.mark.unit
    def test_load_json_nonexistent(self, tmp_path: Path) -> None:
        """存在しないファイルの読み込み"""
        nonexistent = tmp_path / "does_not_exist.json"

        with pytest.raises((FileIOError, FileNotFoundError)):
            load_json(nonexistent)

    @pytest.mark.unit
    def test_load_json_directory_instead_of_file(self, tmp_path: Path) -> None:
        """ディレクトリをファイルとして読み込もうとした場合"""
        directory = tmp_path / "is_a_directory"
        directory.mkdir()

        with pytest.raises((FileIOError, IsADirectoryError, PermissionError)):
            load_json(directory)


# =============================================================================
# エンコーディングエラーテスト
# =============================================================================


class TestEncodingErrors:
    """エンコーディングエラーのテスト"""

    @pytest.mark.unit
    def test_load_json_utf8_bom(self, tmp_path: Path) -> None:
        """UTF-8 BOM付きファイルの読み込み"""
        test_file = tmp_path / "bom.json"
        # UTF-8 BOM + JSON content
        content = b'\xef\xbb\xbf{"key": "value"}'
        test_file.write_bytes(content)

        # BOM付きでも正常に読み込めるべき（または適切なエラー）
        try:
            result = load_json(test_file)
            assert "key" in result
        except (FileIOError, json.JSONDecodeError):
            # BOM処理ができない場合はエラーでも可
            pass

    @pytest.mark.unit
    def test_load_json_utf16(self, tmp_path: Path) -> None:
        """UTF-16エンコードファイルの読み込み"""
        test_file = tmp_path / "utf16.json"
        content = '{"key": "value"}'
        test_file.write_text(content, encoding="utf-16")

        # UTF-8を期待するのでエラーになるはず
        with pytest.raises((FileIOError, json.JSONDecodeError, UnicodeDecodeError)):
            load_json(test_file)

    @pytest.mark.unit
    def test_save_and_load_unicode(self, tmp_path: Path) -> None:
        """Unicode文字の保存と読み込み"""
        test_file = tmp_path / "unicode.json"
        test_data = {
            "japanese": "日本語テスト",
            "emoji": "🎉🎊🎁",
            "special": "αβγδ",
        }

        save_json(test_file, test_data)
        loaded = load_json(test_file)

        assert loaded["japanese"] == "日本語テスト"
        assert loaded["emoji"] == "🎉🎊🎁"
        assert loaded["special"] == "αβγδ"


# =============================================================================
# 同時アクセスエラーテスト（シミュレーション）
# =============================================================================


class TestConcurrentAccessErrors:
    """同時アクセスエラーのテスト（シミュレーション）"""

    @pytest.mark.unit
    def test_save_json_file_locked_simulation(self, tmp_path: Path) -> None:
        """ファイルロックのシミュレーション"""
        test_file = tmp_path / "locked.json"

        # ファイルロックエラーをシミュレート
        # Windows: OSError with errno 32 (ERROR_SHARING_VIOLATION)
        # Unix: IOError with appropriate errno
        mock_error = OSError(32, "The process cannot access the file")

        with patch("builtins.open", side_effect=mock_error):
            with pytest.raises((FileIOError, OSError)):
                save_json(test_file, {"key": "value"})


# =============================================================================
# 境界値テスト
# =============================================================================


class TestEdgeCases:
    """境界値・エッジケースのテスト"""

    @pytest.mark.unit
    def test_save_and_load_empty_dict(self, tmp_path: Path) -> None:
        """空のdictの保存と読み込み"""
        test_file = tmp_path / "empty.json"
        save_json(test_file, {})
        loaded = load_json(test_file)
        assert loaded == {}

    @pytest.mark.unit
    def test_save_and_load_nested_structure(self, tmp_path: Path) -> None:
        """深くネストした構造の保存と読み込み"""
        test_file = tmp_path / "nested.json"
        test_data = {"level1": {"level2": {"level3": {"level4": {"value": "deep"}}}}}
        save_json(test_file, test_data)
        loaded = load_json(test_file)
        assert loaded["level1"]["level2"]["level3"]["level4"]["value"] == "deep"

    @pytest.mark.unit
    def test_save_and_load_large_list(self, tmp_path: Path) -> None:
        """大きなリストの保存と読み込み"""
        test_file = tmp_path / "large.json"
        test_data = {"items": list(range(10000))}
        save_json(test_file, test_data)
        loaded = load_json(test_file)
        assert len(loaded["items"]) == 10000

    @pytest.mark.unit
    def test_save_and_load_special_keys(self, tmp_path: Path) -> None:
        """特殊なキー名の保存と読み込み"""
        test_file = tmp_path / "special_keys.json"
        test_data = {
            "": "empty key",
            " ": "space key",
            "\t": "tab key",
            "key with spaces": "value",
        }
        save_json(test_file, test_data)
        loaded = load_json(test_file)
        assert loaded[""] == "empty key"
        assert loaded[" "] == "space key"
