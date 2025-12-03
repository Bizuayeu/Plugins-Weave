#!/usr/bin/env python3
"""
設定Property-Based Tests
========================

設定（DigestConfig）の不変条件をHypothesisで検証。

不変条件:
    - 設定の読み込み→保存→読み込みでデータが保持される
    - 全レベルの閾値は正の整数
    - パス解決は絶対パスを返す
    - 設定構造は型安全
"""

import json
import tempfile
from pathlib import Path

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from domain.constants import LEVEL_CONFIG, LEVEL_NAMES

# Property-Based Test マーカー
pytestmark = pytest.mark.property

# =============================================================================
# Strategies
# =============================================================================

# 有効なレベル名
valid_levels = st.sampled_from(LEVEL_NAMES)

# 有効なパス文字列（英数字とアンダースコア、ハイフン、スラッシュ）
valid_path_chars = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N"),
        whitelist_characters="_-/",
    ),
    min_size=1,
    max_size=50,
)

# 有効な閾値
valid_thresholds = st.integers(min_value=1, max_value=100)

# 有効な設定辞書
valid_config_dicts = st.fixed_dictionaries(
    {
        "base_dir": st.just("."),
        "paths": st.fixed_dictionaries(
            {
                "loops": st.just("data/Loops"),
                "digests": st.just("data/Digests"),
                "essences": st.just("data/Essences"),
            }
        ),
    }
)


# =============================================================================
# Config Loading Invariants
# =============================================================================


class TestConfigLoadingInvariants:
    """設定読み込みの不変条件"""

    @given(level=valid_levels)
    @settings(max_examples=50)
    def test_level_config_consistency(self, level) -> None:

        """
        LEVEL_CONFIGは一貫した構造を持つ
        """
        config = LEVEL_CONFIG[level]

        # 必須キーの存在
        assert "prefix" in config
        assert "digits" in config
        assert "dir" in config  # キー名は "dir"（"dir_name"ではない）

        # 型の一貫性
        assert isinstance(config["prefix"], str)
        assert isinstance(config["digits"], int)
        assert isinstance(config["dir"], str)

    @given(level=valid_levels)
    @settings(max_examples=50)
    def test_dir_format(self, level) -> None:

        """
        dirは "N_LevelName" 形式である
        """
        config = LEVEL_CONFIG[level]
        dir_value = config["dir"]  # キー名は "dir"

        # 数字_名前 の形式
        parts = dir_value.split("_", 1)
        assert len(parts) == 2, f"dirは'N_Name'形式であること: {dir_value}"
        assert parts[0].isdigit(), f"dirの先頭は数字であること: {dir_value}"


# =============================================================================
# Threshold Invariants
# =============================================================================


class TestConfigThresholdInvariants:
    """設定閾値の不変条件"""

    @given(level=valid_levels)
    @settings(max_examples=50)
    def test_threshold_from_level_config(self, level) -> None:

        """
        LEVEL_CONFIGから取得した閾値は妥当な値である
        """
        config = LEVEL_CONFIG[level]
        threshold = config.get("threshold", 5)  # デフォルト5

        assert threshold > 0, "閾値は正であること"
        assert threshold <= 100, "閾値は妥当な範囲内であること"

    @given(level=valid_levels)
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
    )
    def test_threshold_is_positive_integer(self, level, temp_plugin_env) -> None:

        """
        DigestConfigの閾値は正の整数である

        Note: LEVEL_CONFIGにthresholdを統合（Single Source of Truth）。
        このテストはLEVEL_CONFIGの閾値が正しく適用されていることを検証。
        """
        from application.config import DigestConfig
        from domain.constants import LEVEL_CONFIG

        digest_config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        attr_name = f"{level.replace('-', '_')}_threshold"
        # config.thresholdプロパティ経由でアクセス
        digest_config_threshold = getattr(digest_config.threshold, attr_name, 5)

        # 閾値は正の整数であること
        assert isinstance(digest_config_threshold, int), f"{level}の閾値はint型であること"
        assert digest_config_threshold > 0, f"{level}の閾値は正であること"

        # LEVEL_CONFIGと一致すること（config.jsonでオーバーライドされていない場合）
        expected = LEVEL_CONFIG[level].get("threshold", 5)
        assert digest_config_threshold == expected, (
            f"{level}の閾値がLEVEL_CONFIGと一致すること（期待: {expected}, 実際: {digest_config_threshold}）"
        )


