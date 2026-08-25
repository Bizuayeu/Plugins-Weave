#!/usr/bin/env python3
"""
infrastructure/logging_config.py のユニットテスト
==================================================

ロギング設定とユーティリティ関数の動作を検証。
- setup_logging: ロガーの初期化
- log_info/log_warning/log_error: ログ出力関数
- 環境変数によるカスタマイズ
"""

import io
import logging
import os
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from infrastructure.logging_config import (
    FORMAT_DETAILED,
    FORMAT_SIMPLE,
    LOG_LEVELS,
    _get_log_format_from_env,
    _get_log_level_from_env,
    get_logger,
    log_debug,
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
    def test_returns_logger_with_default_name(self) -> None:
        """デフォルト名でロガーを返す"""
        logger = get_logger()
        assert logger.name == "episodic_rag"

    @pytest.mark.unit
    def test_returns_logger_with_custom_name(self) -> None:
        """カスタム名でロガーを返す"""
        logger = get_logger("custom_logger")
        assert logger.name == "custom_logger"

    @pytest.mark.unit
    def test_returns_logger_instance(self) -> None:
        """logging.Logger インスタンスを返す"""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)


# =============================================================================
# _get_log_level_from_env テスト
# =============================================================================


class TestGetLogLevelFromEnv:
    """_get_log_level_from_env 関数のテスト"""

    @pytest.mark.unit
    def test_returns_info_by_default(self) -> None:
        """環境変数未設定時はINFOを返す"""
        with patch.dict(os.environ, {}, clear=True):
            # 環境変数をクリアしてテスト
            if "EPISODIC_RAG_LOG_LEVEL" in os.environ:
                del os.environ["EPISODIC_RAG_LOG_LEVEL"]
            level = _get_log_level_from_env()
            assert level == logging.INFO

    @pytest.mark.unit
    def test_returns_debug_when_set(self) -> None:
        """DEBUG設定時はDEBUGを返す"""
        with patch.dict(os.environ, {"EPISODIC_RAG_LOG_LEVEL": "DEBUG"}):
            level = _get_log_level_from_env()
            assert level == logging.DEBUG

    @pytest.mark.unit
    def test_returns_warning_when_set(self) -> None:
        """WARNING設定時はWARNINGを返す"""
        with patch.dict(os.environ, {"EPISODIC_RAG_LOG_LEVEL": "WARNING"}):
            level = _get_log_level_from_env()
            assert level == logging.WARNING

    @pytest.mark.unit
    def test_returns_error_when_set(self) -> None:
        """ERROR設定時はERRORを返す"""
        with patch.dict(os.environ, {"EPISODIC_RAG_LOG_LEVEL": "ERROR"}):
            level = _get_log_level_from_env()
            assert level == logging.ERROR

    @pytest.mark.unit
    def test_case_insensitive(self) -> None:
        """大文字小文字を区別しない"""
        with patch.dict(os.environ, {"EPISODIC_RAG_LOG_LEVEL": "debug"}):
            level = _get_log_level_from_env()
            assert level == logging.DEBUG

    @pytest.mark.unit
    def test_invalid_level_returns_info(self) -> None:
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
    def test_returns_simple_by_default(self) -> None:
        """環境変数未設定時はsimpleフォーマットを返す"""
        with patch.dict(os.environ, {}, clear=True):
            if "EPISODIC_RAG_LOG_FORMAT" in os.environ:
                del os.environ["EPISODIC_RAG_LOG_FORMAT"]
            fmt = _get_log_format_from_env()
            assert fmt == FORMAT_SIMPLE

    @pytest.mark.unit
    def test_returns_detailed_when_set(self) -> None:
        """detailed設定時はdetailedフォーマットを返す"""
        with patch.dict(os.environ, {"EPISODIC_RAG_LOG_FORMAT": "detailed"}):
            fmt = _get_log_format_from_env()
            assert fmt == FORMAT_DETAILED

    @pytest.mark.unit
    def test_case_insensitive(self) -> None:
        """大文字小文字を区別しない"""
        with patch.dict(os.environ, {"EPISODIC_RAG_LOG_FORMAT": "DETAILED"}):
            fmt = _get_log_format_from_env()
            assert fmt == FORMAT_DETAILED

    @pytest.mark.unit
    def test_invalid_format_returns_simple(self) -> None:
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
    def reset_logger(self) -> None:
        """各テスト後にロガーをリセット"""
        yield
        # テスト後にハンドラーをクリア
        logger = logging.getLogger("episodic_rag_test")
        logger.handlers.clear()

    @pytest.mark.unit
    def test_returns_logger(self) -> None:
        """Loggerインスタンスを返す"""
        # 新しいロガー名を使用してテスト間の干渉を防ぐ
        with patch("infrastructure.logging_config.logging.getLogger") as mock_get:
            mock_logger = MagicMock(spec=logging.Logger)
            mock_logger.handlers = []
            mock_get.return_value = mock_logger

            result = setup_logging()

            assert result is mock_logger

    @pytest.mark.unit
    def test_accepts_custom_level(self) -> None:
        """カスタムレベルを受け付ける"""
        with patch("infrastructure.logging_config.logging.getLogger") as mock_get:
            mock_logger = MagicMock(spec=logging.Logger)
            mock_logger.handlers = []
            mock_get.return_value = mock_logger

            setup_logging(level=logging.DEBUG)

            mock_logger.setLevel.assert_called_with(logging.DEBUG)

    @pytest.mark.unit
    def test_skips_if_handlers_exist(self) -> None:
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
    def test_logs_info_message(self, caplog: pytest.LogCaptureFixture) -> None:
        """INFOレベルでメッセージをログ出力"""
        with caplog.at_level(logging.INFO, logger="episodic_rag"):
            log_info("Test info message")

        assert "Test info message" in caplog.text

    @pytest.mark.unit
    def test_accepts_unicode_message(self, caplog: pytest.LogCaptureFixture) -> None:
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
    def test_logs_warning_message(self, caplog: pytest.LogCaptureFixture) -> None:
        """WARNINGレベルでメッセージをログ出力"""
        with caplog.at_level(logging.WARNING, logger="episodic_rag"):
            log_warning("Test warning message")

        assert "Test warning message" in caplog.text

    @pytest.mark.unit
    def test_accepts_unicode_message(self, caplog: pytest.LogCaptureFixture) -> None:
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
    def test_logs_error_message(self, caplog: pytest.LogCaptureFixture) -> None:
        """ERRORレベルでメッセージをログ出力"""
        with caplog.at_level(logging.ERROR, logger="episodic_rag"):
            log_error("Test error message")

        assert "Test error message" in caplog.text

    @pytest.mark.unit
    def test_accepts_unicode_message(self, caplog: pytest.LogCaptureFixture) -> None:
        """Unicode文字を含むメッセージを受け付ける"""
        with caplog.at_level(logging.ERROR, logger="episodic_rag"):
            log_error("テストエラーメッセージ")

        assert "テストエラーメッセージ" in caplog.text

    @pytest.mark.unit
    def test_exits_when_exit_code_provided(self) -> None:
        """exit_code指定時はプログラムを終了"""
        with pytest.raises(SystemExit) as exc_info:
            log_error("Fatal error", exit_code=1)

        assert exc_info.value.code == 1

    @pytest.mark.unit
    def test_does_not_exit_without_exit_code(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
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
    def test_contains_standard_levels(self) -> None:
        """標準ログレベルを含む"""
        assert "DEBUG" in LOG_LEVELS
        assert "INFO" in LOG_LEVELS
        assert "WARNING" in LOG_LEVELS
        assert "ERROR" in LOG_LEVELS

    @pytest.mark.unit
    def test_maps_to_logging_constants(self) -> None:
        """logging モジュールの定数にマップされる"""
        assert LOG_LEVELS["DEBUG"] == logging.DEBUG
        assert LOG_LEVELS["INFO"] == logging.INFO
        assert LOG_LEVELS["WARNING"] == logging.WARNING
        assert LOG_LEVELS["ERROR"] == logging.ERROR


# =============================================================================
# log_debug テスト
# =============================================================================


class TestLogDebug:
    """log_debug 関数のテスト"""

    @pytest.mark.unit
    def test_logs_debug_message(self, caplog: pytest.LogCaptureFixture) -> None:
        """DEBUGレベルでメッセージをログ出力"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            log_debug("Test debug message")

        assert "Test debug message" in caplog.text

    @pytest.mark.unit
    def test_accepts_unicode_message(self, caplog: pytest.LogCaptureFixture) -> None:
        """Unicode文字を含むメッセージを受け付ける"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            log_debug("テストデバッグメッセージ 🐛")

        assert "テストデバッグメッセージ" in caplog.text

    @pytest.mark.unit
    def test_not_shown_at_info_level(self, caplog: pytest.LogCaptureFixture) -> None:
        """INFOレベルでは表示されない"""
        with caplog.at_level(logging.INFO, logger="episodic_rag"):
            log_debug("Should not appear")

        assert "Should not appear" not in caplog.text


# =============================================================================
# Handler エンコーディング安全性テスト（Windows cp932 対応）
# =============================================================================


class TestHandlerEncodingSafety:
    """cp932 コンソールでも UnicodeEncodeError を出さない handler 構成の検証

    Windows の cmd.exe / PowerShell は既定で cp932 (Shift-JIS) を使う。
    digest_type に頻出する em-dash「——」(U+2014) は cp932 にマップが存在せず、
    StreamHandler.emit → stream.write で UnicodeEncodeError となり
    "--- Logging error ---" を吐く（finalize カスケードで実観測されたバグ）。

    caplog は pytest の capture handler 経由で stream encoding を通らないため、
    このバグを検出できない。実 stream（cp932 の TextIOWrapper）を handler に
    踏ませて検証する。
    """

    EMDASH_MESSAGE = "digest_type: 知性安価化・装置化・基質依存——五段降下"

    @pytest.fixture(autouse=True)
    def restore_episodic_logger(self):
        """テスト後に episodic_rag ロガーの handler/propagate を復元する

        注意: sys.stdout/stderr の差し替えは fixture では行わない。
        pytest の capture マネージャが fixture→call のフェーズ境界で
        sys.stdout を自分の capture オブジェクトへ再代入するため、
        fixture 内で差した疑似コンソールは call フェーズで失われる。
        差し替えは各テスト本体（call フェーズ）で行うこと。
        """
        logger = logging.getLogger("episodic_rag")
        saved_handlers = logger.handlers[:]
        saved_propagate = logger.propagate
        yield
        logger.handlers.clear()
        logger.handlers.extend(saved_handlers)
        logger.propagate = saved_propagate

    def _make_console(
        self, monkeypatch: pytest.MonkeyPatch, encoding: str
    ) -> "tuple[io.BytesIO, io.BytesIO]":
        """指定エンコーディングの疑似コンソールを sys.stdout/stderr に差す

        call フェーズ内から呼ぶこと（restore_episodic_logger の注意を参照）。
        """
        logging.getLogger("episodic_rag").handlers.clear()
        out_buf = io.BytesIO()
        err_buf = io.BytesIO()
        fake_out = io.TextIOWrapper(out_buf, encoding=encoding, line_buffering=True)
        fake_err = io.TextIOWrapper(err_buf, encoding=encoding, line_buffering=True)
        monkeypatch.setattr(sys, "stdout", fake_out)
        monkeypatch.setattr(sys, "stderr", fake_err)
        return out_buf, err_buf

    def _emit_and_collect_errors(self, message: str, level: int = logging.INFO) -> list:
        """setup_logging → 1メッセージ emit し、handleError 呼び出しを収集"""
        logger = setup_logging()
        logger.propagate = False  # caplog への波及を止め、実 handler だけを通す
        errors: list = []
        for h in logger.handlers:
            h.handleError = lambda record, _h=h: errors.append(type(_h).__name__)  # type: ignore[method-assign]
        logger.log(level, message)
        for h in logger.handlers:
            h.flush()
        return errors

    @pytest.mark.unit
    def test_emdash_info_does_not_hit_handle_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """em-dash を含む INFO ログが UnicodeEncodeError を起こさない"""
        self._make_console(monkeypatch, "cp932")
        errors = self._emit_and_collect_errors(self.EMDASH_MESSAGE)
        assert errors == [], f"handler がエンコード失敗を報告: {errors}"

    @pytest.mark.unit
    def test_emdash_warning_does_not_hit_handle_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """em-dash を含む WARNING ログ（stderr handler）も安全"""
        self._make_console(monkeypatch, "cp932")
        errors = self._emit_and_collect_errors(
            self.EMDASH_MESSAGE, level=logging.WARNING
        )
        assert errors == [], f"handler がエンコード失敗を報告: {errors}"

    @pytest.mark.unit
    def test_emdash_message_content_reaches_stdout(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """メッセージ本体が失われず stdout 側バッファへ到達する"""
        out_buf, _ = self._make_console(monkeypatch, "cp932")
        self._emit_and_collect_errors(self.EMDASH_MESSAGE)
        written = out_buf.getvalue().decode("utf-8", errors="replace")
        assert "五段降下" in written, f"メッセージが書き込まれていない: {written!r}"

    @pytest.mark.unit
    def test_ascii_format_unchanged(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """従来の ASCII ログ書式（[INFO] ...）が不変（リグレッションガード）"""
        out_buf, _ = self._make_console(monkeypatch, "cp932")
        self._emit_and_collect_errors("plain ascii message")
        written = out_buf.getvalue().decode("utf-8", errors="replace")
        assert "[INFO] plain ascii message" in written

    @pytest.mark.unit
    def test_stringio_stream_still_works(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """buffer を持たない stream（StringIO 等）でも setup_logging が壊れない"""
        logging.getLogger("episodic_rag").handlers.clear()
        fake_out = StringIO()
        fake_err = StringIO()
        monkeypatch.setattr(sys, "stdout", fake_out)
        monkeypatch.setattr(sys, "stderr", fake_err)

        configured = setup_logging()
        configured.propagate = False
        configured.info("stringio safe")
        for h in configured.handlers:
            h.flush()

        assert "stringio safe" in fake_out.getvalue()
