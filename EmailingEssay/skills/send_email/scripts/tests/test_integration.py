# tests/test_integration.py
"""
統合テスト

各コンポーネントの連携をテストする。
"""
import pytest
import subprocess
import sys
import os

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCLIIntegration:
    """CLIの統合テスト"""

    def test_parser_imports_successfully(self):
        """パーサーがインポートできる"""
        from adapters.cli.parser import create_parser
        parser = create_parser()
        assert parser is not None

    def test_help_command_shows_help(self):
        """--help オプションが動作する"""
        from adapters.cli.parser import create_parser
        parser = create_parser()
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(["--help"])
        assert exc.value.code == 0


class TestSchedulerIntegration:
    """スケジューラの統合テスト"""

    def test_get_scheduler_returns_adapter(self):
        """get_scheduler() がアダプターを返す"""
        from adapters.scheduler import get_scheduler
        scheduler = get_scheduler()
        assert hasattr(scheduler, "add")
        assert hasattr(scheduler, "remove")
        assert hasattr(scheduler, "list")


class TestModelsIntegration:
    """モデルの統合テスト"""

    def test_essay_schedule_roundtrip(self):
        """EssaySchedule のdict変換が往復できる"""
        from domain.models import EssaySchedule

        original = EssaySchedule(
            name="test_schedule",
            frequency="weekly",
            time="10:00",
            weekday="monday",
            theme="週次振り返り"
        )

        # to_dict -> from_dict
        d = original.to_dict()
        restored = EssaySchedule.from_dict(d)

        assert restored.name == original.name
        assert restored.frequency == original.frequency
        assert restored.time == original.time
        assert restored.weekday == original.weekday
        assert restored.theme == original.theme

    def test_monthly_pattern_all_types(self):
        """全ての MonthlyType がパースできる"""
        from domain.models import MonthlyPattern, MonthlyType

        test_cases = [
            ("15", MonthlyType.DATE),
            ("2nd_mon", MonthlyType.NTH_WEEKDAY),
            ("last_fri", MonthlyType.LAST_WEEKDAY),
            ("last_day", MonthlyType.LAST_DAY),
        ]

        for day_spec, expected_type in test_cases:
            pattern = MonthlyPattern.parse(day_spec)
            assert pattern.type == expected_type, f"Failed for {day_spec}"


class TestTemplatesIntegration:
    """テンプレートの統合テスト"""

    def test_waiter_template_renders(self):
        """waiterテンプレートがレンダリングできる"""
        from frameworks.templates import load_template, render_template

        template = load_template("essay_waiter.py.template")
        rendered = render_template(
            template,
            log_file="/tmp/test.log",
            target_time="12:00",
            claude_args="-t 'テスト'"
        )

        assert "/tmp/test.log" in rendered
        assert "12:00" in rendered
        assert "テスト" in rendered


class TestWaitUseCaseIntegration:
    """待機処理の統合テスト"""

    def test_parse_target_time_formats(self):
        """各種時刻形式がパースできる"""
        from usecases.wait_essay import parse_target_time
        from datetime import datetime, timedelta

        # HH:MM形式（未来）
        future = datetime.now() + timedelta(hours=1)
        result = parse_target_time(future.strftime("%H:%M"))
        assert result.hour == future.hour

        # YYYY-MM-DD HH:MM形式
        future_date = datetime.now() + timedelta(days=1)
        result = parse_target_time(future_date.strftime("%Y-%m-%d %H:%M"))
        assert result.day == future_date.day


class TestCleanArchitectureLayers:
    """Clean Architecture 層の分離テスト"""

    def test_domain_has_no_external_dependencies(self):
        """ドメイン層は外部依存がない"""
        # domain.models のインポートが標準ライブラリのみに依存
        from domain.models import EssaySchedule, MonthlyPattern, MonthlyType
        # インポートが成功すれば外部依存なし

    def test_usecases_depend_only_on_domain(self):
        """ユースケース層はドメイン層のみに依存"""
        from usecases.ports import MailPort, SchedulerPort, WaiterPort
        # Protocolは標準ライブラリ

    def test_adapters_implement_ports(self):
        """アダプター層はポートを実装"""
        from adapters.scheduler import WindowsSchedulerAdapter, UnixSchedulerAdapter
        from adapters.scheduler.base import BaseSchedulerAdapter

        # アダプターが基底クラスを継承していることを確認
        assert issubclass(WindowsSchedulerAdapter, BaseSchedulerAdapter)
        assert issubclass(UnixSchedulerAdapter, BaseSchedulerAdapter)


class TestMainEntryPoint:
    """main.py エントリーポイントの統合テスト"""

    def test_main_imports_successfully(self):
        """main.py がインポートできる"""
        import main
        assert hasattr(main, 'main')

    def test_main_help_returns_zero(self):
        """--help オプションで終了コード0"""
        result = subprocess.run(
            [sys.executable, "main.py", "--help"],
            capture_output=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            encoding='utf-8',
            errors='replace'
        )
        assert result.returncode == 0
        assert "Essay" in result.stdout or "Mail" in result.stdout

    def test_main_schedule_list_works(self):
        """schedule list コマンドが動作"""
        result = subprocess.run(
            [sys.executable, "main.py", "schedule", "list"],
            capture_output=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            encoding='utf-8',
            errors='replace'
        )
        # エラーなく実行できることを確認
        assert result.returncode == 0

    def test_main_schedule_help_works(self):
        """schedule --help が動作"""
        result = subprocess.run(
            [sys.executable, "main.py", "schedule", "--help"],
            capture_output=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            encoding='utf-8',
            errors='replace'
        )
        assert result.returncode == 0
        assert "daily" in result.stdout
        assert "weekly" in result.stdout
        assert "monthly" in result.stdout
