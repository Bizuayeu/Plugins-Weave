#!/usr/bin/env python3
"""
Types パッケージ後方互換性テスト
================================

domain.types パッケージの分割後も、すべてのインポートが動作することを確認。
"""

import pytest


class TestTypesImportBackwardCompatibility:
    """domain.types からの全インポートが動作することを確認"""

    def test_import_metadata_types(self) -> None:
        """メタデータ型がインポート可能"""
        from domain.types import BaseMetadata, DigestMetadata, DigestMetadataComplete

        # 型が存在することを確認
        assert BaseMetadata is not None
        assert DigestMetadata is not None
        assert DigestMetadataComplete is not None

    def test_import_level_types(self) -> None:
        """レベル型がインポート可能"""
        from domain.types import LevelConfigData, LevelHierarchyEntry

        assert LevelConfigData is not None
        assert LevelHierarchyEntry is not None

    def test_import_text_types(self) -> None:
        """テキスト型がインポート可能"""
        from domain.types import LongShortText

        assert LongShortText is not None

    def test_import_digest_types(self) -> None:
        """ダイジェスト型がインポート可能"""
        from domain.types import (
            GrandDigestData,
            GrandDigestLevelData,
            IndividualDigestData,
            OverallDigestData,
            RegularDigestData,
            ShadowDigestData,
            ShadowLevelData,
        )

        assert OverallDigestData is not None
        assert IndividualDigestData is not None
        assert ShadowLevelData is not None
        assert ShadowDigestData is not None
        assert GrandDigestLevelData is not None
        assert GrandDigestData is not None
        assert RegularDigestData is not None

    def test_import_config_types(self) -> None:
        """設定型がインポート可能"""
        from domain.types import (
            ConfigData,
            DigestTimeData,
            DigestTimesData,
            LevelsConfigData,
            PathsConfigData,
        )

        assert PathsConfigData is not None
        assert LevelsConfigData is not None
        assert ConfigData is not None
        assert DigestTimeData is not None
        assert DigestTimesData is not None

    def test_import_entry_types(self) -> None:
        """エントリ型がインポート可能"""
        from domain.types import ProvisionalDigestEntry, ProvisionalDigestFile

        assert ProvisionalDigestEntry is not None
        assert ProvisionalDigestFile is not None

    def test_import_utils(self) -> None:
        """ユーティリティ関数がインポート可能"""
        from domain.types import as_dict

        assert callable(as_dict)

    def test_import_guards(self) -> None:
        """TypeGuard関数がインポート可能"""
        from domain.types import (
            is_config_data,
            is_level_config_data,
            is_long_short_text,
            is_shadow_digest_data,
        )

        assert callable(is_config_data)
        assert callable(is_level_config_data)
        assert callable(is_shadow_digest_data)
        assert callable(is_long_short_text)


class TestTypesSubmoduleImports:
    """サブモジュールからの直接インポートが動作することを確認"""

    def test_import_from_metadata_submodule(self) -> None:
        """domain.types.metadata からインポート可能"""
        from domain.types.metadata import BaseMetadata, DigestMetadata

        assert BaseMetadata is not None
        assert DigestMetadata is not None

    def test_import_from_digest_submodule(self) -> None:
        """domain.types.digest からインポート可能"""
        from domain.types.digest import OverallDigestData, ShadowDigestData

        assert OverallDigestData is not None
        assert ShadowDigestData is not None

    def test_import_from_config_submodule(self) -> None:
        """domain.types.config からインポート可能"""
        from domain.types.config import ConfigData, PathsConfigData

        assert ConfigData is not None
        assert PathsConfigData is not None

    def test_import_from_guards_submodule(self) -> None:
        """domain.types.guards からインポート可能"""
        from domain.types.guards import is_config_data, is_long_short_text

        assert callable(is_config_data)
        assert callable(is_long_short_text)


class TestTypesUsability:
    """型が実際に使用可能であることを確認"""

    def test_create_overall_digest(self) -> None:
        """OverallDigestData型を使用してデータ作成可能"""
        from domain.types import OverallDigestData

        data: OverallDigestData = {
            "name": "test",
            "timestamp": "2024-01-01T00:00:00",
            "source_files": ["file1.txt"],
            "digest_type": "loop",
            "keywords": ["test"],
            "abstract": "Test abstract",
            "impression": "Test impression",
        }

        assert data["name"] == "test"
        assert len(data["source_files"]) == 1

    def test_as_dict_function(self) -> None:
        """as_dict関数が正しく動作"""
        from domain.types import ConfigData, as_dict

        config: ConfigData = {"base_dir": ".", "paths": {}, "levels": {}}
        result = as_dict(config)

        assert isinstance(result, dict)
        assert result.get("base_dir") == "."

    def test_is_config_data_guard(self) -> None:
        """is_config_data TypeGuardが正しく動作"""
        from domain.types import is_config_data

        valid_config = {"base_dir": ".", "paths": {}, "levels": {}}
        invalid_config = {"paths": "not a dict"}

        assert is_config_data(valid_config) is True
        assert is_config_data(invalid_config) is False
        assert is_config_data("string") is False
