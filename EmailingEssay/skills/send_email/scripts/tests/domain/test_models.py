# tests/domain/test_models.py
"""
ドメインモデルのテスト

EssaySchedule と MonthlyPattern のテスト。
"""

import os
import sys

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from domain.models import EssaySchedule, MonthlyPattern, MonthlyType


class TestEssaySchedule:
    """EssaySchedule のテスト"""

    def test_create_daily_schedule(self):
        """日次スケジュールの作成"""
        schedule = EssaySchedule(
            name="morning_essay", frequency="daily", time="09:00", theme="朝の振り返り"
        )
        assert schedule.name == "morning_essay"
        assert schedule.frequency == "daily"
        assert schedule.time == "09:00"
        assert schedule.theme == "朝の振り返り"

    def test_create_weekly_schedule(self):
        """週次スケジュールの作成"""
        schedule = EssaySchedule(
            name="weekly_review", frequency="weekly", time="10:00", weekday="monday"
        )
        assert schedule.frequency == "weekly"
        assert schedule.weekday == "monday"

    def test_create_monthly_schedule(self):
        """月次スケジュールの作成"""
        schedule = EssaySchedule(
            name="monthly_summary", frequency="monthly", time="15:00", day_spec="last_fri"
        )
        assert schedule.frequency == "monthly"
        assert schedule.day_spec == "last_fri"

    def test_default_values(self):
        """デフォルト値の確認"""
        schedule = EssaySchedule(name="test", frequency="daily", time="12:00")
        assert schedule.theme == ""
        assert schedule.context == ""
        assert schedule.file_list == ""
        assert schedule.lang == "auto"
        assert schedule.weekday == ""
        assert schedule.day_spec == ""

    def test_to_dict(self):
        """to_dict() メソッドのテスト"""
        schedule = EssaySchedule(name="test", frequency="daily", time="09:00", theme="test_theme")
        d = schedule.to_dict()
        assert d["name"] == "test"
        assert d["frequency"] == "daily"
        assert d["time"] == "09:00"
        assert d["theme"] == "test_theme"
        assert isinstance(d, dict)

    def test_from_dict(self):
        """from_dict() メソッドのテスト"""
        d = {
            "name": "test",
            "frequency": "weekly",
            "time": "10:00",
            "weekday": "monday",
            "theme": "週次",
        }
        schedule = EssaySchedule.from_dict(d)
        assert schedule.name == "test"
        assert schedule.frequency == "weekly"
        assert schedule.weekday == "monday"
        assert schedule.theme == "週次"

    def test_from_dict_ignores_unknown_keys(self):
        """from_dict() が未知のキーを無視する"""
        d = {
            "name": "test",
            "frequency": "daily",
            "time": "09:00",
            "unknown_key": "value",
            "another_unknown": 123,
        }
        schedule = EssaySchedule.from_dict(d)
        assert schedule.name == "test"
        # 未知のキーがあってもエラーにならない

    def test_from_dict_with_missing_optional_keys(self):
        """from_dict() がオプショナルキーがなくても動作する"""
        d = {"name": "test", "frequency": "daily", "time": "09:00"}
        schedule = EssaySchedule.from_dict(d)
        assert schedule.theme == ""
        assert schedule.lang == "auto"


class TestMonthlyType:
    """MonthlyType のテスト"""

    def test_enum_values(self):
        """enum の値が正しい"""
        assert MonthlyType.DATE.value == "date"
        assert MonthlyType.NTH_WEEKDAY.value == "nth"
        assert MonthlyType.LAST_WEEKDAY.value == "last_weekday"
        assert MonthlyType.LAST_DAY.value == "last_day"


