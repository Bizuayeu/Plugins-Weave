#!/usr/bin/env python3
"""
診断コンテキストサポート
========================

エラーメッセージに診断情報を付加するためのユーティリティ。

## 設計目的

エラーが発生した際、単純なエラーメッセージだけでなく、
設定状態やコンテキスト情報を追加することでデバッグを容易にする。
"""

from pathlib import Path
from typing import Optional


def with_diagnostic_context(
    message: str,
    *,
    config_path: Optional[Path] = None,
    current_level: Optional[str] = None,
    file_count: Optional[int] = None,
    threshold: Optional[int] = None,
    last_operation: Optional[str] = None,
    project_root: Optional[Path] = None,
) -> str:
    """
    診断情報付きエラーメッセージを生成

    エラーメッセージに設定状態やコンテキスト情報を追加し、
    デバッグを容易にする。

    Args:
        message: 基本エラーメッセージ
        config_path: 設定ファイルのパス
        current_level: 処理中のダイジェストレベル
        file_count: 処理中のファイル数
        threshold: 適用されている閾値
        last_operation: 最後に実行した操作
        project_root: パス正規化の基準（省略時はカレントディレクトリ）

    Returns:
        診断情報を含むエラーメッセージ

    Example:
        >>> msg = with_diagnostic_context(
        ...     "Processing failed",
        ...     current_level="weekly",
        ...     file_count=3,
        ...     threshold=5
        ... )
        >>> print(msg)
        'Processing failed | level: weekly | files: 3/5'
    """
    # 遅延インポートで循環参照を回避
    from domain.error_formatter import get_error_formatter

    parts = [message]

    # パス正規化用フォーマッター
    formatter = get_error_formatter(project_root)

    if config_path:
        parts.append(f"config: {formatter.format_path(config_path)}")

    if current_level:
        parts.append(f"level: {current_level}")

    if file_count is not None and threshold is not None:
        parts.append(f"files: {file_count}/{threshold}")
    elif file_count is not None:
        parts.append(f"file_count: {file_count}")
    elif threshold is not None:
        parts.append(f"threshold: {threshold}")

    if last_operation:
        parts.append(f"operation: {last_operation}")

    return " | ".join(parts)
