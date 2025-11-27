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
# 非連続ファイル（ユーザー入力）テスト（レガシー: monkeypatch方式）
# =============================================================================

class TestShadowValidatorNonConsecutiveFiles:
    """非連続ファイル検出時のユーザー入力テスト（レガシー）"""

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


# =============================================================================
# コールバック注入テスト（推奨: confirm_callback方式）
# =============================================================================

class TestShadowValidatorConfirmCallback:
    """confirm_callback注入方式のテスト"""

    @pytest.mark.unit
    def test_non_consecutive_cancelled_via_callback(self, shadow_manager):
        """コールバックでキャンセル時にValidationErrorが発生"""
        # 常にキャンセルするコールバック
        validator = ShadowValidator(
            shadow_manager,
            confirm_callback=lambda msg: False
        )

        # 非連続ファイル
        source_files = ["Loop0001_test.txt", "Loop0003_test.txt"]

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", source_files)
        assert "User cancelled" in str(exc_info.value)

    @pytest.mark.unit
    def test_non_consecutive_continued_via_callback(self, shadow_manager):
        """コールバックで承認時に正常に継続される"""
        # 常に承認するコールバック
        validator = ShadowValidator(
            shadow_manager,
            confirm_callback=lambda msg: True
        )

        # 非連続ファイル
        source_files = ["Loop0001_test.txt", "Loop0003_test.txt"]

        # 例外が発生しないことを確認
        validator.validate_shadow_content("weekly", source_files)

    @pytest.mark.unit
    def test_callback_receives_correct_message(self, shadow_manager):
        """コールバックが正しいメッセージを受け取る"""
        received_messages = []

        def capture_callback(msg):
            received_messages.append(msg)
            return True

        validator = ShadowValidator(
            shadow_manager,
            confirm_callback=capture_callback
        )

        # 非連続ファイル
        source_files = ["Loop0001_test.txt", "Loop0003_test.txt"]
        validator.validate_shadow_content("weekly", source_files)

        assert len(received_messages) == 1
        assert "Continue anyway?" in received_messages[0]

    @pytest.mark.unit
    def test_default_callback_used_when_none_provided(self, shadow_manager):
        """confirm_callbackがNoneの場合、デフォルトコールバックが使用される"""
        validator = ShadowValidator(shadow_manager, confirm_callback=None)

        # _default_confirmメソッドが設定されていることを確認
        assert validator.confirm_callback == ShadowValidator._default_confirm

    @pytest.mark.unit
    def test_custom_callback_stored(self, shadow_manager):
        """カスタムコールバックが正しく保存される"""
        custom_callback = lambda msg: True
        validator = ShadowValidator(shadow_manager, confirm_callback=custom_callback)

        assert validator.confirm_callback is custom_callback

    @pytest.mark.unit
    def test_consecutive_files_no_callback(self, shadow_manager):
        """連続ファイルの場合はコールバックが呼ばれない"""
        callback_called = []

        def detect_callback(msg):
            callback_called.append(True)
            return True

        validator = ShadowValidator(shadow_manager, confirm_callback=detect_callback)

        # 連続ファイル
        source_files = ["Loop0001_test.txt", "Loop0002_test.txt", "Loop0003_test.txt"]
        validator.validate_shadow_content("weekly", source_files)

        # コールバックは呼ばれていない
        assert len(callback_called) == 0


# =============================================================================
# エッジケーステスト（追加）
# =============================================================================

