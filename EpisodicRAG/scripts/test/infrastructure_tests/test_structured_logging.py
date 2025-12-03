#!/usr/bin/env python3
"""
Structured Logging Tests
========================

infrastructure/structured_logging.py のテスト

- StructuredLogger クラスの初期化と各メソッド
- _format_context ヘルパー
- get_structured_logger ファクトリ関数
"""

import logging

import pytest

from domain.constants import (
    LOG_PREFIX_DECISION,
    LOG_PREFIX_FILE,
    LOG_PREFIX_STATE,
    LOG_PREFIX_VALIDATE,
)
from infrastructure.structured_logging import StructuredLogger, get_structured_logger

# =============================================================================
# TestStructuredLoggerInit - 初期化テスト
# =============================================================================


class TestStructuredLoggerInit:
    """StructuredLogger 初期化テスト"""

    @pytest.mark.unit
    def test_init_with_name(self) -> None:
        """名前を渡して初期化できる"""
        logger = StructuredLogger("test_module")
        assert logger._name == "test_module"

    @pytest.mark.unit
    def test_init_stores_name(self) -> None:
        """名前が保持される"""
        logger = StructuredLogger("my.custom.logger")
        assert logger._name == "my.custom.logger"

    @pytest.mark.unit
    def test_init_with_empty_name(self) -> None:
        """空文字でも初期化できる"""
        logger = StructuredLogger("")
        assert logger._name == ""

    @pytest.mark.unit
    def test_init_with_dunder_name(self) -> None:
        """__name__ 形式の名前を受け付ける"""
        logger = StructuredLogger(__name__)
        assert logger._name == __name__


# =============================================================================
# TestStructuredLoggerFormatContext - コンテキストフォーマットテスト
# =============================================================================


class TestStructuredLoggerFormatContext:
    """_format_context メソッドテスト"""

    @pytest.fixture
    def logger(self) -> StructuredLogger:
        """テスト用ロガーインスタンス"""
        return StructuredLogger("test")

    @pytest.mark.unit
    def test_format_context_empty(self, logger: StructuredLogger) -> None:
        """空dictで空文字列を返す"""
        result = logger._format_context({})
        assert result == ""

    @pytest.mark.unit
    def test_format_context_single_key(self, logger: StructuredLogger) -> None:
        """1つのkey=valueをフォーマット"""
        result = logger._format_context({"level": "weekly"})
        assert result == "level=weekly"

    @pytest.mark.unit
    def test_format_context_multiple_keys(self, logger: StructuredLogger) -> None:
        """複数のkey=valueをフォーマット"""
        result = logger._format_context({"level": "weekly", "count": 5})
        # 順序は保証されないがkey=valueペアが含まれる
        assert "level=weekly" in result
        assert "count=5" in result
        assert " " in result  # スペース区切り

    @pytest.mark.unit
    def test_format_context_with_none_value(self, logger: StructuredLogger) -> None:
        """None値を含むコンテキスト"""
        result = logger._format_context({"value": None})
        assert result == "value=None"

    @pytest.mark.unit
    def test_format_context_with_list_value(self, logger: StructuredLogger) -> None:
        """リスト値を含むコンテキスト"""
        result = logger._format_context({"files": ["a.txt", "b.txt"]})
        assert "files=" in result
        assert "a.txt" in result
        assert "b.txt" in result

    @pytest.mark.unit
    def test_format_context_with_dict_value(self, logger: StructuredLogger) -> None:
        """dict値を含むコンテキスト"""
        result = logger._format_context({"data": {"key": "value"}})
        assert "data=" in result
        assert "key" in result

    @pytest.mark.unit
    def test_format_context_unicode(self, logger: StructuredLogger) -> None:
        """Unicode文字を含むコンテキスト"""
        result = logger._format_context({"message": "テスト"})
        assert "message=テスト" in result

    @pytest.mark.unit
    def test_format_context_with_int_value(self, logger: StructuredLogger) -> None:
        """整数値を含むコンテキスト"""
        result = logger._format_context({"count": 42})
        assert result == "count=42"

    @pytest.mark.unit
    def test_format_context_with_bool_value(self, logger: StructuredLogger) -> None:
        """bool値を含むコンテキスト"""
        result = logger._format_context({"is_valid": True})
        assert result == "is_valid=True"


