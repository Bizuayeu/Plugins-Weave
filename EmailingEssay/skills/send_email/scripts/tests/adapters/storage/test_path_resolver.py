# tests/adapters/storage/test_path_resolver.py
"""
PathResolverAdapter のテスト

Stage 5.1: ストレージアダプター責務分離
"""

import os
import sys
from pathlib import Path

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from usecases.ports import PathResolverPort


class TestPathResolverAdapter:
    """PathResolverAdapter のテスト"""

    def test_conforms_to_protocol(self):
        """Protocol準拠"""
        from adapters.storage.path_resolver import PathResolverAdapter

        adapter = PathResolverAdapter()
        assert isinstance(adapter, PathResolverPort)

    def test_get_persistent_dir_creates_directory(self, tmp_path):
        """永続化ディレクトリを作成"""
        from adapters.storage.path_resolver import PathResolverAdapter

        adapter = PathResolverAdapter(base_dir=str(tmp_path))
        path = adapter.get_persistent_dir()
        assert Path(path).exists()
        assert Path(path).is_dir()

    def test_get_persistent_dir_returns_base_dir(self, tmp_path):
        """base_dir指定時はそのディレクトリを返す"""
        from adapters.storage.path_resolver import PathResolverAdapter

        adapter = PathResolverAdapter(base_dir=str(tmp_path))
        path = adapter.get_persistent_dir()
        assert path == str(tmp_path)

    def test_get_persistent_dir_default_path(self):
        """base_dir未指定時はデフォルトパスを返す"""
        from adapters.storage.path_resolver import PathResolverAdapter

        adapter = PathResolverAdapter()
        path = adapter.get_persistent_dir()
        assert ".claude" in path
        assert ".emailingessay" in path

    def test_get_runners_dir_creates_directory(self, tmp_path):
        """ランナーディレクトリを作成"""
        from adapters.storage.path_resolver import PathResolverAdapter

        adapter = PathResolverAdapter(base_dir=str(tmp_path))
        path = adapter.get_runners_dir()
        assert Path(path).exists()
        assert Path(path).is_dir()
        assert "runners" in path

    def test_get_runners_dir_is_subdirectory(self, tmp_path):
        """ランナーディレクトリはpersistent_dirのサブディレクトリ"""
        from adapters.storage.path_resolver import PathResolverAdapter

        adapter = PathResolverAdapter(base_dir=str(tmp_path))
        persistent_dir = adapter.get_persistent_dir()
        runners_dir = adapter.get_runners_dir()
        assert runners_dir.startswith(persistent_dir)
