# usecases/factories.py
"""
ユースケースファクトリ

依存性注入を行い、ユースケースを生成する。
main.py や便利関数から使用される。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ports import SchedulerPort, StoragePort, ProcessSpawnerPort, MailPort


def get_mail_adapter() -> "MailPort":
    """メールアダプターを取得する"""
    from adapters.mail import YagmailAdapter
    return YagmailAdapter()


def get_scheduler() -> "SchedulerPort":
    """プラットフォームに応じたスケジューラを取得する"""
    from adapters.scheduler import get_scheduler as _get_scheduler
    return _get_scheduler()


def get_storage() -> "StoragePort":
    """ストレージアダプターを取得する"""
    from adapters.storage import JsonStorageAdapter
    return JsonStorageAdapter()


def get_spawner() -> "ProcessSpawnerPort":
    """プロセススポーナーを取得する"""
    from adapters.process import ProcessSpawner
    return ProcessSpawner()


def create_schedule_usecase() -> "ScheduleEssayUseCase":
    """ScheduleEssayUseCaseを生成する"""
    from .schedule_essay import ScheduleEssayUseCase
    return ScheduleEssayUseCase(
        scheduler_port=get_scheduler(),
        storage_port=get_storage()
    )


def create_wait_usecase() -> "WaitEssayUseCase":
    """WaitEssayUseCaseを生成する"""
    from .wait_essay import WaitEssayUseCase
    return WaitEssayUseCase(
        storage_port=get_storage(),
        spawner_port=get_spawner()
    )


# 後方互換性のため、schedule_essay.py の便利関数をここでも提供
def schedule_add(
    frequency: str,
    time_spec: str,
    weekday: str = "",
    theme: str = "",
    context_file: str = "",
    file_list: str = "",
    lang: str = "",
    name: str = "",
    day_spec: str = ""
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
        day_spec=day_spec
    )


def schedule_list() -> None:
    """スケジュール一覧を表示する（便利関数）"""
    usecase = create_schedule_usecase()
    usecase.list()


def schedule_remove(name: str) -> None:
    """スケジュールを削除する（便利関数）"""
    usecase = create_schedule_usecase()
    usecase.remove(name)


# 型ヒント用の遅延インポート
from .schedule_essay import ScheduleEssayUseCase  # noqa: E402
from .wait_essay import WaitEssayUseCase  # noqa: E402

__all__ = [
    "get_mail_adapter",
    "get_scheduler",
    "get_storage",
    "get_spawner",
    "create_schedule_usecase",
    "create_wait_usecase",
    "schedule_add",
    "schedule_list",
    "schedule_remove",
]
