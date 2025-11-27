#!/usr/bin/env python3
"""
finalize/shadow_validator.py のユニットテスト
=============================================

ShadowValidatorクラスの動作を検証。
- validate_shadow_content: Shadowコンテンツの検証
- validate_and_get_shadow: 検証済みShadowの取得
"""
import pytest

# Application層
from application.finalize import ShadowValidator
from application.grand import ShadowGrandDigestManager

# Domain層
from domain.exceptions import ValidationError, DigestError

# 設定
from config import DigestConfig
from test_helpers import create_test_loop_file


# =============================================================================
# フィクスチャ
# =============================================================================

@pytest.fixture
def config(temp_plugin_env):
    """テスト用DigestConfig"""
    return DigestConfig(plugin_root=temp_plugin_env.plugin_root)


@pytest.fixture
def shadow_manager(config):
    """テスト用ShadowGrandDigestManager"""
    return ShadowGrandDigestManager(config)


@pytest.fixture
def validator(shadow_manager):
    """テスト用ShadowValidator"""
    return ShadowValidator(shadow_manager)


# =============================================================================
# ShadowValidator.validate_shadow_content テスト
# =============================================================================

class TestShadowValidatorValidateShadowContent:
    """validate_shadow_content メソッドのテスト"""

    @pytest.mark.unit
    def test_valid_consecutive_files(self, validator):
        """連続したファイルは検証通過"""
        source_files = ["Loop0001_test.txt", "Loop0002_test.txt", "Loop0003_test.txt"]
        # エラーなく完了すればOK
        validator.validate_shadow_content("weekly", source_files)

    @pytest.mark.unit
    def test_raises_on_non_list(self, validator):
        """source_filesがlistでない場合はValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", "not a list")
        assert "must be a list" in str(exc_info.value)

    @pytest.mark.unit
    def test_raises_on_dict(self, validator):
        """source_filesがdictの場合はValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", {"key": "value"})
        assert "must be a list" in str(exc_info.value)

    @pytest.mark.unit
    def test_raises_on_empty_list(self, validator):
        """source_filesが空の場合はValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", [])
        assert "has no source files" in str(exc_info.value)

    @pytest.mark.unit
    def test_raises_on_non_string_filename(self, validator):
        """ファイル名が文字列でない場合はValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", ["Loop0001.txt", 123])
        assert "expected str" in str(exc_info.value)

    @pytest.mark.unit
    def test_raises_on_invalid_filename_format(self, validator):
        """無効なファイル名形式の場合はValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", ["invalid_format.txt"])
        assert "Invalid filename format" in str(exc_info.value)

    @pytest.mark.unit
    def test_single_file_passes(self, validator):
        """1ファイルでも検証通過"""
        source_files = ["Loop0001_test.txt"]
        validator.validate_shadow_content("weekly", source_files)


# =============================================================================
# ShadowValidator.validate_and_get_shadow テスト
# =============================================================================

class TestShadowValidatorValidateAndGetShadow:
    """validate_and_get_shadow メソッドのテスト"""

    @pytest.mark.integration
    def test_raises_on_empty_title(self, validator):
        """weave_titleが空の場合はValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_and_get_shadow("weekly", "")
        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.integration
    def test_raises_on_whitespace_title(self, validator):
        """weave_titleが空白のみの場合はValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_and_get_shadow("weekly", "   ")
        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.integration
    def test_raises_on_no_shadow_digest(self, validator):
        """shadow_digestがない場合はDigestError"""
        with pytest.raises(DigestError) as exc_info:
            validator.validate_and_get_shadow("weekly", "Test Title")
        assert "No shadow digest found" in str(exc_info.value)

    @pytest.mark.integration
    def test_returns_valid_shadow(self, validator, shadow_manager, temp_plugin_env):
        """有効なshadow_digestを返す"""
        # Loopファイルを作成してShadowに追加
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)
        shadow_manager.update_shadow_for_new_loops()

        result = validator.validate_and_get_shadow("weekly", "Test Title")

        assert result is not None
        assert "source_files" in result
        assert len(result["source_files"]) == 1


# =============================================================================
# ShadowValidator 初期化テスト
# =============================================================================

class TestShadowValidatorInit:
    """ShadowValidator 初期化のテスト"""

    @pytest.mark.unit
    def test_stores_shadow_manager(self, shadow_manager):
        """shadow_managerが正しく保存される"""
        validator = ShadowValidator(shadow_manager)
        assert validator.shadow_manager is shadow_manager


# =============================================================================
# 非連続ファイル（ユーザー入力）テスト
# =============================================================================

class TestShadowValidatorNonConsecutiveFiles:
    """非連続ファイル検出時のユーザー入力テスト"""

    @pytest.mark.unit
    def test_non_consecutive_files_user_continues(self, validator, monkeypatch):
        """非連続ファイル検出時、ユーザーが'y'で続行"""
        # input()を'y'を返すようにモック
        monkeypatch.setattr('builtins.input', lambda _: 'y')

        # 非連続ファイル（1, 3 で 2 が抜けている）
        source_files = ["Loop0001_test.txt", "Loop0003_test.txt"]

        # 'y'入力で例外なく完了
        validator.validate_shadow_content("weekly", source_files)

    @pytest.mark.unit
    def test_non_consecutive_files_user_cancels(self, validator, monkeypatch):
        """非連続ファイル検出時、ユーザーが'n'でキャンセル"""
        # input()を'n'を返すようにモック
        monkeypatch.setattr('builtins.input', lambda _: 'n')

        # 非連続ファイル
        source_files = ["Loop0001_test.txt", "Loop0003_test.txt"]

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", source_files)
        assert "User cancelled" in str(exc_info.value)

    @pytest.mark.unit
    def test_non_consecutive_files_user_empty_input_cancels(self, validator, monkeypatch):
        """非連続ファイル検出時、空入力でもキャンセル"""
        # input()を空文字を返すようにモック
        monkeypatch.setattr('builtins.input', lambda _: '')

        source_files = ["Loop0001_test.txt", "Loop0005_test.txt"]

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", source_files)
        assert "User cancelled" in str(exc_info.value)

    @pytest.mark.unit
    def test_consecutive_files_no_prompt(self, validator, monkeypatch):
        """連続ファイルの場合はinput()が呼ばれない"""
        # input()が呼ばれたらエラーを発生させる
        def raise_if_called(_):
            raise AssertionError("input() should not be called for consecutive files")

        monkeypatch.setattr('builtins.input', raise_if_called)

        # 連続ファイル
        source_files = ["Loop0001_test.txt", "Loop0002_test.txt", "Loop0003_test.txt"]

        # エラーなく完了
        validator.validate_shadow_content("weekly", source_files)
