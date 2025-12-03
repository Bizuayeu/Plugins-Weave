#!/usr/bin/env python3
"""
domain/level_registry.py のユニットテスト
==========================================

LevelRegistry、LevelBehavior戦略パターンの動作を検証。
"""

import pytest

from domain.level_registry import (
    LevelBehavior,
    LevelMetadata,
    LevelRegistry,
    LoopLevelBehavior,
    StandardLevelBehavior,
    get_level_registry,
    reset_level_registry,
)

# =============================================================================
# テストセットアップ
# =============================================================================


@pytest.fixture(autouse=True)
def reset_registry_between_tests() -> None:
    """各テスト後にRegistryをリセット"""
    yield
    reset_level_registry()


# =============================================================================
# LevelMetadata テスト
# =============================================================================


class TestLevelMetadata:
    """LevelMetadata dataclass のテスト"""

    @pytest.mark.unit
    def test_create_metadata(self) -> None:
        """メタデータの作成"""
        metadata = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )
        assert metadata.name == "weekly"
        assert metadata.prefix == "W"
        assert metadata.digits == 4
        assert metadata.dir == "1_Weekly"
        assert metadata.source == "loops"
        assert metadata.next_level == "monthly"

    @pytest.mark.unit
    def test_metadata_is_immutable(self) -> None:
        """メタデータは不変"""
        metadata = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )
        with pytest.raises(AttributeError):
            metadata.name = "changed"

    @pytest.mark.unit
    def test_top_level_metadata(self) -> None:
        """最上位レベルのメタデータ（next_level=None）"""
        metadata = LevelMetadata(
            name="centurial",
            prefix="C",
            digits=2,
            dir="8_Centurial",
            source="multi_decadal",
            next_level=None,
        )
        assert metadata.next_level is None


# =============================================================================
# StandardLevelBehavior テスト
# =============================================================================


class TestStandardLevelBehavior:
    """StandardLevelBehavior クラスのテスト"""

    @pytest.mark.unit
    def test_format_number_weekly(self) -> None:
        """weeklyレベルのフォーマット"""
        metadata = LevelMetadata("weekly", "W", 4, "1_Weekly", "loops", "monthly")
        behavior = StandardLevelBehavior(metadata)
        assert behavior.format_number(1) == "W0001"
        assert behavior.format_number(42) == "W0042"
        assert behavior.format_number(9999) == "W9999"

    @pytest.mark.unit
    def test_format_number_multi_decadal(self) -> None:
        """multi_decadalレベル（2文字プレフィックス）のフォーマット"""
        metadata = LevelMetadata(
            "multi_decadal", "MD", 2, "7_Multi-decadal", "decadal", "centurial"
        )
        behavior = StandardLevelBehavior(metadata)
        assert behavior.format_number(1) == "MD01"
        assert behavior.format_number(3) == "MD03"

    @pytest.mark.unit
    def test_should_cascade_with_next_level(self) -> None:
        """次レベルがある場合はカスケードする"""
        metadata = LevelMetadata("weekly", "W", 4, "1_Weekly", "loops", "monthly")
        behavior = StandardLevelBehavior(metadata)
        assert behavior.should_cascade() is True

    @pytest.mark.unit
    def test_should_not_cascade_top_level(self) -> None:
        """最上位レベルはカスケードしない"""
        metadata = LevelMetadata("centurial", "C", 2, "8_Centurial", "multi_decadal", None)
        behavior = StandardLevelBehavior(metadata)
        assert behavior.should_cascade() is False


# =============================================================================
# LoopLevelBehavior テスト
# =============================================================================


class TestLoopLevelBehavior:
    """LoopLevelBehavior クラスのテスト"""

    @pytest.mark.unit
    def test_format_number(self) -> None:
        """Loopファイルのフォーマット"""
        behavior = LoopLevelBehavior()
        assert behavior.format_number(1) == "L00001"
        assert behavior.format_number(186) == "L00186"
        assert behavior.format_number(9999) == "L09999"

    @pytest.mark.unit
    def test_should_not_cascade(self) -> None:
        """Loopはカスケードしない"""
        behavior = LoopLevelBehavior()
        assert behavior.should_cascade() is False


# =============================================================================
# LevelRegistry テスト
# =============================================================================


