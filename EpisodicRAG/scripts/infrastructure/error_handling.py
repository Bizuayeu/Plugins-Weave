#!/usr/bin/env python3
"""
統一エラー処理ユーティリティ
============================

ファイル操作等のエラー処理を統一するためのユーティリティ関数。
一貫したエラーハンドリングパターンを提供。

Usage:
    from infrastructure.error_handling import safe_file_operation

    def cleanup():
        file_path.unlink()

    safe_file_operation(cleanup, "cleanup provisional file", on_error=lambda e: log_warning(str(e)))
"""

from typing import Callable, Optional, TypeVar

from domain.exceptions import FileIOError
from infrastructure.logging_config import log_warning

T = TypeVar("T")


def safe_file_operation(
    operation: Callable[[], T],
    context: str,
    on_error: Optional[Callable[[Exception], T]] = None,
    *,
    reraise: bool = False,
) -> Optional[T]:
    """
    ファイル操作を安全に実行するラッパー

    一般的なファイルI/Oエラーをキャッチし、一貫した方法で処理する。

    Args:
        operation: 実行するファイル操作（引数なしの関数）
        context: エラーメッセージに含めるコンテキスト情報
        on_error: エラー時のフォールバックハンドラ（省略時はNoneを返す）
        reraise: Trueの場合、on_errorがない時にFileIOErrorを再送出

    Returns:
        操作が成功した場合はその戻り値、失敗しon_errorがある場合はその戻り値、
        それ以外はNone

    Raises:
        FileIOError: reraise=Trueかつon_errorがない場合、I/Oエラー発生時

    Example:
        # 基本的な使用（エラーを無視）
        >>> safe_file_operation(lambda: file_path.unlink(), "delete file")

        # フォールバック付き
        >>> result = safe_file_operation(
        ...     lambda: load_json(path),
        ...     "load config",
        ...     on_error=lambda e: {}
        ... )

        # エラーを再送出
        >>> safe_file_operation(
        ...     lambda: save_json(path, data),
        ...     "save config",
        ...     reraise=True
        ... )
    """
    try:
        return operation()
    except (FileNotFoundError, PermissionError, IsADirectoryError, OSError) as e:
        if on_error is not None:
            return on_error(e)
        if reraise:
            raise FileIOError(f"Error during {context}: {e}") from e
        return None


def safe_cleanup(
    cleanup_func: Callable[[], None],
    context: str,
    *,
    log_on_error: bool = True,
) -> bool:
    """
    クリーンアップ操作を安全に実行する

    エラーが発生しても処理を継続し、オプションで警告をログ出力。

    Args:
        cleanup_func: クリーンアップ関数
        context: エラーメッセージに含めるコンテキスト
        log_on_error: エラー時に警告ログを出力するか

    Returns:
        クリーンアップが成功した場合True、失敗した場合False

    Example:
        >>> success = safe_cleanup(
        ...     lambda: temp_file.unlink(),
        ...     "remove temporary file"
        ... )
        >>> if not success:
        ...     print("Cleanup failed but continuing...")
    """

    def on_error(e: Exception) -> None:
        if log_on_error:
            log_warning(f"Failed to {context}: {e}")

    result = safe_file_operation(cleanup_func, context, on_error=on_error)
    return result is None  # Noneが返る = on_errorが呼ばれた = 失敗


def with_error_context(
    operation: Callable[[], T],
    context: str,
    error_type: type = FileIOError,
) -> T:
    """
    操作を実行し、エラー時にコンテキスト付きの例外を送出

    Args:
        operation: 実行する操作
        context: エラーメッセージに含めるコンテキスト
        error_type: 送出する例外の型（デフォルト: FileIOError）

    Returns:
        操作の戻り値

    Raises:
        error_type: 操作が失敗した場合

    Example:
        >>> data = with_error_context(
        ...     lambda: json.load(f),
        ...     "parsing config.json"
        ... )
    """
    try:
        return operation()
    except Exception as e:
        raise error_type(f"Error during {context}: {e}") from e
