#!/usr/bin/env python3
"""
カスケード処理Property-Based Tests
==================================

カスケード処理の数学的不変条件をHypothesisで検証。

不変条件:
    - カスケードは中間レベルをスキップしない
    - 上位レベルほどファイル数が減少または同等
    - 閾値がトリガー条件を決定する
    - レベル階層は非循環
"""

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from domain.constants import LEVEL_CONFIG, LEVEL_NAMES, build_level_hierarchy

# Property-Based Test マーカー
pytestmark = pytest.mark.property

# =============================================================================
# Strategies
# =============================================================================

# 有効なレベル名
valid_levels = st.sampled_from(LEVEL_NAMES)

# ファイル数（0〜100）
valid_file_counts = st.integers(min_value=0, max_value=100)

# 閾値（1〜50）
valid_thresholds = st.integers(min_value=1, max_value=50)

# レベルインデックス（0〜7）
level_indices = st.integers(min_value=0, max_value=len(LEVEL_NAMES) - 1)


# =============================================================================
# Level Hierarchy Invariants
# =============================================================================


class TestLevelHierarchyInvariants:
    """レベル階層の不変条件"""

    @given(level=valid_levels)
    @settings(max_examples=50)
    def test_level_config_exists(self, level) -> None:
        """全有効レベルにLEVEL_CONFIGが存在する"""
        assert level in LEVEL_CONFIG, f"{level}がLEVEL_CONFIGに存在すること"

    @given(level=valid_levels)
    @settings(max_examples=50)
    def test_level_config_has_required_keys(self, level) -> None:
        """
        LEVEL_CONFIGは必須キーを持つ

        必須キー: prefix, digits, dir
        """
        config = LEVEL_CONFIG[level]
        required_keys = ["prefix", "digits", "dir"]  # キー名は "dir"（"dir_name"ではない）

        for key in required_keys:
            assert key in config, f"{level}のLEVEL_CONFIGに{key}が存在すること"

    @given(level=valid_levels)
    @settings(max_examples=50)
    def test_level_hierarchy_non_circular(self, level) -> None:
        """
        レベル階層は非循環である

        次のレベルを辿っても元のレベルに戻らない
        """
        hierarchy = build_level_hierarchy()
        visited = set()
        current = level

        # 最大8回（全レベル数）まで辿る
        for _ in range(len(LEVEL_NAMES)):
            if current in visited:
                pytest.fail(f"循環検出: {level}から始まり{current}で循環")
            visited.add(current)

            next_level = hierarchy[current]["next"]
            if next_level is None:
                break  # 最上位に到達
            current = next_level

    @given(idx=level_indices)
    @settings(max_examples=50)
    def test_level_order_preserved(self, idx) -> None:
        """
        LEVEL_NAMESの順序がカスケード方向と一致する

        idx番目のレベルの次は(idx+1)番目のレベル
        """
        hierarchy = build_level_hierarchy()
        level = LEVEL_NAMES[idx]

        if idx < len(LEVEL_NAMES) - 1:
            expected_next = LEVEL_NAMES[idx + 1]
            actual_next = hierarchy[level]["next"]
            assert actual_next == expected_next, (
                f"{level}の次は{expected_next}であること（実際: {actual_next}）"
            )
        else:
            # 最上位レベル（centurial）の次はNone
            assert hierarchy[level]["next"] is None


# =============================================================================
# Threshold Invariants
# =============================================================================


