#!/usr/bin/env python3
"""
finalize/shadow_validator.py のユニットテスト
=============================================

ShadowValidatorクラスの動作を検証。
- validate_shadow_content: Shadowコンテンツの検証
- validate_and_get_shadow: 検証済みShadowの取得
"""

import pytest
from test_helpers import create_test_loop_file

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Dict, List, Tuple
    from test_helpers import TempPluginEnvironment
    from application.config import DigestConfig
    from application.tracking import DigestTimesTracker
    from application.shadow import ShadowTemplate, ShadowIO, FileDetector
    from application.shadow.placeholder_manager import PlaceholderManager
    from application.grand import ShadowGrandDigestManager, GrandDigestManager
    from domain.types.level import LevelHierarchyEntry


from application.finalize import ShadowValidator
from application.grand import ShadowGrandDigestManager
from application.config import DigestConfig
from domain.exceptions import DigestError, ValidationError

# slow マーカーを適用（ファイル全体）
pytestmark = pytest.mark.slow

# =============================================================================
# フィクスチャ
# =============================================================================
# Note: config, shadow_manager は conftest.py で定義済み


@pytest.fixture
def validator(shadow_manager: "ShadowGrandDigestManager"):

    """テスト用ShadowValidator"""
    return ShadowValidator(shadow_manager)


# =============================================================================
# ShadowValidator.validate_shadow_content テスト
# =============================================================================


