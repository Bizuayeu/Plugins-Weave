# tests/usecases/test_factories.py
"""
factories.py のテスト

ファクトリ関数とwait_list便利関数のテスト。
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestWaitListFactory:
    """factories.wait_list()のテスト"""

    def test_wait_list_calls_usecase(self):
        """wait_list()がcreate_wait_usecaseを使用する"""
        with patch('usecases.factories.create_wait_usecase') as mock_create:
            mock_usecase = Mock()
            mock_usecase.list_waiters.return_value = []
            mock_create.return_value = mock_usecase

            from usecases.factories import wait_list

            wait_list()

            mock_create.assert_called_once()
            mock_usecase.list_waiters.assert_called_once()

    def test_wait_list_prints_empty_message(self, capsys):
        """空リストで適切なメッセージを表示"""
        with patch('usecases.factories.create_wait_usecase') as mock_create:
            mock_usecase = Mock()
            mock_usecase.list_waiters.return_value = []
            mock_create.return_value = mock_usecase

            from usecases.factories import wait_list

            wait_list()

            captured = capsys.readouterr()
            assert "No active" in captured.out

    def test_wait_list_prints_waiter_count(self, capsys):
        """待機プロセス数を表示"""
        with patch('usecases.factories.create_wait_usecase') as mock_create:
            mock_usecase = Mock()
            mock_usecase.list_waiters.return_value = [
                {"pid": 123, "target_time": "22:00", "theme": "test"},
                {"pid": 456, "target_time": "23:00", "theme": "test2"},
            ]
            mock_create.return_value = mock_usecase

            from usecases.factories import wait_list

            wait_list()

            captured = capsys.readouterr()
            assert "2" in captured.out
            assert "123" in captured.out
            assert "456" in captured.out


class TestCreateWaitUsecase:
    """create_wait_usecase()のテスト"""

    def test_create_wait_usecase_returns_usecase(self):
        """create_wait_usecaseがWaitEssayUseCaseを返す"""
        from usecases.factories import create_wait_usecase
        from usecases.wait_essay import WaitEssayUseCase

        usecase = create_wait_usecase()
        assert isinstance(usecase, WaitEssayUseCase)

    def test_create_wait_usecase_injects_dependencies(self):
        """依存性が注入される"""
        with (
            patch('usecases.factories.get_storage') as mock_get_storage,
            patch('usecases.factories.get_spawner') as mock_get_spawner,
        ):
            mock_storage = Mock()
            mock_spawner = Mock()
            mock_get_storage.return_value = mock_storage
            mock_get_spawner.return_value = mock_spawner

            from usecases.factories import create_wait_usecase

            _usecase = create_wait_usecase()  # noqa: F841

            mock_get_storage.assert_called_once()
            mock_get_spawner.assert_called_once()
