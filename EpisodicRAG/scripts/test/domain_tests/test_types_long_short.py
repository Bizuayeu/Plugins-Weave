#!/usr/bin/env python3
"""
LongShortText 型のテスト
========================

テスト対象：domain/types.py の LongShortText, is_long_short_text
責任範囲：型定義とTypeGuard関数のテスト
"""

import pytest

from domain.types import LongShortText, is_long_short_text

pytestmark = pytest.mark.unit


# =============================================================================
# is_long_short_text のテスト
# =============================================================================


class TestIsLongShortText:
    """is_long_short_text() のテスト"""

    def test_valid_long_short_text(self):
        """有効な{long, short}形式はTrueを返す"""
        text: LongShortText = {"long": "詳細な要約", "short": "簡潔な要約"}
        assert is_long_short_text(text) is True

    def test_empty_strings_valid(self):
        """空文字列でも{long, short}形式であればTrue"""
        text = {"long": "", "short": ""}
        assert is_long_short_text(text) is True

    def test_missing_long_key(self):
        """longキーがない場合はFalse"""
        text = {"short": "簡潔な要約"}
        assert is_long_short_text(text) is False

    def test_missing_short_key(self):
        """shortキーがない場合はFalse"""
        text = {"long": "詳細な要約"}
        assert is_long_short_text(text) is False

    def test_non_string_long_value(self):
        """long値が文字列でない場合はFalse"""
        text = {"long": 123, "short": "簡潔な要約"}
        assert is_long_short_text(text) is False

    def test_non_string_short_value(self):
        """short値が文字列でない場合はFalse"""
        text = {"long": "詳細な要約", "short": 123}
        assert is_long_short_text(text) is False

    def test_not_a_dict(self):
        """辞書でない場合はFalse"""
        assert is_long_short_text("not a dict") is False
        assert is_long_short_text(None) is False
        assert is_long_short_text(123) is False
        assert is_long_short_text(["long", "short"]) is False

    def test_extra_keys_allowed(self):
        """追加キーがあってもTrue"""
        text = {"long": "詳細", "short": "簡潔", "extra": "追加"}
        assert is_long_short_text(text) is True

    def test_unicode_content(self):
        """Unicode文字を含む場合もTrue"""
        text = {"long": "日本語の詳細な要約 🎉", "short": "簡潔 ✨"}
        assert is_long_short_text(text) is True

    def test_multiline_content(self):
        """複数行の場合もTrue"""
        text = {
            "long": "1行目\n2行目\n3行目",
            "short": "簡潔な\n要約",
        }
        assert is_long_short_text(text) is True
