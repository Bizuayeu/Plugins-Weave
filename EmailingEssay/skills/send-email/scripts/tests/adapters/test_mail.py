# tests/adapters/test_mail.py
"""
メールアダプターのテスト

YagmailAdapterのテスト。
"""

import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from adapters.mail.yagmail_adapter import MailError, YagmailAdapter
from domain.config import Config


class TestYagmailAdapter:
    """YagmailAdapter のテスト"""

    @pytest.fixture
    def mock_config(self):
        """設定のモック"""
        return {
            "sender": "sender@example.com",
            "password": "password123",
            "recipient": "recipient@example.com",
        }

    @pytest.fixture
    def adapter(self, mock_config):
        """アダプターのインスタンス"""
        Config.reset()  # シングルトンリセット
        with patch.dict(
            os.environ,
            {
                "ESSAY_SENDER_EMAIL": mock_config["sender"],
                "ESSAY_APP_PASSWORD": mock_config["password"],
                "ESSAY_RECIPIENT_EMAIL": mock_config["recipient"],
            },
        ):
            return YagmailAdapter()

    @patch('adapters.mail.yagmail_adapter.yagmail')
    def test_send_email_success(self, mock_yagmail, adapter):
        """メール送信成功"""
        mock_smtp = MagicMock()
        mock_yagmail.SMTP.return_value.__enter__.return_value = mock_smtp

        adapter.send(to="test@example.com", subject="Test Subject", body="Test Body")

        mock_yagmail.SMTP.assert_called_once()
        mock_smtp.send.assert_called_once()

    @patch('adapters.mail.yagmail_adapter.yagmail')
    def test_send_email_uses_default_recipient(self, mock_yagmail, adapter):
        """デフォルト送信先を使用"""
        mock_smtp = MagicMock()
        mock_yagmail.SMTP.return_value.__enter__.return_value = mock_smtp

        adapter.send(
            to="",  # 空の場合はデフォルト
            subject="Test Subject",
            body="Test Body",
        )

        mock_smtp.send.assert_called_once()
        call_kwargs = mock_smtp.send.call_args[1]
        assert call_kwargs["to"] == "recipient@example.com"

    @patch('adapters.mail.yagmail_adapter.yagmail')
    def test_test_email_sends_correctly(self, mock_yagmail, adapter):
        """テストメール送信"""
        mock_smtp = MagicMock()
        mock_yagmail.SMTP.return_value.__enter__.return_value = mock_smtp

        adapter.test()

        mock_smtp.send.assert_called_once()
        call_kwargs = mock_smtp.send.call_args[1]
        assert "Essay System" in call_kwargs["subject"] or "Test" in call_kwargs["subject"]

    def test_missing_sender_raises_error(self):
        """送信者未設定でエラー"""
        Config.reset()  # シングルトンリセット
        with patch.dict(os.environ, {}, clear=True), pytest.raises(MailError):
            YagmailAdapter()

    def test_missing_password_raises_error(self):
        """パスワード未設定でエラー"""
        Config.reset()  # シングルトンリセット
        with (
            patch.dict(os.environ, {"ESSAY_SENDER_EMAIL": "sender@example.com"}, clear=True),
            pytest.raises(MailError),
        ):
            YagmailAdapter()

    def test_missing_recipient_raises_error(self):
        """受信者未設定でエラー"""
        Config.reset()  # シングルトンリセット
        with (
            patch.dict(
                os.environ,
                {"ESSAY_SENDER_EMAIL": "sender@example.com", "ESSAY_APP_PASSWORD": "password"},
                clear=True,
            ),
            pytest.raises(MailError),
        ):
            YagmailAdapter()

    @patch('adapters.mail.yagmail_adapter.yagmail')
    def test_smtp_connection_uses_context_manager(self, mock_yagmail, adapter):
        """SMTPはコンテキストマネージャで管理される"""
        mock_smtp_instance = MagicMock()
        mock_yagmail.SMTP.return_value.__enter__ = MagicMock(return_value=mock_smtp_instance)
        mock_yagmail.SMTP.return_value.__exit__ = MagicMock(return_value=False)

        adapter.send(to="test@example.com", subject="Test Subject", body="Test Body")

        # コンテキストマネージャが使用されたことを確認
        mock_yagmail.SMTP.return_value.__enter__.assert_called_once()
        mock_yagmail.SMTP.return_value.__exit__.assert_called_once()


