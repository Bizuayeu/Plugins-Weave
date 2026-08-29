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
from pathlib import Path

# デフォルトのフォーマット
DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ルートロガー名
ROOT_LOGGER_NAME = "emailingessay"

# ログファイル名（永続化ディレクトリ配下）。
# essay_wait.log とは別物——あれは wait 経路専用として v1.2.3 で定義し直した。
LOG_FILE_NAME = "emailingessay.log"


def _default_log_path() -> str:
    """
    既定のログファイルパス（永続化ディレクトリ配下）を返す。

    Returns:
        永続化ディレクトリ/emailingessay.log

    Raises:
        OSError: 永続化ディレクトリを作れない場合
    """
    # 遅延 import: adapters 側が本モジュールを import するため、
    # モジュール先頭で読むと循環する。
    from adapters.storage.path_resolver import PathResolverAdapter

    return str(Path(PathResolverAdapter().get_persistent_dir()) / LOG_FILE_NAME)


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
            "line": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)


def configure_logging(
    level: int = logging.INFO,
    format_str: str = DEFAULT_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
    json_format: bool | None = None,
    log_file: str | None = None,
) -> None:
    """
    アプリケーション全体のログ設定を行う。

    stdout（対話実行時の可視性）とファイル（定期便は stdout が捨てられるため、
    失敗と試行の唯一の痕跡）の両方へ出す。ファイル出力は既定 ON。

    Args:
        level: ログレベル（default: INFO）
        format_str: ログフォーマット
        date_format: 日時フォーマット
        json_format: JSON形式を使用するか（NoneはESSAY_LOG_JSON環境変数に従う）
        log_file: ログファイルのパス（NoneはESSAY_LOG_FILE環境変数、
            それも無ければ永続化ディレクトリ配下の既定パス）
    """
    # JSON形式の判定（環境変数を参照）
    if json_format is None:
        json_format = os.environ.get("ESSAY_LOG_JSON", "").lower() == "true"

    formatter: logging.Formatter
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(fmt=format_str, datefmt=date_format)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # ルートロガーを設定
    root_logger = logging.getLogger(ROOT_LOGGER_NAME)
    root_logger.setLevel(level)

    # 既存のハンドラーをクリア（重複防止）。閉じてから外す——開いたままのファイル
    # ハンドルを捨てると、再設定のたびにハンドルが漏れる。
    for existing in list(root_logger.handlers):
        existing.close()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # ファイル出力（既定 ON）。ここが失敗しても本業は止めない。
    try:
        path = log_file or os.environ.get("ESSAY_LOG_FILE") or _default_log_path()
        # cc-defer: ローテーション無しの追記（日に数行の量で、根拠のある閾値を
        # 持たないため上限を発明しない）。ファイルが実用上邪魔になる大きさに
        # 育ったら RotatingFileHandler へ昇格する。
        file_handler = logging.FileHandler(path, encoding="utf-8")
    except OSError as e:
        # stdout は生かしたまま続行し、開けなかったことだけ 1 行残す
        root_logger.warning(f"Log file unavailable ({e}); logging to stdout only")
    else:
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    子loggerを取得する。

    Args:
        name: ロガー名（例: 'storage', 'scheduler'）

    Returns:
        emailingessay.{name} のlogger
    """
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")
