# usecases/ports.py
"""
ポートインターフェース定義

Use Cases層が依存する抽象インターフェース（Protocol）を定義する。
Adapters層がこれらを実装する。
"""
from __future__ import annotations

from typing import Protocol, Any


class MailPort(Protocol):
    """メール送信の抽象インターフェース"""

    def send(self, to: str, subject: str, body: str) -> None:
        """メールを送信する"""
        ...

    def test(self) -> None:
        """テストメールを送信する"""
        ...


class SchedulerPort(Protocol):
    """スケジューラの抽象インターフェース"""

    def add(
        self,
        task_name: str,
        command: str,
        frequency: str,
        time: str,
        **kwargs: Any
    ) -> None:
        """スケジュールを追加する"""
        ...

    def remove(self, name: str) -> None:
        """スケジュールを削除する"""
        ...

    def list(self) -> list[dict[str, Any]]:
        """スケジュール一覧を取得する"""
        ...


class WaiterPort(Protocol):
    """待機処理の抽象インターフェース"""

    def spawn(
        self,
        target_time: str,
        theme: str,
        context: str,
        file_list: str,
        lang: str
    ) -> None:
        """待機プロセスを起動する"""
        ...


class StoragePort(Protocol):
    """スケジュールストレージの抽象インターフェース"""

    def load_schedules(self) -> list[dict[str, Any]]:
        """スケジュール一覧を読み込む"""
        ...

    def save_schedules(self, schedules: list[dict[str, Any]]) -> None:
        """スケジュール一覧を保存する"""
        ...

    def get_persistent_dir(self) -> str:
        """永続化ディレクトリのパスを取得する"""
        ...

    def get_runners_dir(self) -> str:
        """ランナースクリプト用ディレクトリのパスを取得する"""
        ...
