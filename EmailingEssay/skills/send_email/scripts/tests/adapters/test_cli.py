# tests/adapters/test_cli.py
"""
CLI パーサーのテスト

argparse ベースの CLI インターフェースをテストする。
"""
import pytest
import sys
import os

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from adapters.cli.parser import create_parser, add_common_options


class TestCreateParser:
    """create_parser() のテスト"""

    @pytest.fixture
    def parser(self):
        return create_parser()

    def test_test_command(self, parser):
        """test コマンドのパース"""
        args = parser.parse_args(["test"])
        assert args.command == "test"

    def test_send_command(self, parser):
        """send コマンドのパース"""
        args = parser.parse_args(["send", "Subject", "Body"])
        assert args.command == "send"
        assert args.subject == "Subject"
        assert args.body == "Body"

    def test_wait_command_basic(self, parser):
        """wait コマンドの基本パース"""
        args = parser.parse_args(["wait", "09:30"])
        assert args.command == "wait"
        assert args.time == "09:30"

    def test_wait_command_with_options(self, parser):
        """wait コマンドのオプション付きパース"""
        args = parser.parse_args([
            "wait", "09:30",
            "-t", "test_theme",
            "-c", "/path/to/context.md",
            "-l", "ja"
        ])
        assert args.command == "wait"
        assert args.time == "09:30"
        assert args.theme == "test_theme"
        assert args.context == "/path/to/context.md"
        assert args.lang == "ja"

    def test_schedule_daily(self, parser):
        """schedule daily コマンドのパース"""
        args = parser.parse_args(["schedule", "daily", "09:00", "-t", "morning"])
        assert args.command == "schedule"
        assert args.schedule_cmd == "daily"
        assert args.time == "09:00"
        assert args.theme == "morning"

    def test_schedule_weekly(self, parser):
        """schedule weekly コマンドのパース"""
        args = parser.parse_args(["schedule", "weekly", "monday", "10:00"])
        assert args.command == "schedule"
        assert args.schedule_cmd == "weekly"
        assert args.weekday == "monday"
        assert args.time == "10:00"

    def test_schedule_monthly(self, parser):
        """schedule monthly コマンドのパース"""
        args = parser.parse_args(["schedule", "monthly", "last_fri", "15:00"])
        assert args.command == "schedule"
        assert args.schedule_cmd == "monthly"
        assert args.day_spec == "last_fri"
        assert args.time == "15:00"

    def test_schedule_list(self, parser):
        """schedule list コマンドのパース"""
        args = parser.parse_args(["schedule", "list"])
        assert args.command == "schedule"
        assert args.schedule_cmd == "list"

    def test_schedule_remove(self, parser):
        """schedule remove コマンドのパース"""
        args = parser.parse_args(["schedule", "remove", "task_name"])
        assert args.command == "schedule"
        assert args.schedule_cmd == "remove"
        assert args.name == "task_name"

    def test_common_options_defaults(self, parser):
        """共通オプションのデフォルト値"""
        args = parser.parse_args(["wait", "12:00"])
        assert args.theme == ""
        assert args.context == ""
        assert args.file_list == ""
        assert args.lang == "auto"

    def test_file_list_option(self, parser):
        """--file-list オプションのパース"""
        args = parser.parse_args(["wait", "12:00", "-f", "files.txt"])
        assert args.file_list == "files.txt"

    def test_name_option(self, parser):
        """--name オプションのパース"""
        args = parser.parse_args(["schedule", "daily", "09:00", "--name", "custom_name"])
        assert args.name == "custom_name"

    def test_help_does_not_error(self, parser):
        """--help オプションがエラーにならない"""
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(["--help"])
        assert exc.value.code == 0


class TestAddCommonOptions:
    """add_common_options() のテスト"""

    def test_adds_theme_option(self):
        """-t/--theme オプションが追加される"""
        import argparse
        parser = argparse.ArgumentParser()
        add_common_options(parser)
        args = parser.parse_args(["-t", "my_theme"])
        assert args.theme == "my_theme"

    def test_adds_context_option(self):
        """-c/--context オプションが追加される"""
        import argparse
        parser = argparse.ArgumentParser()
        add_common_options(parser)
        args = parser.parse_args(["-c", "/path/to/file"])
        assert args.context == "/path/to/file"

    def test_adds_lang_option(self):
        """-l/--lang オプションが追加される"""
        import argparse
        parser = argparse.ArgumentParser()
        add_common_options(parser)
        args = parser.parse_args(["-l", "en"])
        assert args.lang == "en"

    def test_lang_option_choices(self):
        """-l/--lang オプションの選択肢が正しい"""
        import argparse
        parser = argparse.ArgumentParser()
        add_common_options(parser)

        # 有効な値
        for lang in ["ja", "en", "auto"]:
            args = parser.parse_args(["-l", lang])
            assert args.lang == lang

        # 無効な値
        with pytest.raises(SystemExit):
            parser.parse_args(["-l", "invalid"])
