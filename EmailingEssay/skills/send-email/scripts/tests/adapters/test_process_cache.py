# tests/adapters/test_process_cache.py
"""
ProcessAlivenessCache のテスト（Stage 3: プロセスキャッシュ抽出）
"""

import os
import sys
from unittest.mock import Mock

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestProcessAlivenessCache:
    """ProcessAlivenessCache クラスのテスト"""

    def test_cache_returns_cached_value_within_ttl(self):
        """TTL内ではキャッシュされた値を返す"""
        from adapters.storage.process_cache import ProcessAlivenessCache

        mock_checker = Mock(return_value=True)
        cache = ProcessAlivenessCache(ttl=5.0, cleanup_interval=60.0)

        # 最初の呼び出し: 実際にチェック
        result1 = cache.is_alive(123, mock_checker)
        assert result1 is True
        assert mock_checker.call_count == 1

        # 2回目の呼び出し（TTL内）: キャッシュから返す
        result2 = cache.is_alive(123, mock_checker)
        assert result2 is True
        assert mock_checker.call_count == 1  # 追加呼び出しなし

    def test_cache_refreshes_after_ttl(self):
        """TTL経過後は再チェックする"""
        from adapters.storage.process_cache import ProcessAlivenessCache

        mock_checker = Mock(return_value=True)
        cache = ProcessAlivenessCache(ttl=0.0, cleanup_interval=60.0)  # TTL=0で即時期限切れ

        # 最初の呼び出し
        result1 = cache.is_alive(123, mock_checker)
        assert result1 is True
        assert mock_checker.call_count == 1

        # TTL経過後（0秒なので即時）
        result2 = cache.is_alive(123, mock_checker)
        assert result2 is True
        assert mock_checker.call_count == 2  # 再チェック

    def test_cleanup_removes_dead_processes(self):
        """クリーンアップで死亡プロセスを削除"""
        from adapters.storage.process_cache import ProcessAlivenessCache

        # 最初は生存、後で死亡
        is_alive = True

        def mock_checker(pid: int) -> bool:
            return is_alive

        cache = ProcessAlivenessCache(ttl=5.0, cleanup_interval=0.0)  # 即時クリーンアップ

        # プロセス生存時にキャッシュ
        cache.is_alive(123, mock_checker)
        assert 123 in cache._cache

        # プロセス死亡
        is_alive = False

        # クリーンアップをトリガー（cleanup_interval=0なので次の呼び出しで実行）
        cache.is_alive(456, mock_checker)

        # 死亡プロセスはキャッシュから削除されている
        assert 123 not in cache._cache

    def test_different_pids_are_cached_separately(self):
        """異なるPIDは別々にキャッシュされる"""
        from adapters.storage.process_cache import ProcessAlivenessCache

        call_counts = {}

        def mock_checker(pid: int) -> bool:
            call_counts[pid] = call_counts.get(pid, 0) + 1
            return True

        cache = ProcessAlivenessCache(ttl=5.0, cleanup_interval=60.0)

        cache.is_alive(100, mock_checker)
        cache.is_alive(200, mock_checker)
        cache.is_alive(100, mock_checker)  # キャッシュから
        cache.is_alive(200, mock_checker)  # キャッシュから

        assert call_counts[100] == 1
        assert call_counts[200] == 1

    def test_cache_stores_false_values(self):
        """Falseの結果もキャッシュする"""
        from adapters.storage.process_cache import ProcessAlivenessCache

        mock_checker = Mock(return_value=False)
        cache = ProcessAlivenessCache(ttl=5.0, cleanup_interval=60.0)

        result1 = cache.is_alive(999, mock_checker)
        assert result1 is False
        assert mock_checker.call_count == 1

        result2 = cache.is_alive(999, mock_checker)
        assert result2 is False
        assert mock_checker.call_count == 1  # キャッシュから

    def test_clear_removes_all_entries(self):
        """clear()で全エントリを削除"""
        from adapters.storage.process_cache import ProcessAlivenessCache

        mock_checker = Mock(return_value=True)
        cache = ProcessAlivenessCache(ttl=5.0, cleanup_interval=60.0)

        cache.is_alive(100, mock_checker)
        cache.is_alive(200, mock_checker)
        assert len(cache._cache) == 2

        cache.clear()
        assert len(cache._cache) == 0
