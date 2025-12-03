#!/usr/bin/env python3
"""
domain/constants.py のProperty-basedテスト
==========================================

hypothesisを使用してプレースホルダーファクトリー関数の不変条件を検証。
"""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from domain.constants import (
    LEVEL_CONFIG,
    LEVEL_NAMES,
    PLACEHOLDER_END,
    PLACEHOLDER_MARKER,
    create_placeholder_keywords,
    create_placeholder_text,
)

# =============================================================================
# Strategies
# =============================================================================

# コンテンツタイプ（空文字を含む任意のテキスト）
content_types = st.text(min_size=0, max_size=100)

# 文字数制限（0以上の整数）
char_limits = st.integers(min_value=0, max_value=100000)

# キーワード数（0〜100の範囲）
keyword_counts = st.integers(min_value=0, max_value=100)


# =============================================================================
# create_placeholder_text Properties
# =============================================================================


class TestCreatePlaceholderTextProperties:
    """create_placeholder_text関数のProperty-basedテスト"""

    @pytest.mark.property
    @given(content_type=content_types, char_limit=char_limits)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_常にマーカーで開始する(self, content_type, char_limit) -> None:
        """プレースホルダーテキストは常にPLACEHOLDER_MARKERで開始"""
        result = create_placeholder_text(content_type, char_limit)
        assert result.startswith(PLACEHOLDER_MARKER)

    @pytest.mark.property
    @given(content_type=content_types, char_limit=char_limits)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_常にエンドで終了する(self, content_type, char_limit) -> None:
        """プレースホルダーテキストは常にPLACEHOLDER_ENDで終了"""
        result = create_placeholder_text(content_type, char_limit)
        assert result.endswith(PLACEHOLDER_END)

    @pytest.mark.property
    @given(content_type=content_types, char_limit=char_limits)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_コンテンツタイプを含む(self, content_type, char_limit) -> None:
        """プレースホルダーテキストは入力されたコンテンツタイプを含む"""
        result = create_placeholder_text(content_type, char_limit)
        assert content_type in result

    @pytest.mark.property
    @given(content_type=content_types, char_limit=char_limits)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_文字数制限を含む(self, content_type, char_limit) -> None:
        """プレースホルダーテキストは入力された文字数制限を含む"""
        result = create_placeholder_text(content_type, char_limit)
        assert str(char_limit) in result

    @pytest.mark.property
    @given(content_type=content_types, char_limit=char_limits)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_文字程度という表記を含む(self, content_type, char_limit) -> None:
        """プレースホルダーテキストは'文字程度'という表記を含む"""
        result = create_placeholder_text(content_type, char_limit)
        assert "文字程度" in result

    @pytest.mark.property
    @given(content_type=content_types, char_limit=char_limits)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_戻り値は文字列(self, content_type, char_limit) -> None:
        """プレースホルダーテキストは常に文字列を返す"""
        result = create_placeholder_text(content_type, char_limit)
        assert isinstance(result, str)


# =============================================================================
# create_placeholder_keywords Properties
# =============================================================================


