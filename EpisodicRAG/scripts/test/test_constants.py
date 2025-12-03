#!/usr/bin/env python3
"""
domain/constants.py のユニットテスト
====================================

プレースホルダーファクトリー関数とレベル設定定数のテスト。
"""

import pytest

from domain.constants import (
    LEVEL_CONFIG,
    LEVEL_NAMES,
    PLACEHOLDER_END,
    PLACEHOLDER_LIMITS,
    PLACEHOLDER_MARKER,
    PLACEHOLDER_SIMPLE,
    SOURCE_TYPE_LOOPS,
    create_placeholder_keywords,
    create_placeholder_text,
)

# =============================================================================
# LEVEL_CONFIG 構造テスト
# =============================================================================


class TestLevelConfig:
    """LEVEL_CONFIG定数の構造検証"""

    @pytest.mark.unit
    def test_全8レベルが定義されている(self) -> None:
        """weekly〜centurialまで8レベルが存在する"""
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
        assert list(LEVEL_CONFIG.keys()) == expected_levels

    @pytest.mark.unit
    def test_各レベルに必須キーが存在する(self) -> None:
        """各レベル設定にprefix, digits, dir, source, nextが含まれる"""
        required_keys = {"prefix", "digits", "dir", "source", "next"}
        for level, config in LEVEL_CONFIG.items():
            assert set(config.keys()) >= required_keys, f"Level {level} に必須キーが不足"

    @pytest.mark.unit
    def test_weeklyのソースはloops(self) -> None:
        """weeklyレベルのソースはLoopファイル"""
        assert LEVEL_CONFIG["weekly"]["source"] == SOURCE_TYPE_LOOPS

    @pytest.mark.unit
    def test_centurialは最上位で次がない(self) -> None:
        """centurialは最上位階層なのでnextはNone"""
        assert LEVEL_CONFIG["centurial"]["next"] is None

    @pytest.mark.unit
    def test_カスケードチェーンは非循環(self) -> None:
        """nextによるチェーンは循環しない"""
        for start_level in LEVEL_NAMES:
            visited = set()
            current = start_level
            chain_length = 0
            while current is not None:
                assert current not in visited, f"循環検出: {start_level}から始まり{current}で循環"
                visited.add(current)
                current = LEVEL_CONFIG.get(current, {}).get("next")
                chain_length += 1
                # 無限ループ防止
                assert chain_length <= 10, "チェーンが長すぎる"


class TestLevelNames:
    """LEVEL_NAMES定数のテスト"""

    @pytest.mark.unit
    def test_LEVEL_CONFIGのキーと一致する(self) -> None:
        """LEVEL_NAMESはLEVEL_CONFIGのキーリスト"""
        assert LEVEL_NAMES == list(LEVEL_CONFIG.keys())

    @pytest.mark.unit
    def test_8要素のリスト(self) -> None:
        """8階層分の名前が含まれる"""
        assert len(LEVEL_NAMES) == 8


# =============================================================================
# プレースホルダー定数テスト
# =============================================================================


class TestPlaceholderConstants:
    """プレースホルダー関連定数のテスト"""

    @pytest.mark.unit
    def test_PLACEHOLDER_SIMPLEはマーカーとエンドで構成(self) -> None:
        """PLACEHOLDER_SIMPLEはMARKERとENDの結合"""
        assert PLACEHOLDER_SIMPLE == f"{PLACEHOLDER_MARKER}{PLACEHOLDER_END}"

    @pytest.mark.unit
    def test_PLACEHOLDER_MARKERはHTMLコメント開始(self) -> None:
        """マーカーはHTMLコメント形式で始まる"""
        assert PLACEHOLDER_MARKER.startswith("<!--")

    @pytest.mark.unit
    def test_PLACEHOLDER_ENDはHTMLコメント終了(self) -> None:
        """エンドはHTMLコメント終了形式"""
        assert PLACEHOLDER_END.endswith("-->")


class TestPlaceholderLimits:
    """PLACEHOLDER_LIMITS定数のテスト"""

    @pytest.mark.unit
    def test_必須キーが存在する(self) -> None:
        """abstract_chars, impression_chars, keyword_countが定義されている"""
        required_keys = {"abstract_chars", "impression_chars", "keyword_count"}
        assert set(PLACEHOLDER_LIMITS.keys()) == required_keys

    @pytest.mark.unit
    def test_全ての値が正の整数(self) -> None:
        """制限値は全て正の整数"""
        for key, value in PLACEHOLDER_LIMITS.items():
            assert isinstance(value, int), f"{key}は整数であるべき"
            assert value > 0, f"{key}は正の値であるべき"


# =============================================================================
# create_placeholder_text() テスト
# =============================================================================


