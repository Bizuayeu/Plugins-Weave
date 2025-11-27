#!/usr/bin/env python3
"""
Logging Configuration
=====================

ロギング設定とユーティリティ関数を提供するインフラストラクチャ層。

Usage:
    from infrastructure.logging_config import get_logger, log_info, log_warning, log_error

環境変数:
    EPISODIC_RAG_LOG_LEVEL: ログレベル (DEBUG, INFO, WARNING, ERROR)
    EPISODIC_RAG_LOG_FORMAT: ログフォーマット (simple, detailed)
"""

import logging
import os
import sys
from typing import Optional

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


def setup_logging(level: Optional[int] = None) -> logging.Logger:
    """
    デフォルトのロギング設定をセットアップ

    Args:
        level: ロギングレベル（省略時は環境変数またはINFO）

    Returns:
        設定済みのLoggerインスタンス
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
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(logging.Formatter(log_format))

    # stdoutハンドラー（INFO）
    class StdoutFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return record.levelno == logging.INFO

    stdout_handler = logging.StreamHandler(sys.stdout)
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


def log_error(message: str, exit_code: Optional[int] = None) -> None:
    """
    エラーメッセージを出力

    Args:
        message: エラーメッセージ
        exit_code: 指定時はこのコードでプログラムを終了
    """
    _logger.error(message)
    if exit_code is not None:
        sys.exit(exit_code)


def log_warning(message: str) -> None:
    """
    警告メッセージを出力

    Args:
        message: 警告メッセージ
    """
    _logger.warning(message)


def log_info(message: str) -> None:
    """
    情報メッセージを出力

    Args:
        message: 情報メッセージ
    """
    _logger.info(message)
