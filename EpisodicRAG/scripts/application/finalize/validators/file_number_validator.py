#!/usr/bin/env python3
"""
File Number Validator
=====================

ファイル番号の抽出と連番チェックを担当するバリデータ
"""

from collections.abc import Sequence

from domain.error_formatter import CompositeErrorFormatter, get_error_formatter
from domain.file_naming import extract_file_number
from domain.protocols import LevelRegistryProtocol


class FileNumberValidator:
    """
    ファイル番号の検証を担当

    Single Responsibility: ファイル名からの番号抽出と連番検証のみを行う
    """

    def __init__(
        self,
        formatter: CompositeErrorFormatter | None = None,
        registry: LevelRegistryProtocol | None = None,
    ):
        """
        Args:
            formatter: エラーフォーマッタ（DIによるテスト容易化）
                      未指定時はグローバルシングルトンを使用
            registry: レベルレジストリ（DIによるテスト容易化）
                     未指定時はグローバルシングルトンを使用
        """
        self._formatter = formatter
        self._registry = registry

    @property
    def formatter(self) -> CompositeErrorFormatter:
        """遅延初期化でフォーマッタを取得"""
        if self._formatter is None:
            self._formatter = get_error_formatter()
        return self._formatter

    def extract_numbers(
        self, filenames: Sequence[object]
    ) -> tuple[list[int], list[str]]:
        """
        ファイル名リストから番号を抽出

        Args:
            filenames: ファイル名のリスト
                       非str要素はエラーとして報告（防御的プログラミング）

        Returns:
            (numbers, errors) のタプル
            - numbers: 抽出に成功した番号のリスト
            - errors: 抽出に失敗したファイルのエラーメッセージリスト

        Example:
            >>> validator = FileNumberValidator()
            >>> validator.extract_numbers(["L00186.txt", "L00187.txt"])
            ([186, 187], [])
        """
        numbers: list[int] = []
        errors: list[str] = []

        for i, filename in enumerate(filenames):
            # 型チェック（防御的プログラミング - ランタイムで非strが渡される可能性）
            if not isinstance(filename, str):
                errors.append(
                    self.formatter.validation.invalid_type(
                        f"filename at index {i}", "str", filename
                    )
                )
                continue

            # 番号抽出
            result = extract_file_number(filename, registry=self._registry)
            if result:
                numbers.append(result[1])
            else:
                errors.append(f"Invalid filename format: {filename}")

        return numbers, errors

    def check_consecutive(self, numbers: list[int]) -> bool:
        """
        番号リストが連番かをチェック

        Args:
            numbers: 番号のリスト（ソート済みである必要はない）

        Returns:
            連番の場合True、そうでない場合False

        Example:
            >>> validator = FileNumberValidator()
            >>> validator.check_consecutive([1, 2, 3])
            True
            >>> validator.check_consecutive([1, 3, 5])
            False
        """
        if len(numbers) <= 1:
            return True

        sorted_nums = sorted(numbers)
        return all(
            sorted_nums[i + 1] == sorted_nums[i] + 1
            for i in range(len(sorted_nums) - 1)
        )

    def validate_consecutive(
        self, numbers: list[int], source_files: list[str]
    ) -> list[str]:
        """
        番号が連番かを検証し、連番でない場合は警告メッセージを返す

        Args:
            numbers: 検証する番号リスト
            source_files: 元のファイル名リスト（エラーメッセージ用）

        Returns:
            警告メッセージのリスト（連番の場合は空）

        Example:
            >>> validator = FileNumberValidator()
            >>> validator.validate_consecutive([1, 2, 3], ["L00001.txt", "L00002.txt", "L00003.txt"])
            []
            >>> validator.validate_consecutive([1, 3], ["L00001.txt", "L00003.txt"])
            ["Non-consecutive files detected: [1, 3]"]
        """
        if not numbers:
            return []

        sorted_nums = sorted(numbers)
        if not self.check_consecutive(sorted_nums):
            return [f"Non-consecutive files detected: {sorted_nums}"]
        return []
