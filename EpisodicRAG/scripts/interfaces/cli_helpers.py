#!/usr/bin/env python3
"""
CLI Helpers
===========

CLI共通ヘルパー関数。
すべてのCLIツールで使用するJSON出力とエラー出力を提供する。

Usage:
    from interfaces.cli_helpers import output_json, output_error

    output_json({"status": "ok", "data": result})
    output_error("Something went wrong", details={"action": "retry"})
"""

import json
import sys
from typing import Any

__all__ = ["output_json", "output_error"]


def output_json(data: Any) -> None:
    """
    JSON形式で標準出力に出力

    Args:
        data: 出力するデータ（JSON変換可能な任意の型）

    Example:
        output_json({"status": "ok", "count": 42})
    """
    print(json.dumps(data, ensure_ascii=False, indent=2))


def output_error(error: str, details: dict[str, Any] | None = None) -> None:
    """
    エラーをJSON形式で出力し、終了コード1で終了

    Args:
        error: エラーメッセージ
        details: 追加の詳細情報（オプション）

    Example:
        output_error("File not found", details={"action": "Run setup"})
    """
    result: dict[str, Any] = {"status": "error", "error": error}
    if details:
        result["details"] = details
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(1)