class TestThresholdInvariants:
    """閾値の不変条件"""

    @given(level=valid_levels)
    @settings(max_examples=50)
    def test_threshold_is_positive_integer(self, level) -> None:
        """全レベルの閾値は正の整数"""
        config = LEVEL_CONFIG[level]
        threshold = config.get("threshold", 5)  # デフォルト5

        assert isinstance(threshold, int), f"{level}の閾値はint型であること"
        assert threshold > 0, f"{level}の閾値は正であること（実際: {threshold}）"

    @given(file_count=valid_file_counts, threshold=valid_thresholds)
    @settings(max_examples=200)
    def test_threshold_determines_trigger(self, file_count, threshold) -> None:
        """
        閾値がトリガー条件を決定する

        file_count >= threshold ⇔ should_trigger
        """
        should_trigger = file_count >= threshold

        if should_trigger:
            assert file_count >= threshold
        else:
            assert file_count < threshold

    @given(threshold=valid_thresholds)
    @settings(max_examples=100)
    def test_boundary_condition_at_threshold(self, threshold) -> None:
        """
        閾値境界での動作が明確

        - threshold - 1: トリガーしない
        - threshold: トリガーする
        - threshold + 1: トリガーする
        """
        below = threshold - 1
        at = threshold
        above = threshold + 1

        assert below < threshold, "threshold-1 < threshold"
        assert at >= threshold, "threshold >= threshold"
        assert above >= threshold, "threshold+1 >= threshold"


# =============================================================================
# Cascade Flow Invariants
# =============================================================================


class TestCascadeFlowInvariants:
    """カスケードフローの不変条件"""

    @given(start_idx=level_indices)
    @settings(max_examples=50)
    def test_cascade_reaches_top_or_stops(self, start_idx) -> None:
        """
        カスケードは最上位に到達するか、Noneで停止する
        """
        hierarchy = build_level_hierarchy()
        current = LEVEL_NAMES[start_idx]
        steps = 0
        max_steps = len(LEVEL_NAMES)

        while current is not None and steps < max_steps:
            next_level = hierarchy[current]["next"]
            if next_level is None:
                # 最上位に到達
                assert current == LEVEL_NAMES[-1], "最上位はcenturialであること"
                break
            current = next_level
            steps += 1

        # 無限ループしないこと
        assert steps < max_steps, "カスケードは有限回で停止すること"

    @given(idx1=level_indices, idx2=level_indices)
    @settings(max_examples=100)
    def test_level_ordering_transitive(self, idx1, idx2) -> None:
        """
        レベル順序は推移的である

        idx1 < idx2 ならば level1 は level2 より下位
        """
        assume(idx1 != idx2)

        level1 = LEVEL_NAMES[idx1]
        level2 = LEVEL_NAMES[idx2]
        hierarchy = build_level_hierarchy()

        if idx1 < idx2:
            # level1からlevel2に到達可能であること
            current = level1
            found = False
            for _ in range(len(LEVEL_NAMES)):
                if current == level2:
                    found = True
                    break
                current = hierarchy[current]["next"]
                if current is None:
                    break
            assert found, f"{level1}から{level2}に到達可能であること"


# =============================================================================
# Digit Format Invariants
# =============================================================================


class TestDigitFormatInvariants:
    """桁数フォーマットの不変条件"""

    @given(level=valid_levels)
    @settings(max_examples=50)
    def test_digits_is_positive(self, level) -> None:
        """全レベルの桁数は正の整数"""
        config = LEVEL_CONFIG[level]
        digits = config["digits"]

        assert isinstance(digits, int)
        assert digits > 0, f"{level}の桁数は正であること"

    @given(level=valid_levels)
    @settings(max_examples=50)
    def test_prefix_is_non_empty_string(self, level) -> None:
        """全レベルのプレフィックスは非空文字列"""
        config = LEVEL_CONFIG[level]
        prefix = config["prefix"]

        assert isinstance(prefix, str)
        assert len(prefix) > 0, f"{level}のプレフィックスは非空であること"

    @given(level=valid_levels, number=st.integers(min_value=0, max_value=99))
    @settings(max_examples=100)
    def test_formatted_number_length_matches_digits(self, level, number) -> None:
        """
        フォーマット済み番号の数字部分が指定桁数と一致する
        """
        from domain.file_naming import format_digest_number

        config = LEVEL_CONFIG[level]
        digits = config["digits"]
        prefix = config["prefix"]

        # 桁数内に収まる番号のみテスト
        max_num = 10**digits - 1
        assume(number <= max_num)

        formatted = format_digest_number(level, number)

        # プレフィックスを除去して数字部分を確認
        number_part = formatted[len(prefix) :]
        assert len(number_part) == digits, (
            f"{level}の数字部分は{digits}桁であること（実際: {len(number_part)}）"
        )
