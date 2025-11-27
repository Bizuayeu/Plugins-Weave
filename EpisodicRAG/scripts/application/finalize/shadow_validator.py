#!/usr/bin/env python3
"""
Shadow Validator
================

ShadowGrandDigestの内容を検証するクラス
"""

from typing import Dict, Any

from config import extract_file_number
from application.validators import is_valid_dict, is_valid_list
from domain.exceptions import ValidationError, DigestError
from infrastructure import log_info, log_warning
from application.grand import ShadowGrandDigestManager


class ShadowValidator:
    """ShadowGrandDigestの検証を担当"""

    def __init__(self, shadow_manager: ShadowGrandDigestManager):
        """
        Args:
            shadow_manager: ShadowGrandDigestManager インスタンス
        """
        self.shadow_manager = shadow_manager

    def validate_shadow_content(self, level: str, source_files: list) -> None:
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
                print(f"  Files: {source_files}")
                print(f"  Numbers: {numbers}")
                response = input("Continue anyway? (y/n): ")
                if response.lower() != 'y':
                    raise ValidationError("User cancelled due to non-consecutive files")
                break

        log_info(f"Shadow validation passed: {len(source_files)} file(s), range: {numbers[0]}-{numbers[-1]}")

    def validate_and_get_shadow(self, level: str, weave_title: str) -> Dict[str, Any]:
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
        # 空文字列チェック
        if not weave_title or not weave_title.strip():
            raise ValidationError("weave_title cannot be empty")

        # Shadowからダイジェスト内容を取得
        shadow_digest = self.shadow_manager.get_shadow_digest_for_level(level)

        if shadow_digest is None:
            log_info("Run 'python shadow_grand_digest.py' to update shadow first")
            raise DigestError(f"No shadow digest found for level: {level}")

        if not is_valid_dict(shadow_digest):
            raise ValidationError(f"Invalid shadow digest format: expected dict, got {type(shadow_digest).__name__}")

        source_files = shadow_digest.get("source_files", [])

        # Shadow内容のバリデーション（例外を投げる）
        self.validate_shadow_content(level, source_files)

        log_info(f"Shadow digest contains {len(source_files)} source file(s)")
        return shadow_digest
