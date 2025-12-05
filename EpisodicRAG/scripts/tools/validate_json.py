#!/usr/bin/env python3
"""
JSON Validator
==============

config.json と config.template.json のスキーマ検証ツール。

Usage:
    python -m tools.validate_json config.json               # 基本検証
    python -m tools.validate_json config.json --template t.json  # テンプレート整合性
    python -m tools.validate_json config.json --check-paths # パス形式検証

Features:
    - JSON構文の検証
    - config.template.json との構造整合性チェック
    - パス形式の検証（相対パス/絶対パス）
"""

import argparse
import json
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class JSONStatus(Enum):
    """JSON検証ステータス"""

    VALID = "valid"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    WARNING = "warning"


@dataclass
class ValidationResult:
    """検証結果"""

    status: JSONStatus
    file_path: Path
    message: str = ""


class JSONValidator:
    """JSON検証クラス"""

    def validate_file(self, file_path: Path) -> ValidationResult:
        """
        JSONファイルの構文を検証

        Args:
            file_path: 検証対象のJSONファイルパス

        Returns:
            ValidationResult: 検証結果
        """
        if not file_path.exists():
            return ValidationResult(
                status=JSONStatus.NOT_FOUND,
                file_path=file_path,
                message="File not found",
            )

        try:
            with open(file_path, encoding="utf-8") as f:
                json.load(f)
            return ValidationResult(
                status=JSONStatus.VALID,
                file_path=file_path,
                message="",
            )
        except json.JSONDecodeError as e:
            return ValidationResult(
                status=JSONStatus.INVALID,
                file_path=file_path,
                message=f"JSON syntax error: {e}",
            )

    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """JSONファイルを読み込んで辞書として返す"""
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)  # type: ignore[no-any-return]

    def validate_against_template(self, config_path: Path, template_path: Path) -> ValidationResult:
        """
        configがtemplateと同じ構造を持つか検証

        Args:
            config_path: 検証対象のconfig.jsonパス
            template_path: テンプレートのconfig.template.jsonパス

        Returns:
            ValidationResult: 検証結果
        """
        # ファイル存在チェック
        if not template_path.exists():
            return ValidationResult(
                status=JSONStatus.NOT_FOUND,
                file_path=template_path,
                message="Template file not found",
            )

        if not config_path.exists():
            return ValidationResult(
                status=JSONStatus.NOT_FOUND,
                file_path=config_path,
                message="Config file not found",
            )

        # JSON読み込み
        try:
            template_data = self._load_json(template_path)
            config_data = self._load_json(config_path)
        except json.JSONDecodeError as e:
            return ValidationResult(
                status=JSONStatus.INVALID,
                file_path=config_path,
                message=f"JSON syntax error: {e}",
            )

        # 必須キーのチェック（templateのトップレベルキー）
        missing_keys = self._find_missing_keys(template_data, config_data)
        if missing_keys:
            return ValidationResult(
                status=JSONStatus.INVALID,
                file_path=config_path,
                message=f"Missing required keys: {', '.join(missing_keys)}",
            )

        return ValidationResult(
            status=JSONStatus.VALID,
            file_path=config_path,
            message="",
        )

    def _find_missing_keys(
        self, template: Dict[str, Any], config: Dict[str, Any], prefix: str = ""
    ) -> list[str]:
        """templateに存在するがconfigに存在しないキーを再帰的に検索"""
        missing: list[str] = []

        for key in template:
            # コメントキー（_comment_で始まる）はスキップ
            if key.startswith("_comment"):
                continue

            full_key = f"{prefix}.{key}" if prefix else key

            if key not in config:
                missing.append(full_key)
            elif isinstance(template[key], dict) and isinstance(config.get(key), dict):
                # ネストされた辞書を再帰的にチェック
                missing.extend(self._find_missing_keys(template[key], config[key], full_key))

        return missing

    def validate_paths(self, config_path: Path) -> ValidationResult:
        """
        config内のパス形式を検証

        絶対パスやチルダ展開パスが trusted_external_paths なしで
        使用されている場合は警告を返す。

        Args:
            config_path: 検証対象のconfig.jsonパス

        Returns:
            ValidationResult: 検証結果
        """
        if not config_path.exists():
            return ValidationResult(
                status=JSONStatus.NOT_FOUND,
                file_path=config_path,
                message="File not found",
            )

        try:
            config_data = self._load_json(config_path)
        except json.JSONDecodeError as e:
            return ValidationResult(
                status=JSONStatus.INVALID,
                file_path=config_path,
                message=f"JSON syntax error: {e}",
            )

        # trusted_external_paths の有無をチェック
        trusted_paths = config_data.get("trusted_external_paths", [])
        has_trusted = bool(trusted_paths)

        # base_dir のチェック
        base_dir = config_data.get("base_dir", ".")
        if self._is_external_path(base_dir) and not has_trusted:
            return ValidationResult(
                status=JSONStatus.WARNING,
                file_path=config_path,
                message=f"Absolute path '{base_dir}' requires trusted_external_paths",
            )

        # paths内の各パスをチェック
        paths = config_data.get("paths", {})
        for key, path_value in paths.items():
            if path_value and self._is_external_path(path_value) and not has_trusted:
                return ValidationResult(
                    status=JSONStatus.WARNING,
                    file_path=config_path,
                    message=f"Absolute path in paths.{key} requires trusted_external_paths",
                )

        return ValidationResult(
            status=JSONStatus.VALID,
            file_path=config_path,
            message="",
        )

    def _is_external_path(self, path: str) -> bool:
        """パスが外部パス（絶対パス、チルダ展開）かどうかを判定"""
        if not path:
            return False

        # チルダで始まる（ホームディレクトリ展開）
        if path.startswith("~"):
            return True

        # Unix絶対パス
        if path.startswith("/"):
            return True

        # Windows絶対パス（C:/, D:\, etc.）
        if len(path) >= 2 and path[1] == ":":
            return True

        return False


