# tests/usecases/test_factories.py
"""
factories.py のテスト

ファクトリ関数のテスト。
"""

import os
import sys
from unittest.mock import Mock, patch

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


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
            patch('usecases.factories.get_waiter_storage') as mock_get_waiter_storage,
            patch('usecases.factories.get_path_resolver') as mock_get_path_resolver,
            patch('usecases.factories.get_spawner') as mock_get_spawner,
        ):
            mock_waiter_storage = Mock()
            mock_path_resolver = Mock()
            mock_spawner = Mock()
            mock_get_waiter_storage.return_value = mock_waiter_storage
            mock_get_path_resolver.return_value = mock_path_resolver
            mock_get_spawner.return_value = mock_spawner

            from usecases.factories import create_wait_usecase

            _usecase = create_wait_usecase()

            mock_get_waiter_storage.assert_called_once()
            mock_get_path_resolver.assert_called_once()
            mock_get_spawner.assert_called_once()
