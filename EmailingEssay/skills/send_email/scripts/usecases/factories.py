# usecases/factories.py
"""
ユースケースファクトリ

依存性注入を行い、ユースケースを生成する。
main.py や便利関数から使用される。
AdapterRegistryによるシングルトンパターンを提供。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, TypeVar

if TYPE_CHECKING:
    from .ports import MailPort, ProcessSpawnerPort, SchedulerPort, StoragePort
    from .schedule_essay import ScheduleEssayUseCase
    from .wait_essay import WaitEssayUseCase

T = TypeVar("T")


# =============================================================================
# AdapterRegistry: シングルトンレジストリ
# =============================================================================


class AdapterRegistry:
    """
    アダプターのシングルトンレジストリ。

    遅延初期化とキャッシュにより、同じアダプターは1回だけ生成される。
    テスト時はclear()でリセット可能。
    """

    _instances: dict[str, object] = {}

    @classmethod
    def get_or_create(cls, key: str, factory: Callable[[], T]) -> T:
        """
        キーに対応するインスタンスを取得する。

        存在しない場合はfactoryを呼び出して生成・キャッシュする。

        Args:
            key: インスタンスを識別するキー
            factory: インスタンスを生成するファクトリ関数

        Returns:
            キーに対応するインスタンス
        """
        if key not in cls._instances:
            cls._instances[key] = factory()
        return cls._instances[key]  # type: ignore

    @classmethod
    def clear(cls) -> None:
        """
        全インスタンスをクリアする。

        テスト用。本番コードでは使用しない。
        """
        cls._instances.clear()


# =============================================================================
# アダプター取得関数（シングルトン）
# =============================================================================


def get_mail_adapter() -> "MailPort":
    """メールアダプターを取得する（シングルトン）"""
    from adapters.mail import YagmailAdapter

    return AdapterRegistry.get_or_create("mail", YagmailAdapter)


def get_scheduler() -> "SchedulerPort":
    """プラットフォームに応じたスケジューラを取得する（シングルトン）"""
    from adapters.scheduler import get_scheduler as _get_scheduler

    return AdapterRegistry.get_or_create("scheduler", _get_scheduler)


def get_storage() -> "StoragePort":
    """ストレージアダプターを取得する（シングルトン）"""
    from adapters.storage import JsonStorageAdapter

    return AdapterRegistry.get_or_create("storage", JsonStorageAdapter)


def get_spawner() -> "ProcessSpawnerPort":
    """プロセススポーナーを取得する（シングルトン）"""
    from adapters.process import ProcessSpawner

    return AdapterRegistry.get_or_create("spawner", ProcessSpawner)


# =============================================================================
# ユースケース生成関数
# =============================================================================


def create_schedule_usecase() -> "ScheduleEssayUseCase":
    """ScheduleEssayUseCaseを生成する"""
    from .schedule_essay import ScheduleEssayUseCase

    return ScheduleEssayUseCase(scheduler_port=get_scheduler(), storage_port=get_storage())


def create_wait_usecase() -> "WaitEssayUseCase":
    """WaitEssayUseCaseを生成する"""
    from .wait_essay import WaitEssayUseCase

    return WaitEssayUseCase(storage_port=get_storage(), spawner_port=get_spawner())


# =============================================================================
# 便利関数（後方互換性）
# =============================================================================


def schedule_add(
    frequency: str,
    time_spec: str,
    weekday: str = "",
    theme: str = "",
    context_file: str = "",
    file_list: str = "",
    lang: str = "",
    name: str = "",
    day_spec: str = "",
) -> None:
    """スケジュールを追加する（便利関数）"""
    usecase = create_schedule_usecase()
    usecase.add(
        frequency=frequency,
        time_spec=time_spec,
        weekday=weekday,
        theme=theme,
        context_file=context_file,
        file_list=file_list,
        lang=lang,
        name=name,
        day_spec=day_spec,
    )


def schedule_list() -> None:
    """スケジュール一覧を表示する（便利関数）"""
    usecase = create_schedule_usecase()
    usecase.list()


def schedule_remove(name: str) -> None:
    """スケジュールを削除する（便利関数）"""
    usecase = create_schedule_usecase()
    usecase.remove(name)


def wait_list() -> None:
    """待機プロセス一覧を表示する（便利関数）"""
    usecase = create_wait_usecase()
    waiters = usecase.list_waiters()

    if not waiters:
        print("No active waiting processes.")
        return

    print(f"Active waiting processes: {len(waiters)}")
    print("-" * 60)
    for w in waiters:
        pid = w.get("pid", "?")
        target = w.get("target_time", "?")
        theme = w.get("theme", "") or "(no theme)"
        registered = w.get("registered_at", "?")
        print(f"  PID: {pid}")
        print(f"    Target: {target}")
        print(f"    Theme:  {theme}")
        print(f"    Registered: {registered}")
        print()


__all__ = [
    "AdapterRegistry",
    "get_mail_adapter",
    "get_scheduler",
    "get_storage",
    "get_spawner",
    "create_schedule_usecase",
    "create_wait_usecase",
    "schedule_add",
    "schedule_list",
    "schedule_remove",
    "wait_list",
]
