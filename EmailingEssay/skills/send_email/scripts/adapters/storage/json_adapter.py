# adapters/storage/json_adapter.py
"""
JSON ストレージアダプター

スケジュール情報をJSONファイルで永続化する。
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any


PERSISTENT_DIR_NAME = ".emailingessay"

# モジュールロガー
logger = logging.getLogger('emailingessay.storage')


class JsonStorageAdapter:
    """JSONファイルによるストレージ実装"""

    def __init__(self, base_dir: str | None = None) -> None:
        """
        Args:
            base_dir: 基底ディレクトリ（テスト用）。Noneの場合はデフォルトを使用
        """
        self._base_dir = base_dir

    def get_persistent_dir(self) -> str:
        """永続化ディレクトリのパスを取得（なければ作成）"""
        if self._base_dir:
            os.makedirs(self._base_dir, exist_ok=True)
            return self._base_dir

        home = os.path.expanduser("~")
        persistent_dir = os.path.join(home, ".claude", "plugins", PERSISTENT_DIR_NAME)
        os.makedirs(persistent_dir, exist_ok=True)
        return persistent_dir

    def get_schedules_file(self) -> str:
        """スケジュールファイルのパスを取得"""
        return os.path.join(self.get_persistent_dir(), "schedules.json")

    def get_runners_dir(self) -> str:
        """ランナースクリプト用ディレクトリのパスを取得（なければ作成）"""
        runners_dir = os.path.join(self.get_persistent_dir(), "runners")
        os.makedirs(runners_dir, exist_ok=True)
        return runners_dir

    def load_schedules(self) -> list[dict[str, Any]]:
        """
        スケジュール一覧を読み込む。

        破損したJSONファイルや無効なデータ構造の場合は空リストを返す。
        これによりサービス継続性を確保する。
        """
        schedules_file = self.get_schedules_file()
        if not os.path.exists(schedules_file):
            return []

        try:
            with open(schedules_file, "r", encoding="utf-8") as f:
                content = f.read()
                # 空または空白のみのファイル
                if not content.strip():
                    return []
                data = json.loads(content)
                # dictでない場合（配列など）
                if not isinstance(data, dict):
                    return []
                return data.get("schedules", [])
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # 破損したJSONの場合は警告ログを出力して空リストを返す
            logger.warning(f"Corrupted schedules.json, returning empty list: {e}")
            return []

    def save_schedules(self, schedules: list[dict[str, Any]]) -> None:
        """スケジュール一覧を保存する"""
        with open(self.get_schedules_file(), "w", encoding="utf-8") as f:
            json.dump({"schedules": schedules}, f, indent=2, ensure_ascii=False)
