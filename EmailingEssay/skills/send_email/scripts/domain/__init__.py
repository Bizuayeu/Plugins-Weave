# domain/__init__.py
"""
ドメイン層

ビジネスルール、ドメインモデル、定数、例外を提供する。
"""
from .constants import (
    VALID_WEEKDAYS,
    WEEKDAYS_FULL,
    WEEKDAYS_ABBR,
    ABBR_TO_WEEKDAY_NUM,
    weekday_to_python_num,
    weekday_to_schtasks,
    weekday_to_cron,
    ordinal_to_schtasks,
)
from .exceptions import (
    EmailingEssayError,
    DomainError,
    ValidationError,
    AdapterError,
    MailError,
    SchedulerError,
    StorageError,
    TemplateError,
    WaiterError,
)
from .models import (
    MonthlyType,
    MonthlyPattern,
    EssaySchedule,
    TargetTime,
)

__all__ = [
    # constants
    "VALID_WEEKDAYS",
    "WEEKDAYS_FULL",
    "WEEKDAYS_ABBR",
    "ABBR_TO_WEEKDAY_NUM",
    "weekday_to_python_num",
    "weekday_to_schtasks",
    "weekday_to_cron",
    "ordinal_to_schtasks",
    # exceptions
    "EmailingEssayError",
    "DomainError",
    "ValidationError",
    "AdapterError",
    "MailError",
    "SchedulerError",
    "StorageError",
    "TemplateError",
    "WaiterError",
    # models
    "MonthlyType",
    "MonthlyPattern",
    "EssaySchedule",
    "TargetTime",
]
