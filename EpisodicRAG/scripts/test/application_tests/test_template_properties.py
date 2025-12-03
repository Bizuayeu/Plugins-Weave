#!/usr/bin/env python3
"""
Property-Based Tests for Shadow Template
=========================================

Using hypothesis to test invariants in application/shadow/template.py
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from application.shadow.template import ShadowTemplate
from domain.constants import LEVEL_NAMES

# =============================================================================
# Strategies for generating test data
# =============================================================================

# Valid level names (non-empty unique strings)
valid_levels = st.lists(
    st.text(
        alphabet=st.characters(whitelist_categories=("L", "N")),
        min_size=1,
        max_size=20,
    ),
    min_size=1,
    max_size=8,
    unique=True,
)

# Real level names from the domain
real_levels = st.just(LEVEL_NAMES)


# =============================================================================
# ShadowTemplate.get_template Properties
# =============================================================================


class TestTemplateGetTemplateProperties:
    """Property-based tests for ShadowTemplate.get_template"""

    @pytest.mark.property
    @given(levels=valid_levels)
    @settings(max_examples=200)
    def test_template_contains_all_levels(self, levels) -> None:
        """テンプレートに全レベルが含まれる"""
        template = ShadowTemplate(levels)
        data = template.get_template()

        assert "latest_digests" in data
        assert set(data["latest_digests"].keys()) == set(levels)

    @pytest.mark.property
    @given(levels=valid_levels)
    @settings(max_examples=100)
    def test_template_has_metadata(self, levels) -> None:
        """テンプレートにmetadataセクションが存在"""
        template = ShadowTemplate(levels)
        data = template.get_template()

        assert "metadata" in data
        assert "version" in data["metadata"]
        assert "last_updated" in data["metadata"]
        assert "description" in data["metadata"]

    @pytest.mark.property
    @given(levels=valid_levels)
    @settings(max_examples=100)
    def test_each_level_has_overall_digest(self, levels) -> None:
        """各レベルにoverall_digestが存在"""
        template = ShadowTemplate(levels)
        data = template.get_template()

        for level in levels:
            assert "overall_digest" in data["latest_digests"][level]

    @pytest.mark.property
    @given(levels=real_levels)
    @settings(max_examples=10)
    def test_real_levels_work(self, levels) -> None:
        """実際のLEVEL_NAMESでも正しく動作"""
        template = ShadowTemplate(levels)
        data = template.get_template()

        assert set(data["latest_digests"].keys()) == set(levels)


# =============================================================================
# ShadowTemplate.create_empty_overall_digest Properties
# =============================================================================


class TestTemplateEmptyOverallDigestProperties:
    """Property-based tests for ShadowTemplate.create_empty_overall_digest"""

    @pytest.mark.property
    @given(levels=valid_levels)
    @settings(max_examples=200)
    def test_empty_digest_has_required_keys(self, levels) -> None:
        """overall_digestに必須キーが存在"""
        template = ShadowTemplate(levels)
        digest = template.create_empty_overall_digest()

        required_keys = [
            "source_files",
            "digest_type",
            "keywords",
            "abstract",
            "impression",
        ]
        for key in required_keys:
            assert key in digest, f"Missing key: {key}"

    @pytest.mark.property
    @given(levels=valid_levels)
    @settings(max_examples=200)
    def test_source_files_starts_empty(self, levels) -> None:
        """source_filesは空リストで初期化"""
        template = ShadowTemplate(levels)
        digest = template.create_empty_overall_digest()

        assert digest["source_files"] == []

    @pytest.mark.property
    @given(levels=valid_levels)
    @settings(max_examples=100)
    def test_keywords_is_list(self, levels) -> None:
        """keywordsはリスト型"""
        template = ShadowTemplate(levels)
        digest = template.create_empty_overall_digest()

        assert isinstance(digest["keywords"], list)

    @pytest.mark.property
    @given(levels=valid_levels)
    @settings(max_examples=100)
    def test_abstract_is_string(self, levels) -> None:
        """abstractは文字列型"""
        template = ShadowTemplate(levels)
        digest = template.create_empty_overall_digest()

        assert isinstance(digest["abstract"], str)

    @pytest.mark.property
    @given(levels=valid_levels)
    @settings(max_examples=100)
    def test_impression_is_string(self, levels) -> None:
        """impressionは文字列型"""
        template = ShadowTemplate(levels)
        digest = template.create_empty_overall_digest()

        assert isinstance(digest["impression"], str)

    @pytest.mark.property
    @given(levels=valid_levels)
    @settings(max_examples=50)
    def test_digest_type_is_string(self, levels) -> None:
        """digest_typeは文字列型"""
        template = ShadowTemplate(levels)
        digest = template.create_empty_overall_digest()

        assert isinstance(digest["digest_type"], str)


# =============================================================================
# Consistency Properties
# =============================================================================


class TestTemplateConsistencyProperties:
    """Cross-method consistency tests"""

    @pytest.mark.property
    @given(levels=valid_levels)
    @settings(max_examples=100)
    def test_template_overall_digest_matches_empty_digest(self, levels) -> None:
        """get_template()内のoverall_digestはcreate_empty_overall_digest()と同じ構造"""
        template = ShadowTemplate(levels)

        template_data = template.get_template()
        empty_digest = template.create_empty_overall_digest()

        # 任意のレベルのoverall_digestを取得
        first_level = levels[0]
        template_digest = template_data["latest_digests"][first_level]["overall_digest"]

        # キーセットが同じ
        assert set(template_digest.keys()) == set(empty_digest.keys())

    @pytest.mark.property
    @given(levels=valid_levels)
    @settings(max_examples=50)
    def test_multiple_calls_create_independent_digests(self, levels) -> None:
        """create_empty_overall_digest()の複数呼び出しは独立したオブジェクトを返す"""
        template = ShadowTemplate(levels)

        digest1 = template.create_empty_overall_digest()
        digest2 = template.create_empty_overall_digest()

        # 異なるオブジェクト
        assert digest1 is not digest2

        # 片方を変更しても他方に影響しない
        digest1["source_files"].append("test.txt")
        assert digest2["source_files"] == []

    @pytest.mark.property
    @given(levels=valid_levels)
    @settings(max_examples=50)
    def test_multiple_template_calls_create_independent_data(self, levels) -> None:
        """get_template()の複数呼び出しは独立したオブジェクトを返す"""
        template = ShadowTemplate(levels)

        data1 = template.get_template()
        data2 = template.get_template()

        # 異なるオブジェクト
        assert data1 is not data2

        # 片方を変更しても他方に影響しない
        first_level = levels[0]
        data1["latest_digests"][first_level]["overall_digest"]["source_files"].append("test.txt")
        assert data2["latest_digests"][first_level]["overall_digest"]["source_files"] == []
