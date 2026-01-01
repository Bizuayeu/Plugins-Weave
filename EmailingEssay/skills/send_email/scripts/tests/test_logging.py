# tests/test_logging.py
"""
loggingモジュール統合テスト（Item 5）
"""
import pytest
import logging
import sys
import os

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLoggingConfiguration:
    """ログ設定のテスト"""

    def test_configure_logging_creates_logger(self):
        """configure_logging()がloggerを作成"""
        from frameworks.logging_config import configure_logging

        configure_logging()
        logger = logging.getLogger('emailingessay')
        assert logger is not None

    def test_configure_logging_sets_level(self):
        """configure_logging()がログレベルを設定"""
        from frameworks.logging_config import configure_logging

        configure_logging(level=logging.DEBUG)
        logger = logging.getLogger('emailingessay')
        assert logger.level == logging.DEBUG

    def test_get_logger_returns_child_logger(self):
        """get_logger()が子loggerを返す"""
        from frameworks.logging_config import get_logger

        logger = get_logger('storage')
        assert logger.name == 'emailingessay.storage'


class TestModuleLoggers:
    """各モジュールのlogger統合テスト"""

    def test_json_adapter_has_logger(self):
        """JsonStorageAdapterモジュールがloggerを持つ"""
        from adapters.storage import json_adapter
        assert hasattr(json_adapter, 'logger')

    def test_json_adapter_logs_on_corruption(self, tmp_path, caplog):
        """JSON破損時に警告ログを出力"""
        from adapters.storage.json_adapter import JsonStorageAdapter

        adapter = JsonStorageAdapter(base_dir=str(tmp_path))
        file_path = tmp_path / "schedules.json"
        file_path.write_text("{corrupted")

        with caplog.at_level(logging.WARNING, logger='emailingessay'):
            adapter.load_schedules()

        # 警告ログが出力されている
        assert len([r for r in caplog.records if r.levelno >= logging.WARNING]) >= 1
