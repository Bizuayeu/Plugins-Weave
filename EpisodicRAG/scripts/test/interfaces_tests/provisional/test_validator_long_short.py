#!/usr/bin/env python3
"""
validate_long_short_text のテスト
==================================

テスト対象：interfaces/provisional/validator.py の validate_long_short_text
責任範囲：{long, short}形式のバリデーション
"""

import pytest

from domain.exceptions import ValidationError
from interfaces.provisional.validator import (
    validate_individual_digest,
    validate_long_short_text,
)

pytestmark = pytest.mark.unit


# =============================================================================
# validate_long_short_text のテスト
# =============================================================================


class TestValidateLongShortText:
    """validate_long_short_text() のテスト"""

    def test_valid_long_short_format(self) -> None:
        """有効な{long, short}形式は例外を発生しない"""
        value = {"long": "詳細な要約", "short": "簡潔な要約"}
        # Should not raise
        validate_long_short_text(value, "abstract", 0)

    def test_none_value_allowed(self) -> None:
        """None値は許容される（オプショナルフィールド）"""
        # Should not raise
        validate_long_short_text(None, "abstract", 0)

    def test_string_value_rejected(self) -> None:
        """文字列値は拒否される"""
        with pytest.raises(ValidationError) as exc_info:
            validate_long_short_text("plain string", "abstract", 0)
        assert "abstract at index 0" in str(exc_info.value)
        assert "{long: str, short: str}" in str(exc_info.value)
        assert "str" in str(exc_info.value)

    def test_missing_long_key_rejected(self) -> None:
        """longキーがない場合は拒否"""
        with pytest.raises(ValidationError) as exc_info:
            validate_long_short_text({"short": "簡潔"}, "abstract", 0)
        assert "'long' and 'short' keys" in str(exc_info.value)

    def test_missing_short_key_rejected(self) -> None:
        """shortキーがない場合は拒否"""
        with pytest.raises(ValidationError) as exc_info:
            validate_long_short_text({"long": "詳細"}, "impression", 1)
        assert "'long' and 'short' keys" in str(exc_info.value)

    def test_non_string_long_value_rejected(self) -> None:
        """long値が文字列でない場合は拒否"""
        with pytest.raises(ValidationError) as exc_info:
            validate_long_short_text({"long": 123, "short": "簡潔"}, "abstract", 0)
        assert "'long' and 'short' must be strings" in str(exc_info.value)

    def test_non_string_short_value_rejected(self) -> None:
        """short値が文字列でない場合は拒否"""
        with pytest.raises(ValidationError) as exc_info:
            validate_long_short_text({"long": "詳細", "short": None}, "abstract", 0)
        assert "'long' and 'short' must be strings" in str(exc_info.value)

    def test_empty_strings_allowed(self) -> None:
        """空文字列は許容される"""
        value = {"long": "", "short": ""}
        # Should not raise
        validate_long_short_text(value, "abstract", 0)

    def test_list_value_rejected(self) -> None:
        """リスト値は拒否される"""
        with pytest.raises(ValidationError) as exc_info:
            validate_long_short_text(["long", "short"], "abstract", 0)
        assert "list" in str(exc_info.value)


# =============================================================================
# validate_individual_digest での {long, short} 検証テスト
# =============================================================================


class TestValidateIndividualDigestLongShort:
    """validate_individual_digest() での abstract/impression 検証テスト"""

    def test_valid_digest_with_long_short(self) -> None:
        """有効な{long, short}形式のdigestは例外を発生しない"""
        digest = {
            "source_file": "L00001_test.txt",
            "digest_type": "テスト",
            "keywords": ["test"],
            "abstract": {"long": "詳細な要約", "short": "簡潔な要約"},
            "impression": {"long": "詳細な所感", "short": "簡潔な所感"},
        }
        # Should not raise
        validate_individual_digest(digest, 0)

    def test_string_abstract_rejected(self) -> None:
        """文字列形式のabstractは拒否される"""
        digest = {
            "source_file": "L00001_test.txt",
            "abstract": "単純な文字列",
            "impression": {"long": "詳細", "short": "簡潔"},
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_individual_digest(digest, 0)
        assert "abstract" in str(exc_info.value)

    def test_string_impression_rejected(self) -> None:
        """文字列形式のimpressionは拒否される"""
        digest = {
            "source_file": "L00001_test.txt",
            "abstract": {"long": "詳細", "short": "簡潔"},
            "impression": "単純な文字列",
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_individual_digest(digest, 0)
        assert "impression" in str(exc_info.value)

    def test_missing_abstract_allowed(self) -> None:
        """abstractがない場合は許容（オプショナル）"""
        digest = {
            "source_file": "L00001_test.txt",
            "impression": {"long": "詳細", "short": "簡潔"},
        }
        # Should not raise
        validate_individual_digest(digest, 0)

    def test_missing_impression_allowed(self) -> None:
        """impressionがない場合は許容（オプショナル）"""
        digest = {
            "source_file": "L00001_test.txt",
            "abstract": {"long": "詳細", "short": "簡潔"},
        }
        # Should not raise
        validate_individual_digest(digest, 0)
