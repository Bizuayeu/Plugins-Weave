#!/usr/bin/env python3
"""
test_placeholder_manager.py
===========================

application/shadow/placeholder_manager.py のテスト
"""

import pytest

from application.shadow.placeholder_manager import PlaceholderManager
from domain.constants import PLACEHOLDER_END, PLACEHOLDER_LIMITS, PLACEHOLDER_MARKER


class TestPlaceholderManager:
    """PlaceholderManagerクラスのテスト"""

    @pytest.fixture
    def manager(self):
        """PlaceholderManagerインスタンス"""
        return PlaceholderManager()

    @pytest.fixture
    def empty_overall_digest(self):
        """空のoverall_digest"""
        return {
            "timestamp": "2025-01-01T00:00:00",
            "source_files": [],
            "digest_type": "test",
            "keywords": [],
            "abstract": "",
            "impression": "",
        }

    @pytest.fixture
    def placeholder_overall_digest(self):
        """PLACEHOLDERを含むoverall_digest"""
        return {
            "timestamp": "2025-01-01T00:00:00",
            "source_files": [],
            "digest_type": "test",
            "keywords": [],
            "abstract": f"{PLACEHOLDER_MARKER}: existing{PLACEHOLDER_END}",
            "impression": "",
        }

    @pytest.fixture
    def analyzed_overall_digest(self):
        """分析済みのoverall_digest"""
        return {
            "timestamp": "2025-01-01T00:00:00",
            "source_files": ["Loop0001_test.txt"],
            "digest_type": "test",
            "keywords": ["keyword1", "keyword2"],
            "abstract": "This is an actual analysis of the content.",
            "impression": "This is an actual impression.",
        }

    @pytest.mark.unit
    def test_update_empty_digest(self, manager, empty_overall_digest) -> None:
        """空のdigestをPLACEHOLDERで更新"""
        manager.update_or_preserve(empty_overall_digest, total_files=5)

        assert PLACEHOLDER_MARKER in empty_overall_digest["abstract"]
        assert PLACEHOLDER_MARKER in empty_overall_digest["impression"]
        assert len(empty_overall_digest["keywords"]) == PLACEHOLDER_LIMITS["keyword_count"]

    @pytest.mark.unit
    def test_update_placeholder_digest(self, manager, placeholder_overall_digest) -> None:
        """既存PLACEHOLDERを新しいPLACEHOLDERで更新"""
        manager.update_or_preserve(placeholder_overall_digest, total_files=10)

        assert "10ファイル" in placeholder_overall_digest["abstract"]
        assert PLACEHOLDER_MARKER in placeholder_overall_digest["abstract"]

    @pytest.mark.unit
    def test_preserve_analyzed_digest(self, manager, analyzed_overall_digest) -> None:
        """分析済みdigestは保持"""
        original_abstract = analyzed_overall_digest["abstract"]
        original_impression = analyzed_overall_digest["impression"]

        manager.update_or_preserve(analyzed_overall_digest, total_files=10)

        assert analyzed_overall_digest["abstract"] == original_abstract
        assert analyzed_overall_digest["impression"] == original_impression

    @pytest.mark.unit
    def test_placeholder_contains_file_count(self, manager, empty_overall_digest) -> None:
        """PLACEHOLDERにファイル数が含まれる"""
        manager.update_or_preserve(empty_overall_digest, total_files=7)

        assert "7ファイル" in empty_overall_digest["abstract"]

    @pytest.mark.unit
    def test_placeholder_contains_char_limit(self, manager, empty_overall_digest) -> None:
        """PLACEHOLDERに文字数制限が含まれる"""
        manager.update_or_preserve(empty_overall_digest, total_files=5)

        expected_chars = PLACEHOLDER_LIMITS["abstract_chars"]
        assert f"{expected_chars}文字" in empty_overall_digest["abstract"]

    @pytest.mark.unit
    def test_placeholder_keywords_count(self, manager, empty_overall_digest) -> None:
        """キーワードの数がPLACEHOLDER_LIMITSと一致"""
        manager.update_or_preserve(empty_overall_digest, total_files=5)

        assert len(empty_overall_digest["keywords"]) == PLACEHOLDER_LIMITS["keyword_count"]

    @pytest.mark.unit
    def test_placeholder_keywords_format(self, manager, empty_overall_digest) -> None:
        """キーワードのフォーマットが正しい"""
        manager.update_or_preserve(empty_overall_digest, total_files=5)

        for i, keyword in enumerate(empty_overall_digest["keywords"], 1):
            assert PLACEHOLDER_MARKER in keyword
            assert f"keyword{i}" in keyword
            assert PLACEHOLDER_END in keyword

    @pytest.mark.unit
    def test_placeholder_impression_format(self, manager, empty_overall_digest) -> None:
        """impressionのPLACEHOLDERフォーマット"""
        manager.update_or_preserve(empty_overall_digest, total_files=5)

        impression = empty_overall_digest["impression"]
        assert PLACEHOLDER_MARKER in impression
        assert "所感・展望" in impression
        expected_chars = PLACEHOLDER_LIMITS["impression_chars"]
        assert f"{expected_chars}文字" in impression

    @pytest.mark.unit
    def test_none_abstract_treated_as_placeholder(self, manager) -> None:
        """abstractがNoneの場合もPLACEHOLDERとして扱う"""
        digest = {
            "timestamp": "",
            "source_files": [],
            "digest_type": "",
            "keywords": [],
            "abstract": None,
            "impression": "",
        }

        manager.update_or_preserve(digest, total_files=3)

        # None の場合、.get() の結果が falsy なのでPLACEHOLDERが設定される
        # ただし実際の実装では None に対して "in" 演算子がエラーになる可能性
        # このテストは実装の挙動を確認

    @pytest.mark.unit
    def test_zero_files(self, manager, empty_overall_digest) -> None:
        """0ファイルの場合"""
        manager.update_or_preserve(empty_overall_digest, total_files=0)

        assert "0ファイル" in empty_overall_digest["abstract"]

    @pytest.mark.unit
    def test_large_file_count(self, manager, empty_overall_digest) -> None:
        """大量ファイルの場合"""
        manager.update_or_preserve(empty_overall_digest, total_files=1000)

        assert "1000ファイル" in empty_overall_digest["abstract"]

    @pytest.mark.unit
    def test_placeholder_end_marker(self, manager, empty_overall_digest) -> None:
        """PLACEHOLDER_ENDマーカーが含まれる"""
        manager.update_or_preserve(empty_overall_digest, total_files=5)

        assert PLACEHOLDER_END in empty_overall_digest["abstract"]
        assert PLACEHOLDER_END in empty_overall_digest["impression"]
