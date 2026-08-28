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
from typing import TYPE_CHECKING, ClassVar, cast

if TYPE_CHECKING:
    from .import_legacy import ImportLegacyUseCase
    from .ingest_replies import IngestRepliesUseCase
    from .ports import (
        InboxPort,
        LedgerPort,
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
    """
    メールアダプターを取得する（シングルトン）。

    台帳記録デコレータで包んで返す。送信経路はすべてここを通るため、
    呼び出し側を変えずに全送信が台帳に載る（Stage 3）。
    """
    from adapters.mail import LedgerRecordingMail, YagmailAdapter
    from domain.config import Config

    def factory() -> LedgerRecordingMail:
        return LedgerRecordingMail(
            YagmailAdapter(), get_ledger(), Config.load().email.recipient
        )

    adapter = AdapterRegistry.get_or_create("mail", factory)
    # Note: MailPort は Protocol のため isinstance チェック不可、cast を使用
    return cast("MailPort", adapter)


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


def get_ledger() -> LedgerPort:
    """
    送信台帳ストレージアダプターを取得する（シングルトン）。

    Stage 2: 台帳の永続化 - LedgerStorageAdapter を使用
    """
    from adapters.storage.ledger_storage import LedgerStorageAdapter

    from .ports import LedgerPort

    def factory() -> LedgerStorageAdapter:
        return LedgerStorageAdapter(get_path_resolver())

    ledger = AdapterRegistry.get_or_create("ledger", factory)
    assert isinstance(ledger, LedgerPort), (
        f"Ledger does not conform to LedgerPort: {type(ledger).__name__}"
    )
    return ledger


def get_inbox() -> InboxPort:
    """
    受信箱アダプターを取得する（シングルトン）。

    構築時に接続は張らない（YagmailAdapter と同じく設定の検証のみ）。

    Stage 4: IMAP による返信の取り込み
    """
    from adapters.mail import ImapInboxAdapter

    from .ports import InboxPort

    inbox = AdapterRegistry.get_or_create("inbox", ImapInboxAdapter)
    assert isinstance(inbox, InboxPort), (
        f"Inbox does not conform to InboxPort: {type(inbox).__name__}"
    )
    return inbox


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


def create_ingest_replies_usecase() -> IngestRepliesUseCase:
    """IngestRepliesUseCaseを生成する"""
    from domain.config import Config

    from .ingest_replies import IngestRepliesUseCase

    return IngestRepliesUseCase(
        inbox=get_inbox(),
        ledger=get_ledger(),
        recipient=Config.load().email.recipient,
    )


def create_import_legacy_usecase() -> ImportLegacyUseCase:
    """ImportLegacyUseCaseを生成する

    移行元は永続化ディレクトリそのもの（台帳の置き場に過去の本文が散っている）。
    """
    from domain.config import Config

    from .import_legacy import ImportLegacyUseCase

    return ImportLegacyUseCase(
        source_dir=get_path_resolver().get_persistent_dir(),
        ledger=get_ledger(),
        recipient=Config.load().email.recipient,
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
    "create_import_legacy_usecase",
    "create_ingest_replies_usecase",
    "create_schedule_usecase",
    "create_wait_usecase",
    "get_inbox",
    "get_ledger",
    "get_mail_adapter",
    "get_path_resolver",
    "get_schedule_storage",
    "get_scheduler",
    "get_spawner",
    "get_waiter_storage",
]
