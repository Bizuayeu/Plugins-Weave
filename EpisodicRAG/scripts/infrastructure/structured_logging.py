#!/usr/bin/env python3
"""
Structured Logging
==================

構造化されたロギングユーティリティ。
LOG_PREFIX_* 定数を使用したボイラープレートを統合し、
一貫したログ出力を提供。

Usage:
    from infrastructure.structured_logging import get_structured_logger

    logger = get_structured_logger(__name__)
    logger.state("cascade_update", level="weekly", count=5)
    # -> [DEBUG] [STATE] cascade_update: level=weekly count=5
"""

from typing import Any, Protocol

from domain.constants import (
    LOG_PREFIX_DECISION,
    LOG_PREFIX_FILE,
    LOG_PREFIX_STATE,
    LOG_PREFIX_VALIDATE,
)
from infrastructure.logging_config import log_debug


class StructuredLoggerProtocol(Protocol):
    """構造化ロガーのプロトコル"""

    def info(self, message: str) -> None:
        """一般的な情報ログ"""
        ...

    def state(self, message: str, **context: Any) -> None:
        """状態変化のログ"""
        ...

    def file_op(self, message: str, **context: Any) -> None:
        """ファイル操作のログ"""
        ...

    def validation(self, message: str, **context: Any) -> None:
        """検証処理のログ"""
        ...

    def decision(self, message: str, **context: Any) -> None:
        """判断分岐のログ"""
        ...


class StructuredLogger:
    """
    構造化されたロギングを提供するクラス

    LOG_PREFIX_* 定数を使用したボイラープレートを統合し、
    一貫したフォーマットでログを出力する。

    従来のコード:
        log_debug(f"{LOG_PREFIX_STATE} cascade_update: level={level}, count={count}")

    新しいコード:
        logger.state("cascade_update", level=level, count=count)
    """

    def __init__(self, name: str):
        """
        初期化

        Args:
            name: ロガー名（通常は __name__ を渡す）
        """
        self._name = name

    def _format_context(self, context: dict[str, Any]) -> str:
        """
        コンテキスト辞書をログ文字列にフォーマット

        Args:
            context: key=value ペアの辞書

        Returns:
            "key1=value1 key2=value2" 形式の文字列
        """
        if not context:
            return ""
        return " ".join(f"{k}={v}" for k, v in context.items())

    def _log(self, prefix: str, message: str, **context: Any) -> None:
        """
        プレフィックス付きでログを出力

        Args:
            prefix: LOG_PREFIX_* 定数
            message: ログメッセージ
            **context: 追加のコンテキスト情報
        """
        ctx_str = self._format_context(context)
        if ctx_str:
            log_debug(f"{prefix} {message}: {ctx_str}")
        else:
            log_debug(f"{prefix} {message}")

    def info(self, message: str) -> None:
        """
        一般的な情報ログを出力

        Args:
            message: ログメッセージ

        Example:
            logger.info("Processing started")
            # -> [DEBUG] Processing started
        """
        log_debug(message)

    def state(self, message: str, **context: Any) -> None:
        """
        状態変化のログを出力

        Args:
            message: ログメッセージ
            **context: 追加のコンテキスト情報

        Example:
            logger.state("cascade_update", level="weekly", count=5)
            # -> [DEBUG] [STATE] cascade_update: level=weekly count=5
        """
        self._log(LOG_PREFIX_STATE, message, **context)

    def file_op(self, message: str, **context: Any) -> None:
        """
        ファイル操作のログを出力

        Args:
            message: ログメッセージ
            **context: 追加のコンテキスト情報

        Example:
            logger.file_op("new_files", count=3, names=["a.txt", "b.txt"])
            # -> [DEBUG] [FILE] new_files: count=3 names=['a.txt', 'b.txt']
        """
        self._log(LOG_PREFIX_FILE, message, **context)

    def validation(self, message: str, **context: Any) -> None:
        """
        検証処理のログを出力

        Args:
            message: ログメッセージ
            **context: 追加のコンテキスト情報

        Example:
            logger.validation("overall_digest", is_valid=True)
            # -> [DEBUG] [VALIDATE] overall_digest: is_valid=True
        """
        self._log(LOG_PREFIX_VALIDATE, message, **context)

    def decision(self, message: str, **context: Any) -> None:
        """
        判断分岐のログを出力

        Args:
            message: ログメッセージ
            **context: 追加のコンテキスト情報

        Example:
            logger.decision("next_level", level="monthly")
            # -> [DEBUG] [DECISION] next_level: level=monthly
        """
        self._log(LOG_PREFIX_DECISION, message, **context)


def get_structured_logger(name: str) -> StructuredLogger:
    """
    構造化ロガーのインスタンスを取得

    Args:
        name: ロガー名（通常は __name__ を渡す）

    Returns:
        StructuredLogger インスタンス

    Example:
        logger = get_structured_logger(__name__)
        logger.state("processing", item="test")
    """
    return StructuredLogger(name)
