# usecases/ports.py
"""
ポートインターフェース定義

Use Cases層が依存する抽象インターフェース（Protocol）を定義する。
Adapters層がこれらを実装する。

型定義を厳格化し、Any型の使用を最小限に抑える。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypedDict, runtime_checkable

if TYPE_CHECKING:
    from domain.models import LedgerRecord, ReplyRecord

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

    def send(
        self, to: str, subject: str, body: str, *, message_id: str | None = None
    ) -> None:
        """メールを送信する（message_id 省略時は送信側で採番される）"""
        ...

    def test(self) -> None:
        """テストメールを送信する"""
        ...

    def send_custom(
        self, subject: str, content: str, *, message_id: str | None = None
    ) -> None:
        """カスタムコンテンツを送信する（message_id 省略時は送信側で採番される）"""
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
        day_spec: str = "",
    ) -> None:
        """スケジュールを追加する"""
        ...

    def remove(self, name: str) -> None:
        """スケジュールを削除する"""
        ...

    def list(self, known_names: list[str] | None = None) -> list[TaskInfo]:
        """スケジュール一覧を取得する

        Args:
            known_names: 追加で検索する既知のタスク名リスト（Essay_プレフィックス以外も検出可能にする）
        """
        ...


@runtime_checkable
class ScheduleStoragePort(Protocol):
    """スケジュール永続化の抽象インターフェース"""

    def load_schedules(self) -> list[ScheduleEntry]:
        """スケジュール一覧を読み込む"""
        ...

    def save_schedules(self, schedules: list[ScheduleEntry]) -> None:
        """スケジュール一覧を保存する"""
        ...


@runtime_checkable
class WaiterStoragePort(Protocol):
    """待機プロセス追跡の抽象インターフェース"""

    def register_waiter(self, pid: int, target_time: str, theme: str) -> None:
        """待機プロセスを登録する"""
        ...

    def get_active_waiters(self) -> list[WaiterEntry]:
        """アクティブな待機プロセス一覧を取得する（死亡プロセスは除外）"""
        ...


@runtime_checkable
class LedgerPort(Protocol):
    """送信台帳（追記専用）の抽象インターフェース"""

    def record_sent(
        self,
        message_id: str,
        sent_at: str,
        subject: str,
        recipient: str,
        body: str,
    ) -> LedgerRecord | None:
        """
        送信を台帳に記録する。

        Args:
            message_id: 採番済み Message-ID（角括弧込み。台帳の主キー）
            sent_at: ISO 8601 形式の送信日時
            subject: 送信した件名
            recipient: 宛先アドレス
            body: 本文（別ファイルへ書き出される）

        Returns:
            記録した LedgerRecord。message_id が既出の場合は None（冪等）
        """
        ...

    def load_records(self) -> list[LedgerRecord]:
        """台帳を読み込む（壊れた行は飛ばす）"""
        ...

    def append_reply(self, reply: ReplyRecord) -> bool:
        """
        取り込んだ返信を追記する。

        Returns:
            追記した場合は True。message_id が既出の場合は False（冪等）
        """
        ...

    def load_replies(self) -> list[ReplyRecord]:
        """返信一覧を読み込む（壊れた行は飛ばす）"""
        ...


@runtime_checkable
class InboxPort(Protocol):
    """受信箱の抽象インターフェース"""

    def fetch_replies(self, sender: str) -> list[ReplyRecord]:
        """
        指定の差出人から届いた返信候補を取得する。

        返るのはあくまで**候補**——取り込むか否かの判定（In-Reply-To の突合と
        From の照合）は UseCase の領分。受信箱の横断検索は行わない。

        Args:
            sender: 差出人アドレス（受信箱の絞り込みに使う）

        Returns:
            返信候補のリスト（該当なしなら空）

        Raises:
            MailError: 接続・認証・取得に失敗した場合
        """
        ...


@runtime_checkable
class PathResolverPort(Protocol):
    """ディレクトリパス解決の抽象インターフェース"""

    def get_persistent_dir(self) -> str:
        """永続化ディレクトリのパスを取得する"""
        ...

    def get_runners_dir(self) -> str:
        """ランナースクリプト用ディレクトリのパスを取得する"""
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
        lang: str = "",
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


# 全てエクスポート
__all__ = [
    "InboxPort",
    "LedgerPort",
    "MailPort",
    "PathResolverPort",
    "ProcessSpawnerPort",
    "ScheduleEntry",
    "ScheduleStoragePort",
    "SchedulerPort",
    "TaskInfo",
    "WaiterEntry",
    "WaiterPort",
    "WaiterStoragePort",
]