# =============================================================================
# TestStructuredLoggerState - state メソッドテスト
# =============================================================================


class TestStructuredLoggerState:
    """state メソッドテスト"""

    @pytest.fixture
    def logger(self) -> StructuredLogger:
        """テスト用ロガーインスタンス"""
        return StructuredLogger("test")

    @pytest.mark.unit
    def test_state_message_only(self, logger: StructuredLogger, caplog: pytest.LogCaptureFixture) -> None:
        """メッセージのみの状態ログ"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            logger.state("cascade_update")

        assert LOG_PREFIX_STATE in caplog.text
        assert "cascade_update" in caplog.text

    @pytest.mark.unit
    def test_state_with_context(self, logger: StructuredLogger, caplog: pytest.LogCaptureFixture) -> None:
        """コンテキスト付きの状態ログ"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            logger.state("cascade_update", level="weekly", count=5)

        assert LOG_PREFIX_STATE in caplog.text
        assert "cascade_update" in caplog.text
        assert "level=weekly" in caplog.text
        assert "count=5" in caplog.text

    @pytest.mark.unit
    def test_state_prefix_format(self, logger: StructuredLogger, caplog: pytest.LogCaptureFixture) -> None:
        """[STATE]プレフィックスが正しくフォーマットされる"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            logger.state("test_message")

        assert "[STATE]" in caplog.text


# =============================================================================
# TestStructuredLoggerFileOp - file_op メソッドテスト
# =============================================================================


class TestStructuredLoggerFileOp:
    """file_op メソッドテスト"""

    @pytest.fixture
    def logger(self) -> StructuredLogger:
        """テスト用ロガーインスタンス"""
        return StructuredLogger("test")

    @pytest.mark.unit
    def test_file_op_message_only(self, logger: StructuredLogger, caplog: pytest.LogCaptureFixture) -> None:
        """メッセージのみのファイル操作ログ"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            logger.file_op("new_files")

        assert LOG_PREFIX_FILE in caplog.text
        assert "new_files" in caplog.text

    @pytest.mark.unit
    def test_file_op_with_context(self, logger: StructuredLogger, caplog: pytest.LogCaptureFixture) -> None:
        """コンテキスト付きのファイル操作ログ"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            logger.file_op("new_files", count=3, path="/tmp")

        assert LOG_PREFIX_FILE in caplog.text
        assert "new_files" in caplog.text
        assert "count=3" in caplog.text
        assert "path=/tmp" in caplog.text

    @pytest.mark.unit
    def test_file_op_prefix_format(self, logger: StructuredLogger, caplog: pytest.LogCaptureFixture) -> None:
        """[FILE]プレフィックスが正しくフォーマットされる"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            logger.file_op("test_operation")

        assert "[FILE]" in caplog.text


# =============================================================================
# TestStructuredLoggerValidation - validation メソッドテスト
# =============================================================================


