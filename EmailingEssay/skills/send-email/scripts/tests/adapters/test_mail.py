# tests/adapters/test_mail.py
"""
メールアダプターのテスト

YagmailAdapterのテスト。
"""

import logging
import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

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

    @patch("adapters.mail.yagmail_adapter.yagmail")
    def test_send_email_success(self, mock_yagmail, adapter):
        """メール送信成功"""
        mock_smtp = MagicMock()
        mock_yagmail.SMTP.return_value.__enter__.return_value = mock_smtp

        adapter.send(to="test@example.com", subject="Test Subject", body="Test Body")

        mock_yagmail.SMTP.assert_called_once()
        mock_smtp.send.assert_called_once()

    @patch("adapters.mail.yagmail_adapter.yagmail")
    def test_send_logs_success_as_info(self, mock_yagmail, adapter, caplog):
        """送信成功が INFO 1 行として残る（print はログレコードを発しない）"""
        mock_yagmail.SMTP.return_value.__enter__.return_value = MagicMock()

        with caplog.at_level(logging.INFO, logger="emailingessay"):
            adapter.send(
                to="test@example.com", subject="Test Subject", body="Test Body"
            )

        infos = [
            r
            for r in caplog.records
            if r.name.startswith("emailingessay") and r.levelno == logging.INFO
        ]
        assert len(infos) == 1
        assert "test@example.com" in infos[0].getMessage()

    @patch("adapters.mail.yagmail_adapter.yagmail")
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

    @patch("adapters.mail.yagmail_adapter.yagmail")
    def test_test_email_sends_correctly(self, mock_yagmail, adapter):
        """テストメール送信"""
        mock_smtp = MagicMock()
        mock_yagmail.SMTP.return_value.__enter__.return_value = mock_smtp

        adapter.test()

        mock_smtp.send.assert_called_once()
        call_kwargs = mock_smtp.send.call_args[1]
        assert (
            "Essay System" in call_kwargs["subject"] or "Test" in call_kwargs["subject"]
        )

    def test_missing_sender_raises_error(self):
        """送信者未設定でエラー"""
        Config.reset()  # シングルトンリセット
        with patch.dict(os.environ, {}, clear=True), pytest.raises(MailError):
            YagmailAdapter()

    def test_missing_password_raises_error(self):
        """パスワード未設定でエラー"""
        Config.reset()  # シングルトンリセット
        with (
            patch.dict(
                os.environ, {"ESSAY_SENDER_EMAIL": "sender@example.com"}, clear=True
            ),
            pytest.raises(MailError),
        ):
            YagmailAdapter()

    def test_missing_recipient_raises_error(self):
        """受信者未設定でエラー"""
        Config.reset()  # シングルトンリセット
        with (
            patch.dict(
                os.environ,
                {
                    "ESSAY_SENDER_EMAIL": "sender@example.com",
                    "ESSAY_APP_PASSWORD": "password",
                },
                clear=True,
            ),
            pytest.raises(MailError),
        ):
            YagmailAdapter()

    @patch("adapters.mail.yagmail_adapter.yagmail")
    def test_smtp_connection_uses_context_manager(self, mock_yagmail, adapter):
        """SMTPはコンテキストマネージャで管理される"""
        mock_smtp_instance = MagicMock()
        mock_yagmail.SMTP.return_value.__enter__ = MagicMock(
            return_value=mock_smtp_instance
        )
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
        assert hasattr(config, "mail_retry_count")
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


