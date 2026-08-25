#!/usr/bin/env python3
"""
domain/constants.py のユニットテスト - loop レベル追加
======================================================

loop レベルと DIGEST_LEVEL_NAMES 定数のテスト。
"""

import pytest

from domain.constants import LEVEL_CONFIG, LEVEL_NAMES


class TestLoopLevelInLevelConfig:
    """loop レベルが LEVEL_CONFIG に存在することを検証"""

    @pytest.mark.unit
    def test_loop_level_exists(self) -> None:
        """loop レベルが LEVEL_CONFIG に存在する"""
        assert "loop" in LEVEL_CONFIG

    @pytest.mark.unit
    def test_loop_level_is_first(self) -> None:
        """loop は LEVEL_NAMES の先頭に位置する"""
        assert LEVEL_NAMES[0] == "loop"

    @pytest.mark.unit
    def test_loop_level_config_has_prefix(self) -> None:
        """loop レベルの prefix は 'L'"""
        assert LEVEL_CONFIG["loop"]["prefix"] == "L"

    @pytest.mark.unit
    def test_loop_level_config_has_digits(self) -> None:
        """loop レベルの digits は 5"""
        assert LEVEL_CONFIG["loop"]["digits"] == 5

    @pytest.mark.unit
    def test_loop_level_config_has_source_raw(self) -> None:
        """loop レベルの source は 'raw'（階層の起点）"""
        assert LEVEL_CONFIG["loop"]["source"] == "raw"

    @pytest.mark.unit
    def test_loop_level_config_has_next_weekly(self) -> None:
        """loop レベルの next は 'weekly'"""
        assert LEVEL_CONFIG["loop"]["next"] == "weekly"

    @pytest.mark.unit
    def test_loop_level_config_has_threshold_none(self) -> None:
        """loop レベルの threshold は None（手動トリガー）"""
        assert LEVEL_CONFIG["loop"]["threshold"] is None


class TestLevelNamesCount:
    """LEVEL_NAMES の要素数テスト"""

    @pytest.mark.unit
    def test_level_names_count_is_nine(self) -> None:
        """LEVEL_NAMES は9レベル（loop + 8つのダイジェストレベル）"""
        assert len(LEVEL_NAMES) == 9


class TestDigestLevelNames:
    """DIGEST_LEVEL_NAMES 定数のテスト"""

    @pytest.mark.unit
    def test_digest_level_names_exists(self) -> None:
        """DIGEST_LEVEL_NAMES がインポートできる"""
        from domain.constants import DIGEST_LEVEL_NAMES

        assert DIGEST_LEVEL_NAMES is not None

    @pytest.mark.unit
    def test_digest_level_names_count_is_eight(self) -> None:
        """DIGEST_LEVEL_NAMES は8レベル（loopを除く）"""
        from domain.constants import DIGEST_LEVEL_NAMES

        assert len(DIGEST_LEVEL_NAMES) == 8

    @pytest.mark.unit
    def test_digest_level_names_excludes_loop(self) -> None:
        """DIGEST_LEVEL_NAMES には loop が含まれない"""
        from domain.constants import DIGEST_LEVEL_NAMES

        assert "loop" not in DIGEST_LEVEL_NAMES

    @pytest.mark.unit
    def test_digest_level_names_starts_with_weekly(self) -> None:
        """DIGEST_LEVEL_NAMES は weekly から始まる"""
        from domain.constants import DIGEST_LEVEL_NAMES

        assert DIGEST_LEVEL_NAMES[0] == "weekly"

    @pytest.mark.unit
    def test_digest_level_names_ends_with_centurial(self) -> None:
        """DIGEST_LEVEL_NAMES は centurial で終わる"""
        from domain.constants import DIGEST_LEVEL_NAMES

        assert DIGEST_LEVEL_NAMES[-1] == "centurial"

    @pytest.mark.unit
    def test_digest_level_names_contains_all_digest_levels(self) -> None:
        """DIGEST_LEVEL_NAMES は全ての8ダイジェストレベルを含む"""
        from domain.constants import DIGEST_LEVEL_NAMES

        expected_levels = [
            "weekly",
            "monthly",
            "quarterly",
            "annual",
            "triennial",
            "decadal",
            "multi_decadal",
            "centurial",
        ]
        assert expected_levels == DIGEST_LEVEL_NAMES
