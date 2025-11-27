#!/usr/bin/env python3
"""
infrastructure/logging_config.py のユニットテスト
==================================================

ロギング設定とユーティリティ関数の動作を検証。
- setup_logging: ロガーの初期化
- log_info/log_warning/log_error: ログ出力関数
- 環境変数によるカスタマイズ
"""

import logging
import os
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

# 親ディレクトリをパスに追加
sys.path.insert(0, str(__file__).rsplit('test', 1)[0])

from infrastructure.logging_config import (
    FORMAT_DETAILED,
    FORMAT_SIMPLE,
    LOG_LEVELS,
    _get_log_format_from_env,
    _get_log_level_from_env,
    get_logger,
    log_error,
    log_info,
    log_warning,
    setup_logging,
)

# =============================================================================
# get_logger テスト
# =============================================================================


class TestGetLogger:
    """get_logger 関数のテスト"""

    @pytest.mark.unit
    def test_returns_logger_with_default_name(self):
        """デフォルト名でロガーを返す"""
        logger = get_logger()
        assert logger.name == "episodic_rag"

    @pytest.mark.unit
    def test_returns_logger_with_custom_name(self):
        """カスタム名でロガーを返す"""
        logger = get_logger("custom_logger")
        assert logger.name == "custom_logger"

    @pytest.mark.unit
    def test_returns_logger_instance(self):
        """logging.Logger インスタンスを返す"""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)


# =============================================================================
# _get_log_level_from_env テスト
# =============================================================================


class TestGetLogLevelFromEnv:
    """_get_log_level_from_env 関数のテスト"""

    @pytest.mark.unit
    def test_returns_info_by_default(self):
        """環境変数未設定時はINFOを返す"""
        with patch.dict(os.environ, {}, clear=True):
            # 環境変数をクリアしてテスト
            if "EPISODIC_RAG_LOG_LEVEL" in os.environ:
                del os.environ["EPISODIC_RAG_LOG_LEVEL"]
            level = _get_log_level_from_env()
            assert level == logging.INFO

    @pytest.mark.unit
    def test_returns_debug_when_set(self):
        """DEBUG設定時はDEBUGを返す"""
        with patch.dict(os.environ, {"EPISODIC_RAG_LOG_LEVEL": "DEBUG"}):
            level = _get_log_level_from_env()
            assert level == logging.DEBUG

    @pytest.mark.unit
    def test_returns_warning_when_set(self):
        """WARNING設定時はWARNINGを返す"""
        with patch.dict(os.environ, {"EPISODIC_RAG_LOG_LEVEL": "WARNING"}):
            level = _get_log_level_from_env()
            assert level == logging.WARNING

    @pytest.mark.unit
    def test_returns_error_when_set(self):
        """ERROR設定時はERRORを返す"""
        with patch.dict(os.environ, {"EPISODIC_RAG_LOG_LEVEL": "ERROR"}):
            level = _get_log_level_from_env()
            assert level == logging.ERROR

    @pytest.mark.unit
    def test_case_insensitive(self):
        """大文字小文字を区別しない"""
        with patch.dict(os.environ, {"EPISODIC_RAG_LOG_LEVEL": "debug"}):
            level = _get_log_level_from_env()
            assert level == logging.DEBUG

    @pytest.mark.unit
    def test_invalid_level_returns_info(self):
        """無効な値の場合はINFOを返す"""
        with patch.dict(os.environ, {"EPISODIC_RAG_LOG_LEVEL": "INVALID"}):
            level = _get_log_level_from_env()
            assert level == logging.INFO


# =============================================================================
# _get_log_format_from_env テスト
# =============================================================================


class TestGetLogFormatFromEnv:
    """_get_log_format_from_env 関数のテスト"""

    @pytest.mark.unit
    def test_returns_simple_by_default(self):
        """環境変数未設定時はsimpleフォーマットを返す"""
        with patch.dict(os.environ, {}, clear=True):
            if "EPISODIC_RAG_LOG_FORMAT" in os.environ:
                del os.environ["EPISODIC_RAG_LOG_FORMAT"]
            fmt = _get_log_format_from_env()
            assert fmt == FORMAT_SIMPLE

    @pytest.mark.unit
    def test_returns_detailed_when_set(self):
        """detailed設定時はdetailedフォーマットを返す"""
        with patch.dict(os.environ, {"EPISODIC_RAG_LOG_FORMAT": "detailed"}):
            fmt = _get_log_format_from_env()
            assert fmt == FORMAT_DETAILED

    @pytest.mark.unit
    def test_case_insensitive(self):
        """大文字小文字を区別しない"""
        with patch.dict(os.environ, {"EPISODIC_RAG_LOG_FORMAT": "DETAILED"}):
            fmt = _get_log_format_from_env()
            assert fmt == FORMAT_DETAILED

    @pytest.mark.unit
    def test_invalid_format_returns_simple(self):
        """無効な値の場合はsimpleを返す"""
        with patch.dict(os.environ, {"EPISODIC_RAG_LOG_FORMAT": "invalid"}):
            fmt = _get_log_format_from_env()
            assert fmt == FORMAT_SIMPLE


# =============================================================================
# setup_logging テスト
# =============================================================================