class TestLevelRegistry:
    """LevelRegistry クラスのテスト"""

    @pytest.mark.unit
    def test_all_levels_registered(self) -> None:
        """全レベルが登録されている"""
        registry = get_level_registry()
        expected = [
            "weekly",
            "monthly",
            "quarterly",
            "annual",
            "triennial",
            "decadal",
            "multi_decadal",
            "centurial",
        ]
        for level in expected:
            metadata = registry.get_metadata(level)
            assert metadata is not None
            assert metadata.name == level

    @pytest.mark.unit
    def test_loop_level_registered(self) -> None:
        """Loopレベルが登録されている"""
        registry = get_level_registry()
        metadata = registry.get_metadata("loop")
        assert metadata.prefix == "L"
        assert metadata.digits == 5

    @pytest.mark.unit
    def test_get_level_names_excludes_loop(self) -> None:
        """get_level_names()は'loop'を除外"""
        registry = get_level_registry()
        level_names = registry.get_level_names()
        assert "loop" not in level_names
        assert "weekly" in level_names
        assert "centurial" in level_names
        assert len(level_names) == 8

    @pytest.mark.unit
    def test_get_all_level_names_includes_loop(self) -> None:
        """get_all_level_names()は'loop'を含む"""
        registry = get_level_registry()
        all_names = registry.get_all_level_names()
        assert "loop" in all_names
        assert len(all_names) == 9

    @pytest.mark.unit
    def test_should_cascade_weekly(self) -> None:
        """weeklyはカスケードする"""
        registry = get_level_registry()
        assert registry.should_cascade("weekly") is True

    @pytest.mark.unit
    def test_should_not_cascade_centurial(self) -> None:
        """centurialはカスケードしない"""
        registry = get_level_registry()
        assert registry.should_cascade("centurial") is False

    @pytest.mark.unit
    def test_should_not_cascade_loop(self) -> None:
        """loopはカスケードしない"""
        registry = get_level_registry()
        assert registry.should_cascade("loop") is False

    @pytest.mark.unit
    def test_get_all_prefixes_sorted_by_length(self) -> None:
        """プレフィックスは長さ降順でソート"""
        registry = get_level_registry()
        prefixes = registry.get_all_prefixes()
        # 最初の要素は最長（MD）
        assert prefixes[0] == "MD"
        # 長いものが先
        for i in range(len(prefixes) - 1):
            assert len(prefixes[i]) >= len(prefixes[i + 1])

    @pytest.mark.unit
    def test_get_level_by_prefix(self) -> None:
        """プレフィックスからレベルを逆引き"""
        registry = get_level_registry()
        assert registry.get_level_by_prefix("W") == "weekly"
        assert registry.get_level_by_prefix("M") == "monthly"
        assert registry.get_level_by_prefix("MD") == "multi_decadal"
        assert registry.get_level_by_prefix("L") == "loop"

    @pytest.mark.unit
    def test_get_level_by_prefix_unknown(self) -> None:
        """不明なプレフィックスはNone"""
        registry = get_level_registry()
        assert registry.get_level_by_prefix("X") is None
        assert registry.get_level_by_prefix("ZZ") is None

    @pytest.mark.unit
    def test_build_prefix_pattern(self) -> None:
        """正規表現パターンの生成"""
        registry = get_level_registry()
        pattern = registry.build_prefix_pattern()
        # 主要なプレフィックスが含まれている
        assert "L" in pattern
        assert "MD" in pattern
        assert "W" in pattern
        assert "C" in pattern
        # パイプで区切られている
        assert "|" in pattern

    @pytest.mark.unit
    def test_get_behavior_unknown_level(self) -> None:
        """不明なレベルでConfigError"""
        from domain.exceptions import ConfigError

        registry = get_level_registry()
        with pytest.raises(ConfigError, match="Unknown level"):
            registry.get_behavior("unknown")

    @pytest.mark.unit
    def test_get_metadata_unknown_level(self) -> None:
        """不明なレベルでConfigError"""
        from domain.exceptions import ConfigError

        registry = get_level_registry()
        with pytest.raises(ConfigError, match="Unknown level"):
            registry.get_metadata("unknown")


# =============================================================================
# Singleton テスト
# =============================================================================


class TestSingleton:
    """Singletonパターンのテスト"""

    @pytest.mark.unit
    def test_singleton_returns_same_instance(self) -> None:
        """同じインスタンスを返す"""
        registry1 = get_level_registry()
        registry2 = get_level_registry()
        assert registry1 is registry2

    @pytest.mark.unit
    def test_reset_clears_singleton(self) -> None:
        """リセット後は新しいインスタンス"""
        registry1 = get_level_registry()
        reset_level_registry()
        registry2 = get_level_registry()
        assert registry1 is not registry2


# =============================================================================
# 統合テスト: format_digest_number経由
# =============================================================================


class TestFormatDigestNumberIntegration:
    """format_digest_numberとの統合テスト"""

    @pytest.mark.integration
    def test_format_via_registry(self) -> None:
        """Registry経由でフォーマット"""
        from domain.file_naming import format_digest_number

        assert format_digest_number("loop", 186) == "L00186"
        assert format_digest_number("weekly", 1) == "W0001"
        assert format_digest_number("multi_decadal", 3) == "MD03"

    @pytest.mark.integration
    def test_extract_and_format_roundtrip(self) -> None:
        """抽出→フォーマットのラウンドトリップ"""
        from domain.file_naming import extract_file_number, format_digest_number

        registry = get_level_registry()

        test_cases = [
            ("L00186_test.txt", "loop", 186),
            ("W0001_weekly.txt", "weekly", 1),
            ("MD03_multi.txt", "multi_decadal", 3),
        ]

        for filename, expected_level, expected_num in test_cases:
            result = extract_file_number(filename)
            assert result is not None
            prefix, num = result
            assert num == expected_num

            # プレフィックスからレベルを逆引き
            level = registry.get_level_by_prefix(prefix)
            assert level == expected_level

            # 再フォーマット
            formatted = format_digest_number(level, num)
            assert prefix in formatted
            assert str(num) in formatted.replace(prefix, "")
