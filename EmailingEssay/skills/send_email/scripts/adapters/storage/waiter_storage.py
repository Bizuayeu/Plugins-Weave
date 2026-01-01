# adapters/storage/waiter_storage.py
"""
待機プロセスストレージアダプター

待機プロセス（Waiter）のPIDトラッキングをJSONファイルで永続化する。
プロセス生存チェック機能により、死亡したプロセスを自動除外。

Stage 5.3: ストレージアダプター責務分離
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from domain.validators import validate_waiter_entries
from usecases.ports import WaiterEntry

from .process_cache import ProcessAlivenessCache

if TYPE_CHECKING:
    from usecases.ports import PathResolverPort

# プロセス生存チェックのキャッシュTTL
PROCESS_CACHE_TTL = 5.0  # 5秒
PROCESS_CLEANUP_INTERVAL = 60.0  # 60秒

# モジュールロガー
logger = logging.getLogger('emailingessay.storage')


class WaiterStorageAdapter:
    """
    待機プロセスストレージアダプター（WaiterStoragePort実装）

    待機プロセスのPIDトラッキングを担当する。
    """

    def __init__(self, path_resolver: PathResolverPort) -> None:
        """
        Args:
            path_resolver: パス解決アダプター
        """
        self._path_resolver = path_resolver
        self._process_cache = ProcessAlivenessCache(
            ttl=PROCESS_CACHE_TTL,
            cleanup_interval=PROCESS_CLEANUP_INTERVAL,
        )

    def _get_active_waiters_file(self) -> Path:
        """アクティブ待機プロセスファイルのパスを取得"""
        return Path(self._path_resolver.get_persistent_dir()) / "active_waiters.json"

    def _is_process_alive(self, pid: int) -> bool:
        """
        プロセスが生存しているかチェックする。

        Args:
            pid: プロセスID

        Returns:
            プロセスが存在する場合はTrue
        """
        import os
        import sys

        try:
            if sys.platform == "win32":
                # Windows: os.kill(pid, 0) は動作しないため、ctypesを使用
                import ctypes

                kernel32 = ctypes.windll.kernel32
                SYNCHRONIZE = 0x00100000
                handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
                if handle:
                    kernel32.CloseHandle(handle)
                    return True
                return False
            else:
                # Unix: シグナル0を送信（実際にはシグナルを送らず存在確認のみ）
                os.kill(pid, 0)
                return True
        except (OSError, PermissionError):
            return False

    def _is_process_alive_cached(self, pid: int) -> bool:
        """
        プロセス生存チェック（キャッシュ付き）。

        Args:
            pid: プロセスID

        Returns:
            プロセスが存在する場合はTrue
        """
        return self._process_cache.is_alive(pid, self._is_process_alive)

    def register_waiter(self, pid: int, target_time: str, theme: str) -> None:
        """
        待機プロセスを登録する。

        Args:
            pid: プロセスID
            target_time: 目標時刻
            theme: エッセイのテーマ
        """
        waiters_file = self._get_active_waiters_file()

        # 既存データを読み込み
        waiters: list[dict[str, Any]] = []
        if waiters_file.exists():
            try:
                with open(waiters_file, encoding="utf-8") as f:
                    content = f.read()
                    if content.strip():
                        data = json.loads(content)
                        if isinstance(data, dict):
                            waiters = data.get("waiters", [])
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to read waiters file: {e}")

        # 新しいエントリを追加
        entry = {
            "pid": pid,
            "target_time": target_time,
            "theme": theme,
            "registered_at": datetime.now().isoformat(),
        }
        waiters.append(entry)

        # 保存
        with open(waiters_file, "w", encoding="utf-8") as f:
            json.dump({"waiters": waiters}, f, indent=2, ensure_ascii=False)

        logger.debug(f"Registered waiter: PID={pid}, target={target_time}")

    def get_active_waiters(self) -> list[WaiterEntry]:
        """
        アクティブな待機プロセス一覧を取得する。

        死亡したプロセスは自動的に除外され、ファイルも更新される。

        Returns:
            アクティブな待機プロセスのリスト（型安全）
        """
        waiters_file = self._get_active_waiters_file()

        if not waiters_file.exists():
            return []

        # 既存データを読み込み
        try:
            with open(waiters_file, encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    return []
                data = json.loads(content)
                if not isinstance(data, dict):
                    return []
                waiters = data.get("waiters", [])
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read waiters file: {e}")
            return []

        # 生存プロセスのみフィルタ（キャッシュ付き）
        # dictでないエントリは除外
        active_waiters = [
            w for w in waiters
            if isinstance(w, dict) and self._is_process_alive_cached(w.get("pid", 0))
        ]

        # 死亡プロセスがあった場合はファイルを更新
        if len(active_waiters) != len(waiters):
            removed_count = len(waiters) - len(active_waiters)
            logger.debug(f"Removed {removed_count} dead waiter(s)")
            with open(waiters_file, "w", encoding="utf-8") as f:
                json.dump({"waiters": active_waiters}, f, indent=2, ensure_ascii=False)

        return validate_waiter_entries(active_waiters)
