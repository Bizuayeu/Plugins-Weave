# adapters/storage/json_adapter.py
"""
JSON ストレージアダプター

スケジュール情報をJSONファイルで永続化する。
"""
from __future__ import annotations

import json
import os
from typing import Any


PERSISTENT_DIR_NAME = ".emailingessay"


class JsonStorageAdapter:
    """JSONファイルによるストレージ実装"""

    def __init__(self, base_dir: str | None = None):
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
        """スケジュール一覧を読み込む"""
        schedules_file = self.get_schedules_file()
        if os.path.exists(schedules_file):
            with open(schedules_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("schedules", [])
        return []

    def save_schedules(self, schedules: list[dict[str, Any]]) -> None:
        """スケジュール一覧を保存する"""
        with open(self.get_schedules_file(), "w", encoding="utf-8") as f:
            json.dump({"schedules": schedules}, f, indent=2, ensure_ascii=False)
