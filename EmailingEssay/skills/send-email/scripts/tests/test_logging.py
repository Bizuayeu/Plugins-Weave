# tests/test_logging.py
"""
loggingモジュール統合テスト（Item 5）
"""

import logging
import os
import sys

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLoggingConfiguration:
    """ログ設定のテスト"""

    def test_configure_logging_creates_logger(self):
        """configure_logging()がloggerを作成"""
        from frameworks.logging_config import configure_logging

        configure_logging()
        logger = logging.getLogger("emailingessay")
        assert logger is not None

    def test_configure_logging_sets_level(self):
        """configure_logging()がログレベルを設定"""
        from frameworks.logging_config import configure_logging

        configure_logging(level=logging.DEBUG)
        logger = logging.getLogger("emailingessay")
        assert logger.level == logging.DEBUG

    def test_get_logger_returns_child_logger(self):
        """get_logger()が子loggerを返す"""
        from frameworks.logging_config import get_logger

        logger = get_logger("storage")
        assert logger.name == "emailingessay.storage"


class TestModuleLoggers:
    """各モジュールのlogger統合テスト"""

    def test_schedule_storage_has_logger(self):
        """ScheduleStorageAdapterモジュールがloggerを持つ"""
        from adapters.storage import schedule_storage

        assert hasattr(schedule_storage, "logger")

    def test_schedule_storage_logs_on_corruption(self, tmp_path, caplog):
        """JSON破損時に警告ログを出力"""
        from adapters.storage import PathResolverAdapter, ScheduleStorageAdapter

        path_resolver = PathResolverAdapter(base_dir=str(tmp_path))
        adapter = ScheduleStorageAdapter(path_resolver)
        file_path = tmp_path / "schedules.json"
        file_path.write_text("{corrupted")

        with caplog.at_level(logging.WARNING, logger="emailingessay"):
            adapter.load_schedules()

        # 警告ログが出力されている
        assert len([r for r in caplog.records if r.levelno >= logging.WARNING]) >= 1


# =============================================================================
# ログファイル出力（v1.3.0: 定期便は stdout が捨てられるため、
# 失敗と試行の痕跡はファイルに残す）
# =============================================================================


def _reset_root_handlers():
    """ルートロガーのハンドラを閉じて外す（tmp_path のファイルを掴んだままにしない）"""
    root = logging.getLogger("emailingessay")
    for handler in list(root.handlers):
        handler.close()
        root.removeHandler(handler)


@pytest.fixture
def log_path(tmp_path):
    """テスト専用のログファイルパス（後始末でハンドラを閉じる）"""
    path = tmp_path / "emailingessay.log"
    yield path
    _reset_root_handlers()


class TestLogFileOutput:
    """ファイルハンドラ（既定 ON）のテスト"""

    def test_send_failure_leaves_line_in_log_file(self, log_path):
        """送信失敗（EmailingEssayError 経路）がログファイルに 1 行残る"""
        from unittest.mock import Mock, patch

        from domain.exceptions import MailError
        from frameworks.logging_config import configure_logging
        from main import main

        configure_logging(log_file=str(log_path))

        with patch("main.create_parser") as mock_parser, patch("main.dispatch") as disp:
            mock_parser.return_value.parse_args.return_value = Mock()
            disp.side_effect = MailError("SMTP send failed")
            assert main() == 1

        content = log_path.read_text(encoding="utf-8")
        assert "MailError: SMTP send failed" in content

    def test_replies_fetch_logs_even_when_empty(self, log_path, tmp_path):
        """replies fetch は 0 件でもログ行を残す（空振りが残ることが要件）"""
        from adapters.storage.ledger_storage import LedgerStorageAdapter
        from adapters.storage.path_resolver import PathResolverAdapter
        from frameworks.logging_config import configure_logging
        from usecases.ingest_replies import IngestRepliesUseCase

        class FakeInbox:
            def fetch_replies(self, sender):
                return []

        ledger = LedgerStorageAdapter(PathResolverAdapter(str(tmp_path / "ledger")))
        configure_logging(log_file=str(log_path))

        usecase = IngestRepliesUseCase(
            inbox=FakeInbox(), ledger=ledger, recipient="reader@example.com"
        )
        assert usecase.fetch() == []

        assert "Ingested replies: 0" in log_path.read_text(encoding="utf-8")

    def test_password_never_reaches_log_file(self, log_path, monkeypatch):
        """認証失敗をログに残しても、パスワードは書かない（ops-rules 1）"""
        import imaplib
        from unittest.mock import Mock, patch

        from adapters.mail.imap_inbox import ImapInboxAdapter
        from domain.config import Config
        from frameworks.logging_config import configure_logging
        from main import main

        password = "abcdefghijklmnop"
        monkeypatch.setenv("ESSAY_SENDER_EMAIL", "essay@example.com")
        monkeypatch.setenv("ESSAY_APP_PASSWORD", password)
        monkeypatch.setenv("ESSAY_RECIPIENT_EMAIL", "reader@example.com")
        Config.reset()

        fake_client = Mock()
        fake_client.login.side_effect = imaplib.IMAP4.error(
            f"b'[AUTHENTICATIONFAILED] Invalid credentials {password}'"
        )
        configure_logging(log_file=str(log_path))

        try:
            with (
                patch(
                    "adapters.mail.imap_inbox.imaplib.IMAP4_SSL",
                    return_value=fake_client,
                ),
                patch("main.create_parser") as mock_parser,
                patch("main.dispatch") as disp,
            ):
                mock_parser.return_value.parse_args.return_value = Mock()
                disp.side_effect = lambda _args: ImapInboxAdapter().fetch_replies(
                    "reader@example.com"
                )
                assert main() == 1
        finally:
            Config.reset()

        content = log_path.read_text(encoding="utf-8")
        assert "IMAP authentication failed" in content
        assert password not in content

    def test_env_var_selects_log_file(self, tmp_path, monkeypatch):
        """明示引数が無ければ ESSAY_LOG_FILE に従う"""
        from frameworks.logging_config import configure_logging, get_logger

        path = tmp_path / "from_env.log"
        monkeypatch.setenv("ESSAY_LOG_FILE", str(path))
        configure_logging()
        try:
            get_logger("main").info("hello from env")
        finally:
            _reset_root_handlers()

        assert "hello from env" in path.read_text(encoding="utf-8")

    def test_default_path_is_persistent_dir(self, tmp_path, monkeypatch):
        """環境変数も無ければ永続化ディレクトリ配下へ書く（既定 ON）"""
        from pathlib import Path

        from frameworks.logging_config import configure_logging, get_logger

        monkeypatch.delenv("ESSAY_LOG_FILE", raising=False)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        configure_logging()
        try:
            get_logger("main").info("hello default")
        finally:
            _reset_root_handlers()

        expected = (
            tmp_path / ".claude" / "plugins" / ".emailingessay" / "emailingessay.log"
        )
        assert "hello default" in expected.read_text(encoding="utf-8")

    def test_unopenable_log_file_does_not_break_logging(self, tmp_path, capsys):
        """ログファイルが開けなくてもアプリを落とさず、stdout は生きている"""
        from frameworks.logging_config import configure_logging, get_logger

        blocker = tmp_path / "blocker"
        blocker.write_text("not a directory", encoding="utf-8")

        configure_logging(log_file=str(blocker / "emailingessay.log"))
        try:
            get_logger("main").info("still alive")
        finally:
            _reset_root_handlers()

        out = capsys.readouterr().out
        assert "still alive" in out
        assert "Log file unavailable" in out