def main(args: Optional[List[str]] = None) -> int:
    """
    CLIエントリーポイント

    Args:
        args: コマンドライン引数（Noneの場合はsys.argvを使用）

    Returns:
        int: 終了コード（0=成功、1=エラー）
    """
    parser = argparse.ArgumentParser(
        prog="validate_json",
        description="JSON検証ツール - config.jsonのスキーマと構造を検証",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="検証対象のJSONファイル",
    )
    parser.add_argument(
        "--template",
        "-t",
        metavar="FILE",
        help="テンプレートJSONファイル（構造整合性チェック用）",
    )
    parser.add_argument(
        "--check-paths",
        "-p",
        action="store_true",
        help="パス形式を検証（絶対パスの警告）",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="エラー時のみ出力",
    )

    parsed_args = parser.parse_args(args)

    # 引数なしの場合はヘルプを表示
    if not parsed_args.file:
        parser.print_usage()
        return 1

    file_path = Path(parsed_args.file)
    validator = JSONValidator()
    has_error = False

    # 基本的なJSON構文チェック
    result = validator.validate_file(file_path)
    if result.status != JSONStatus.VALID:
        print(f"ERROR: {result.file_path}: {result.message}", file=sys.stderr)
        return 1

    if not parsed_args.quiet:
        print(f"OK: {file_path} - JSON syntax valid")

    # テンプレート整合性チェック
    if parsed_args.template:
        template_path = Path(parsed_args.template)
        result = validator.validate_against_template(file_path, template_path)
        if result.status != JSONStatus.VALID:
            print(f"ERROR: {result.file_path}: {result.message}", file=sys.stderr)
            has_error = True
        elif not parsed_args.quiet:
            print(f"OK: {file_path} - Template structure valid")

    # パス検証
    if parsed_args.check_paths:
        result = validator.validate_paths(file_path)
        if result.status == JSONStatus.WARNING:
            print(f"WARNING: {result.file_path}: {result.message}", file=sys.stderr)
            has_error = True
        elif result.status == JSONStatus.INVALID:
            print(f"ERROR: {result.file_path}: {result.message}", file=sys.stderr)
            has_error = True
        elif not parsed_args.quiet:
            print(f"OK: {file_path} - Path validation passed")

    return 1 if has_error else 0


if __name__ == "__main__":
    sys.exit(main())
