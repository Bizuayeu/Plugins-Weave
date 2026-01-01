# usecases/ports.py
"""
ポートインターフェース定義

Use Cases層が依存する抽象インターフェース（Protocol）を定義する。
Adapters層がこれらを実装する。

型定義を厳格化し、Any型の使用を最小限に抑える。
"""
from __future__ import annotations

from typing import Protocol, TypedDict, runtime_checkable


# =============================================================================
# 型定義
# =============================================================================

class ScheduleEntry(TypedDict, total=False):
    """スケジュールエントリの型定義"""
    name: str
    frequency: str
    weekday: str
    time: str
    theme: str
    context: str
    file_list: str
    lang: str
    day_spec: str
    monthly_type: str
    created: str


class TaskInfo(TypedDict):
    """タスク情報の型定義"""
    name: str


class WaiterEntry(TypedDict):
    """待機プロセスエントリの型定義"""
    pid: int
    target_time: str
    theme: str
    registered_at: str


# =============================================================================
# ポートインターフェース
# =============================================================================

@runtime_checkable
class MailPort(Protocol):
    """メール送信の抽象インターフェース"""

    def send(self, to: str, subject: str, body: str) -> None:
        """メールを送信する"""
        ...

    def test(self) -> None:
        """テストメールを送信する"""
        ...

    def send_custom(self, subject: str, content: str) -> None:
        """カスタムコンテンツを送信する"""
        ...


@runtime_checkable
class SchedulerPort(Protocol):
    """スケジューラの抽象インターフェース"""

    def add(
        self,
        task_name: str,
        command: str,
        frequency: str,
        time: str,
        *,
        weekday: str = "",
        day_spec: str = ""
    ) -> None:
        """スケジュールを追加する"""
        ...

    def remove(self, name: str) -> None:
        """スケジュールを削除する"""
        ...

    def list(self) -> list[TaskInfo]:
        """スケジュール一覧を取得する"""
        ...


@runtime_checkable
class StoragePort(Protocol):
    """スケジュールストレージの抽象インターフェース"""

    def load_schedules(self) -> list[ScheduleEntry]:
        """スケジュール一覧を読み込む"""
        ...

    def save_schedules(self, schedules: list[ScheduleEntry]) -> None:
        """スケジュール一覧を保存する"""
        ...

    def get_persistent_dir(self) -> str:
        """永続化ディレクトリのパスを取得する"""
        ...

    def get_runners_dir(self) -> str:
        """ランナースクリプト用ディレクトリのパスを取得する"""
        ...

    def register_waiter(self, pid: int, target_time: str, theme: str) -> None:
        """待機プロセスを登録する"""
        ...

    def get_active_waiters(self) -> list[WaiterEntry]:
        """アクティブな待機プロセス一覧を取得する（死亡プロセスは除外）"""
        ...


@runtime_checkable
class ProcessSpawnerPort(Protocol):
    """プロセス起動の抽象インターフェース（WaitEssayUseCase用）"""

    def spawn_detached(self, script_path: str) -> int:
        """
        デタッチドプロセスを起動する。

        Args:
            script_path: 実行するスクリプトのパス

        Returns:
            プロセスID
        """
        ...


@runtime_checkable
class WaiterPort(Protocol):
    """待機処理の抽象インターフェース"""

    def spawn(
        self,
        target_time: str,
        theme: str = "",
        context: str = "",
        file_list: str = "",
        lang: str = ""
    ) -> int:
        """
        待機プロセスを起動する。

        Args:
            target_time: HH:MM または YYYY-MM-DD HH:MM
            theme: エッセイのテーマ
            context: コンテキストファイルパス
            file_list: ファイルリストパス
            lang: 言語（ja, en, auto）

        Returns:
            プロセスID
        """
        ...


# 後方互換性のため全てエクスポート
__all__ = [
    "ScheduleEntry",
    "TaskInfo",
    "WaiterEntry",
    "MailPort",
    "SchedulerPort",
    "StoragePort",
    "ProcessSpawnerPort",
    "WaiterPort",
]
