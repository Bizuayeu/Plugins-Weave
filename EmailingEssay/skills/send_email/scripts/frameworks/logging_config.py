# frameworks/logging_config.py
"""
ロギング設定モジュール

アプリケーション全体のログ設定を管理する。
JSON形式の構造化ロギングをオプションでサポート。
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime


# デフォルトのフォーマット
DEFAULT_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# ルートロガー名
ROOT_LOGGER_NAME = 'emailingessay'


class JsonFormatter(logging.Formatter):
    """
    JSON形式でログを出力するフォーマッタ。

    構造化ログ分析ツールとの連携を容易にする。
    環境変数 ESSAY_LOG_JSON=true で有効化される。
    """

    def format(self, record: logging.LogRecord) -> str:
        """ログレコードをJSON形式に変換する"""
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)


def configure_logging(
    level: int = logging.INFO,
    format_str: str = DEFAULT_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
    json_format: bool | None = None
) -> None:
    """
    アプリケーション全体のログ設定を行う。

    Args:
        level: ログレベル（default: INFO）
        format_str: ログフォーマット
        date_format: 日時フォーマット
        json_format: JSON形式を使用するか（NoneはESSAY_LOG_JSON環境変数に従う）
    """
    # JSON形式の判定（環境変数を参照）
    if json_format is None:
        json_format = os.environ.get("ESSAY_LOG_JSON", "").lower() == "true"

    if json_format:
        formatter = JsonFormatter()
    else:
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
