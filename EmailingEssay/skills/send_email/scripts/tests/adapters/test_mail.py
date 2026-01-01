# tests/adapters/test_mail.py
"""
メールアダプターのテスト

YagmailAdapterのテスト。
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from adapters.mail.yagmail_adapter import YagmailAdapter, MailError


class TestYagmailAdapter:
    """YagmailAdapter のテスト"""

    @pytest.fixture
    def mock_config(self):
        """設定のモック"""
        return {
            "sender": "sender@example.com",
            "password": "password123",
            "recipient": "recipient@example.com"
        }

    @pytest.fixture
    def adapter(self, mock_config):
        """アダプターのインスタンス"""
        with patch.dict(os.environ, {
            "ESSAY_SENDER_EMAIL": mock_config["sender"],
            "ESSAY_APP_PASSWORD": mock_config["password"],
            "ESSAY_RECIPIENT_EMAIL": mock_config["recipient"]
        }):
            return YagmailAdapter()

    @patch('adapters.mail.yagmail_adapter.yagmail')
    def test_send_email_success(self, mock_yagmail, adapter):
        """メール送信成功"""
        mock_smtp = MagicMock()
        mock_yagmail.SMTP.return_value.__enter__.return_value = mock_smtp

        adapter.send(
            to="test@example.com",
            subject="Test Subject",
            body="Test Body"
        )

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
            body="Test Body"
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
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(MailError):
                YagmailAdapter()

    def test_missing_password_raises_error(self):
        """パスワード未設定でエラー"""
        with patch.dict(os.environ, {
            "ESSAY_SENDER_EMAIL": "sender@example.com"
        }, clear=True):
            with pytest.raises(MailError):
                YagmailAdapter()

    def test_missing_recipient_raises_error(self):
        """受信者未設定でエラー"""
        with patch.dict(os.environ, {
            "ESSAY_SENDER_EMAIL": "sender@example.com",
            "ESSAY_APP_PASSWORD": "password"
        }, clear=True):
            with pytest.raises(MailError):
                YagmailAdapter()

    @patch('adapters.mail.yagmail_adapter.yagmail')
    def test_smtp_connection_uses_context_manager(self, mock_yagmail, adapter):
        """SMTPはコンテキストマネージャで管理される"""
        mock_smtp_instance = MagicMock()
        mock_yagmail.SMTP.return_value.__enter__ = MagicMock(return_value=mock_smtp_instance)
        mock_yagmail.SMTP.return_value.__exit__ = MagicMock(return_value=False)

        adapter.send(
            to="test@example.com",
            subject="Test Subject",
            body="Test Body"
        )

        # コンテキストマネージャが使用されたことを確認
        mock_yagmail.SMTP.return_value.__enter__.assert_called_once()
        mock_yagmail.SMTP.return_value.__exit__.assert_called_once()
