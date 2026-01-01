# usecases/factories.py
"""
ユースケースファクトリ

依存性注入を行い、ユースケースを生成する。
main.py や便利関数から使用される。
AdapterRegistryによるシングルトンパターンを提供。

Stage 5: 型安全なファクトリー改善
- Protocol準拠検証テストを追加
- cast()の使用を最小限に
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar, TypeVar, cast

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

    _instances: ClassVar[dict[str, object]] = {}

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
        return cast(T, cls._instances[key])

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

    return AdapterRegistry.get_or_create("mail", YagmailAdapter)


def get_scheduler() -> SchedulerPort:
    """
    プラットフォームに応じたスケジューラを取得する（シングルトン）。

    Note:
        Stage 5: cast()はBaseSchedulerAdapter→SchedulerPortの変換に必要。
        Protocol準拠はTestProtocolConformance.test_scheduler_conforms_to_protocol()で検証済み。
    """
    from adapters.scheduler import get_scheduler as _get_scheduler

    return cast("SchedulerPort", AdapterRegistry.get_or_create("scheduler", _get_scheduler))


def get_schedule_storage() -> ScheduleStoragePort:
    """スケジュールストレージアダプターを取得する（シングルトン）"""
    from adapters.storage import JsonStorageAdapter

    return AdapterRegistry.get_or_create("storage", JsonStorageAdapter)


def get_waiter_storage() -> WaiterStoragePort:
    """待機プロセスストレージアダプターを取得する（シングルトン）"""
    from adapters.storage import JsonStorageAdapter

    return AdapterRegistry.get_or_create("storage", JsonStorageAdapter)


def get_path_resolver() -> PathResolverPort:
    """パス解決アダプターを取得する（シングルトン）"""
    from adapters.storage import JsonStorageAdapter

    return AdapterRegistry.get_or_create("storage", JsonStorageAdapter)


def get_spawner() -> ProcessSpawnerPort:
    """プロセススポーナーを取得する（シングルトン）"""
    from adapters.process import ProcessSpawner

    return AdapterRegistry.get_or_create("spawner", ProcessSpawner)


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