# =============================================================================
# Path Resolution Invariants
# =============================================================================


class TestPathResolutionInvariants:
    """パス解決の不変条件"""

    @given(level=valid_levels)
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
    )
    def test_level_dir_returns_absolute_path(self, level, temp_plugin_env) -> None:

        """
        get_level_dir()は絶対パスを返す
        """
        from application.config import DigestConfig

        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        level_dir = config.get_level_dir(level)

        assert level_dir.is_absolute(), f"{level}のディレクトリは絶対パスであること"

    @given(level=valid_levels)
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
    )
    def test_level_dir_contains_level_name(self, level, temp_plugin_env) -> None:

        """
        get_level_dir()のパスにレベル関連の名前が含まれる
        """
        from application.config import DigestConfig

        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        level_dir = config.get_level_dir(level)

        # パスにdirが含まれる
        expected_dir = LEVEL_CONFIG[level]["dir"]
        assert expected_dir in str(level_dir), (
            f"{level}のディレクトリパスに{expected_dir}が含まれること"
        )


# =============================================================================
# Config Structure Invariants
# =============================================================================


class TestConfigStructureInvariants:
    """設定構造の不変条件"""

    @given(level=valid_levels)
    @settings(max_examples=50)
    def test_level_config_prefix_uniqueness(self, level) -> None:

        """
        各レベルのプレフィックスは一意である
        """
        prefixes = [LEVEL_CONFIG[level_name]["prefix"] for level_name in LEVEL_NAMES]
        # 注意: "L" は loop 用に予約されているが LEVEL_NAMES には含まれない
        assert len(prefixes) == len(set(prefixes)), "プレフィックスは一意であること"

    @given(level=valid_levels)
    @settings(max_examples=50)
    def test_level_config_dir_uniqueness(self, level) -> None:

        """
        各レベルのdirは一意である
        """
        dirs = [LEVEL_CONFIG[level_name]["dir"] for level_name in LEVEL_NAMES]
        assert len(dirs) == len(set(dirs)), "dirは一意であること"

    @given(level=valid_levels)
    @settings(max_examples=50)
    def test_level_config_dir_ordering(self, level) -> None:

        """
        dirの番号は階層順序と一致する
        """
        config = LEVEL_CONFIG[level]
        dir_value = config["dir"]

        # 番号を抽出
        dir_number = int(dir_value.split("_")[0])
        level_index = LEVEL_NAMES.index(level)

        # 番号は1から始まり、レベルインデックス+1と一致
        assert dir_number == level_index + 1, (
            f"{level}のdir番号は{level_index + 1}であること（実際: {dir_number}）"
        )


# =============================================================================
# JSON Roundtrip Invariants
# =============================================================================


class TestJSONRoundtripInvariants:
    """JSON読み書きの不変条件"""

    @given(config_data=valid_config_dicts)
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_config_json_roundtrip(self, config_data) -> None:

        """
        設定JSONの書き込み→読み込みで内容が保持される
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(config_data, f, ensure_ascii=False)
            temp_path = f.name

        try:
            with open(temp_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            assert loaded == config_data, "JSONラウンドトリップで内容が保持されること"
        finally:
            Path(temp_path).unlink()

    @given(
        threshold=valid_thresholds,
        level=valid_levels,
    )
    @settings(max_examples=50)
    def test_threshold_json_serializable(self, threshold, level) -> None:

        """
        閾値はJSON形式で保存可能である
        """
        data = {f"{level}_threshold": threshold}
        json_str = json.dumps(data)
        loaded = json.loads(json_str)

        assert loaded[f"{level}_threshold"] == threshold


# =============================================================================
# Note: temp_plugin_env フィクスチャは conftest.py で定義
# =============================================================================
