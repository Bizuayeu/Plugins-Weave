#!/usr/bin/env python3
"""
error_messages ユニットテスト
=============================

config/error_messages.py のユニットテスト。
各エラーメッセージ生成関数の動作を検証:
- invalid_level_message
- unknown_level_message
- config_key_missing_message
- config_invalid_value_message
- config_section_missing_message
- initialization_failed_message
- file_not_found_message
- invalid_json_message
- directory_not_found_message
"""

from pathlib import Path

import pytest

from infrastructure.config.error_messages import (
    config_invalid_value_message,
    config_key_missing_message,
    config_section_missing_message,
    directory_not_found_message,
    file_not_found_message,
    initialization_failed_message,
    invalid_json_message,
    invalid_level_message,
    unknown_level_message,
)

# =============================================================================
# TestInvalidLevelMessage
# =============================================================================


class TestInvalidLevelMessage:
    """invalid_level_messageのテスト"""

    @pytest.mark.unit
    def test_without_valid_levels(self) -> None:
        """有効レベルなしのメッセージ"""
        result = invalid_level_message("invalid_level")
        assert result == "Invalid level: 'invalid_level'"

    @pytest.mark.unit
    def test_with_valid_levels(self) -> None:
        """有効レベルありのメッセージ"""
        valid = ["weekly", "monthly", "annual"]
        result = invalid_level_message("bad", valid)
        assert "Invalid level: 'bad'" in result
        assert "weekly" in result
        assert "monthly" in result
        assert "annual" in result

    @pytest.mark.unit
    def test_with_single_valid_level(self) -> None:
        """単一の有効レベル"""
        result = invalid_level_message("bad", ["weekly"])
        assert "Invalid level: 'bad'" in result
        assert "weekly" in result

    @pytest.mark.unit
    def test_with_empty_valid_levels(self) -> None:
        """空の有効レベルリスト"""
        result = invalid_level_message("bad", [])
        # 空リストはFalsyなので、valid_levelsなしと同じ扱い
        assert result == "Invalid level: 'bad'"

    @pytest.mark.unit
    def test_with_none_valid_levels(self) -> None:
        """None の有効レベル"""
        result = invalid_level_message("bad", None)
        assert result == "Invalid level: 'bad'"

    @pytest.mark.unit
    def test_special_characters_in_level(self) -> None:
        """特殊文字を含むレベル名"""
        result = invalid_level_message("level<script>")
        assert "level<script>" in result


# =============================================================================
# TestUnknownLevelMessage
# =============================================================================


class TestUnknownLevelMessage:
    """unknown_level_messageのテスト"""

    @pytest.mark.unit
    def test_basic_message(self) -> None:
        """基本的なメッセージ"""
        result = unknown_level_message("unknown")
        assert result == "Unknown level: 'unknown'"

    @pytest.mark.unit
    def test_empty_level(self) -> None:
        """空のレベル名"""
        result = unknown_level_message("")
        assert result == "Unknown level: ''"

    @pytest.mark.unit
    def test_level_with_spaces(self) -> None:
        """スペースを含むレベル名"""
        result = unknown_level_message("weekly level")
        assert "weekly level" in result


# =============================================================================
# TestConfigKeyMissingMessage
# =============================================================================


class TestConfigKeyMissingMessage:
    """config_key_missing_messageのテスト"""

    @pytest.mark.unit
    def test_basic_message(self) -> None:
        """基本的なメッセージ"""
        result = config_key_missing_message("loops_path")
        assert result == "Required configuration key missing: 'loops_path'"

    @pytest.mark.unit
    def test_nested_key(self) -> None:
        """ネストされたキー名"""
        result = config_key_missing_message("paths.loops_dir")
        assert "paths.loops_dir" in result


# =============================================================================
# TestConfigInvalidValueMessage
# =============================================================================


