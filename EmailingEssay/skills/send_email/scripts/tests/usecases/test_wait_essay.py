# tests/usecases/test_wait_essay.py
"""
待機処理のテスト

parse_target_time と spawn_waiter のテスト。
"""
import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from usecases.wait_essay import parse_target_time, WaitEssayUseCase, WaiterError


class TestParseTargetTime:
    """parse_target_time() のテスト"""

    def test_parse_hhmm_format_future(self):
        """HH:MM形式（未来）のパース"""
        # 1時間後の時刻をテスト
        future_time = datetime.now() + timedelta(hours=1)
        time_str = future_time.strftime("%H:%M")

        result = parse_target_time(time_str)

        assert result.hour == future_time.hour
        assert result.minute == future_time.minute

    def test_parse_hhmm_format_past_schedules_tomorrow(self):
        """HH:MM形式（過去）は翌日にスケジュール"""
        # 1時間前の時刻をテスト
        past_time = datetime.now() - timedelta(hours=1)
        time_str = past_time.strftime("%H:%M")

        result = parse_target_time(time_str)

        # 翌日にスケジュールされるはず
        expected = datetime.now() + timedelta(days=1)
        assert result.day == expected.day or result > datetime.now()

    def test_parse_datetime_format(self):
        """YYYY-MM-DD HH:MM形式のパース"""
        # 明日の時刻をテスト
        future = datetime.now() + timedelta(days=1)
        time_str = future.strftime("%Y-%m-%d %H:%M")

        result = parse_target_time(time_str)

        assert result.year == future.year
        assert result.month == future.month
        assert result.day == future.day

    def test_parse_datetime_past_raises_error(self):
        """過去の日時指定でエラー"""
        past = datetime.now() - timedelta(days=1)
        time_str = past.strftime("%Y-%m-%d %H:%M")

        with pytest.raises(ValueError, match="past"):
            parse_target_time(time_str)

    def test_parse_invalid_format_raises_error(self):
        """無効な形式でエラー"""
        with pytest.raises(ValueError):
            parse_target_time("invalid")


class TestWaitEssayUseCase:
    """WaitEssayUseCase のテスト"""

    @pytest.fixture
    def usecase(self):
        return WaitEssayUseCase()

    @patch('subprocess.Popen')
    @patch('usecases.wait_essay.get_persistent_dir')
    def test_spawn_creates_script_file(self, mock_dir, mock_popen, usecase, tmp_path):
        """spawn() がスクリプトファイルを作成"""
        mock_dir.return_value = str(tmp_path)
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        # 1時間後の時刻
        future_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")

        usecase.spawn(
            target_time=future_time,
            theme="test_theme",
            context="",
            file_list="",
            lang="ja"
        )

        # スクリプトファイルが作成されたことを確認
        script_file = tmp_path / "essay_waiter_temp.py"
        assert script_file.exists()

    @patch('subprocess.Popen')
    @patch('usecases.wait_essay.get_persistent_dir')
    def test_spawn_starts_detached_process(self, mock_dir, mock_popen, usecase, tmp_path):
        """spawn() がデタッチドプロセスを起動"""
        mock_dir.return_value = str(tmp_path)
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        future_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")

        usecase.spawn(
            target_time=future_time,
            theme="",
            context="",
            file_list="",
            lang=""
        )

        mock_popen.assert_called_once()

    @patch('subprocess.Popen')
    @patch('usecases.wait_essay.get_persistent_dir')
    def test_spawn_includes_theme_in_script(self, mock_dir, mock_popen, usecase, tmp_path):
        """spawn() がテーマをスクリプトに含める"""
        mock_dir.return_value = str(tmp_path)
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        future_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")

        usecase.spawn(
            target_time=future_time,
            theme="朝の振り返り",
            context="",
            file_list="",
            lang=""
        )

        script_file = tmp_path / "essay_waiter_temp.py"
        content = script_file.read_text(encoding="utf-8")
        assert "朝の振り返り" in content
