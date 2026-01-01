# tests/domain/test_validators.py
"""domain/validators.py のテスト"""

import pytest

from domain.validators import (
    is_schedule_entry,
    is_waiter_entry,
    validate_schedule_entries,
    validate_waiter_entries,
)


class TestIsScheduleEntry:
    """is_schedule_entry のテスト"""

    def test_valid_schedule_entry_with_required_fields(self):
        """必須フィールド（name, frequency, time）を持つ辞書はTrue"""
        entry = {"name": "test", "frequency": "daily", "time": "22:00"}
        assert is_schedule_entry(entry) is True

    def test_valid_schedule_entry_with_all_fields(self):
        """全フィールドを持つ辞書もTrue"""
        entry = {
            "name": "test",
            "frequency": "weekly",
            "time": "22:00",
            "weekday": "mon",
            "theme": "test theme",
            "context": "",
            "file_list": "",
            "lang": "ja",
            "day_spec": "",
            "monthly_type": "",
            "created": "2025-01-01T00:00:00",
        }
        assert is_schedule_entry(entry) is True

    def test_missing_name_returns_false(self):
        """nameが欠けた辞書はFalse"""
        entry = {"frequency": "daily", "time": "22:00"}
        assert is_schedule_entry(entry) is False

    def test_missing_frequency_returns_false(self):
        """frequencyが欠けた辞書はFalse"""
        entry = {"name": "test", "time": "22:00"}
        assert is_schedule_entry(entry) is False

    def test_missing_time_returns_false(self):
        """timeが欠けた辞書はFalse"""
        entry = {"name": "test", "frequency": "daily"}
        assert is_schedule_entry(entry) is False

    def test_non_dict_returns_false(self):
        """辞書以外はFalse"""
        assert is_schedule_entry("not a dict") is False
        assert is_schedule_entry(None) is False
        assert is_schedule_entry([]) is False
        assert is_schedule_entry(123) is False

    def test_empty_dict_returns_false(self):
        """空の辞書はFalse"""
        assert is_schedule_entry({}) is False


class TestIsWaiterEntry:
    """is_waiter_entry のテスト"""

    def test_valid_waiter_entry(self):
        """必須フィールドを持つ辞書はTrue"""
        entry = {
            "pid": 12345,
            "target_time": "22:00",
            "theme": "test theme",
            "registered_at": "2025-01-01T00:00:00",
        }
        assert is_waiter_entry(entry) is True

    def test_missing_pid_returns_false(self):
        """pidが欠けた辞書はFalse"""
        entry = {
            "target_time": "22:00",
            "theme": "test theme",
            "registered_at": "2025-01-01T00:00:00",
        }
        assert is_waiter_entry(entry) is False

    def test_missing_target_time_returns_false(self):
        """target_timeが欠けた辞書はFalse"""
        entry = {
            "pid": 12345,
            "theme": "test theme",
            "registered_at": "2025-01-01T00:00:00",
        }
        assert is_waiter_entry(entry) is False

    def test_missing_theme_returns_false(self):
        """themeが欠けた辞書はFalse"""
        entry = {
            "pid": 12345,
            "target_time": "22:00",
            "registered_at": "2025-01-01T00:00:00",
        }
        assert is_waiter_entry(entry) is False

    def test_missing_registered_at_returns_false(self):
        """registered_atが欠けた辞書はFalse"""
        entry = {
            "pid": 12345,
            "target_time": "22:00",
            "theme": "test theme",
        }
        assert is_waiter_entry(entry) is False

    def test_non_dict_returns_false(self):
        """辞書以外はFalse"""
        assert is_waiter_entry("not a dict") is False
        assert is_waiter_entry(None) is False
        assert is_waiter_entry([]) is False


class TestValidateScheduleEntries:
    """validate_schedule_entries のテスト"""

    def test_filters_invalid_entries(self):
        """不正エントリをフィルタリング"""
        data = [
            {"name": "valid", "frequency": "daily", "time": "22:00"},
            {"name": "invalid"},  # 必須フィールド欠落
            "not a dict",
            None,
        ]
        result = validate_schedule_entries(data)
        assert len(result) == 1
        assert result[0]["name"] == "valid"

    def test_empty_list_returns_empty(self):
        """空リストは空リストを返す"""
        assert validate_schedule_entries([]) == []

    def test_all_valid_entries_preserved(self):
        """全て有効なエントリは全て保持"""
        data = [
            {"name": "test1", "frequency": "daily", "time": "22:00"},
            {"name": "test2", "frequency": "weekly", "time": "23:00"},
        ]
        result = validate_schedule_entries(data)
        assert len(result) == 2

    def test_all_invalid_entries_returns_empty(self):
        """全て不正なエントリは空リスト"""
        data = [
            {"name": "invalid"},  # time欠落
            {"frequency": "daily"},  # name欠落
            "not a dict",
        ]
        result = validate_schedule_entries(data)
        assert len(result) == 0


class TestValidateWaiterEntries:
    """validate_waiter_entries のテスト"""

    def test_filters_invalid_entries(self):
        """不正エントリをフィルタリング"""
        data = [
            {
                "pid": 12345,
                "target_time": "22:00",
                "theme": "valid",
                "registered_at": "2025-01-01T00:00:00",
            },
            {"pid": 12345},  # 必須フィールド欠落
            "not a dict",
        ]
        result = validate_waiter_entries(data)
        assert len(result) == 1
        assert result[0]["theme"] == "valid"

    def test_empty_list_returns_empty(self):
        """空リストは空リストを返す"""
        assert validate_waiter_entries([]) == []

    def test_all_valid_entries_preserved(self):
        """全て有効なエントリは全て保持"""
        data = [
            {
                "pid": 1,
                "target_time": "22:00",
                "theme": "theme1",
                "registered_at": "2025-01-01T00:00:00",
            },
            {
                "pid": 2,
                "target_time": "23:00",
                "theme": "theme2",
                "registered_at": "2025-01-01T00:00:00",
            },
        ]
        result = validate_waiter_entries(data)
        assert len(result) == 2
