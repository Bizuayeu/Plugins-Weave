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

    # =========================================================================
    # Stage 7: 入力バリデーション強化テスト
    # =========================================================================

    def test_parse_day_num_out_of_range_zero(self):
        """日付0でValueError（Stage 7: 入力バリデーション強化）"""
        with pytest.raises(ValueError, match="day"):
            MonthlyPattern.parse("0")

    def test_parse_day_num_out_of_range_32(self):
        """日付32でValueError（Stage 7: 入力バリデーション強化）"""
        with pytest.raises(ValueError, match="day"):
            MonthlyPattern.parse("32")

    def test_parse_day_num_valid_range_1(self):
        """日付1は有効（Stage 7: 入力バリデーション強化）"""
        result = MonthlyPattern.parse("1")
        assert result.day_num == 1

    def test_parse_day_num_valid_range_31(self):
        """日付31は有効（Stage 7: 入力バリデーション強化）"""
        result = MonthlyPattern.parse("31")
        assert result.day_num == 31

    def test_parse_ordinal_out_of_range_zero(self):
        """序数0でValueError（Stage 7: 入力バリデーション強化）"""
        with pytest.raises(ValueError, match="ordinal"):
            MonthlyPattern.parse("0th_mon")

    def test_parse_ordinal_out_of_range_6(self):
        """序数6でValueError（Stage 7: 入力バリデーション強化）"""
        with pytest.raises(ValueError, match="ordinal"):
            MonthlyPattern.parse("6th_mon")

    def test_parse_ordinal_valid_range_5(self):
        """序数5は有効（Stage 7: 入力バリデーション強化）"""
        result = MonthlyPattern.parse("5th_fri")
        assert result.ordinal == 5
        assert result.weekday == "fri"

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


class TestScheduleConfig:
    """ScheduleConfig Value Object のテスト（Stage 1: パラメータ蓄積問題の解消）"""

    def test_create_daily_config(self):
        """日次スケジュール設定の作成"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(
            frequency="daily",
            time_spec="09:00",
            theme="朝の振り返り",
        )
        assert config.frequency == "daily"
        assert config.time_spec == "09:00"
        assert config.theme == "朝の振り返り"

    def test_create_weekly_config(self):
        """週次スケジュール設定の作成"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(
            frequency="weekly",
            time_spec="10:00",
            weekday="monday",
        )
        assert config.frequency == "weekly"
        assert config.weekday == "monday"

    def test_create_monthly_config(self):
        """月次スケジュール設定の作成"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(
            frequency="monthly",
            time_spec="15:00",
            day_spec="last_fri",
        )
        assert config.frequency == "monthly"
        assert config.day_spec == "last_fri"

    def test_default_values(self):
        """デフォルト値の確認"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(frequency="daily", time_spec="12:00")
        assert config.theme == ""
        assert config.context_file == ""
        assert config.file_list == ""
        assert config.lang == ""
        assert config.weekday == ""
        assert config.day_spec == ""
        assert config.name == ""

    def test_all_parameters(self):
        """全パラメータを指定"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(
            frequency="monthly",
            time_spec="22:00",
            weekday="",
            theme="月次振り返り",
            context_file="/path/to/context.md",
            file_list="/path/to/files.txt",
            lang="ja",
            name="custom_name",
            day_spec="15",
        )
        assert config.frequency == "monthly"
        assert config.time_spec == "22:00"
        assert config.theme == "月次振り返り"
        assert config.context_file == "/path/to/context.md"
        assert config.file_list == "/path/to/files.txt"
        assert config.lang == "ja"
        assert config.name == "custom_name"
        assert config.day_spec == "15"

    def test_immutable_like_behavior(self):
        """dataclassとしての動作確認（frozen=Falseでも実質的に値オブジェクト）"""
        from domain.models import ScheduleConfig

        config1 = ScheduleConfig(frequency="daily", time_spec="09:00")
        config2 = ScheduleConfig(frequency="daily", time_spec="09:00")
        # dataclassは同じ値なら等価
        assert config1 == config2


class TestScheduleConfigValidation:
    """ScheduleConfig.validate() のテスト（Stage 3: バリデーションのドメイン層移行）"""

    def test_valid_daily_config(self):
        """有効なdaily設定は例外なし"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(frequency="daily", time_spec="22:00")
        config.validate()  # 例外なし

    def test_valid_weekly_config(self):
        """有効なweekly設定は例外なし"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(frequency="weekly", time_spec="22:00", weekday="monday")
        config.validate()  # 例外なし

    def test_valid_monthly_config(self):
        """有効なmonthly設定は例外なし"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(frequency="monthly", time_spec="22:00", day_spec="15")
        config.validate()  # 例外なし

    def test_invalid_frequency_raises(self):
        """無効なfrequencyはValueError"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(frequency="hourly", time_spec="22:00")
        with pytest.raises(ValueError, match="frequency must be"):
            config.validate()

    def test_weekly_without_weekday_raises(self):
        """weeklyでweekday未指定はValueError"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(frequency="weekly", time_spec="22:00", weekday="")
        with pytest.raises(ValueError, match="weekday"):
            config.validate()

    def test_weekly_with_invalid_weekday_raises(self):
        """weeklyで無効なweekdayはValueError"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(frequency="weekly", time_spec="22:00", weekday="xyz")
        with pytest.raises(ValueError, match="weekday"):
            config.validate()

    def test_monthly_without_day_spec_raises(self):
        """monthlyでday_spec未指定はValueError"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(frequency="monthly", time_spec="22:00", day_spec="")
        with pytest.raises(ValueError, match="day_spec"):
            config.validate()

    def test_invalid_time_format_raises(self):
        """無効な時刻形式はValueError"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(frequency="daily", time_spec="25:00")
        with pytest.raises(ValueError, match="HH:MM"):
            config.validate()

    def test_monthly_type_property(self):
        """monthly_type プロパティのテスト"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(frequency="monthly", time_spec="22:00", day_spec="last_fri")
        assert config.monthly_type == "last_weekday"

    def test_monthly_type_for_non_monthly(self):
        """非monthly設定ではmonthly_typeは空文字"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(frequency="daily", time_spec="22:00")
        assert config.monthly_type == ""
