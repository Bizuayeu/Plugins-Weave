#!/usr/bin/env python3
"""
domain/file_constants.py のユニットテスト
==========================================

ファイル名・パス定数のテスト。
定数値の妥当性と一貫性を検証。
"""

import pytest

from domain.file_constants import (
    CONFIG_FILENAME,
    CONFIG_TEMPLATE,
    DATA_DIR_NAME,
    DIGEST_TIMES_FILENAME,
    DIGEST_TIMES_TEMPLATE,
    ESSENCES_DIR_NAME,
    GRAND_DIGEST_FILENAME,
    GRAND_DIGEST_TEMPLATE,
    INDIVIDUAL_DIGEST_SUFFIX,
    LOOP_FILE_PATTERN,
    LOOPS_DIR_NAME,
    MONTHLY_FILE_PATTERN,
    OVERALL_DIGEST_SUFFIX,
    PLUGIN_CONFIG_DIR,
    PROVISIONALS_SUBDIR,
    SHADOW_GRAND_DIGEST_FILENAME,
    SHADOW_GRAND_DIGEST_TEMPLATE,
    WEEKLY_FILE_PATTERN,
)


# =============================================================================
# Grand Digest ファイル名テスト
# =============================================================================


class TestGrandDigestFilenames:
    """Grand Digest関連ファイル名のテスト"""

    @pytest.mark.unit
    def test_grand_digest_filename_is_txt(self) -> None:

        """GrandDigestファイル名が.txtで終わる"""
        assert GRAND_DIGEST_FILENAME.endswith(".txt")
        assert GRAND_DIGEST_FILENAME == "GrandDigest.txt"

    @pytest.mark.unit
    def test_shadow_grand_digest_filename_is_txt(self) -> None:

        """ShadowGrandDigestファイル名が.txtで終わる"""
        assert SHADOW_GRAND_DIGEST_FILENAME.endswith(".txt")
        assert SHADOW_GRAND_DIGEST_FILENAME == "ShadowGrandDigest.txt"

    @pytest.mark.unit
    def test_grand_digest_template_is_txt(self) -> None:

        """GrandDigestテンプレートが.txtで終わる"""
        assert GRAND_DIGEST_TEMPLATE.endswith(".txt")
        assert "template" in GRAND_DIGEST_TEMPLATE.lower()

    @pytest.mark.unit
    def test_shadow_grand_digest_template_is_txt(self) -> None:

        """ShadowGrandDigestテンプレートが.txtで終わる"""
        assert SHADOW_GRAND_DIGEST_TEMPLATE.endswith(".txt")
        assert "template" in SHADOW_GRAND_DIGEST_TEMPLATE.lower()


# =============================================================================
# 設定ファイル名テスト
# =============================================================================


class TestConfigFilenames:
    """設定ファイル名のテスト"""

    @pytest.mark.unit
    def test_config_filename_is_json(self) -> None:

        """設定ファイル名が.jsonで終わる"""
        assert CONFIG_FILENAME.endswith(".json")
        assert CONFIG_FILENAME == "config.json"

    @pytest.mark.unit
    def test_config_template_is_json(self) -> None:

        """設定テンプレートが.jsonで終わる"""
        assert CONFIG_TEMPLATE.endswith(".json")
        assert "template" in CONFIG_TEMPLATE.lower()

    @pytest.mark.unit
    def test_digest_times_filename_is_json(self) -> None:

        """ダイジェスト時刻ファイル名が.jsonで終わる"""
        assert DIGEST_TIMES_FILENAME.endswith(".json")

    @pytest.mark.unit
    def test_digest_times_template_is_json(self) -> None:

        """ダイジェスト時刻テンプレートが.jsonで終わる"""
        assert DIGEST_TIMES_TEMPLATE.endswith(".json")
        assert "template" in DIGEST_TIMES_TEMPLATE.lower()


# =============================================================================
# ディレクトリ名テスト
# =============================================================================


class TestDirectoryNames:
    """ディレクトリ名のテスト"""

    @pytest.mark.unit
    def test_plugin_config_dir_starts_with_dot(self) -> None:

        """プラグイン設定ディレクトリがドットで始まる（隠しディレクトリ）"""
        assert PLUGIN_CONFIG_DIR.startswith(".")
        assert PLUGIN_CONFIG_DIR == ".claude-plugin"

    @pytest.mark.unit
    def test_essences_dir_name(self) -> None:

        """Essencesディレクトリ名"""
        assert ESSENCES_DIR_NAME == "Essences"

    @pytest.mark.unit
    def test_loops_dir_name(self) -> None:

        """Loopsディレクトリ名"""
        assert LOOPS_DIR_NAME == "Loops"

    @pytest.mark.unit
    def test_provisionals_subdir(self) -> None:

        """Provisionalsサブディレクトリ名"""
        assert PROVISIONALS_SUBDIR == "Provisionals"

    @pytest.mark.unit
    def test_data_dir_name(self) -> None:

        """データルートディレクトリ名"""
        assert DATA_DIR_NAME == "data"


