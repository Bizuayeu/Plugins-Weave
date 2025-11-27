#!/usr/bin/env python3
"""
Shadow Validator
================

ShadowGrandDigestの内容を検証するクラス
"""

from typing import Optional, Callable, List

from config import extract_file_number
from application.validators import is_valid_dict, is_valid_list
from domain.types import OverallDigestData
from domain.exceptions import ValidationError, DigestError
from infrastructure import log_info, log_warning
from application.grand import ShadowGrandDigestManager


class ShadowValidator:
    """ShadowGrandDigestの検証を担当"""

    def __init__(
        self,
        shadow_manager: ShadowGrandDigestManager,
        confirm_callback: Optional[Callable[[str], bool]] = None
    ):
        """
        Args:
            shadow_manager: ShadowGrandDigestManager インスタンス
            confirm_callback: 確認コールバック関数（テスト用にモック可能）
        """
        self.shadow_manager = shadow_manager
        self.confirm_callback = confirm_callback or self._default_confirm

    @staticmethod
    def _default_confirm(message: str) -> bool:
        """
        デフォルトの確認コールバック（対話的）

        Args:
            message: 確認メッセージ

        Returns:
            ユーザーが承認した場合True
        """
        try:
            response = input(f"{message} (y/n): ")
            return response.lower() == 'y'
        except EOFError:
            return True  # 非対話環境では自動承認

    def validate_shadow_content(self, level: str, source_files: List[str]) -> None:
        """
        ShadowGrandDigestの内容が妥当かチェック

        - source_filesがlist型であること
        - source_filesが空でないこと
        - ファイル名が連番になっていること（警告のみ、継続可能）

        Raises:
            ValidationError: source_filesの形式が不正な場合
        """
        # 型チェック
        if not is_valid_list(source_files):
            raise ValidationError(f"source_files must be a list, got {type(source_files).__name__}")

        if not source_files:
            raise ValidationError(f"Shadow digest for level '{level}' has no source files")

        # ファイル名の型チェック
        for i, filename in enumerate(source_files):
            if not isinstance(filename, str):
                raise ValidationError(f"Invalid filename at index {i}: expected str, got {type(filename).__name__}")

        # ファイル名から番号を抽出（共通関数を使用）
        numbers = []
        for filename in source_files:
            result = extract_file_number(filename)
            if result:
                numbers.append(result[1])
            else:
                raise ValidationError(f"Invalid filename format: {filename}")

        # 連番チェック
        numbers.sort()
        for i in range(len(numbers) - 1):
            if numbers[i + 1] != numbers[i] + 1:
                log_warning("Non-consecutive files detected:")
                log_warning(f"  Files: {source_files}")
                log_warning(f"  Numbers: {numbers}")
                if not self.confirm_callback("Continue anyway?"):
                    raise ValidationError("User cancelled due to non-consecutive files")
                break

        log_info(f"Shadow validation passed: {len(source_files)} file(s), range: {numbers[0]}-{numbers[-1]}")

    def _validate_title(self, weave_title: str) -> None:
        """
        タイトルの検証

        Args:
            weave_title: 検証するタイトル

        Raises:
            ValidationError: タイトルが空の場合
        """
        if not weave_title or not weave_title.strip():
            raise ValidationError("weave_title cannot be empty")

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
            log_info("Run 'python shadow_grand_digest.py' to update shadow first")
            raise DigestError(f"No shadow digest found for level: {level}")

        return shadow_digest

    def _validate_shadow_format(self, shadow_digest) -> None:
        """
        Shadowダイジェストの形式検証

        Args:
            shadow_digest: 検証するデータ

        Raises:
            ValidationError: 形式が不正な場合
        """
        if not is_valid_dict(shadow_digest):
            raise ValidationError(f"Invalid shadow digest format: expected dict, got {type(shadow_digest).__name__}")

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

        log_info(f"Shadow digest contains {len(source_files)} source file(s)")
        return shadow_digest
