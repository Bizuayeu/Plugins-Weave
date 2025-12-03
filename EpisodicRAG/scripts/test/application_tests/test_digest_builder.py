#!/usr/bin/env python3
"""
finalize/digest_builder.py のユニットテスト
===========================================

RegularDigestBuilderクラスの動作を検証。
- build: RegularDigest構造の構築
"""

from datetime import datetime

import pytest

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
            "impression": "テスト用の所感・展望です。",
        }

    @pytest.fixture
    def individual_digests(self):
        """個別ダイジェストリスト"""
        return [
            {"source_file": "Loop0001_test.txt", "content": "Content 1"},
            {"source_file": "Loop0002_test.txt", "content": "Content 2"},
        ]

    @pytest.mark.unit
    def test_builds_valid_json_serializable_digest(
        self, valid_shadow_digest, individual_digests
    ) -> None:
        """構築されたダイジェストがJSONシリアライズ可能である"""
        import json

        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests,
        )

        # JSONシリアライズ・デシリアライズ可能
        json_str = json.dumps(result, ensure_ascii=False)
        restored = json.loads(json_str)
        assert restored == result

    @pytest.mark.unit
    def test_builds_complete_digest_structure(
        self, valid_shadow_digest, individual_digests
    ) -> None:
        """ダイジェストに必要な全セクションが含まれる"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests,
        )

        # 必須セクションの存在確認
        assert "metadata" in result
        assert "overall_digest" in result
        assert "individual_digests" in result

        # metadata の必須フィールド
        metadata = result["metadata"]
        assert all(
            key in metadata for key in ["digest_level", "digest_number", "last_updated", "version"]
        )

    @pytest.mark.unit
    def test_metadata_digest_level_matches(self, valid_shadow_digest, individual_digests) -> None:
        """metadata.digest_levelが正しい"""
        result = RegularDigestBuilder.build(
            level="monthly",
            new_digest_name="M001",
            digest_num="M001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests,
        )
        assert result["metadata"]["digest_level"] == "monthly"

    @pytest.mark.unit
    def test_metadata_digest_number_matches(self, valid_shadow_digest, individual_digests) -> None:
        """metadata.digest_numberが正しい"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0123",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests,
        )
        assert result["metadata"]["digest_number"] == "W0123"

    @pytest.mark.unit
    def test_metadata_version_is_correct(self, valid_shadow_digest, individual_digests) -> None:
        """metadata.versionが正しい"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests,
        )
        assert result["metadata"]["version"] == DIGEST_FORMAT_VERSION

    @pytest.mark.unit
    def test_metadata_last_updated_is_iso_format(
        self, valid_shadow_digest, individual_digests
    ) -> None:
        """metadata.last_updatedがISO形式"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests,
        )
        # ISO形式としてパース可能か確認
        datetime.fromisoformat(result["metadata"]["last_updated"])

    @pytest.mark.unit
    def test_overall_digest_has_complete_structure(
        self, valid_shadow_digest, individual_digests
    ) -> None:
        """overall_digestに必須フィールドが全て含まれ、値が正しい型である"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests,
        )
        overall = result["overall_digest"]

        # 必須フィールドの存在と型チェック
        assert isinstance(overall.get("name"), str)
        assert isinstance(overall.get("timestamp"), str)
        assert isinstance(overall.get("source_files"), list)
        assert isinstance(overall.get("digest_type"), str)
        assert isinstance(overall.get("keywords"), list)
        assert isinstance(overall.get("abstract"), str)
        assert isinstance(overall.get("impression"), str)

    @pytest.mark.unit
    def test_overall_digest_name_matches(self, valid_shadow_digest, individual_digests) -> None:
        """overall_digest.nameが正しい"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001_CustomTitle",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests,
        )
        assert result["overall_digest"]["name"] == "W0001_CustomTitle"

    @pytest.mark.unit
    def test_overall_digest_source_files_from_shadow(
        self, valid_shadow_digest, individual_digests
    ) -> None:
        """overall_digest.source_filesがshadowから取得される"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests,
        )
        assert result["overall_digest"]["source_files"] == [
            "Loop0001_test.txt",
            "Loop0002_test.txt",
        ]

    @pytest.mark.unit
    def test_overall_digest_fields_from_shadow(
        self, valid_shadow_digest, individual_digests
    ) -> None:
        """overall_digestのフィールドがshadowから取得される"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests,
        )
        overall = result["overall_digest"]
        assert overall["digest_type"] == "週次統合"
        assert overall["keywords"] == ["keyword1", "keyword2"]
        assert overall["abstract"] == "テスト用の全体統合分析です。"
        assert overall["impression"] == "テスト用の所感・展望です。"

    @pytest.mark.unit
    def test_individual_digests_preserved(self, valid_shadow_digest, individual_digests) -> None:
        """individual_digestsがそのまま保持される"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests,
        )
        assert result["individual_digests"] == individual_digests
        assert len(result["individual_digests"]) == 2

    @pytest.mark.unit
    def test_empty_individual_digests(self, valid_shadow_digest) -> None:
        """空のindividual_digestsでも動作"""
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=[],
        )
        assert result["individual_digests"] == []

    @pytest.mark.unit
    def test_missing_shadow_fields_use_defaults(self) -> None:
        """shadowに欠落フィールドがある場合、デフォルト値を使用"""
        minimal_shadow = {
            # source_files, digest_type等がない
        }
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=minimal_shadow,
            individual_digests=[],
        )
        overall = result["overall_digest"]
        assert overall["source_files"] == []
        assert overall["digest_type"] == "統合"  # デフォルト
        assert overall["keywords"] == []
        assert overall["abstract"] == ""
        assert overall["impression"] == ""

    @pytest.mark.unit
    def test_timestamp_is_recent(self, valid_shadow_digest, individual_digests) -> None:
        """timestampが現在時刻に近い"""
        before = datetime.now()
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=valid_shadow_digest,
            individual_digests=individual_digests,
        )
        after = datetime.now()

        timestamp = datetime.fromisoformat(result["overall_digest"]["timestamp"])
        assert before <= timestamp <= after

    @pytest.mark.unit
    def test_very_long_abstract_preserved(self, individual_digests) -> None:
        """非常に長いabstractがそのまま保持される（builderは切り捨てない）"""
        long_abstract = "あ" * LARGE_TEXT_LENGTH
        shadow_with_long_abstract = {
            "source_files": ["Loop0001.txt"],
            "digest_type": "テスト",
            "keywords": [],
            "abstract": long_abstract,
            "impression": "",
        }
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=shadow_with_long_abstract,
            individual_digests=individual_digests,
        )
        assert len(result["overall_digest"]["abstract"]) == LARGE_TEXT_LENGTH
        assert result["overall_digest"]["abstract"] == long_abstract

    @pytest.mark.unit
    def test_empty_source_files_list(self, individual_digests) -> None:
        """空のsource_filesリストを正しく処理"""
        shadow_with_empty_sources = {
            "source_files": [],
            "digest_type": "空テスト",
            "keywords": ["empty"],
            "abstract": "No sources",
            "impression": "",
        }
        result = RegularDigestBuilder.build(
            level="weekly",
            new_digest_name="W0001",
            digest_num="W0001",
            shadow_digest=shadow_with_empty_sources,
            individual_digests=individual_digests,
        )
        assert result["overall_digest"]["source_files"] == []
        assert result["overall_digest"]["digest_type"] == "空テスト"