class TestMonthlyPattern:
    """MonthlyPattern のテスト"""

    def test_parse_date(self):
        """ "15" -> 毎月15日"""
        result = MonthlyPattern.parse("15")
        assert result.type == MonthlyType.DATE
        assert result.day_num == 15

    def test_parse_date_single_digit(self):
        """ "5" -> 毎月5日"""
        result = MonthlyPattern.parse("5")
        assert result.type == MonthlyType.DATE
        assert result.day_num == 5

    def test_parse_nth_weekday_1st(self):
        """ "1st_mon" -> 第1月曜"""
        result = MonthlyPattern.parse("1st_mon")
        assert result.type == MonthlyType.NTH_WEEKDAY
        assert result.ordinal == 1
        assert result.weekday == "mon"

    def test_parse_nth_weekday_2nd(self):
        """ "2nd_tue" -> 第2火曜"""
        result = MonthlyPattern.parse("2nd_tue")
        assert result.type == MonthlyType.NTH_WEEKDAY
        assert result.ordinal == 2
        assert result.weekday == "tue"

    def test_parse_nth_weekday_3rd(self):
        """ "3rd_wed" -> 第3水曜"""
        result = MonthlyPattern.parse("3rd_wed")
        assert result.type == MonthlyType.NTH_WEEKDAY
        assert result.ordinal == 3
        assert result.weekday == "wed"

    def test_parse_nth_weekday_4th(self):
        """ "4th_thu" -> 第4木曜"""
        result = MonthlyPattern.parse("4th_thu")
        assert result.type == MonthlyType.NTH_WEEKDAY
        assert result.ordinal == 4
        assert result.weekday == "thu"

    def test_parse_last_weekday(self):
        """ "last_fri" -> 最終金曜"""
        result = MonthlyPattern.parse("last_fri")
        assert result.type == MonthlyType.LAST_WEEKDAY
        assert result.weekday == "fri"

    def test_parse_last_day(self):
        """ "last_day" -> 月末"""
        result = MonthlyPattern.parse("last_day")
        assert result.type == MonthlyType.LAST_DAY

    def test_parse_invalid_format(self):
        """無効な形式でValueError"""
        with pytest.raises(ValueError):
            MonthlyPattern.parse("invalid")

    def test_parse_invalid_weekday_format(self):
        """無効な曜日でValueError"""
        with pytest.raises(ValueError):
            MonthlyPattern.parse("5th_xyz")  # xyzは有効な曜日ではない

    def test_generate_condition_code_date(self):
        """generate_condition_code() for DATE"""
        pattern = MonthlyPattern(type=MonthlyType.DATE, day_num=15)
        code = pattern.generate_condition_code()
        assert "day == 15" in code

    def test_generate_condition_code_last_day(self):
        """generate_condition_code() for LAST_DAY"""
        pattern = MonthlyPattern(type=MonthlyType.LAST_DAY)
        code = pattern.generate_condition_code()
        # 月末判定のコードが含まれる
        assert code != ""


class TestTargetTime:
    """TargetTime クラスのテスト（Item 3）"""

    def test_parse_hhmm_format(self):
        """HH:MM形式のパース"""
        from datetime import datetime

        from domain.models import TargetTime

        # 未来の時刻を作成
        now = datetime.now()
        future_hour = (now.hour + 2) % 24
        time_str = f"{future_hour:02d}:30"

        target = TargetTime.parse(time_str)
        assert target.datetime.hour == future_hour
        assert target.datetime.minute == 30
        assert target.original_format == "HH:MM"

    def test_parse_hhmm_past_rolls_to_tomorrow(self):
        """過去のHH:MM形式は翌日になる"""
        from datetime import datetime

        from domain.models import TargetTime

        # 過去の時刻を作成（今日の時刻より前）
        now = datetime.now()
        past_hour = (now.hour - 2) % 24
        time_str = f"{past_hour:02d}:00"

        target = TargetTime.parse(time_str)
        # 翌日になっているはず
        assert target.datetime > now

    def test_parse_datetime_format(self):
        """YYYY-MM-DD HH:MM形式のパース"""
        from datetime import datetime, timedelta

        from domain.models import TargetTime

        future = datetime.now() + timedelta(days=1)
        time_str = future.strftime("%Y-%m-%d %H:%M")

        target = TargetTime.parse(time_str)
        assert target.datetime.day == future.day
        assert target.original_format == "YYYY-MM-DD HH:MM"

    def test_parse_past_datetime_raises_error(self):
        """過去の日時指定でValidationError"""
        from datetime import datetime, timedelta

        from domain.models import TargetTime, ValidationError

        past = datetime.now() - timedelta(days=1)
        time_str = past.strftime("%Y-%m-%d %H:%M")

        with pytest.raises(ValidationError, match="past"):
            TargetTime.parse(time_str)

    def test_parse_invalid_format_raises_error(self):
        """無効な形式でValidationError"""
        from domain.models import TargetTime, ValidationError

        with pytest.raises(ValidationError, match="Invalid"):
            TargetTime.parse("not a time")

    def test_generate_parsing_code_contains_datetime(self):
        """生成コードにdatetimeが含まれる"""
        from domain.models import TargetTime

        target = TargetTime.parse("12:00")
        code = target.generate_parsing_code()
        assert "datetime" in code
        assert "12:00" in code

    def test_generate_parsing_code_is_valid_python(self):
        """生成コードが有効なPython"""
        from datetime import datetime, timedelta

        from domain.models import TargetTime

        target = TargetTime.parse("23:59")
        code = target.generate_parsing_code()
        # 構文エラーがなく実行可能
        exec(f"from datetime import datetime, timedelta\n{code}")