class TestStructuredLoggerValidation:
    """validation メソッドテスト"""

    @pytest.fixture
    def logger(self) -> StructuredLogger:
        """テスト用ロガーインスタンス"""
        return StructuredLogger("test")

    @pytest.mark.unit
    def test_validation_message_only(self, logger: StructuredLogger, caplog: pytest.LogCaptureFixture) -> None:
        """メッセージのみの検証ログ"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            logger.validation("overall_digest")

        assert LOG_PREFIX_VALIDATE in caplog.text
        assert "overall_digest" in caplog.text

    @pytest.mark.unit
    def test_validation_with_context(self, logger: StructuredLogger, caplog: pytest.LogCaptureFixture) -> None:
        """コンテキスト付きの検証ログ"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            logger.validation("overall_digest", is_valid=True)

        assert LOG_PREFIX_VALIDATE in caplog.text
        assert "overall_digest" in caplog.text
        assert "is_valid=True" in caplog.text

    @pytest.mark.unit
    def test_validation_prefix_format(self, logger: StructuredLogger, caplog: pytest.LogCaptureFixture) -> None:
        """[VALIDATE]プレフィックスが正しくフォーマットされる"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            logger.validation("test_validation")

        assert "[VALIDATE]" in caplog.text


# =============================================================================
# TestStructuredLoggerDecision - decision メソッドテスト
# =============================================================================


class TestStructuredLoggerDecision:
    """decision メソッドテスト"""

    @pytest.fixture
    def logger(self) -> StructuredLogger:
        """テスト用ロガーインスタンス"""
        return StructuredLogger("test")

    @pytest.mark.unit
    def test_decision_message_only(self, logger: StructuredLogger, caplog: pytest.LogCaptureFixture) -> None:
        """メッセージのみの判断ログ"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            logger.decision("next_level")

        assert LOG_PREFIX_DECISION in caplog.text
        assert "next_level" in caplog.text

    @pytest.mark.unit
    def test_decision_with_context(self, logger: StructuredLogger, caplog: pytest.LogCaptureFixture) -> None:
        """コンテキスト付きの判断ログ"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            logger.decision("next_level", level="monthly")

        assert LOG_PREFIX_DECISION in caplog.text
        assert "next_level" in caplog.text
        assert "level=monthly" in caplog.text

    @pytest.mark.unit
    def test_decision_prefix_format(self, logger: StructuredLogger, caplog: pytest.LogCaptureFixture) -> None:
        """[DECISION]プレフィックスが正しくフォーマットされる"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            logger.decision("test_decision")

        assert "[DECISION]" in caplog.text


# =============================================================================
# TestGetStructuredLogger - ファクトリ関数テスト
# =============================================================================


class TestGetStructuredLogger:
    """get_structured_logger ファクトリ関数テスト"""

    @pytest.mark.unit
    def test_returns_structured_logger(self) -> None:
        """StructuredLoggerインスタンスを返す"""
        logger = get_structured_logger("test")
        assert isinstance(logger, StructuredLogger)

    @pytest.mark.unit
    def test_returns_new_instance_each_call(self) -> None:
        """呼び出しごとに新しいインスタンスを返す"""
        logger1 = get_structured_logger("test")
        logger2 = get_structured_logger("test")
        assert logger1 is not logger2

    @pytest.mark.unit
    def test_passes_name_correctly(self) -> None:
        """名前が正しく渡される"""
        logger = get_structured_logger("my.module.name")
        assert logger._name == "my.module.name"

    @pytest.mark.unit
    def test_accepts_dunder_name(self) -> None:
        """__name__ を受け付ける"""
        logger = get_structured_logger(__name__)
        assert logger._name == __name__


# =============================================================================
# TestStructuredLoggerIntegration - 統合テスト
# =============================================================================


class TestStructuredLoggerIntegration:
    """構造化ロガーの統合テスト"""

    @pytest.mark.unit
    def test_multiple_log_methods_in_sequence(self, caplog: pytest.LogCaptureFixture) -> None:
        """複数のログメソッドを順次呼び出し"""
        logger = get_structured_logger("integration_test")

        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            logger.state("starting", phase="init")
            logger.file_op("reading", file="test.txt")
            logger.validation("checking", is_valid=True)
            logger.decision("proceeding", reason="valid")

        assert "[STATE]" in caplog.text
        assert "[FILE]" in caplog.text
        assert "[VALIDATE]" in caplog.text
        assert "[DECISION]" in caplog.text

    @pytest.mark.unit
    def test_log_not_shown_at_info_level(self, caplog: pytest.LogCaptureFixture) -> None:
        """INFOレベルではDEBUGログは表示されない"""
        logger = get_structured_logger("test")

        with caplog.at_level(logging.INFO, logger="episodic_rag"):
            logger.state("should_not_appear")

        assert "should_not_appear" not in caplog.text
