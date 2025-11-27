#!/usr/bin/env python3
"""
Logging Configuration
=====================

ロギング設定とユーティリティ関数を提供するインフラストラクチャ層。

Usage:
    from infrastructure.logging_config import get_logger, log_info, log_warning, log_error
"""
import logging
import sys
from typing import Optional


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


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    デフォルトのロギング設定をセットアップ

    Args:
        level: ロギングレベル

    Returns:
        設定済みのLoggerインスタンス
    """
    logger = logging.getLogger("episodic_rag")

    # 既にハンドラーが設定されている場合はスキップ
    if logger.handlers:
        return logger

    # stderrハンドラー（WARNING以上）
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

    # stdoutハンドラー（INFO）
    class StdoutFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return record.levelno == logging.INFO

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.addFilter(StdoutFilter())
    stdout_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

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
