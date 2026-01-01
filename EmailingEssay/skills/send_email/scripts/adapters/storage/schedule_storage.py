# adapters/storage/schedule_storage.py
"""
スケジュールストレージアダプター

スケジュール情報をJSONファイルで永続化する。
バックアップ/復旧機能により、破損時のデータ回復を支援。

Stage 5.2: ストレージアダプター責務分離
"""

from __future__ import annotations

import json
import logging
import shutil
import time
from pathlib import Path
from typing import TYPE_CHECKING

from domain.validators import validate_schedule_entries
from usecases.ports import ScheduleEntry

if TYPE_CHECKING:
    from usecases.ports import PathResolverPort

# バックアップ作成の閾値
BACKUP_SIZE_THRESHOLD = 1024  # 1KB以上でバックアップ
BACKUP_TIME_THRESHOLD = 3600  # 1時間以上経過でバックアップ

# モジュールロガー
logger = logging.getLogger('emailingessay.storage')


class ScheduleStorageAdapter:
    """
    スケジュールストレージアダプター（ScheduleStoragePort実装）

    スケジュール情報のJSONファイル永続化を担当する。
    """

    def __init__(self, path_resolver: PathResolverPort) -> None:
        """
        Args:
            path_resolver: パス解決アダプター
        """
        self._path_resolver = path_resolver

    def _get_schedules_file(self) -> Path:
        """スケジュールファイルのパスを取得"""
        return Path(self._path_resolver.get_persistent_dir()) / "schedules.json"

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
        schedules_file = self._get_schedules_file()
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
                return validate_schedule_entries(data.get("schedules", []))
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
        schedules_file = self._get_schedules_file()
        # 条件を満たす場合のみバックアップ
        if force_backup or self._should_create_backup(schedules_file):
            self._backup_file(schedules_file)
        # 新しいデータを書き込み
        with open(schedules_file, "w", encoding="utf-8") as f:
            json.dump({"schedules": schedules}, f, indent=2, ensure_ascii=False)
