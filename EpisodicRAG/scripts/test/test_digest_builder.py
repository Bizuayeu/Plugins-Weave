#!/usr/bin/env python3
"""
finalize/digest_builder.py のユニットテスト
===========================================

RegularDigestBuilderクラスの動作を検証。
- build: RegularDigest構造の構築
"""
import pytest
from datetime import datetime

# Application層
from application.finalize import RegularDigestBuilder

# Domain層
from domain.version import DIGEST_FORMAT_VERSION


# =============================================================================
# テスト用定数
# =============================================================================
# 大容量テキスト: 通常の制限を超えるサイズでの動作確認
LARGE_TEXT_LENGTH = 5000


# =============================================================================
# RegularDigestBuilder.build テスト
# =============================================================================

class TestRegularDigestBuilderBuild:
    """build メソッドのテスト"""

    @pytest.fixture
    def valid_shadow_digest(self):
        """有効なShadowDigestデータ"""
        return {
            "source_files": ["Loop0001_test.txt", "Loop0002_test.txt"],
            "digest_type": "週次統合",
            "keywords": ["keyword1", "keyword2"],
            "abstract": "テスト用の全体統合分析です。",
            "impression": "テスト用の所感・展望です。"
        }

    @pytest.fixture
    def individual_digests(self):
        """個別ダイジェストリスト"""
        return [
            {"source_file": "Loop0001_test.txt", "content": "Content 1"},
            {"source_file": "Loop0002_test.txt", "content": "Content 2"}
        ]

    @pytest.mark.unit
    def test_returns_dict(self, valid_shadow_digest, individual_digests):
        """dictを返す"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests
        )
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_has_metadata_section(self, valid_shadow_digest, individual_digests):
        """metadataセクションが含まれる"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests
        )
        assert "metadata" in result

    @pytest.mark.unit
    def test_metadata_has_required_fields(self, valid_shadow_digest, individual_digests):
        """metadataに必須フィールドが含まれる"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests
        )
        metadata = result["metadata"]
        assert "digest_level" in metadata
        assert "digest_number" in metadata
        assert "last_updated" in metadata
        assert "version" in metadata

    @pytest.mark.unit
    def test_metadata_digest_level_matches(self, valid_shadow_digest, individual_digests):
        """metadata.digest_levelが正しい"""
        result = RegularDigestBuilder.build(
            level="monthly",
            new_digest_name="M001",
            digest_num="M001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests
        )
        assert result["metadata"]["digest_level"] == "monthly"

    @pytest.mark.unit
    def test_metadata_digest_number_matches(self, valid_shadow_digest, individual_digests):
        """metadata.digest_numberが正しい"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0123",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests
        )
        assert result["metadata"]["digest_number"] == "W0123"

    @pytest.mark.unit
    def test_metadata_version_is_correct(self, valid_shadow_digest, individual_digests):
        """metadata.versionが正しい"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests
        )
        assert result["metadata"]["version"] == DIGEST_FORMAT_VERSION

    @pytest.mark.unit
    def test_metadata_last_updated_is_iso_format(self, valid_shadow_digest, individual_digests):
        """metadata.last_updatedがISO形式"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests
        )
        # ISO形式としてパース可能か確認
        datetime.fromisoformat(result["metadata"]["last_updated"])

    @pytest.mark.unit
    def test_has_overall_digest_section(self, valid_shadow_digest, individual_digests):
        """overall_digestセクションが含まれる"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests
        )
        assert "overall_digest" in result

    @pytest.mark.unit
    def test_overall_digest_has_required_fields(self, valid_shadow_digest, individual_digests):
        """overall_digestに必須フィールドが含まれる"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests
        )
        overall = result["overall_digest"]
        assert "name" in overall
        assert "timestamp" in overall
        assert "source_files" in overall
        assert "digest_type" in overall
        assert "keywords" in overall
        assert "abstract" in overall
        assert "impression" in overall

    @pytest.mark.unit
    def test_overall_digest_name_matches(self, valid_shadow_digest, individual_digests):
        """overall_digest.nameが正しい"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001_CustomTitle",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests
        )
        assert result["overall_digest"]["name"] == "W0001_CustomTitle"

    @pytest.mark.unit
    def test_overall_digest_source_files_from_shadow(self, valid_shadow_digest, individual_digests):
        """overall_digest.source_filesがshadowから取得される"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests
        )
        assert result["overall_digest"]["source_files"] == ["Loop0001_test.txt", "Loop0002_test.txt"]

    @pytest.mark.unit
    def test_overall_digest_fields_from_shadow(self, valid_shadow_digest, individual_digests):
        """overall_digestのフィールドがshadowから取得される"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests
        )
        overall = result["overall_digest"]
        assert overall["digest_type"] == "週次統合"
        assert overall["keywords"] == ["keyword1", "keyword2"]
        assert overall["abstract"] == "テスト用の全体統合分析です。"
        assert overall["impression"] == "テスト用の所感・展望です。"

    @pytest.mark.unit
    def test_has_individual_digests_section(self, valid_shadow_digest, individual_digests):
        """individual_digestsセクションが含まれる"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests
        )
        assert "individual_digests" in result

    @pytest.mark.unit
    def test_individual_digests_preserved(self, valid_shadow_digest, individual_digests):
        """individual_digestsがそのまま保持される"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests
        )
        assert result["individual_digests"] == individual_digests
        assert len(result["individual_digests"]) == 2

    @pytest.mark.unit
    def test_empty_individual_digests(self, valid_shadow_digest):
        """空のindividual_digestsでも動作"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=[]
        )
        assert result["individual_digests"] == []

    @pytest.mark.unit
    def test_missing_shadow_fields_use_defaults(self):
        """shadowに欠落フィールドがある場合、デフォルト値を使用"""
        minimal_shadow = {
            # source_files, digest_type等がない
        }
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=minimal_shadow,
            individual_digests=[]
        )
        overall = result["overall_digest"]
        assert overall["source_files"] == []
        assert overall["digest_type"] == "統合"  # デフォルト
        assert overall["keywords"] == []
        assert overall["abstract"] == ""
        assert overall["impression"] == ""

    @pytest.mark.unit
    def test_timestamp_is_recent(self, valid_shadow_digest, individual_digests):
        """timestampが現在時刻に近い"""
        before = datetime.now()
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests
        )
        after = datetime.now()

        timestamp = datetime.fromisoformat(result["overall_digest"]["timestamp"])
        assert before <= timestamp <= after

    @pytest.mark.unit
    def test_very_long_abstract_preserved(self, individual_digests):
        """非常に長いabstractがそのまま保持される（builderは切り捨てない）"""
        long_abstract = "あ" * LARGE_TEXT_LENGTH
        shadow_with_long_abstract = {
            "source_files": ["Loop0001.txt"],
            "digest_type": "テスト",
            "keywords": [],
            "abstract": long_abstract,
            "impression": ""
        }
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=shadow_with_long_abstract,
            individual_digests=individual_digests
        )
        assert len(result["overall_digest"]["abstract"]) == LARGE_TEXT_LENGTH
        assert result["overall_digest"]["abstract"] == long_abstract

    @pytest.mark.unit
    def test_empty_source_files_list(self, individual_digests):
        """空のsource_filesリストを正しく処理"""
        shadow_with_empty_sources = {
            "source_files": [],
            "digest_type": "空テスト",
            "keywords": ["empty"],
            "abstract": "No sources",
            "impression": ""
        }
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=shadow_with_empty_sources,
            individual_digests=individual_digests
        )
        assert result["overall_digest"]["source_files"] == []
        assert result["overall_digest"]["digest_type"] == "空テスト"
