# adapters/storage/json_adapter.py
"""
JSON ストレージアダプター

スケジュール情報をJSONファイルで永続化する。
バックアップ/復旧機能により、破損時のデータ回復を支援。
待機プロセスのPIDトラッキング機能も提供。
"""

from __future__ import annotations

import json
import logging
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from usecases.ports import ScheduleEntry, WaiterEntry

PERSISTENT_DIR_NAME = ".emailingessay"

# バックアップ作成の閾値
BACKUP_SIZE_THRESHOLD = 1024  # 1KB以上でバックアップ
BACKUP_TIME_THRESHOLD = 3600  # 1時間以上経過でバックアップ

# プロセス生存チェックのキャッシュTTL
PROCESS_CACHE_TTL = 5.0  # 5秒

# モジュールロガー
logger = logging.getLogger('emailingessay.storage')


class JsonStorageAdapter:
    """JSONファイルによるストレージ実装"""

    def __init__(self, base_dir: str | None = None) -> None:
        """
        Args:
            base_dir: 基底ディレクトリ（テスト用）。Noneの場合はデフォルトを使用
        """
        self._base_dir = Path(base_dir) if base_dir else None
        # プロセス生存チェックのキャッシュ: {pid: (is_alive, timestamp)}
        self._process_cache: dict[int, tuple[bool, float]] = {}

    def get_persistent_dir(self) -> str:
        """永続化ディレクトリのパスを取得（なければ作成）"""
        if self._base_dir:
            self._base_dir.mkdir(parents=True, exist_ok=True)
            return str(self._base_dir)

        persistent_dir = Path.home() / ".claude" / "plugins" / PERSISTENT_DIR_NAME
        persistent_dir.mkdir(parents=True, exist_ok=True)
        return str(persistent_dir)

    def get_schedules_file(self) -> str:
        """スケジュールファイルのパスを取得"""
        return str(Path(self.get_persistent_dir()) / "schedules.json")

    def get_runners_dir(self) -> str:
        """ランナースクリプト用ディレクトリのパスを取得（なければ作成）"""
        runners_dir = Path(self.get_persistent_dir()) / "runners"
        runners_dir.mkdir(parents=True, exist_ok=True)
        return str(runners_dir)

    def _should_create_backup(self, filepath: Path) -> bool:
        """
        バックアップを作成すべきか判定する。

        条件:
        - ファイルサイズが1KB以上
        - または、前回バックアップから1時間以上経過

        Args:
            filepath: 対象ファイルパス

        Returns:
            バックアップすべき場合はTrue
        """
        if not filepath.exists():
            return False

        # サイズチェック
        try:
            if filepath.stat().st_size >= BACKUP_SIZE_THRESHOLD:
                return True
        except OSError:
            return False

        # 時間チェック（バックアップファイルの更新時刻）
        backup = filepath.with_suffix('.json.bak')
        if not backup.exists():
            return True  # バックアップが無ければ作成

        try:
            backup_mtime = backup.stat().st_mtime
            if time.time() - backup_mtime >= BACKUP_TIME_THRESHOLD:
                return True
        except OSError:
            return True

        return False

    def _backup_file(self, filepath: Path) -> Path | None:
        """
        書き込み前にバックアップを作成する。

        Args:
            filepath: バックアップ対象のファイルパス

        Returns:
            バックアップファイルのパス。ファイルが存在しない場合はNone
        """
        if filepath.exists():
            backup = filepath.with_suffix('.json.bak')
            try:
                shutil.copy2(filepath, backup)
                logger.debug(f"Created backup: {backup}")
                return backup
            except OSError as e:
                logger.warning(f"Failed to create backup: {e}")
        return None

    def _restore_from_backup(self, filepath: Path) -> bool:
        """
        バックアップからの復旧を試行する。

        Args:
            filepath: 復旧対象のファイルパス

        Returns:
            復旧に成功した場合はTrue
        """
        backup = filepath.with_suffix('.json.bak')
        if not backup.exists():
            return False

        try:
            with open(backup, encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    return False
                data = json.loads(content)
                if isinstance(data, dict) and "schedules" in data:
                    shutil.copy2(backup, filepath)
                    logger.info(f"Restored from backup: {backup}")
                    return True
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Backup also corrupted or inaccessible: {e}")
        return False

    def load_schedules(self) -> list[ScheduleEntry]:
        """
        スケジュール一覧を読み込む。

        破損したJSONファイルの場合はバックアップからの復旧を試行。
        復旧に失敗した場合は空リストを返し、サービス継続性を確保する。

        Returns:
            スケジュールエントリのリスト（型安全）
        """
        schedules_file = Path(self.get_schedules_file())
        if not schedules_file.exists():
            return []

        try:
            with open(schedules_file, encoding="utf-8") as f:
                content = f.read()
                # 空または空白のみのファイル
                if not content.strip():
                    return []
                data = json.loads(content)
                # dictでない場合（配列など）
                if not isinstance(data, dict):
                    return []
                return cast(list[ScheduleEntry], data.get("schedules", []))
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # 破損したJSONの場合はバックアップからの復旧を試行
            logger.warning(f"Corrupted schedules.json: {e}")
            if self._restore_from_backup(schedules_file):
                # 復旧成功、再度読み込み
                return self.load_schedules()
            logger.error("No valid backup available, returning empty list")
            return []

    def save_schedules(self, schedules: list[ScheduleEntry], force_backup: bool = False) -> None:
        """
        スケジュール一覧を保存する。

        条件付きでバックアップを作成する（効率化）。

        Args:
            schedules: 保存するスケジュールリスト
            force_backup: 強制的にバックアップを作成する場合はTrue
        """
        schedules_file = Path(self.get_schedules_file())
        # 条件を満たす場合のみバックアップ
        if force_backup or self._should_create_backup(schedules_file):
            self._backup_file(schedules_file)
        # 新しいデータを書き込み
        with open(schedules_file, "w", encoding="utf-8") as f:
            json.dump({"schedules": schedules}, f, indent=2, ensure_ascii=False)

    # =========================================================================
    # 待機プロセス（Waiter）トラッキング
    # =========================================================================

    def get_active_waiters_file(self) -> str:
        """アクティブ待機プロセスファイルのパスを取得"""
        return str(Path(self.get_persistent_dir()) / "active_waiters.json")

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

    def _cleanup_dead_processes(self) -> None:
        """
        死亡プロセスをキャッシュから削除する。

        メモリリーク防止のため、定期的に呼び出す。
        """
        self._process_cache = {
            pid: (alive, ts)
            for pid, (alive, ts) in self._process_cache.items()
            if self._is_process_alive(pid)
        }

    def _is_process_alive_cached(self, pid: int) -> bool:
        """
        プロセス生存チェック（キャッシュ付き）。

        TTL（5秒）以内の結果はキャッシュから返す。
        60秒ごとに死亡プロセスをクリーンアップする。

        Args:
            pid: プロセスID

        Returns:
            プロセスが存在する場合はTrue
        """
        now = time.time()

        # キャッシュ確認（クリーンアップ前に行う）
        if pid in self._process_cache:
            is_alive, timestamp = self._process_cache[pid]
            if now - timestamp < PROCESS_CACHE_TTL:
                return is_alive

        # 60秒ごとにクリーンアップ（初回は現在時刻で初期化）
        if not hasattr(self, '_last_cleanup'):
            self._last_cleanup = now
        elif now - self._last_cleanup > 60.0:
            self._cleanup_dead_processes()
            self._last_cleanup = now

        # キャッシュミス: 実際にチェック
        is_alive = self._is_process_alive(pid)
        self._process_cache[pid] = (is_alive, now)

        return is_alive

    def register_waiter(self, pid: int, target_time: str, theme: str) -> None:
        """
        待機プロセスを登録する。

        Args:
            pid: プロセスID
            target_time: 目標時刻
            theme: エッセイのテーマ
        """
        waiters_file = Path(self.get_active_waiters_file())

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
        waiters_file = Path(self.get_active_waiters_file())

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
        active_waiters = [w for w in waiters if self._is_process_alive_cached(w.get("pid", 0))]

        # 死亡プロセスがあった場合はファイルを更新
        if len(active_waiters) != len(waiters):
            removed_count = len(waiters) - len(active_waiters)
            logger.debug(f"Removed {removed_count} dead waiter(s)")
            with open(waiters_file, "w", encoding="utf-8") as f:
                json.dump({"waiters": active_waiters}, f, indent=2, ensure_ascii=False)

        return cast(list[WaiterEntry], active_waiters)