# =============================================================================
# Stage 8: リトライポリシー設定化テスト
# =============================================================================


class TestRetryPolicyConfiguration:
    """リトライポリシー設定のテスト（Stage 8）"""

    def test_config_has_mail_retry_count(self, monkeypatch):
        """Configにmail_retry_countが存在する"""
        monkeypatch.setenv("ESSAY_SENDER_EMAIL", "test@example.com")
        monkeypatch.setenv("ESSAY_APP_PASSWORD", "password")
        monkeypatch.setenv("ESSAY_RECIPIENT_EMAIL", "recv@example.com")

        Config.reset()
        config = Config.load()

        # デフォルト値は3
        assert hasattr(config, 'mail_retry_count')
        assert config.mail_retry_count == 3

    def test_config_reads_retry_count_from_env(self, monkeypatch):
        """環境変数からリトライ回数を読み込む"""
        monkeypatch.setenv("ESSAY_SENDER_EMAIL", "test@example.com")
        monkeypatch.setenv("ESSAY_APP_PASSWORD", "password")
        monkeypatch.setenv("ESSAY_RECIPIENT_EMAIL", "recv@example.com")
        monkeypatch.setenv("ESSAY_MAIL_RETRY_COUNT", "5")

        Config.reset()
        config = Config.load()

        assert config.mail_retry_count == 5

    def test_adapter_uses_configured_retry_count(self, monkeypatch):
        """アダプターがConfigからリトライ回数を読み込む"""
        monkeypatch.setenv("ESSAY_SENDER_EMAIL", "test@example.com")
        monkeypatch.setenv("ESSAY_APP_PASSWORD", "password")
        monkeypatch.setenv("ESSAY_RECIPIENT_EMAIL", "recv@example.com")
        monkeypatch.setenv("ESSAY_MAIL_RETRY_COUNT", "5")

        Config.reset()
        adapter = YagmailAdapter()

        assert adapter._max_retries == 5


# =============================================================================
# 既存テスト
# =============================================================================


class TestYagmailAdapterWithConfig:
    """Config統合テスト（Phase 5）"""

    def test_yagmail_adapter_uses_config(self, monkeypatch):
        """YagmailAdapterがConfigを使用"""
        monkeypatch.setenv("ESSAY_SENDER_EMAIL", "config_test@example.com")
        monkeypatch.setenv("ESSAY_APP_PASSWORD", "config_testpass")
        monkeypatch.setenv("ESSAY_RECIPIENT_EMAIL", "config_recv@example.com")

        from domain.config import Config

        Config.reset()

        from adapters.mail import YagmailAdapter

        adapter = YagmailAdapter()

        assert adapter._sender == "config_test@example.com"
        assert adapter._password == "config_testpass"
        assert adapter._recipient == "config_recv@example.com"

    def test_yagmail_adapter_config_validation_error(self, monkeypatch):
        """Config検証エラー時にMailError"""
        monkeypatch.delenv("ESSAY_SENDER_EMAIL", raising=False)
        monkeypatch.delenv("ESSAY_APP_PASSWORD", raising=False)
        monkeypatch.delenv("ESSAY_RECIPIENT_EMAIL", raising=False)

        from domain.config import Config

        Config.reset()

        from adapters.mail import YagmailAdapter
        from adapters.mail.yagmail_adapter import MailError

        with pytest.raises(MailError) as exc_info:
            YagmailAdapter()

        # 複数のエラーが含まれることを確認
        assert "ESSAY_SENDER_EMAIL" in str(exc_info.value)