class TestShadowValidatorEdgeCases:
    """ShadowValidator のエッジケーステスト"""

    @pytest.mark.unit
    def test_different_file_prefixes_weekly(self, validator):
        """Weekly用: Loopプレフィックスのファイル"""
        source_files = ["Loop0001_test.txt", "Loop0002_another.txt"]
        validator.validate_shadow_content("weekly", source_files)

    @pytest.mark.unit
    def test_different_file_prefixes_monthly(self, validator):
        """Monthly用: Wプレフィックスのファイル"""
        source_files = ["W0001_digest1.txt", "W0002_digest2.txt"]
        validator.validate_shadow_content("monthly", source_files)

    @pytest.mark.unit
    def test_different_file_prefixes_quarterly(self, validator):
        """Quarterly用: Mプレフィックスのファイル"""
        source_files = ["M001_digest1.txt", "M002_digest2.txt"]
        validator.validate_shadow_content("quarterly", source_files)

    @pytest.mark.unit
    def test_large_file_numbers(self, validator):
        """大きなファイル番号を処理"""
        source_files = ["Loop9998_test.txt", "Loop9999_final.txt"]
        validator.validate_shadow_content("weekly", source_files)

    @pytest.mark.unit
    def test_source_files_with_none_raises(self, validator):
        """source_filesにNoneが含まれる場合はValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", [None, "Loop0001.txt"])
        assert "expected str" in str(exc_info.value)

    @pytest.mark.unit
    def test_mixed_valid_invalid_filenames(self, validator):
        """有効と無効のファイル名が混在する場合"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", ["Loop0001_test.txt", "bad.txt"])
        assert "Invalid filename format" in str(exc_info.value)

    @pytest.mark.unit
    def test_unicode_in_filename_suffix(self, validator):
        """ファイル名に日本語が含まれる場合"""
        source_files = ["Loop0001_テスト会話.txt", "Loop0002_別の会話.txt"]
        validator.validate_shadow_content("weekly", source_files)

    @pytest.mark.integration
    def test_validate_and_get_shadow_with_multiple_files(
        self, validator, shadow_manager, temp_plugin_env
    ):
        """複数ファイルを含むshadow_digestを検証"""
        from test_helpers import create_test_loop_file

        # 複数のLoopファイルを作成
        for i in range(1, 4):
            create_test_loop_file(temp_plugin_env.loops_path, i, f"test_{i}")
        shadow_manager.update_shadow_for_new_loops()

        result = validator.validate_and_get_shadow("weekly", "Test Title")

        assert result is not None
        assert len(result["source_files"]) == 3


# =============================================================================
# プライベートメソッドの単体テスト（Phase 6: カバレッジ向上）
# =============================================================================

class TestShadowValidatorPrivateMethods:
    """プライベートメソッドの単体テスト"""

    # -------------------------------------------------------------------------
    # _validate_title() テスト
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_validate_title_empty_string_raises(self, validator):
        """_validate_title: 空文字列でValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_title("")
        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_title_whitespace_only_raises(self, validator):
        """_validate_title: 空白のみでValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_title("   ")
        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_title_none_raises(self, validator):
        """_validate_title: NoneでValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_title(None)
        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_title_valid_string_passes(self, validator):
        """_validate_title: 正常な文字列でエラーなし"""
        # 例外が発生しなければOK
        validator._validate_title("Valid Title")

    @pytest.mark.unit
    def test_validate_title_unicode_passes(self, validator):
        """_validate_title: 日本語タイトルでエラーなし"""
        validator._validate_title("テストタイトル")

    # -------------------------------------------------------------------------
    # _fetch_shadow_digest() テスト
    # -------------------------------------------------------------------------

    @pytest.mark.integration
    def test_fetch_shadow_digest_none_raises(self, validator):
        """_fetch_shadow_digest: Noneの場合DigestError"""
        with pytest.raises(DigestError) as exc_info:
            validator._fetch_shadow_digest("weekly")
        assert "No shadow digest found" in str(exc_info.value)

    @pytest.mark.integration
    def test_fetch_shadow_digest_returns_data(
        self, validator, shadow_manager, temp_plugin_env
    ):
        """_fetch_shadow_digest: 正常なデータを返す"""
        # Loopファイルを作成してShadowに追加
        create_test_loop_file(temp_plugin_env.loops_path, 1)
        shadow_manager.update_shadow_for_new_loops()

        result = validator._fetch_shadow_digest("weekly")

        assert result is not None
        assert isinstance(result, dict)
        assert "source_files" in result

    # -------------------------------------------------------------------------
    # _validate_shadow_format() テスト
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_validate_shadow_format_none_raises(self, validator):
        """_validate_shadow_format: NoneでValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_shadow_format(None)
        assert "Invalid shadow digest format" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_shadow_format_list_raises(self, validator):
        """_validate_shadow_format: listでValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_shadow_format([1, 2, 3])
        assert "Invalid shadow digest format" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_shadow_format_string_raises(self, validator):
        """_validate_shadow_format: 文字列でValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_shadow_format("not a dict")
        assert "Invalid shadow digest format" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_shadow_format_valid_dict_passes(self, validator):
        """_validate_shadow_format: 正常なdictでエラーなし"""
        # 例外が発生しなければOK
        validator._validate_shadow_format({"source_files": []})

    @pytest.mark.unit
    def test_validate_shadow_format_empty_dict_passes(self, validator):
        """_validate_shadow_format: 空のdictでもエラーなし"""
        validator._validate_shadow_format({})
