#!/usr/bin/env python3
"""
Shadow Validator
================

ShadowGrandDigestの内容を検証するクラス
"""

from typing import Any, Callable, List, Optional, Tuple

from application.grand import ShadowGrandDigestManager
from domain.error_formatter import get_error_formatter
from domain.exceptions import DigestError, ValidationError
from domain.file_naming import extract_file_number
from domain.types import OverallDigestData
from domain.validators import is_valid_dict, is_valid_list
from infrastructure import get_default_confirm_callback, get_structured_logger, log_warning

_logger = get_structured_logger(__name__)


class ShadowValidator:
    """ShadowGrandDigestの検証を担当"""

    def __init__(
        self,
        shadow_manager: ShadowGrandDigestManager,
        confirm_callback: Optional[Callable[[str], bool]] = None,
    ):
        """
        Args:
            shadow_manager: ShadowGrandDigestManager インスタンス
            confirm_callback: 確認コールバック関数（テスト用にモック可能）
        """
        self.shadow_manager = shadow_manager
        self.confirm_callback = confirm_callback or get_default_confirm_callback()

    def _collect_validation_errors(
        self, level: str, source_files: List[str]
    ) -> Tuple[List[str], List[str], List[int]]:
        """
        検証エラーを1パスで収集

        Args:
            level: ダイジェストレベル
            source_files: 検証対象のファイルリスト

        Returns:
            (fatal_errors, warnings, numbers) のタプル
            - fatal_errors: 致命的エラー（処理続行不可）
            - warnings: 警告（ユーザー確認で続行可能）
            - numbers: 抽出されたファイル番号リスト
        """
        fatal_errors: List[str] = []
        warnings: List[str] = []
        numbers: List[int] = []

        # 型チェック
        formatter = get_error_formatter()
        if not is_valid_list(source_files):
            fatal_errors.append(formatter.validation.invalid_type("source_files", "list", source_files))
            return fatal_errors, warnings, numbers

        # 空チェック
        if not source_files:
            fatal_errors.append(formatter.validation.empty_collection(f"Shadow digest for level '{level}'"))
            return fatal_errors, warnings, numbers

        # ファイル名検証と番号抽出を1ループで実行
        for i, filename in enumerate(source_files):
            if not isinstance(filename, str):
                fatal_errors.append(
                    formatter.validation.invalid_type(f"filename at index {i}", "str", filename)
                )
                continue

            result = extract_file_number(filename)
            if result:
                numbers.append(result[1])
            else:
                fatal_errors.append(f"Invalid filename format: {filename}")

        # 連番チェック（致命的エラーがなければ）
        if not fatal_errors and numbers:
            numbers.sort()
            if not self._is_consecutive(numbers):
                warnings.append(f"Non-consecutive files detected: {numbers}")

        return fatal_errors, warnings, numbers

    def _is_consecutive(self, numbers: List[int]) -> bool:
        """
        番号リストが連番かチェック

        Args:
            numbers: ソート済み番号リスト

        Returns:
            連番の場合True
        """
        for i in range(len(numbers) - 1):
            if numbers[i + 1] != numbers[i] + 1:
                return False
        return True

    def validate_shadow_content(self, level: str, source_files: List[str]) -> None:
        """
        ShadowGrandDigestの内容が妥当かチェック

        - source_filesがlist型であること
        - source_filesが空でないこと
        - ファイル名が連番になっていること（警告のみ、継続可能）

        Raises:
            ValidationError: source_filesの形式が不正な場合
        """
        fatal_errors, warnings, numbers = self._collect_validation_errors(level, source_files)

        # 致命的エラーがあれば即座に例外
        if fatal_errors:
            raise ValidationError(fatal_errors[0])

        # 警告があればユーザーに確認
        if warnings:
            for warning in warnings:
                log_warning(warning)
            log_warning(f"  Files: {source_files}")
            if not self.confirm_callback("Continue anyway?"):
                raise ValidationError("User cancelled due to non-consecutive files")

        _logger.info(
            f"Shadow validation passed: {len(source_files)} file(s), range: {numbers[0]}-{numbers[-1]}"
        )

    def _validate_title(self, weave_title: str) -> None:
        """
        タイトルの検証

        Args:
            weave_title: 検証するタイトル

        Raises:
            ValidationError: タイトルが空の場合
        """
        if not weave_title or not weave_title.strip():
            formatter = get_error_formatter()
            raise ValidationError(formatter.validation.empty_collection("weave_title"))

    def _fetch_shadow_digest(self, level: str) -> OverallDigestData:
        """
        Shadowダイジェストの取得

        Args:
            level: ダイジェストレベル

        Returns:
            取得したshadow_digest

        Raises:
            DigestError: shadow_digestが見つからない場合
        """
        shadow_digest = self.shadow_manager.get_shadow_digest_for_level(level)

        if shadow_digest is None:
            _logger.info("Run 'python shadow_grand_digest.py' to update shadow first")
            formatter = get_error_formatter()
            raise DigestError(formatter.digest.digest_not_found(level, "shadow"))

        return shadow_digest

    def _validate_shadow_format(self, shadow_digest: Any) -> None:
        """
        Shadowダイジェストの形式検証

        Args:
            shadow_digest: 検証するデータ（任意の型を受け入れて検証する）

        Raises:
            ValidationError: 形式が不正な場合
        """
        if not is_valid_dict(shadow_digest):
            formatter = get_error_formatter()
            raise ValidationError(formatter.validation.invalid_type("shadow digest", "dict", shadow_digest))

    def validate_and_get_shadow(self, level: str, weave_title: str) -> OverallDigestData:
        """
        Shadowデータの検証と取得

        Args:
            level: ダイジェストレベル
            weave_title: タイトル

        Returns:
            検証済みのshadow_digest

        Raises:
            ValidationError: weave_titleが空、またはshadow_digestの形式が不正な場合
            DigestError: shadow_digestが見つからない場合
        """
        # 1. タイトル検証
        self._validate_title(weave_title)

        # 2. Shadowデータ取得
        shadow_digest = self._fetch_shadow_digest(level)

        # 3. 形式検証
        self._validate_shadow_format(shadow_digest)

        # 4. source_files取得と内容検証
        source_files = shadow_digest.get("source_files", [])
        self.validate_shadow_content(level, source_files)

        _logger.info(f"Shadow digest contains {len(source_files)} source file(s)")
        return shadow_digest