class TestCollapseStyleWhitespace:
    """collapse_style_whitespace のテスト

    yagmail は本文の改行を <br> へ変換するため、<style> ブロック内に改行が残ると
    CSS に <br> が混入して premailer のインライン化が壊れる（メールが無スタイルで届く）。
    """

    def test_collapses_newlines_inside_style(self):
        """<style> 内の改行が潰れる"""
        from adapters.mail.yagmail_adapter import collapse_style_whitespace

        html = "<style>\n  body {\n    margin: 0;\n  }\n</style>"
        result = collapse_style_whitespace(html)

        assert "\n" not in result
        assert "body { margin: 0; }" in result

    def test_preserves_content_outside_style(self):
        """<style> の外側の改行は保持する（本文の <br> 変換は正常な挙動）"""
        from adapters.mail.yagmail_adapter import collapse_style_whitespace

        html = "<style>\na {\ncolor: red;\n}\n</style>\n<p>one</p>\n<p>two</p>"
        result = collapse_style_whitespace(html)

        assert "<p>one</p>\n<p>two</p>" in result

    def test_no_style_block_is_unchanged(self):
        """<style> が無ければ何も変えない"""
        from adapters.mail.yagmail_adapter import collapse_style_whitespace

        html = "<div>\n  hello\n</div>"
        assert collapse_style_whitespace(html) == html

    def test_handles_multiple_style_blocks(self):
        """複数の <style> をすべて処理する"""
        from adapters.mail.yagmail_adapter import collapse_style_whitespace

        html = "<style>\na {\ncolor: red;\n}\n</style><style>\nb {\ncolor: blue;\n}\n</style>"
        result = collapse_style_whitespace(html)

        assert "\n" not in result
        assert result.count("<style>") == 2

    def test_real_template_has_no_newlines_in_style(self):
        """実テンプレートを通しても <style> 内に改行が残らない"""
        from adapters.mail.yagmail_adapter import (
            EMAIL_TEMPLATE_NAME,
            collapse_style_whitespace,
        )
        from frameworks.templates import load_template

        result = collapse_style_whitespace(load_template(EMAIL_TEMPLATE_NAME))
        style = result.split("<style>")[1].split("</style>")[0]

        assert "\n" not in style


# =============================================================================
# Stage 3: Message-ID の受け渡し
# =============================================================================


class TestMessageIdPassthrough:
    """採番済み Message-ID を yagmail へ渡す（Stage 3）"""

    @pytest.fixture
    def adapter(self, monkeypatch):
        """アダプターのインスタンス"""
        monkeypatch.setenv("ESSAY_SENDER_EMAIL", "sender@example.com")
        monkeypatch.setenv("ESSAY_APP_PASSWORD", "password123")
        monkeypatch.setenv("ESSAY_RECIPIENT_EMAIL", "recipient@example.com")
        Config.reset()
        return YagmailAdapter()

    @patch("adapters.mail.yagmail_adapter.yagmail")
    def test_send_passes_message_id_to_yagmail(self, mock_yagmail, adapter):
        """send() の message_id が yagmail の SMTP.send へそのまま渡る"""
        mock_smtp = MagicMock()
        mock_yagmail.SMTP.return_value.__enter__.return_value = mock_smtp

        adapter.send(
            to="test@example.com",
            subject="Test Subject",
            body="Test Body",
            message_id="<given@example.com>",
        )

        assert mock_smtp.send.call_args[1]["message_id"] == "<given@example.com>"

    @patch("adapters.mail.yagmail_adapter.yagmail")
    def test_send_custom_forwards_message_id(self, mock_yagmail, adapter):
        """send_custom() の message_id が内部の send を経て yagmail まで届く"""
        mock_smtp = MagicMock()
        mock_yagmail.SMTP.return_value.__enter__.return_value = mock_smtp

        adapter.send_custom("件名", "本文", message_id="<given@example.com>")

        assert mock_smtp.send.call_args[1]["message_id"] == "<given@example.com>"

    @patch("adapters.mail.yagmail_adapter.yagmail")
    def test_send_without_message_id_still_works(self, mock_yagmail, adapter):
        """message_id 省略時も既存の呼び出しは壊れない"""
        mock_smtp = MagicMock()
        mock_yagmail.SMTP.return_value.__enter__.return_value = mock_smtp

        adapter.send(to="test@example.com", subject="Test Subject", body="Test Body")

        assert mock_smtp.send.call_args[1]["message_id"] is None
