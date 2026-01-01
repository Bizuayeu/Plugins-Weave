# domain/models.py
"""
ドメインモデル

Entities層: ビジネスルールとドメインモデルを定義する。
外部依存なし（最内側）。
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .constants import ABBR_TO_WEEKDAY_NUM, VALID_WEEKDAYS, WEEKDAYS_FULL
from .exceptions import DomainError, ValidationError


@dataclass
class ScheduleConfig:
    """
    スケジュール設定を表すValue Object

    ScheduleEssayUseCase.add() の9パラメータを1つのオブジェクトに集約し、
    パラメータ蓄積問題を解消する。

    Stage 1: パラメータ蓄積問題の解消
    Stage 3: バリデーションのドメイン層移行
    """

    frequency: str  # "daily" | "weekly" | "monthly"
    time_spec: str  # HH:MM 形式

    # オプショナルパラメータ（デフォルト値あり）
    weekday: str = ""  # 曜日（weekly用）
    theme: str = ""  # エッセイテーマ
    context_file: str = ""  # コンテキストファイルパス
    file_list: str = ""  # ファイルリストパス
    lang: str = ""  # 言語（ja, en, auto）
    name: str = ""  # カスタムタスク名
    day_spec: str = ""  # 月間パターン指定（monthly用）

    def validate(self) -> None:
        """
        設定を検証する。無効な場合は ValueError を発生させる。

        Stage 3: バリデーションのドメイン層移行
        """
        self._validate_frequency()
        self._validate_time()
        if self.frequency == "weekly":
            self._validate_weekday()
        if self.frequency == "monthly":
            self._validate_day_spec()

    def _validate_frequency(self) -> None:
        """頻度のバリデーション"""
        if self.frequency not in ["daily", "weekly", "monthly"]:
            raise ValueError(
                f"frequency must be 'daily', 'weekly', or 'monthly', got '{self.frequency}'"
            )

    def _validate_time(self) -> None:
        """時刻形式のバリデーション"""
        try:
            datetime.strptime(self.time_spec, "%H:%M")
        except ValueError as e:
            raise ValueError(f"time must be in HH:MM format, got '{self.time_spec}'") from e

    def _validate_weekday(self) -> None:
        """曜日のバリデーション（weekly用）"""
        weekday_lower = self.weekday.lower() if self.weekday else ""
        # 省略形または完全形のどちらでもOK
        if weekday_lower not in VALID_WEEKDAYS and weekday_lower not in WEEKDAYS_FULL:
            raise ValueError(f"weekday must be one of {WEEKDAYS_FULL}")

    def _validate_day_spec(self) -> None:
        """day_specのバリデーション（monthly用）"""
        if not self.day_spec:
            raise ValueError(
                "monthly schedules require day_spec (e.g., 15, 3rd_wed, last_fri, last_day)"
            )
        # MonthlyPattern.parseで検証（無効な場合は ValueError）
        MonthlyPattern.parse(self.day_spec)

    @property
    def monthly_type(self) -> str:
        """
        月次スケジュールタイプを返す。

        Returns:
            MonthlyType の値（文字列）。monthly以外は空文字を返す。

        Stage 3: バリデーションのドメイン層移行
        """
        if self.frequency != "monthly" or not self.day_spec:
            return ""
        pattern = MonthlyPattern.parse(self.day_spec)
        return pattern.type.value


class MonthlyType(Enum):
    """月次スケジュールのタイプ"""

    DATE = "date"  # 毎月N日
    NTH_WEEKDAY = "nth"  # 第N週の曜日
    LAST_WEEKDAY = "last_weekday"  # 最終週の曜日
    LAST_DAY = "last_day"  # 月末


# 月次条件判定コードのテンプレート（安全な固定パターン）
_CONDITION_TEMPLATES: dict[MonthlyType, str] = {
    MonthlyType.DATE: "today.day == {day_num}",
    MonthlyType.LAST_DAY: "(today + timedelta(days=1)).month != today.month",
    MonthlyType.LAST_WEEKDAY: (
        "today.weekday() == {weekday_num} and (today + timedelta(days=7)).month != today.month"
    ),
    MonthlyType.NTH_WEEKDAY: (
        "today.weekday() == {weekday_num} and ((today.day - 1) // 7 + 1) == {ordinal}"
    ),
}


@dataclass
class MonthlyPattern:
    """
    月次スケジュールパターン

    day_spec文字列（"15", "2nd_mon", "last_fri", "last_day"）を
    構造化されたデータとして保持する。
    """

    type: MonthlyType
    day_num: int | None = None  # DATE用（1-31）
    weekday: str | None = None  # 曜日指定用（mon, tue, wed, ...）
    ordinal: int | None = None  # NTH_WEEKDAY用（1-5）

    # 後方互換性のため残す（constants.VALID_WEEKDAYSを使用推奨）
    # VALID_WEEKDAYS = VALID_WEEKDAYS  # constants からインポート済み

    @classmethod
    def parse(cls, day_spec: str) -> MonthlyPattern:
        """
        day_spec文字列をパースしてMonthlyPatternを返す。

        Args:
            day_spec: "15", "2nd_mon", "last_fri", "last_day" などの形式

        Returns:
            MonthlyPattern インスタンス

        Raises:
            ValueError: 無効な形式の場合
        """
        # last_day
        if day_spec == "last_day":
            return cls(type=MonthlyType.LAST_DAY)

        # last_weekday: "last_mon", "last_tue", etc.
        if day_spec.startswith("last_") and day_spec != "last_day":
            weekday = day_spec[5:].lower()
            if weekday not in VALID_WEEKDAYS:
                raise ValueError(f"Invalid weekday: {weekday}")
            return cls(type=MonthlyType.LAST_WEEKDAY, weekday=weekday)

        # date: "15", "5", "31" etc.
        if re.match(r"^\d+$", day_spec):
            day_num = int(day_spec)
            # Stage 7: 入力バリデーション強化 - 日付範囲チェック
            if day_num < 1 or day_num > 31:
                raise ValueError(f"Invalid day of month: {day_num} (must be 1-31)")
            return cls(type=MonthlyType.DATE, day_num=day_num)

        # nth_weekday: "1st_mon", "2nd_tue", "3rd_wed", "4th_thu", "5th_fri"
        match = re.match(r"^(\d+)(st|nd|rd|th)_(\w+)$", day_spec)
        if match:
            ordinal = int(match.group(1))
            weekday = match.group(3).lower()
            # Stage 7: 入力バリデーション強化 - 序数範囲チェック
            if ordinal < 1 or ordinal > 5:
                raise ValueError(f"Invalid ordinal: {ordinal} (must be 1-5)")
            if weekday not in VALID_WEEKDAYS:
                raise ValueError(f"Invalid weekday: {weekday}")
            return cls(type=MonthlyType.NTH_WEEKDAY, ordinal=ordinal, weekday=weekday)

        raise ValueError(f"Invalid day_spec: {day_spec}")

    def generate_condition_code(self) -> str:
        """
        Runnerスクリプト用のPython条件判定コードを生成する。

        テンプレートベースの安全な実装。整数値のみを代入し、
        コードインジェクションのリスクを排除する。

        Returns:
            Python条件式の文字列
        """
        template = _CONDITION_TEMPLATES.get(self.type, "")
        if not template:
            return ""

        # 整数値のみを代入（安全）
        return template.format(
            day_num=int(self.day_num) if self.day_num else 0,
            weekday_num=self._weekday_to_num(self.weekday) if self.weekday else 0,
            ordinal=int(self.ordinal) if self.ordinal else 0,
        )

    @staticmethod
    def _weekday_to_num(weekday: str) -> int:
        """曜日文字列を数値（0=月曜, 6=日曜）に変換"""
        return ABBR_TO_WEEKDAY_NUM.get(weekday.lower(), 0)


@dataclass
class EssaySchedule:
    """
    エッセイ配信スケジュール

    schedules.json に保存されるスケジュール情報を表す。
    """

    name: str  # スケジュール名（一意）
    frequency: str  # "daily" | "weekly" | "monthly"
    time: str  # HH:MM 形式

    # 共通オプション
    theme: str = ""
    context: str = ""
    file_list: str = ""
    lang: str = "auto"

    # weekly用
    weekday: str = ""  # "monday", "tuesday", etc.

    # monthly用
    day_spec: str = ""  # "15", "2nd_mon", "last_fri", "last_day"
    monthly_type: str = ""  # MonthlyType の値（後方互換用）

    # メタデータ
    created: str = ""  # ISO形式の作成日時

    def to_dict(self) -> dict[str, Any]:
        """
        辞書に変換する。

        Returns:
            属性を含む辞書
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> EssaySchedule:
        """
        辞書からインスタンスを作成する。

        未知のキーは無視される。

        Args:
            d: 属性を含む辞書

        Returns:
            EssaySchedule インスタンス
        """
        # dataclassのフィールド名を取得
        valid_keys = {f.name for f in fields(cls)}

        # 有効なキーのみを抽出
        filtered = {k: v for k, v in d.items() if k in valid_keys}

        # デフォルト値を持つフィールドは省略可能
        return cls(**filtered)