class TestShadowValidatorValidateShadowContent:
    """validate_shadow_content メソッドのテスト"""

    @pytest.mark.unit
    def test_valid_consecutive_files(self, validator) -> None:

        """連続したファイルは検証通過"""
        source_files = ["L00001_test.txt", "L00002_test.txt", "L00003_test.txt"]
        # エラーなく完了すればOK
        validator.validate_shadow_content("weekly", source_files)

    @pytest.mark.unit
    def test_raises_on_non_list(self, validator) -> None:

        """source_filesがlistでない場合はValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", "not a list")
        assert "expected list" in str(exc_info.value)

    @pytest.mark.unit
    def test_raises_on_dict(self, validator) -> None:

        """source_filesがdictの場合はValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", {"key": "value"})
        assert "expected list" in str(exc_info.value)

    @pytest.mark.unit
    def test_raises_on_empty_list(self, validator) -> None:

        """source_filesが空の場合はValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", [])
        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.unit
    def test_raises_on_non_string_filename(self, validator) -> None:

        """ファイル名が文字列でない場合はValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", ["L00001_test.txt", 123])
        assert "expected str" in str(exc_info.value)

    @pytest.mark.unit
    def test_raises_on_invalid_filename_format(self, validator) -> None:

        """無効なファイル名形式の場合はValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", ["invalid_format.txt"])
        assert "Invalid filename format" in str(exc_info.value)

    @pytest.mark.unit
    def test_single_file_passes(self, validator) -> None:

        """1ファイルでも検証通過"""
        source_files = ["L00001_test.txt"]
        validator.validate_shadow_content("weekly", source_files)


# =============================================================================
# ShadowValidator.validate_and_get_shadow テスト
# =============================================================================


class TestShadowValidatorValidateAndGetShadow:
    """validate_and_get_shadow メソッドのテスト"""

    @pytest.mark.integration
    def test_raises_on_empty_title(self, validator) -> None:

        """weave_titleが空の場合はValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_and_get_shadow("weekly", "")
        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.integration
    def test_raises_on_whitespace_title(self, validator) -> None:

        """weave_titleが空白のみの場合はValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_and_get_shadow("weekly", "   ")
        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.integration
    def test_raises_on_no_shadow_digest(self, validator) -> None:

        """shadow_digestがない場合はDigestError"""
        with pytest.raises(DigestError) as exc_info:
            validator.validate_and_get_shadow("weekly", "Test Title")
        assert "Digest not found" in str(exc_info.value)

    @pytest.mark.integration
    def test_returns_valid_shadow(self, validator, shadow_manager: "ShadowGrandDigestManager", temp_plugin_env: "TempPluginEnvironment") -> None:

        """有効なshadow_digestを返す"""
        # Loopファイルを作成してShadowに追加
        _ = create_test_loop_file(temp_plugin_env.loops_path, 1)
        shadow_manager.update_shadow_for_new_loops()

        # digest_typeを分析済み状態に設定
        data = shadow_manager._io.load_or_create()
        data["latest_digests"]["weekly"]["overall_digest"]["digest_type"] = "テスト"
        shadow_manager._io.save(data)

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
    def test_stores_shadow_manager(self, shadow_manager: "ShadowGrandDigestManager") -> None:

        """shadow_managerが正しく保存される"""
        validator = ShadowValidator(shadow_manager)
        assert validator.shadow_manager is shadow_manager


# =============================================================================
# 非連続ファイル（ユーザー入力）テスト（レガシー: monkeypatch方式）
# =============================================================================


class TestShadowValidatorNonConsecutiveFiles:
    """非連続ファイル検出時のユーザー入力テスト（レガシー）"""

    @pytest.mark.unit
    def test_non_consecutive_files_user_continues(self, validator, monkeypatch: pytest.MonkeyPatch) -> None:

        """非連続ファイル検出時、ユーザーが'y'で続行"""
        # input()を'y'を返すようにモック
        monkeypatch.setattr('builtins.input', lambda _: 'y')

        # 非連続ファイル（1, 3 で 2 が抜けている）
        source_files = ["L00001_test.txt", "L00003_test.txt"]

        # 'y'入力で例外なく完了
        validator.validate_shadow_content("weekly", source_files)

    @pytest.mark.unit
    def test_non_consecutive_files_user_cancels(self, validator, monkeypatch: pytest.MonkeyPatch) -> None:

        """非連続ファイル検出時、ユーザーが'n'でキャンセル"""
        # input()を'n'を返すようにモック
        monkeypatch.setattr('builtins.input', lambda _: 'n')

        # 非連続ファイル
        source_files = ["L00001_test.txt", "L00003_test.txt"]

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", source_files)
        assert "User cancelled" in str(exc_info.value)

    @pytest.mark.unit
    def test_non_consecutive_files_user_empty_input_cancels(self, validator, monkeypatch: pytest.MonkeyPatch) -> None:

        """非連続ファイル検出時、空入力でもキャンセル"""
        # input()を空文字を返すようにモック
        monkeypatch.setattr('builtins.input', lambda _: '')

        source_files = ["L00001_test.txt", "L00005_test.txt"]

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", source_files)
        assert "User cancelled" in str(exc_info.value)

    @pytest.mark.unit
    def test_consecutive_files_no_prompt(self, validator, monkeypatch: pytest.MonkeyPatch) -> None:

        """連続ファイルの場合はinput()が呼ばれない"""

        # input()が呼ばれたらエラーを発生させる
        def raise_if_called(_) -> None:

            raise AssertionError("input() should not be called for consecutive files")

        monkeypatch.setattr('builtins.input', raise_if_called)

        # 連続ファイル
        source_files = ["L00001_test.txt", "L00002_test.txt", "L00003_test.txt"]

        # エラーなく完了
        validator.validate_shadow_content("weekly", source_files)


# =============================================================================
# コールバック注入テスト（推奨: confirm_callback方式）
# =============================================================================


class TestShadowValidatorConfirmCallback:
    """confirm_callback注入方式のテスト"""

    @pytest.mark.unit
    def test_non_consecutive_cancelled_via_callback(self, shadow_manager: "ShadowGrandDigestManager") -> None:

        """コールバックでキャンセル時にValidationErrorが発生"""
        # 常にキャンセルするコールバック
        validator = ShadowValidator(shadow_manager, confirm_callback=lambda msg: False)

        # 非連続ファイル
        source_files = ["L00001_test.txt", "L00003_test.txt"]

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", source_files)
        assert "User cancelled" in str(exc_info.value)

    @pytest.mark.unit
    def test_non_consecutive_continued_via_callback(self, shadow_manager: "ShadowGrandDigestManager") -> None:

        """コールバックで承認時に正常に継続される"""
        # 常に承認するコールバック
        validator = ShadowValidator(shadow_manager, confirm_callback=lambda msg: True)

        # 非連続ファイル
        source_files = ["L00001_test.txt", "L00003_test.txt"]

        # 例外が発生しないことを確認
        validator.validate_shadow_content("weekly", source_files)

    @pytest.mark.unit
    def test_callback_receives_correct_message(self, shadow_manager: "ShadowGrandDigestManager"):

        """コールバックが正しいメッセージを受け取る"""
        received_messages = []

        def capture_callback(msg):

            received_messages.append(msg)
            return True

        validator = ShadowValidator(shadow_manager, confirm_callback=capture_callback)

        # 非連続ファイル
        source_files = ["L00001_test.txt", "L00003_test.txt"]
        validator.validate_shadow_content("weekly", source_files)

        assert len(received_messages) == 1
        assert "Continue anyway?" in received_messages[0]

    @pytest.mark.unit
    def test_default_callback_used_when_none_provided(self, shadow_manager: "ShadowGrandDigestManager") -> None:

        """confirm_callbackがNoneの場合、デフォルトコールバックが使用される"""
        validator = ShadowValidator(shadow_manager, confirm_callback=None)

        # デフォルトコールバックがcallableであることを確認
        assert callable(validator.confirm_callback)

    @pytest.mark.unit
    def test_custom_callback_stored(self, shadow_manager: "ShadowGrandDigestManager"):

        """カスタムコールバックが正しく保存される"""

        def custom_callback(msg):

            return True

        validator = ShadowValidator(shadow_manager, confirm_callback=custom_callback)

        assert validator.confirm_callback is custom_callback

    @pytest.mark.unit
    def test_consecutive_files_no_callback(self, shadow_manager: "ShadowGrandDigestManager"):

        """連続ファイルの場合はコールバックが呼ばれない"""
        callback_called = []

        def detect_callback(msg):

            callback_called.append(True)
            return True

        validator = ShadowValidator(shadow_manager, confirm_callback=detect_callback)

        # 連続ファイル
        source_files = ["L00001_test.txt", "L00002_test.txt", "L00003_test.txt"]
        validator.validate_shadow_content("weekly", source_files)

        # コールバックは呼ばれていない
        assert len(callback_called) == 0


# =============================================================================
# エッジケーステスト（追加）
# =============================================================================


class TestShadowValidatorEdgeCases:
    """ShadowValidator のエッジケーステスト"""

    @pytest.mark.unit
    def test_different_file_prefixes_weekly(self, validator) -> None:

        """Weekly用: Lプレフィックスのファイル"""
        source_files = ["L00001_test.txt", "L00002_another.txt"]
        validator.validate_shadow_content("weekly", source_files)

    @pytest.mark.unit
    def test_different_file_prefixes_monthly(self, validator) -> None:

        """Monthly用: Wプレフィックスのファイル"""
        source_files = ["W0001_digest1.txt", "W0002_digest2.txt"]
        validator.validate_shadow_content("monthly", source_files)

    @pytest.mark.unit
    def test_different_file_prefixes_quarterly(self, validator) -> None:

        """Quarterly用: Mプレフィックスのファイル"""
        source_files = ["M0001_digest1.txt", "M0002_digest2.txt"]
        validator.validate_shadow_content("quarterly", source_files)

    @pytest.mark.unit
    def test_large_file_numbers(self, validator) -> None:

        """大きなファイル番号を処理"""
        source_files = ["L09998_test.txt", "L09999_final.txt"]
        validator.validate_shadow_content("weekly", source_files)

    @pytest.mark.unit
    def test_source_files_with_none_raises(self, validator) -> None:

        """source_filesにNoneが含まれる場合はValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", [None, "L00001.txt"])
        assert "expected str" in str(exc_info.value)

    @pytest.mark.unit
    def test_mixed_valid_invalid_filenames(self, validator) -> None:

        """有効と無効のファイル名が混在する場合"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_shadow_content("weekly", ["L00001_test.txt", "bad.txt"])
        assert "Invalid filename format" in str(exc_info.value)

    @pytest.mark.unit
    def test_unicode_in_filename_suffix(self, validator) -> None:

        """ファイル名に日本語が含まれる場合"""
        source_files = ["L00001_テスト会話.txt", "L00002_別の会話.txt"]
        validator.validate_shadow_content("weekly", source_files)

    @pytest.mark.integration
    def test_validate_and_get_shadow_with_multiple_files(
        self, validator, shadow_manager: "ShadowGrandDigestManager", temp_plugin_env: "TempPluginEnvironment"
    ) -> None:

        """複数ファイルを含むshadow_digestを検証"""
        from test_helpers import create_test_loop_file

        # 複数のLoopファイルを作成
        for i in range(1, 4):
            create_test_loop_file(temp_plugin_env.loops_path, i, f"test_{i}")
        shadow_manager.update_shadow_for_new_loops()

        # digest_typeを分析済み状態に設定
        data = shadow_manager._io.load_or_create()
        data["latest_digests"]["weekly"]["overall_digest"]["digest_type"] = "テスト"
        shadow_manager._io.save(data)

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
    def test_validate_title_empty_string_raises(self, validator) -> None:

        """_validate_title: 空文字列でValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_title("")
        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_title_whitespace_only_raises(self, validator) -> None:

        """_validate_title: 空白のみでValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_title("   ")
        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_title_none_raises(self, validator) -> None:

        """_validate_title: NoneでValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_title(None)
        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_title_valid_string_passes(self, validator) -> None:

        """_validate_title: 正常な文字列でエラーなし"""
        # 例外が発生しなければOK
        validator._validate_title("Valid Title")

    @pytest.mark.unit
    def test_validate_title_unicode_passes(self, validator) -> None:

        """_validate_title: 日本語タイトルでエラーなし"""
        validator._validate_title("テストタイトル")

    # -------------------------------------------------------------------------
    # _fetch_shadow_digest() テスト
    # -------------------------------------------------------------------------

    @pytest.mark.integration
    def test_fetch_shadow_digest_none_raises(self, validator) -> None:

        """_fetch_shadow_digest: Noneの場合DigestError"""
        with pytest.raises(DigestError) as exc_info:
            validator._fetch_shadow_digest("weekly")
        assert "Digest not found" in str(exc_info.value)

    @pytest.mark.integration
    def test_fetch_shadow_digest_returns_data(self, validator, shadow_manager: "ShadowGrandDigestManager", temp_plugin_env: "TempPluginEnvironment") -> None:

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
    def test_validate_shadow_format_none_raises(self, validator) -> None:

        """_validate_shadow_format: NoneでValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_shadow_format(None)
        assert "expected dict" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_shadow_format_list_raises(self, validator) -> None:

        """_validate_shadow_format: listでValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_shadow_format([1, 2, 3])
        assert "expected dict" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_shadow_format_string_raises(self, validator) -> None:

        """_validate_shadow_format: 文字列でValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_shadow_format("not a dict")
        assert "expected dict" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_shadow_format_valid_dict_passes(self, validator) -> None:

        """_validate_shadow_format: 正常なdictでエラーなし"""
        # 例外が発生しなければOK
        validator._validate_shadow_format({"source_files": []})

    @pytest.mark.unit
    def test_validate_shadow_format_empty_dict_passes(self, validator) -> None:

        """_validate_shadow_format: 空のdictでもエラーなし"""
        validator._validate_shadow_format({})

    # -------------------------------------------------------------------------
    # _validate_digest_type() テスト
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_validate_digest_type_none_raises(self, validator) -> None:

        """_validate_digest_type: NoneでValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_digest_type({"digest_type": None})
        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_digest_type_empty_string_raises(self, validator) -> None:

        """_validate_digest_type: 空文字列でValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_digest_type({"digest_type": ""})
        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_digest_type_whitespace_only_raises(self, validator) -> None:

        """_validate_digest_type: 空白のみでValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_digest_type({"digest_type": "   "})
        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_digest_type_placeholder_raises(self, validator) -> None:

        """_validate_digest_type: プレースホルダーでValidationError"""
        from domain.constants import PLACEHOLDER_SIMPLE

        with pytest.raises(ValidationError) as exc_info:
            validator._validate_digest_type({"digest_type": PLACEHOLDER_SIMPLE})
        assert "placeholder" in str(exc_info.value).lower()

    @pytest.mark.unit
    def test_validate_digest_type_placeholder_marker_raises(self, validator) -> None:

        """_validate_digest_type: PLACEHOLDERマーカーを含む場合ValidationError"""
        from domain.constants import PLACEHOLDER_MARKER

        with pytest.raises(ValidationError) as exc_info:
            validator._validate_digest_type({"digest_type": f"{PLACEHOLDER_MARKER}: custom -->"})
        assert "placeholder" in str(exc_info.value).lower()

    @pytest.mark.unit
    def test_validate_digest_type_valid_string_passes(self, validator) -> None:

        """_validate_digest_type: 正常な文字列でエラーなし"""
        # 例外が発生しなければOK
        validator._validate_digest_type({"digest_type": "転換"})

    @pytest.mark.unit
    def test_validate_digest_type_valid_types(self, validator) -> None:

        """_validate_digest_type: 有効なdigest_type値でエラーなし"""
        valid_types = ["統合", "深化", "転換", "テスト"]
        for dtype in valid_types:
            validator._validate_digest_type({"digest_type": dtype})

    @pytest.mark.unit
    def test_validate_digest_type_missing_key_raises(self, validator) -> None:

        """_validate_digest_type: digest_typeキーがない場合ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_digest_type({})
        assert "cannot be empty" in str(exc_info.value)
