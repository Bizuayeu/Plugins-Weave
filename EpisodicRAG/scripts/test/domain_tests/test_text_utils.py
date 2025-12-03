#!/usr/bin/env python3
"""
text_utils のテスト
==================

テスト対象：domain/text_utils.py
責任範囲：LongShortTextからのテキスト抽出
"""

import pytest

from domain.text_utils import extract_long_value, extract_short_value, extract_value

pytestmark = pytest.mark.unit


# =============================================================================
# extract_long_value のテスト
# =============================================================================


class TestExtractLongValue:
    """extract_long_value() のテスト"""

    def test_extracts_long_from_dict(self) -> None:
        """辞書形式からlong値を抽出"""
        text = {"long": "詳細な要約（2400字）", "short": "簡潔な要約（1200字）"}
        result = extract_long_value(text)
        assert result == "詳細な要約（2400字）"

    def test_returns_default_for_missing_long(self) -> None:
        """longキーがない場合はデフォルト値を返す"""
        text = {"short": "簡潔な要約"}
        result = extract_long_value(text, default="デフォルト")
        assert result == "デフォルト"

    def test_returns_string_as_is(self) -> None:
        """文字列の場合はそのまま返す（OverallDigestData互換）"""
        result = extract_long_value("plain text")
        assert result == "plain text"

    def test_returns_default_for_non_dict_non_string(self) -> None:
        """辞書でも文字列でもない場合はデフォルト値を返す"""
        result = extract_long_value(123, default="デフォルト")
        assert result == "デフォルト"

    def test_returns_empty_string_by_default(self) -> None:
        """デフォルト値が指定されない場合は空文字を返す"""
        result = extract_long_value(None)
        assert result == ""

    def test_handles_empty_long_value(self) -> None:
        """long値が空文字の場合はその空文字を返す"""
        text = {"long": "", "short": "簡潔な要約"}
        result = extract_long_value(text)
        assert result == ""

    def test_empty_string_returns_default(self) -> None:
        """空文字列の場合はデフォルト値を返す"""
        result = extract_long_value("", default="デフォルト")
        assert result == "デフォルト"


# =============================================================================
# extract_short_value のテスト
# =============================================================================


class TestExtractShortValue:
    """extract_short_value() のテスト"""

    def test_extracts_short_from_dict(self) -> None:
        """辞書形式からshort値を抽出"""
        text = {"long": "詳細な要約", "short": "簡潔な要約（1200字）"}
        result = extract_short_value(text)
        assert result == "簡潔な要約（1200字）"

    def test_returns_default_for_missing_short(self) -> None:
        """shortキーがない場合はデフォルト値を返す"""
        text = {"long": "詳細な要約"}
        result = extract_short_value(text, default="デフォルト")
        assert result == "デフォルト"

    def test_returns_default_for_non_dict(self) -> None:
        """辞書以外の場合はデフォルト値を返す"""
        result = extract_short_value("not a dict", default="デフォルト")
        assert result == "デフォルト"


# =============================================================================
# extract_value のテスト
# =============================================================================


class TestExtractValue:
    """extract_value() のテスト"""

    def test_extracts_any_key(self) -> None:
        """任意のキーで値を抽出"""
        text = {"long": "詳細", "short": "簡潔", "medium": "中程度"}
        assert extract_value(text, "long") == "詳細"
        assert extract_value(text, "short") == "簡潔"
        assert extract_value(text, "medium") == "中程度"

    def test_returns_default_for_missing_key(self) -> None:
        """キーがない場合はデフォルト値を返す"""
        text = {"long": "詳細"}
        result = extract_value(text, "missing", default="なし")
        assert result == "なし"
