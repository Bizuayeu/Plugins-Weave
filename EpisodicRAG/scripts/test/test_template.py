#!/usr/bin/env python3
"""
shadow/template.py のユニットテスト
===================================

ShadowTemplateクラスの動作を検証。
- create_empty_overall_digest: プレースホルダー付きoverall_digest生成
- get_template: ShadowGrandDigestテンプレート生成
"""

from datetime import datetime

import pytest

# Application層
from application.shadow import ShadowTemplate

# Domain層
from domain.constants import (
    LEVEL_NAMES,
    PLACEHOLDER_END,
    PLACEHOLDER_LIMITS,
    PLACEHOLDER_MARKER,
    PLACEHOLDER_SIMPLE,
)
from domain.version import DIGEST_FORMAT_VERSION

# =============================================================================
# ShadowTemplate.create_empty_overall_digest テスト
# =============================================================================


class TestCreateEmptyOverallDigest:
    """create_empty_overall_digest メソッドのテスト"""

    @pytest.fixture
    def template(self):
        """テスト用ShadowTemplateインスタンス"""
        return ShadowTemplate(levels=LEVEL_NAMES)

    @pytest.mark.unit
    def test_returns_dict(self, template):
        """dictを返す"""
        result = template.create_empty_overall_digest()
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_has_all_required_fields(self, template):
        """必須フィールドがすべて存在する"""
        result = template.create_empty_overall_digest()
        required_fields = [
            "timestamp",
            "source_files",
            "digest_type",
            "keywords",
            "abstract",
            "impression",
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    @pytest.mark.unit
    def test_timestamp_is_placeholder(self, template):
        """timestampはプレースホルダー"""
        result = template.create_empty_overall_digest()
        assert result["timestamp"] == PLACEHOLDER_SIMPLE

    @pytest.mark.unit
    def test_source_files_is_empty_list(self, template):
        """source_filesは空リスト"""
        result = template.create_empty_overall_digest()
        assert result["source_files"] == []
        assert isinstance(result["source_files"], list)

    @pytest.mark.unit
    def test_digest_type_is_placeholder(self, template):
        """digest_typeはプレースホルダー"""
        result = template.create_empty_overall_digest()
        assert result["digest_type"] == PLACEHOLDER_SIMPLE

    @pytest.mark.unit
    def test_keywords_count_matches_config(self, template):
        """keywordsの数はPLACEHOLDER_LIMITS.keyword_countと一致"""
        result = template.create_empty_overall_digest()
        expected_count = PLACEHOLDER_LIMITS["keyword_count"]
        assert len(result["keywords"]) == expected_count

    @pytest.mark.unit
    def test_keywords_are_placeholders(self, template):
        """各keywordはプレースホルダー形式"""
        result = template.create_empty_overall_digest()
        for keyword in result["keywords"]:
            assert PLACEHOLDER_MARKER in keyword
            assert PLACEHOLDER_END in keyword

    @pytest.mark.unit
    def test_keywords_have_numbered_names(self, template):
        """keywordsには番号付き名前が含まれる"""
        result = template.create_empty_overall_digest()
        for i, keyword in enumerate(result["keywords"], start=1):
            assert f"keyword{i}" in keyword

    @pytest.mark.unit
    def test_abstract_is_placeholder(self, template):
        """abstractはプレースホルダー"""
        result = template.create_empty_overall_digest()
        assert PLACEHOLDER_MARKER in result["abstract"]
        assert PLACEHOLDER_END in result["abstract"]

    @pytest.mark.unit
    def test_abstract_contains_char_limit(self, template):
        """abstractにはabstract_charsの文字数ガイドラインが含まれる"""
        result = template.create_empty_overall_digest()
        expected_chars = str(PLACEHOLDER_LIMITS["abstract_chars"])
        assert expected_chars in result["abstract"]

    @pytest.mark.unit
    def test_impression_is_placeholder(self, template):
        """impressionはプレースホルダー"""
        result = template.create_empty_overall_digest()
        assert PLACEHOLDER_MARKER in result["impression"]
        assert PLACEHOLDER_END in result["impression"]

    @pytest.mark.unit
    def test_impression_contains_char_limit(self, template):
        """impressionにはimpression_charsの文字数ガイドラインが含まれる"""
        result = template.create_empty_overall_digest()
        expected_chars = str(PLACEHOLDER_LIMITS["impression_chars"])
        assert expected_chars in result["impression"]


# =============================================================================
# ShadowTemplate.get_template テスト
# =============================================================================


class TestGetTemplate:
    """get_template メソッドのテスト"""

    @pytest.fixture
    def template(self):
        """テスト用ShadowTemplateインスタンス（全レベル）"""
        return ShadowTemplate(levels=LEVEL_NAMES)

    @pytest.fixture
    def custom_levels_template(self):
        """カスタムレベルのShadowTemplate"""
        return ShadowTemplate(levels=["weekly", "monthly"])

    @pytest.mark.unit
    def test_returns_dict(self, template):
        """dictを返す"""
        result = template.get_template()
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_has_metadata_section(self, template):
        """metadataセクションが存在する"""
        result = template.get_template()
        assert "metadata" in result
        assert isinstance(result["metadata"], dict)

    @pytest.mark.unit
    def test_has_latest_digests_section(self, template):
        """latest_digestsセクションが存在する"""
        result = template.get_template()
        assert "latest_digests" in result
        assert isinstance(result["latest_digests"], dict)

    @pytest.mark.unit
    def test_metadata_has_last_updated(self, template):
        """metadata.last_updatedが存在する"""
        result = template.get_template()
        assert "last_updated" in result["metadata"]

    @pytest.mark.unit
    def test_metadata_last_updated_is_iso_format(self, template):
        """metadata.last_updatedはISO形式の日時"""
        result = template.get_template()
        last_updated = result["metadata"]["last_updated"]
        # ISO形式としてパース可能であることを確認
        datetime.fromisoformat(last_updated)

    @pytest.mark.unit
    def test_metadata_has_version(self, template):
        """metadata.versionが存在し、正しい値"""
        result = template.get_template()
        assert "version" in result["metadata"]
        assert result["metadata"]["version"] == DIGEST_FORMAT_VERSION

    @pytest.mark.unit
    def test_metadata_has_description(self, template):
        """metadata.descriptionが存在する"""
        result = template.get_template()
        assert "description" in result["metadata"]
        assert isinstance(result["metadata"]["description"], str)
        assert len(result["metadata"]["description"]) > 0

    @pytest.mark.unit
    def test_latest_digests_has_all_levels(self, template):
        """latest_digestsに全レベルが含まれる"""
        result = template.get_template()
        for level in LEVEL_NAMES:
            assert level in result["latest_digests"], f"Missing level: {level}"

    @pytest.mark.unit
    def test_each_level_has_overall_digest(self, template):
        """各レベルにoverall_digestが含まれる"""
        result = template.get_template()
        for level in LEVEL_NAMES:
            assert "overall_digest" in result["latest_digests"][level]

    @pytest.mark.unit
    def test_level_overall_digest_has_placeholders(self, template):
        """各レベルのoverall_digestにプレースホルダーが含まれる"""
        result = template.get_template()
        for level in LEVEL_NAMES:
            overall = result["latest_digests"][level]["overall_digest"]
            assert PLACEHOLDER_SIMPLE in overall["timestamp"]
            assert len(overall["keywords"]) == PLACEHOLDER_LIMITS["keyword_count"]

    @pytest.mark.unit
    def test_custom_levels_only_included(self, custom_levels_template):
        """カスタムレベルのみがlatest_digestsに含まれる"""
        result = custom_levels_template.get_template()
        assert "weekly" in result["latest_digests"]
        assert "monthly" in result["latest_digests"]
        assert "quarterly" not in result["latest_digests"]
        assert len(result["latest_digests"]) == 2


# =============================================================================
# ShadowTemplate 初期化テスト
# =============================================================================


class TestShadowTemplateInit:
    """ShadowTemplate 初期化のテスト"""

    @pytest.mark.unit
    def test_stores_levels(self):
        """levelsが正しく保存される"""
        levels = ["weekly", "monthly"]
        template = ShadowTemplate(levels=levels)
        assert template.levels == levels

    @pytest.mark.unit
    def test_empty_levels(self):
        """空のlevelsでも初期化可能"""
        template = ShadowTemplate(levels=[])
        assert template.levels == []
        result = template.get_template()
        assert result["latest_digests"] == {}

    @pytest.mark.unit
    def test_single_level(self):
        """単一レベルでも動作"""
        template = ShadowTemplate(levels=["weekly"])
        result = template.get_template()
        assert len(result["latest_digests"]) == 1
        assert "weekly" in result["latest_digests"]
