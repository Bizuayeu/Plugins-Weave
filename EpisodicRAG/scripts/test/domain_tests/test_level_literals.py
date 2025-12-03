#!/usr/bin/env python3
"""
Literal Types テスト
====================

domain.types.level_literals モジュールのLiteral型が
正しく定義・エクスポートされていることを確認。
"""

from typing import get_args

import pytest


class TestLiteralTypesImport:
    """Literal型がインポート可能であることを確認"""

    def test_import_level_name(self) -> None:
        """LevelName型がインポート可能"""
        from domain.types import LevelName

        assert LevelName is not None

    def test_import_all_level_name(self) -> None:
        """AllLevelName型がインポート可能"""
        from domain.types import AllLevelName

        assert AllLevelName is not None

    def test_import_level_config_key(self) -> None:
        """LevelConfigKey型がインポート可能"""
        from domain.types import LevelConfigKey

        assert LevelConfigKey is not None

    def test_import_source_type(self) -> None:
        """SourceType型がインポート可能"""
        from domain.types import SourceType

        assert SourceType is not None

    def test_import_provisional_suffix(self) -> None:
        """ProvisionalSuffix型がインポート可能"""
        from domain.types import ProvisionalSuffix

        assert ProvisionalSuffix is not None

    def test_import_path_config_key(self) -> None:
        """PathConfigKey型がインポート可能"""
        from domain.types import PathConfigKey

        assert PathConfigKey is not None

    def test_import_threshold_key(self) -> None:
        """ThresholdKey型がインポート可能"""
        from domain.types import ThresholdKey

        assert ThresholdKey is not None

    def test_import_log_prefix(self) -> None:
        """LogPrefix型がインポート可能"""
        from domain.types import LogPrefix

        assert LogPrefix is not None


class TestLiteralTypesFromSubmodule:
    """サブモジュールからの直接インポートが可能であることを確認"""

    def test_import_from_level_literals_module(self) -> None:
        """domain.types.level_literals からインポート可能"""
        from domain.types.level_literals import (
            AllLevelName,
            LevelConfigKey,
            LevelName,
            LogPrefix,
            PathConfigKey,
            ProvisionalSuffix,
            SourceType,
            ThresholdKey,
        )

        assert LevelName is not None
        assert AllLevelName is not None
        assert LevelConfigKey is not None
        assert SourceType is not None
        assert ProvisionalSuffix is not None
        assert PathConfigKey is not None
        assert ThresholdKey is not None
        assert LogPrefix is not None


class TestLevelNameLiteral:
    """LevelName Literal型の値が正しいことを確認"""

    def test_level_name_contains_weekly(self) -> None:
        """LevelNameに'weekly'が含まれる"""
        from domain.types import LevelName

        args = get_args(LevelName)
        assert "weekly" in args

    def test_level_name_contains_all_8_levels(self) -> None:
        """LevelNameに8階層すべてが含まれる"""
        from domain.types import LevelName

        args = get_args(LevelName)
        expected = {
            "weekly",
            "monthly",
            "quarterly",
            "annual",
            "triennial",
            "decadal",
            "multi_decadal",
            "centurial",
        }
        assert set(args) == expected

    def test_level_name_does_not_contain_loop(self) -> None:
        """LevelNameに'loop'は含まれない"""
        from domain.types import LevelName

        args = get_args(LevelName)
        assert "loop" not in args


class TestAllLevelNameLiteral:
    """AllLevelName Literal型の値が正しいことを確認"""

    def test_all_level_name_contains_loop(self) -> None:
        """AllLevelNameに'loop'が含まれる"""
        from domain.types import AllLevelName

        args = get_args(AllLevelName)
        assert "loop" in args

    def test_all_level_name_contains_9_values(self) -> None:
        """AllLevelNameに9個の値が含まれる（loop + 8階層）"""
        from domain.types import AllLevelName

        args = get_args(AllLevelName)
        assert len(args) == 9


class TestLevelConfigKeyLiteral:
    """LevelConfigKey Literal型の値が正しいことを確認"""

    def test_level_config_key_values(self) -> None:
        """LevelConfigKeyに必要なキーが含まれる"""
        from domain.types import LevelConfigKey

        args = get_args(LevelConfigKey)
        expected = {"prefix", "digits", "dir", "source", "next", "threshold"}
        assert set(args) == expected


class TestSourceTypeLiteral:
    """SourceType Literal型の値が正しいことを確認"""

    def test_source_type_contains_loops(self) -> None:
        """SourceTypeに'loops'が含まれる"""
        from domain.types import SourceType

        args = get_args(SourceType)
        assert "loops" in args

    def test_source_type_contains_weekly(self) -> None:
        """SourceTypeに'weekly'が含まれる"""
        from domain.types import SourceType

        args = get_args(SourceType)
        assert "weekly" in args


class TestProvisionalSuffixLiteral:
    """ProvisionalSuffix Literal型の値が正しいことを確認"""

    def test_provisional_suffix_values(self) -> None:
        """ProvisionalSuffixに正しいサフィックスが含まれる"""
        from domain.types import ProvisionalSuffix

        args = get_args(ProvisionalSuffix)
        expected = {"_Individual.txt", "_Overall.txt"}
        assert set(args) == expected


class TestPathConfigKeyLiteral:
    """PathConfigKey Literal型の値が正しいことを確認"""

    def test_path_config_key_values(self) -> None:
        """PathConfigKeyに必要なキーが含まれる"""
        from domain.types import PathConfigKey

        args = get_args(PathConfigKey)
        expected = {"loops_path", "digests_path", "essences_path", "base_dir", "identity_file"}
        assert set(args) == expected


class TestThresholdKeyLiteral:
    """ThresholdKey Literal型の値が正しいことを確認"""

    def test_threshold_key_contains_8_thresholds(self) -> None:
        """ThresholdKeyに8階層分の閾値キーが含まれる"""
        from domain.types import ThresholdKey

        args = get_args(ThresholdKey)
        assert len(args) == 8
        assert "weekly_threshold" in args
        assert "centurial_threshold" in args


class TestLogPrefixLiteral:
    """LogPrefix Literal型の値が正しいことを確認"""

    def test_log_prefix_values(self) -> None:
        """LogPrefixに正しいプレフィックスが含まれる"""
        from domain.types import LogPrefix

        args = get_args(LogPrefix)
        expected = {"[STATE]", "[FILE]", "[VALIDATE]", "[DECISION]"}
        assert set(args) == expected


class TestLiteralTypesConsistencyWithConstants:
    """Literal型がconstants.pyの定数と一致することを確認"""

    def test_level_name_matches_level_names_constant(self) -> None:
        """LevelNameがLEVEL_NAMES定数と一致"""
        from domain.constants import LEVEL_NAMES
        from domain.types import LevelName

        literal_values = set(get_args(LevelName))
        constant_values = set(LEVEL_NAMES)
        assert literal_values == constant_values

    def test_level_config_key_matches_level_config(self) -> None:
        """LevelConfigKeyがLEVEL_CONFIGのキーと一致"""
        from domain.constants import LEVEL_CONFIG
        from domain.types import LevelConfigKey

        literal_values = set(get_args(LevelConfigKey))
        # LEVEL_CONFIGの最初のレベルのキーを取得
        first_level_keys = set(LEVEL_CONFIG["weekly"].keys())
        assert literal_values == first_level_keys
