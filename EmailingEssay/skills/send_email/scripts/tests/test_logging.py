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

    def test_schedule_storage_has_logger(self):
        """ScheduleStorageAdapterモジュールがloggerを持つ"""
        from adapters.storage import schedule_storage

        assert hasattr(schedule_storage, 'logger')

    def test_schedule_storage_logs_on_corruption(self, tmp_path, caplog):
        """JSON破損時に警告ログを出力"""
        from adapters.storage import PathResolverAdapter, ScheduleStorageAdapter

        path_resolver = PathResolverAdapter(base_dir=str(tmp_path))
        adapter = ScheduleStorageAdapter(path_resolver)
        file_path = tmp_path / "schedules.json"
        file_path.write_text("{corrupted")

        with caplog.at_level(logging.WARNING, logger='emailingessay'):
            adapter.load_schedules()

        # 警告ログが出力されている
        assert len([r for r in caplog.records if r.levelno >= logging.WARNING]) >= 1
