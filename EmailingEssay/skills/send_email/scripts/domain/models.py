# domain/models.py
"""
ドメインモデル

Entities層: ビジネスルールとドメインモデルを定義する。
外部依存なし（最内側）。
"""
from dataclasses import dataclass, asdict, field, fields
from typing import Optional, Any
from enum import Enum
import re


class MonthlyType(Enum):
    """月次スケジュールのタイプ"""
    DATE = "date"               # 毎月N日
    NTH_WEEKDAY = "nth"         # 第N週の曜日
    LAST_WEEKDAY = "last_weekday"  # 最終週の曜日
    LAST_DAY = "last_day"       # 月末


@dataclass
class MonthlyPattern:
    """
    月次スケジュールパターン

    day_spec文字列（"15", "2nd_mon", "last_fri", "last_day"）を
    構造化されたデータとして保持する。
    """
    type: MonthlyType
    day_num: Optional[int] = None      # DATE用（1-31）
    weekday: Optional[str] = None      # 曜日指定用（mon, tue, wed, ...）
    ordinal: Optional[int] = None      # NTH_WEEKDAY用（1-5）

    # 有効な曜日のセット
    VALID_WEEKDAYS = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}

    @classmethod
    def parse(cls, day_spec: str) -> "MonthlyPattern":
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
            if weekday not in cls.VALID_WEEKDAYS:
                raise ValueError(f"Invalid weekday: {weekday}")
            return cls(type=MonthlyType.LAST_WEEKDAY, weekday=weekday)

        # date: "15", "5", "31" etc.
        if re.match(r"^\d+$", day_spec):
            return cls(type=MonthlyType.DATE, day_num=int(day_spec))

        # nth_weekday: "1st_mon", "2nd_tue", "3rd_wed", "4th_thu", "5th_fri"
        match = re.match(r"^(\d+)(st|nd|rd|th)_(\w+)$", day_spec)
        if match:
            ordinal = int(match.group(1))
            weekday = match.group(3).lower()
            if weekday not in cls.VALID_WEEKDAYS:
                raise ValueError(f"Invalid weekday: {weekday}")
            return cls(type=MonthlyType.NTH_WEEKDAY, ordinal=ordinal, weekday=weekday)

        raise ValueError(f"Invalid day_spec: {day_spec}")

    def generate_condition_code(self) -> str:
        """
        Runnerスクリプト用のPython条件判定コードを生成する。

        Returns:
            Python条件式の文字列
        """
        if self.type == MonthlyType.DATE:
            return f"today.day == {self.day_num}"

        if self.type == MonthlyType.LAST_DAY:
            return "(today + timedelta(days=1)).month != today.month"

        if self.type == MonthlyType.LAST_WEEKDAY:
            weekday_num = self._weekday_to_num(self.weekday)
            return (
                f"today.weekday() == {weekday_num} and "
                f"(today + timedelta(days=7)).month != today.month"
            )

        if self.type == MonthlyType.NTH_WEEKDAY:
            weekday_num = self._weekday_to_num(self.weekday)
            return (
                f"today.weekday() == {weekday_num} and "
                f"((today.day - 1) // 7 + 1) == {self.ordinal}"
            )

        return ""

    @staticmethod
    def _weekday_to_num(weekday: str) -> int:
        """曜日文字列を数値（0=月曜, 6=日曜）に変換"""
        mapping = {
            "mon": 0, "tue": 1, "wed": 2, "thu": 3,
            "fri": 4, "sat": 5, "sun": 6
        }
        return mapping.get(weekday.lower(), 0)


@dataclass
class EssaySchedule:
    """
    エッセイ配信スケジュール

    schedules.json に保存されるスケジュール情報を表す。
    """
    name: str               # スケジュール名（一意）
    frequency: str          # "daily" | "weekly" | "monthly"
    time: str               # HH:MM 形式

    # 共通オプション
    theme: str = ""
    context: str = ""
    file_list: str = ""
    lang: str = "auto"

    # weekly用
    weekday: str = ""       # "monday", "tuesday", etc.

    # monthly用
    day_spec: str = ""      # "15", "2nd_mon", "last_fri", "last_day"
    monthly_type: str = ""  # MonthlyType の値（後方互換用）

    # メタデータ
    created: str = ""       # ISO形式の作成日時

    def to_dict(self) -> dict[str, Any]:
        """
        辞書に変換する。

        Returns:
            属性を含む辞書
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EssaySchedule":
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
# ドメインエラー
# =============================================================================

class DomainError(Exception):
    """ドメイン層の基底例外"""
    pass


class ValidationError(DomainError):
    """バリデーションエラー"""
    pass
