# tests/domain/test_config.py
"""
Config dataclass TDD tests

Red -> Green -> Refactor サイクルで実装する。
"""

import os
from pathlib import Path

import pytest


class TestConfig:
    """Config dataclass tests"""

    def test_load_from_environment(self, monkeypatch):
        """環境変数からConfig読込"""
        monkeypatch.setenv("ESSAY_SENDER_EMAIL", "sender@test.com")
        monkeypatch.setenv("ESSAY_APP_PASSWORD", "password123")
        monkeypatch.setenv("ESSAY_RECIPIENT_EMAIL", "recipient@test.com")

        from domain.config import Config

        Config.reset()  # シングルトンリセット
        config = Config.load()

        assert config.email.sender == "sender@test.com"
        assert config.email.password == "password123"
        assert config.email.recipient == "recipient@test.com"

    def test_validate_missing_sender_returns_error(self, monkeypatch):
        """必須フィールド欠落で検証エラー"""
        monkeypatch.delenv("ESSAY_SENDER_EMAIL", raising=False)
        monkeypatch.setenv("ESSAY_APP_PASSWORD", "password123")
        monkeypatch.setenv("ESSAY_RECIPIENT_EMAIL", "recipient@test.com")

        from domain.config import Config

        Config.reset()
        config = Config.load()
        errors = config.validate()

        assert len(errors) == 1
        assert "ESSAY_SENDER_EMAIL" in errors[0]

    def test_validate_all_missing_returns_three_errors(self, monkeypatch):
        """全フィールド欠落で3つの検証エラー"""
        for var in ["ESSAY_SENDER_EMAIL", "ESSAY_APP_PASSWORD", "ESSAY_RECIPIENT_EMAIL"]:
            monkeypatch.delenv(var, raising=False)

        from domain.config import Config

        Config.reset()
        config = Config.load()
        errors = config.validate()

        assert len(errors) == 3

    def test_load_from_env_file(self, tmp_path, monkeypatch):
        """.envファイルから読込"""
        env_file = tmp_path / ".env"
        env_file.write_text('''
ESSAY_SENDER_EMAIL=file@test.com
ESSAY_APP_PASSWORD=filepassword
ESSAY_RECIPIENT_EMAIL=filerecipient@test.com
''')
        # 既存環境変数をクリア
        for var in ["ESSAY_SENDER_EMAIL", "ESSAY_APP_PASSWORD", "ESSAY_RECIPIENT_EMAIL"]:
            monkeypatch.delenv(var, raising=False)

        from domain.config import Config

        Config.reset()
        config = Config.load(env_file=env_file)

        assert config.email.sender == "file@test.com"

    def test_singleton_returns_same_instance(self, monkeypatch):
        """シングルトンパターン確認"""
        monkeypatch.setenv("ESSAY_SENDER_EMAIL", "test@test.com")
        monkeypatch.setenv("ESSAY_APP_PASSWORD", "pass")
        monkeypatch.setenv("ESSAY_RECIPIENT_EMAIL", "recv@test.com")

        from domain.config import Config

        Config.reset()
        config1 = Config.load()
        config2 = Config.load()

        assert config1 is config2

    def test_reset_clears_singleton(self, monkeypatch):
        """resetでシングルトンがクリアされる"""
        monkeypatch.setenv("ESSAY_SENDER_EMAIL", "first@test.com")
        monkeypatch.setenv("ESSAY_APP_PASSWORD", "pass")
        monkeypatch.setenv("ESSAY_RECIPIENT_EMAIL", "recv@test.com")

        from domain.config import Config

        Config.reset()
        config1 = Config.load()

        monkeypatch.setenv("ESSAY_SENDER_EMAIL", "second@test.com")
        Config.reset()
        config2 = Config.load()

        assert config1 is not config2
        assert config1.email.sender == "first@test.com"
        assert config2.email.sender == "second@test.com"

    def test_env_file_with_quotes(self, tmp_path, monkeypatch):
        """.envファイルのクォート除去"""
        env_file = tmp_path / ".env"
        env_file.write_text('''
ESSAY_SENDER_EMAIL="quoted@test.com"
ESSAY_APP_PASSWORD='singlequoted'
ESSAY_RECIPIENT_EMAIL=noquote@test.com
''')
        for var in ["ESSAY_SENDER_EMAIL", "ESSAY_APP_PASSWORD", "ESSAY_RECIPIENT_EMAIL"]:
            monkeypatch.delenv(var, raising=False)

        from domain.config import Config

        Config.reset()
        config = Config.load(env_file=env_file)

        assert config.email.sender == "quoted@test.com"
        assert config.email.password == "singlequoted"
        assert config.email.recipient == "noquote@test.com"

    def test_env_file_ignores_comments(self, tmp_path, monkeypatch):
        """.envファイルのコメント行無視"""
        env_file = tmp_path / ".env"
        env_file.write_text('''
# This is a comment
ESSAY_SENDER_EMAIL=test@test.com
# Another comment
ESSAY_APP_PASSWORD=pass
ESSAY_RECIPIENT_EMAIL=recv@test.com
''')
        for var in ["ESSAY_SENDER_EMAIL", "ESSAY_APP_PASSWORD", "ESSAY_RECIPIENT_EMAIL"]:
            monkeypatch.delenv(var, raising=False)

        from domain.config import Config

        Config.reset()
        config = Config.load(env_file=env_file)

        assert config.email.sender == "test@test.com"

    def test_log_level_default(self, monkeypatch):
        """log_levelのデフォルト値"""
        monkeypatch.setenv("ESSAY_SENDER_EMAIL", "test@test.com")
        monkeypatch.setenv("ESSAY_APP_PASSWORD", "pass")
        monkeypatch.setenv("ESSAY_RECIPIENT_EMAIL", "recv@test.com")
        monkeypatch.delenv("ESSAY_LOG_LEVEL", raising=False)

        from domain.config import Config

        Config.reset()
        config = Config.load()

        assert config.log_level == "INFO"

    def test_log_json_default(self, monkeypatch):
        """log_jsonのデフォルト値"""
        monkeypatch.setenv("ESSAY_SENDER_EMAIL", "test@test.com")
        monkeypatch.setenv("ESSAY_APP_PASSWORD", "pass")
        monkeypatch.setenv("ESSAY_RECIPIENT_EMAIL", "recv@test.com")
        monkeypatch.delenv("ESSAY_LOG_JSON", raising=False)

        from domain.config import Config

        Config.reset()
        config = Config.load()

        assert config.log_json is False