class TestConfigInvalidValueMessage:
    """config_invalid_value_messageのテスト"""

    @pytest.mark.unit
    def test_with_string_value(self) -> None:
        """文字列値の場合"""
        result = config_invalid_value_message("threshold", "int", "five")
        assert "threshold" in result
        assert "expected int" in result
        assert "str" in result

    @pytest.mark.unit
    def test_with_int_value(self) -> None:
        """整数値の場合"""
        result = config_invalid_value_message("path", "str", 123)
        assert "path" in result
        assert "expected str" in result
        assert "int" in result

    @pytest.mark.unit
    def test_with_list_value(self) -> None:
        """リスト値の場合"""
        result = config_invalid_value_message("count", "int", [1, 2, 3])
        assert "count" in result
        assert "list" in result

    @pytest.mark.unit
    def test_with_none_value(self) -> None:
        """None値の場合"""
        result = config_invalid_value_message("required", "str", None)
        assert "required" in result
        assert "NoneType" in result


# =============================================================================
# TestConfigSectionMissingMessage
# =============================================================================


class TestConfigSectionMissingMessage:
    """config_section_missing_messageのテスト"""

    @pytest.mark.unit
    def test_basic_message(self) -> None:
        """基本的なメッセージ"""
        result = config_section_missing_message("paths")
        assert result == "'paths' section missing in config.json"

    @pytest.mark.unit
    def test_levels_section(self) -> None:
        """levelsセクション"""
        result = config_section_missing_message("levels")
        assert "'levels' section missing" in result


# =============================================================================
# TestInitializationFailedMessage
# =============================================================================


class TestInitializationFailedMessage:
    """initialization_failed_messageのテスト"""

    @pytest.mark.unit
    def test_with_value_error(self) -> None:
        """ValueError の場合"""
        error = ValueError("invalid value")
        result = initialization_failed_message("ConfigLoader", error)
        assert "Failed to initialize ConfigLoader" in result
        assert "invalid value" in result

    @pytest.mark.unit
    def test_with_file_not_found_error(self) -> None:
        """FileNotFoundError の場合"""
        error = FileNotFoundError("config.json not found")
        result = initialization_failed_message("DigestConfig", error)
        assert "Failed to initialize DigestConfig" in result
        assert "config.json not found" in result

    @pytest.mark.unit
    def test_with_generic_exception(self) -> None:
        """一般的なException"""
        error = Exception("unknown error")
        result = initialization_failed_message("Component", error)
        assert "Failed to initialize Component" in result


# =============================================================================
# TestFileNotFoundMessage
# =============================================================================


class TestFileNotFoundMessage:
    """file_not_found_messageのテスト"""

    @pytest.mark.unit
    def test_with_path_object(self) -> None:
        """Pathオブジェクトの場合"""
        path = Path("/tmp/missing.json")
        result = file_not_found_message(path)
        assert "File not found:" in result
        assert "missing.json" in result

    @pytest.mark.unit
    def test_with_relative_path(self) -> None:
        """相対パスの場合"""
        path = Path("config/config.json")
        result = file_not_found_message(path)
        assert "config.json" in result

    @pytest.mark.unit
    def test_with_windows_path(self) -> None:
        """Windowsパスの場合"""
        path = Path("C:/Users/test/file.json")
        result = file_not_found_message(path)
        assert "file.json" in result


# =============================================================================
# TestInvalidJsonMessage
# =============================================================================


class TestInvalidJsonMessage:
    """invalid_json_messageのテスト"""

    @pytest.mark.unit
    def test_with_decode_error(self) -> None:
        """デコードエラーの場合"""
        path = Path("/tmp/bad.json")
        error = ValueError("Expecting property name enclosed in double quotes")
        result = invalid_json_message(path, error)
        assert "Invalid JSON" in result
        assert "bad.json" in result
        assert "double quotes" in result

    @pytest.mark.unit
    def test_path_included_in_message(self) -> None:
        """パスがメッセージに含まれる"""
        path = Path("/data/config.json")
        error = Exception("parse error")
        result = invalid_json_message(path, error)
        assert "config.json" in result


# =============================================================================
# TestDirectoryNotFoundMessage
# =============================================================================


class TestDirectoryNotFoundMessage:
    """directory_not_found_messageのテスト"""

    @pytest.mark.unit
    def test_basic_message(self) -> None:
        """基本的なメッセージ"""
        path = Path("/tmp/missing_dir")
        result = directory_not_found_message(path)
        assert "Directory not found:" in result
        assert "missing_dir" in result

    @pytest.mark.unit
    def test_with_nested_path(self) -> None:
        """ネストされたパス"""
        path = Path("/data/Digests/1_Weekly")
        result = directory_not_found_message(path)
        assert "1_Weekly" in result
