# adapters/storage/process_cache.py
"""
プロセス生存チェックのキャッシュ

Stage 3: ProcessAlivenessCache抽出
複雑なキャッシュロジックをjson_adapter.pyから分離し、
テスト可能性と可読性を向上させる。
"""

from __future__ import annotations

import time
from collections.abc import Callable


class ProcessAlivenessCache:
    """
    プロセス生存チェックのキャッシュ

    TTL（Time To Live）ベースのキャッシュにより、
    頻繁なプロセス生存チェックを最適化する。
    定期的に死亡プロセスをクリーンアップしてメモリリークを防止。
    """

    def __init__(self, ttl: float = 5.0, cleanup_interval: float = 60.0) -> None:
        """
        Args:
            ttl: キャッシュの有効期間（秒）
            cleanup_interval: クリーンアップの間隔（秒）
        """
        self._ttl = ttl
        self._cleanup_interval = cleanup_interval
        self._cache: dict[int, tuple[bool, float]] = {}
        self._last_cleanup: float = time.time()

    def is_alive(self, pid: int, checker: Callable[[int], bool]) -> bool:
        """
        プロセスが生存しているかチェックする（キャッシュ付き）。

        Args:
            pid: プロセスID
            checker: 実際にプロセス生存をチェックする関数

        Returns:
            プロセスが存在する場合はTrue
        """
        now = time.time()

        # キャッシュ確認（クリーンアップ前に行う）
        if pid in self._cache:
            is_alive, timestamp = self._cache[pid]
            if now - timestamp < self._ttl:
                return is_alive

        # 定期クリーンアップ
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup(checker)
            self._last_cleanup = now

        # キャッシュミス: 実際にチェック
        is_alive = checker(pid)
        self._cache[pid] = (is_alive, now)

        return is_alive

    def _cleanup(self, checker: Callable[[int], bool]) -> None:
        """
        死亡プロセスをキャッシュから削除する。

        Args:
            checker: プロセス生存をチェックする関数
        """
        self._cache = {pid: (alive, ts) for pid, (alive, ts) in self._cache.items() if checker(pid)}

    def clear(self) -> None:
        """キャッシュを全てクリアする。"""
        self._cache.clear()


__all__ = ["ProcessAlivenessCache"]