class TestCreatePlaceholderText:
    """create_placeholder_text関数のテスト"""

    @pytest.mark.unit
    def test_基本フォーマット(self) -> None:
        """プレースホルダーテキストが正しい形式を持つ"""
        result = create_placeholder_text("全体統合分析", 2400)
        assert "<!-- PLACEHOLDER:" in result
        assert "全体統合分析" in result
        assert "2400" in result
        assert "文字程度" in result
        assert result.endswith(" -->")

    @pytest.mark.unit
    def test_マーカー定数を使用(self) -> None:
        """PLACEHOLDER_MARKERとPLACEHOLDER_END定数を使用"""
        result = create_placeholder_text("テスト", 100)
        assert result.startswith(PLACEHOLDER_MARKER)
        assert result.endswith(PLACEHOLDER_END)

    @pytest.mark.unit
    def test_ドキュメント例と一致(self) -> None:
        """docstringの例と同じ出力"""
        result = create_placeholder_text("全体統合分析", 2400)
        expected = "<!-- PLACEHOLDER: 全体統合分析 (2400文字程度) -->"
        assert result == expected

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "content_type,char_limit",
        [
            ("全体統合分析", 2400),
            ("所感・展望", 800),
            ("", 0),
            ("English content", 1000),
            ("特殊文字!@#$%", 500),
        ],
    )
    def test_様々な入力に対応(self, content_type, char_limit) -> None:
        """様々なコンテンツタイプと文字数制限に対応"""
        result = create_placeholder_text(content_type, char_limit)
        assert content_type in result
        assert str(char_limit) in result
        assert result.startswith(PLACEHOLDER_MARKER)
        assert result.endswith(PLACEHOLDER_END)

    @pytest.mark.unit
    def test_大きな文字数制限(self) -> None:
        """大きな文字数制限も正しく処理"""
        result = create_placeholder_text("長文", 100000)
        assert "100000" in result


# =============================================================================
# create_placeholder_keywords() テスト
# =============================================================================


class TestCreatePlaceholderKeywords:
    """create_placeholder_keywords関数のテスト"""

    @pytest.mark.unit
    def test_指定した数のキーワードを返す(self) -> None:
        """指定したcount分のキーワードリストを返す"""
        result = create_placeholder_keywords(5)
        assert isinstance(result, list)
        assert len(result) == 5

    @pytest.mark.unit
    def test_各キーワードがプレースホルダー形式(self) -> None:
        """各キーワードはプレースホルダー形式"""
        result = create_placeholder_keywords(3)
        for i, kw in enumerate(result, 1):
            assert PLACEHOLDER_MARKER in kw
            assert f"keyword{i}" in kw
            assert kw.endswith(PLACEHOLDER_END)

    @pytest.mark.unit
    def test_ドキュメント例と一致(self) -> None:
        """docstringの例と同じ出力"""
        result = create_placeholder_keywords(5)
        expected_first = "<!-- PLACEHOLDER: keyword1 -->"
        expected_last = "<!-- PLACEHOLDER: keyword5 -->"
        assert result[0] == expected_first
        assert result[4] == expected_last

    @pytest.mark.unit
    def test_0指定で空リスト(self) -> None:
        """count=0の場合は空リストを返す"""
        result = create_placeholder_keywords(0)
        assert result == []

    @pytest.mark.unit
    def test_キーワードは連番(self) -> None:
        """キーワードは1から連番"""
        result = create_placeholder_keywords(5)
        for i in range(1, 6):
            assert any(f"keyword{i}" in kw for kw in result)

    @pytest.mark.unit
    def test_全てのキーワードがユニーク(self) -> None:
        """生成されるキーワードは全てユニーク"""
        result = create_placeholder_keywords(10)
        assert len(result) == len(set(result))

    @pytest.mark.unit
    @pytest.mark.parametrize("count", [1, 3, 5, 10, 20])
    def test_様々な数に対応(self, count) -> None:
        """様々なキーワード数に対応"""
        result = create_placeholder_keywords(count)
        assert len(result) == count


# =============================================================================
# LEVEL_CONFIG 閾値テスト（Single Source of Truth）
# =============================================================================


class TestLevelConfigThresholds:
    """LEVEL_CONFIG内の閾値テスト（Single Source of Truth）"""

    @pytest.mark.unit
    def test_全レベルのしきい値が定義されている(self) -> None:
        """全8レベル分のしきい値がLEVEL_CONFIGに定義されている"""
        for level in LEVEL_NAMES:
            assert "threshold" in LEVEL_CONFIG[level], f"{level}にthresholdキーがない"

    @pytest.mark.unit
    def test_全ての値が正の整数(self) -> None:
        """しきい値は全て正の整数"""
        for level in LEVEL_NAMES:
            threshold = LEVEL_CONFIG[level]["threshold"]
            assert isinstance(threshold, int), f"{level}のしきい値は整数であるべき"
            assert threshold > 0, f"{level}のしきい値は正の値であるべき"
