# usecases/factories.py
"""
ユースケースファクトリ

依存性注入を行い、ユースケースを生成する。
main.py や便利関数から使用される。
AdapterRegistryによるシングルトンパターンを提供。

Stage 5: ストレージアダプター責務分離
- PathResolverAdapter, ScheduleStorageAdapter, WaiterStorageAdapter に分離
- cast() を完全排除（isinstance アサーションに置換）
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from .ports import (
        MailPort,
        PathResolverPort,
        ProcessSpawnerPort,
        SchedulerPort,
        ScheduleStoragePort,
        WaiterStoragePort,
    )
    from .schedule_essay import ScheduleEssayUseCase
    from .wait_essay import WaitEssayUseCase


# =============================================================================
# AdapterRegistry: シングルトンレジストリ
# =============================================================================


class AdapterRegistry:
    """
    アダプターのシングルトンレジストリ。

    遅延初期化とキャッシュにより、同じアダプターは1回だけ生成される。
    テスト時はclear()でリセット可能。
    """

    _instances: ClassVar[dict[str, object]] = {}

    @classmethod
    def get_or_create(cls, key: str, factory: Callable[[], object]) -> object:
        """
        キーに対応するインスタンスを取得する。

        存在しない場合はfactoryを呼び出して生成・キャッシュする。

        Args:
            key: インスタンスを識別するキー
            factory: インスタンスを生成するファクトリ関数

        Returns:
            キーに対応するインスタンス（型安全性は呼び出し側で保証）
        """
        if key not in cls._instances:
            cls._instances[key] = factory()
        return cls._instances[key]

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


def get_mail_adapter() -> MailPort:
    """メールアダプターを取得する（シングルトン）"""
    from adapters.mail import YagmailAdapter

    adapter = AdapterRegistry.get_or_create("mail", YagmailAdapter)
    # Note: MailPort は設定依存のため、インスタンスレベルでの isinstance チェックは省略
    return adapter


def get_scheduler() -> SchedulerPort:
    """
    プラットフォームに応じたスケジューラを取得する（シングルトン）。

    Stage 6: 型安全性強化 - isinstance アサーションを追加
    """
    from adapters.scheduler import get_scheduler as _get_scheduler

    from .ports import SchedulerPort

    scheduler = AdapterRegistry.get_or_create("scheduler", _get_scheduler)
    assert isinstance(scheduler, SchedulerPort), (
        f"Scheduler does not conform to SchedulerPort: {type(scheduler).__name__}"
    )
    return scheduler


def get_path_resolver() -> PathResolverPort:
    """
    パス解決アダプターを取得する（シングルトン）。

    Stage 5: 責務分離 - PathResolverAdapter を使用
    """
    from adapters.storage.path_resolver import PathResolverAdapter

    from .ports import PathResolverPort

    resolver = AdapterRegistry.get_or_create("path_resolver", PathResolverAdapter)
    assert isinstance(resolver, PathResolverPort), (
        f"Resolver does not conform to PathResolverPort: {type(resolver).__name__}"
    )
    return resolver


def get_schedule_storage() -> ScheduleStoragePort:
    """
    スケジュールストレージアダプターを取得する（シングルトン）。

    Stage 5: 責務分離 - ScheduleStorageAdapter を使用
    """
    from adapters.storage.schedule_storage import ScheduleStorageAdapter

    from .ports import ScheduleStoragePort

    def factory() -> ScheduleStorageAdapter:
        return ScheduleStorageAdapter(get_path_resolver())

    storage = AdapterRegistry.get_or_create("schedule_storage", factory)
    assert isinstance(storage, ScheduleStoragePort), (
        f"Storage does not conform to ScheduleStoragePort: {type(storage).__name__}"
    )
    return storage


def get_waiter_storage() -> WaiterStoragePort:
    """
    待機プロセスストレージアダプターを取得する（シングルトン）。

    Stage 5: 責務分離 - WaiterStorageAdapter を使用
    """
    from adapters.storage.waiter_storage import WaiterStorageAdapter

    from .ports import WaiterStoragePort

    def factory() -> WaiterStorageAdapter:
        return WaiterStorageAdapter(get_path_resolver())

    storage = AdapterRegistry.get_or_create("waiter_storage", factory)
    assert isinstance(storage, WaiterStoragePort), (
        f"Storage does not conform to WaiterStoragePort: {type(storage).__name__}"
    )
    return storage


def get_spawner() -> ProcessSpawnerPort:
    """
    プロセススポーナーを取得する（シングルトン）。

    Stage 6: 型安全性強化
    """
    from adapters.process import ProcessSpawner

    from .ports import ProcessSpawnerPort

    spawner = AdapterRegistry.get_or_create("spawner", ProcessSpawner)
    assert isinstance(spawner, ProcessSpawnerPort), (
        f"Spawner does not conform to ProcessSpawnerPort: {type(spawner).__name__}"
    )
    return spawner


# =============================================================================
# ユースケース生成関数
# =============================================================================


def create_schedule_usecase() -> ScheduleEssayUseCase:
    """ScheduleEssayUseCaseを生成する"""
    from .schedule_essay import ScheduleEssayUseCase

    return ScheduleEssayUseCase(
        scheduler_port=get_scheduler(),
        schedule_storage=get_schedule_storage(),
        path_resolver=get_path_resolver(),
    )


def create_wait_usecase() -> WaitEssayUseCase:
    """WaitEssayUseCaseを生成する"""
    from .wait_essay import WaitEssayUseCase

    return WaitEssayUseCase(
        waiter_storage=get_waiter_storage(),
        path_resolver=get_path_resolver(),
        spawner_port=get_spawner(),
    )


__all__ = [
    "AdapterRegistry",
    "create_schedule_usecase",
    "create_wait_usecase",
    "get_mail_adapter",
    "get_path_resolver",
    "get_schedule_storage",
    "get_scheduler",
    "get_spawner",
    "get_waiter_storage",
]