class TestSetupLogging:
    """setup_logging 関数のテスト"""

    @pytest.fixture(autouse=True)
    def reset_logger(self):
        """各テスト後にロガーをリセット"""
        yield
        # テスト後にハンドラーをクリア
        logger = logging.getLogger("episodic_rag_test")
        logger.handlers.clear()

    @pytest.mark.unit
    def test_returns_logger(self):
        """Loggerインスタンスを返す"""
        # 新しいロガー名を使用してテスト間の干渉を防ぐ
        with patch("infrastructure.logging_config.logging.getLogger") as mock_get:
            mock_logger = MagicMock(spec=logging.Logger)
            mock_logger.handlers = []
            mock_get.return_value = mock_logger

            result = setup_logging()

            assert result is mock_logger

    @pytest.mark.unit
    def test_accepts_custom_level(self):
        """カスタムレベルを受け付ける"""
        with patch("infrastructure.logging_config.logging.getLogger") as mock_get:
            mock_logger = MagicMock(spec=logging.Logger)
            mock_logger.handlers = []
            mock_get.return_value = mock_logger

            setup_logging(level=logging.DEBUG)

            mock_logger.setLevel.assert_called_with(logging.DEBUG)

    @pytest.mark.unit
    def test_skips_if_handlers_exist(self):
        """既にハンドラーがある場合はスキップ"""
        with patch("infrastructure.logging_config.logging.getLogger") as mock_get:
            mock_logger = MagicMock(spec=logging.Logger)
            mock_logger.handlers = [MagicMock()]  # 既存ハンドラー
            mock_get.return_value = mock_logger

            result = setup_logging()

            # addHandlerが呼ばれていないことを確認
            mock_logger.addHandler.assert_not_called()
            assert result is mock_logger


# =============================================================================
# log_info テスト
# =============================================================================


class TestLogInfo:
    """log_info 関数のテスト"""

    @pytest.mark.unit
    def test_logs_info_message(self, caplog):
        """INFOレベルでメッセージをログ出力"""
        with caplog.at_level(logging.INFO, logger="episodic_rag"):
            log_info("Test info message")

        assert "Test info message" in caplog.text

    @pytest.mark.unit
    def test_accepts_unicode_message(self, caplog):
        """Unicode文字を含むメッセージを受け付ける"""
        with caplog.at_level(logging.INFO, logger="episodic_rag"):
            log_info("テスト情報メッセージ")

        assert "テスト情報メッセージ" in caplog.text


# =============================================================================
# log_warning テスト
# =============================================================================


class TestLogWarning:
    """log_warning 関数のテスト"""

    @pytest.mark.unit
    def test_logs_warning_message(self, caplog):
        """WARNINGレベルでメッセージをログ出力"""
        with caplog.at_level(logging.WARNING, logger="episodic_rag"):
            log_warning("Test warning message")

        assert "Test warning message" in caplog.text

    @pytest.mark.unit
    def test_accepts_unicode_message(self, caplog):
        """Unicode文字を含むメッセージを受け付ける"""
        with caplog.at_level(logging.WARNING, logger="episodic_rag"):
            log_warning("テスト警告メッセージ")

        assert "テスト警告メッセージ" in caplog.text


# =============================================================================
# log_error テスト
# =============================================================================


class TestLogError:
    """log_error 関数のテスト"""

    @pytest.mark.unit
    def test_logs_error_message(self, caplog):
        """ERRORレベルでメッセージをログ出力"""
        with caplog.at_level(logging.ERROR, logger="episodic_rag"):
            log_error("Test error message")

        assert "Test error message" in caplog.text

    @pytest.mark.unit
    def test_accepts_unicode_message(self, caplog):
        """Unicode文字を含むメッセージを受け付ける"""
        with caplog.at_level(logging.ERROR, logger="episodic_rag"):
            log_error("テストエラーメッセージ")

        assert "テストエラーメッセージ" in caplog.text

    @pytest.mark.unit
    def test_exits_when_exit_code_provided(self):
        """exit_code指定時はプログラムを終了"""
        with pytest.raises(SystemExit) as exc_info:
            log_error("Fatal error", exit_code=1)

        assert exc_info.value.code == 1

    @pytest.mark.unit
    def test_does_not_exit_without_exit_code(self, caplog):
        """exit_code未指定時は終了しない"""
        with caplog.at_level(logging.ERROR, logger="episodic_rag"):
            log_error("Non-fatal error")  # Should not raise

        assert "Non-fatal error" in caplog.text


# =============================================================================
# LOG_LEVELS 定数テスト
# =============================================================================


class TestLogLevelsConstant:
    """LOG_LEVELS 定数のテスト"""

    @pytest.mark.unit
    def test_contains_standard_levels(self):
        """標準ログレベルを含む"""
        assert "DEBUG" in LOG_LEVELS
        assert "INFO" in LOG_LEVELS
        assert "WARNING" in LOG_LEVELS
        assert "ERROR" in LOG_LEVELS

    @pytest.mark.unit
    def test_maps_to_logging_constants(self):
        """logging モジュールの定数にマップされる"""
        assert LOG_LEVELS["DEBUG"] == logging.DEBUG
        assert LOG_LEVELS["INFO"] == logging.INFO
        assert LOG_LEVELS["WARNING"] == logging.WARNING
        assert LOG_LEVELS["ERROR"] == logging.ERROR