# =============================================================================
# ファイルパターンテスト
# =============================================================================


class TestFilePatterns:
    """ファイルパターンのテスト"""

    @pytest.mark.unit
    def test_loop_file_pattern(self) -> None:

        """Loopファイルパターンがglobパターン"""
        assert "*" in LOOP_FILE_PATTERN
        assert LOOP_FILE_PATTERN.startswith("L")
        assert LOOP_FILE_PATTERN.endswith(".txt")

    @pytest.mark.unit
    def test_weekly_file_pattern(self) -> None:

        """Weeklyファイルパターンがglobパターン"""
        assert "*" in WEEKLY_FILE_PATTERN
        assert WEEKLY_FILE_PATTERN.startswith("W")
        assert WEEKLY_FILE_PATTERN.endswith(".txt")

    @pytest.mark.unit
    def test_monthly_file_pattern(self) -> None:

        """Monthlyファイルパターンがglobパターン"""
        assert "*" in MONTHLY_FILE_PATTERN
        assert MONTHLY_FILE_PATTERN.startswith("M")
        assert MONTHLY_FILE_PATTERN.endswith(".txt")


# =============================================================================
# サフィックステスト
# =============================================================================


class TestFileSuffixes:
    """ファイルサフィックスのテスト"""

    @pytest.mark.unit
    def test_individual_digest_suffix(self) -> None:

        """個別ダイジェストサフィックス"""
        assert INDIVIDUAL_DIGEST_SUFFIX.endswith(".txt")
        assert "Individual" in INDIVIDUAL_DIGEST_SUFFIX

    @pytest.mark.unit
    def test_overall_digest_suffix(self) -> None:

        """統合ダイジェストサフィックス"""
        assert OVERALL_DIGEST_SUFFIX.endswith(".txt")
        assert "Overall" in OVERALL_DIGEST_SUFFIX


# =============================================================================
# 一貫性テスト
# =============================================================================


class TestConstantsConsistency:
    """定数間の一貫性テスト"""

    @pytest.mark.unit
    def test_template_names_are_distinct_from_filenames(self) -> None:

        """テンプレート名と実ファイル名が異なる"""
        assert GRAND_DIGEST_FILENAME != GRAND_DIGEST_TEMPLATE
        assert SHADOW_GRAND_DIGEST_FILENAME != SHADOW_GRAND_DIGEST_TEMPLATE
        assert DIGEST_TIMES_FILENAME != DIGEST_TIMES_TEMPLATE
        assert CONFIG_FILENAME != CONFIG_TEMPLATE

    @pytest.mark.unit
    def test_all_constants_are_strings(self) -> None:

        """すべての定数が文字列"""
        constants = [
            GRAND_DIGEST_FILENAME,
            SHADOW_GRAND_DIGEST_FILENAME,
            GRAND_DIGEST_TEMPLATE,
            SHADOW_GRAND_DIGEST_TEMPLATE,
            CONFIG_FILENAME,
            CONFIG_TEMPLATE,
            DIGEST_TIMES_FILENAME,
            DIGEST_TIMES_TEMPLATE,
            PLUGIN_CONFIG_DIR,
            ESSENCES_DIR_NAME,
            LOOPS_DIR_NAME,
            PROVISIONALS_SUBDIR,
            DATA_DIR_NAME,
            LOOP_FILE_PATTERN,
            WEEKLY_FILE_PATTERN,
            MONTHLY_FILE_PATTERN,
            INDIVIDUAL_DIGEST_SUFFIX,
            OVERALL_DIGEST_SUFFIX,
        ]
        for const in constants:
            assert isinstance(const, str), f"{const} is not a string"

    @pytest.mark.unit
    def test_no_empty_constants(self) -> None:

        """空の定数がない"""
        constants = [
            GRAND_DIGEST_FILENAME,
            SHADOW_GRAND_DIGEST_FILENAME,
            CONFIG_FILENAME,
            PLUGIN_CONFIG_DIR,
            ESSENCES_DIR_NAME,
            LOOPS_DIR_NAME,
        ]
        for const in constants:
            assert const, f"Constant should not be empty: {const}"
