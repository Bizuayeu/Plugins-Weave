# frameworks/logging_config.py
"""
ロギング設定モジュール

アプリケーション全体のログ設定を管理する。
"""
from __future__ import annotations

import logging
import sys


# デフォルトのフォーマット
DEFAULT_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# ルートロガー名
ROOT_LOGGER_NAME = 'emailingessay'


def configure_logging(
    level: int = logging.INFO,
    format_str: str = DEFAULT_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT
) -> None:
    """
    アプリケーション全体のログ設定を行う。

    Args:
        level: ログレベル（default: INFO）
        format_str: ログフォーマット
        date_format: 日時フォーマット
    """
    formatter = logging.Formatter(fmt=format_str, datefmt=date_format)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # ルートロガーを設定
    root_logger = logging.getLogger(ROOT_LOGGER_NAME)
    root_logger.setLevel(level)

    # 既存のハンドラーをクリア（重複防止）
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """
    子loggerを取得する。

    Args:
        name: ロガー名（例: 'storage', 'scheduler'）

    Returns:
        emailingessay.{name} のlogger
    """
    return logging.getLogger(f'{ROOT_LOGGER_NAME}.{name}')
