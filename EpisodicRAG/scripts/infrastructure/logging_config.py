#!/usr/bin/env python3
"""
Logging Configuration
=====================

ロギング設定とユーティリティ関数を提供するインフラストラクチャ層。

## Global State

このモジュールはPython標準のloggingモジュールを使用しており、
logging.getLogger()で取得するLoggerはグローバルに共有される。

ハンドラーの追加・削除はグローバルに影響するため、テスト時は注意が必要。

## テスト時の注意

テスト間でロガーの状態が共有される可能性がある。
必要に応じてハンドラーをクリアすること::

    logging.getLogger("episodic_rag").handlers.clear()

Usage:
    from infrastructure.logging_config import get_logger, log_info, log_warning, log_error

環境変数:
    EPISODIC_RAG_LOG_LEVEL: ログレベル (DEBUG, INFO, WARNING, ERROR)
    EPISODIC_RAG_LOG_FORMAT: ログフォーマット (simple, detailed)
"""

import io
import logging
import os
import sys
from typing import TextIO

__all__ = [
    "get_logger",
    "setup_logging",
    "log_info",
    "log_warning",
    "log_error",
    "log_debug",
]

# =============================================================================
# 定数
# =============================================================================

LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}

# フォーマット定義
FORMAT_SIMPLE = "[%(levelname)s] %(message)s"
FORMAT_DETAILED = "[%(levelname)s] %(name)s: %(message)s"


# =============================================================================
# ロガー設定
# =============================================================================


def get_logger(name: str = "episodic_rag") -> logging.Logger:
    """
    モジュールロガーを取得

    Args:
        name: ロガー名

    Returns:
        設定済みのLoggerインスタンス

    Example:
        >>> logger = get_logger("my_module")
        >>> logger.info("Processing started")
    """
    return logging.getLogger(name)


def _get_log_level_from_env() -> int:
    """環境変数からログレベルを取得"""
    level_name = os.environ.get("EPISODIC_RAG_LOG_LEVEL", "INFO").upper()
    return LOG_LEVELS.get(level_name, logging.INFO)


def _get_log_format_from_env() -> str:
    """環境変数からログフォーマットを取得"""
    format_name = os.environ.get("EPISODIC_RAG_LOG_FORMAT", "simple").lower()
    if format_name == "detailed":
        return FORMAT_DETAILED
    return FORMAT_SIMPLE


def _utf8_safe_stream(stream: TextIO) -> TextIO:
    """
    UTF-8 で書き込める stream を返す（非 UTF-8 コンソール対策）

    Windows の cmd.exe / PowerShell はリダイレクト・パイプ時に既定で
    cp932 (Shift-JIS) を使うため、em-dash「—」(U+2014) 等 cp932 に
    存在しない文字のログ出力が UnicodeEncodeError となり
    "--- Logging error ---" を引き起こす。

    バイナリバッファを持つ stream は UTF-8 の TextIOWrapper で包み直して
    返す（handler-local な差し替えで、sys.stdout 自体は変更しない）。

    - 既に UTF-8 の stream はそのまま返す
    - バッファを持たない stream（StringIO 等）は encode を伴わないため
      そのまま返す
    - StreamHandler.close() は stream を close しないため、包んだ wrapper
      の寿命はプロセスと同じ（close 伝播の副作用なし）

    Args:
        stream: 対象の書き込み先 stream（通常 sys.stdout / sys.stderr）

    Returns:
        UTF-8 で安全に書き込める stream
    """
    encoding = (getattr(stream, "encoding", None) or "").replace("-", "").lower()
    if encoding == "utf8":
        return stream

    buffer = getattr(stream, "buffer", None)
    if buffer is None:
        return stream

    try:
        return io.TextIOWrapper(
            buffer, encoding="utf-8", errors="backslashreplace", line_buffering=True
        )
    except (ValueError, OSError):
        return stream


def setup_logging(level: int | None = None) -> logging.Logger:
    """
    デフォルトのロギング設定をセットアップ

    Args:
        level: ロギングレベル（省略時は環境変数またはINFO）

    Returns:
        設定済みのLoggerインスタンス

    Example:
        >>> import logging
        >>> logger = setup_logging(logging.DEBUG)
        >>> logger.debug("Debug message enabled")
    """
    logger = logging.getLogger("episodic_rag")

    # 既にハンドラーが設定されている場合はスキップ
    if logger.handlers:
        return logger

    # レベルとフォーマットを決定
    if level is None:
        level = _get_log_level_from_env()
    log_format = _get_log_format_from_env()

    # stderrハンドラー（WARNING以上）
    stderr_handler = logging.StreamHandler(_utf8_safe_stream(sys.stderr))
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(logging.Formatter(log_format))

    # stdoutハンドラー（INFO）
    class StdoutFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return record.levelno == logging.INFO

    stdout_handler = logging.StreamHandler(_utf8_safe_stream(sys.stdout))
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.addFilter(StdoutFilter())
    stdout_handler.setFormatter(logging.Formatter(log_format))

    logger.addHandler(stderr_handler)
    logger.addHandler(stdout_handler)
    logger.setLevel(level)

    return logger


# =============================================================================
# ロギング関数（後方互換ラッパー）
# =============================================================================

# デフォルトロガーを初期化
_logger = setup_logging()

# 後方互換性のためのエイリアス
logger = _logger


def log_error(message: str, exit_code: int | None = None) -> None:
    """
    エラーメッセージを出力

    Args:
        message: エラーメッセージ
        exit_code: 指定時はこのコードでプログラムを終了

    Example:
        >>> log_error("File not found")
        >>> log_error("Critical error", exit_code=1)  # プログラム終了
    """
    _logger.error(message)
    if exit_code is not None:
        sys.exit(exit_code)


def log_warning(message: str) -> None:
    """
    警告メッセージを出力

    Args:
        message: 警告メッセージ

    Example:
        >>> log_warning("Deprecated function used")
    """
    _logger.warning(message)


def log_info(message: str) -> None:
    """
    情報メッセージを出力

    Args:
        message: 情報メッセージ

    Example:
        >>> log_info("Processing 10 files")
    """
    _logger.info(message)


def log_debug(message: str) -> None:
    """
    デバッグメッセージを出力

    Args:
        message: デバッグメッセージ

    Example:
        >>> log_debug("Variable x = 42")
    """
    _logger.debug(message)