# =============================================================================
# 後方互換性のための再エクスポート（exceptions.py から移動済み）
# 新規コードでは from domain.exceptions import ... を使用推奨
# =============================================================================

# DomainError, ValidationError はファイル先頭でインポート済み
__all__ = [
    "DomainError",
    "EssaySchedule",
    "MonthlyPattern",
    "MonthlyType",
    "ScheduleConfig",  # Stage 1: パラメータ蓄積問題の解消
    "TargetTime",
    "ValidationError",  # 後方互換性のため再エクスポート
]


@dataclass
class TargetTime:
    """
    ターゲット時刻のドメインモデル

    時刻解析ロジックを一元化し、実行時パース用のコード生成も提供する。
    wait_essay.pyとランナースクリプトで共通利用される。
    """

    datetime: datetime
    original_format: str  # "HH:MM" or "YYYY-MM-DD HH:MM"

    @classmethod
    def parse(cls, time_str: str) -> TargetTime:
        """
        時刻文字列をパースしてTargetTimeを返す。

        Args:
            time_str: HH:MM または YYYY-MM-DD HH:MM

        Returns:
            TargetTime インスタンス

        Raises:
            ValidationError: 無効な形式または過去の日時
        """
        # YYYY-MM-DD HH:MM 形式を試行
        if " " in time_str and len(time_str) > 10:
            try:
                target = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                if target < datetime.now():
                    raise ValidationError(f"Target time {time_str} is in the past")
                return cls(datetime=target, original_format="YYYY-MM-DD HH:MM")
            except ValueError as e:
                if "past" in str(e):
                    raise
                pass  # HH:MM形式を試行

        # HH:MM 形式（今日または明日）
        try:
            target = datetime.strptime(time_str, "%H:%M").replace(
                year=datetime.now().year, month=datetime.now().month, day=datetime.now().day
            )
            # 今日の指定時刻が過ぎていれば明日にスケジュール
            if target < datetime.now():
                target += timedelta(days=1)
            return cls(datetime=target, original_format="HH:MM")
        except ValueError as e:
            raise ValidationError(f"Invalid time format: {time_str}") from e

    def generate_parsing_code(self) -> str:
        """
        Runnerスクリプト用のPython時刻パースコードを生成する。

        Returns:
            実行可能なPythonコード文字列
        """
        time_str = (
            self.datetime.strftime("%H:%M")
            if self.original_format == "HH:MM"
            else self.datetime.strftime("%Y-%m-%d %H:%M")
        )

        return f'''time_str = "{time_str}"
if " " in time_str and len(time_str) > 10:
    target = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
else:
    target = datetime.strptime(time_str, "%H:%M").replace(
        year=datetime.now().year,
        month=datetime.now().month,
        day=datetime.now().day
    )
    if target < datetime.now():
        target += timedelta(days=1)'''