class TestCreatePlaceholderKeywordsProperties:
    """create_placeholder_keywords関数のProperty-basedテスト"""

    @pytest.mark.property
    @given(count=keyword_counts)
    @settings(max_examples=100)
    def test_リストの長さは指定した数と一致(self, count) -> None:
        """キーワードリストの長さは常に指定した数と一致"""
        result = create_placeholder_keywords(count)
        assert len(result) == count

    @pytest.mark.property
    @given(count=st.integers(min_value=1, max_value=50))
    @settings(max_examples=100)
    def test_各キーワードはマーカーで開始(self, count) -> None:
        """各キーワードはPLACEHOLDER_MARKERで開始"""
        result = create_placeholder_keywords(count)
        for kw in result:
            assert kw.startswith(PLACEHOLDER_MARKER)

    @pytest.mark.property
    @given(count=st.integers(min_value=1, max_value=50))
    @settings(max_examples=100)
    def test_各キーワードはエンドで終了(self, count) -> None:
        """各キーワードはPLACEHOLDER_ENDで終了"""
        result = create_placeholder_keywords(count)
        for kw in result:
            assert kw.endswith(PLACEHOLDER_END)

    @pytest.mark.property
    @given(count=st.integers(min_value=1, max_value=50))
    @settings(max_examples=100)
    def test_全てのキーワードはユニーク(self, count) -> None:
        """生成されるキーワードは全てユニーク"""
        result = create_placeholder_keywords(count)
        assert len(result) == len(set(result))

    @pytest.mark.property
    @given(count=st.integers(min_value=1, max_value=50))
    @settings(max_examples=100)
    def test_各キーワードにkeywordNが含まれる(self, count) -> None:
        """各キーワードはkeywordNの形式を含む（Nは1から連番）"""
        result = create_placeholder_keywords(count)
        for i, kw in enumerate(result, 1):
            assert f"keyword{i}" in kw

    @pytest.mark.property
    @given(count=keyword_counts)
    @settings(max_examples=100)
    def test_戻り値はリスト(self, count) -> None:
        """create_placeholder_keywordsは常にリストを返す"""
        result = create_placeholder_keywords(count)
        assert isinstance(result, list)

    @pytest.mark.property
    @given(count=st.integers(min_value=1, max_value=50))
    @settings(max_examples=100)
    def test_各要素は文字列(self, count) -> None:
        """リストの各要素は文字列"""
        result = create_placeholder_keywords(count)
        for kw in result:
            assert isinstance(kw, str)


# =============================================================================
# LEVEL_CONFIG Structure Properties
# =============================================================================


class TestLevelConfigProperties:
    """LEVEL_CONFIG定数の構造に関するProperty-basedテスト"""

    @pytest.mark.property
    @given(level=st.sampled_from(LEVEL_NAMES))
    @settings(max_examples=50)
    def test_各レベルに必須キーが存在(self, level) -> None:
        """LEVEL_CONFIGの各レベルには必須キーが全て存在"""
        required_keys = {"prefix", "digits", "dir", "source", "next"}
        config = LEVEL_CONFIG[level]
        assert set(config.keys()) >= required_keys

    @pytest.mark.property
    @given(level=st.sampled_from(LEVEL_NAMES))
    @settings(max_examples=50)
    def test_prefixは非空文字列(self, level) -> None:
        """各レベルのprefixは非空の文字列"""
        prefix = LEVEL_CONFIG[level]["prefix"]
        assert isinstance(prefix, str)
        assert len(prefix) > 0

    @pytest.mark.property
    @given(level=st.sampled_from(LEVEL_NAMES))
    @settings(max_examples=50)
    def test_digitsは正の整数(self, level) -> None:
        """各レベルのdigitsは正の整数"""
        digits = LEVEL_CONFIG[level]["digits"]
        assert isinstance(digits, int)
        assert digits > 0

    @pytest.mark.property
    @given(level=st.sampled_from(LEVEL_NAMES))
    @settings(max_examples=50)
    def test_dirは非空文字列(self, level) -> None:
        """各レベルのdirは非空の文字列"""
        dir_name = LEVEL_CONFIG[level]["dir"]
        assert isinstance(dir_name, str)
        assert len(dir_name) > 0

    @pytest.mark.property
    def test_カスケードチェーンは非循環(self) -> None:
        """nextによるカスケードチェーンは循環しない"""
        for start_level in LEVEL_NAMES:
            visited = set()
            current = start_level
            while current is not None:
                assert current not in visited, f"循環検出: {start_level}から始まり{current}で循環"
                visited.add(current)
                current = LEVEL_CONFIG[current]["next"]

    @pytest.mark.property
    def test_全てのnextは有効なレベルかNone(self) -> None:
        """各レベルのnextは有効なレベル名かNone"""
        for level in LEVEL_NAMES:
            next_level = LEVEL_CONFIG[level]["next"]
            assert next_level is None or next_level in LEVEL_NAMES
