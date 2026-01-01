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

from usecases.wait_essay import parse_target_time, WaitEssayUseCase, WaiterError, get_persistent_dir


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
    def mock_storage(self, tmp_path):
        """モックストレージを作成"""
        storage = Mock()
        storage.get_persistent_dir.return_value = str(tmp_path)
        return storage

    @pytest.fixture
    def mock_spawner(self):
        """モックスポーナーを作成"""
        spawner = Mock()
        spawner.spawn_detached.return_value = 12345
        return spawner

    @pytest.fixture
    def usecase(self, mock_storage, mock_spawner):
        """DI済みユースケースを作成"""
        return WaitEssayUseCase(
            storage_port=mock_storage,
            spawner_port=mock_spawner
        )

    def test_spawn_creates_script_file(self, usecase, tmp_path):
        """spawn() がスクリプトファイルを作成"""
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

    def test_spawn_starts_detached_process(self, usecase, mock_spawner):
        """spawn() がデタッチドプロセスを起動"""
        future_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")

        usecase.spawn(
            target_time=future_time,
            theme="",
            context="",
            file_list="",
            lang=""
        )

        mock_spawner.spawn_detached.assert_called_once()

    def test_spawn_includes_theme_in_script(self, usecase, tmp_path):
        """spawn() がテーマをスクリプトに含める"""
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

    def test_spawn_returns_pid(self, usecase, mock_spawner):
        """spawn() がプロセスIDを返す"""
        future_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")

        pid = usecase.spawn(target_time=future_time)

        assert pid == 12345

    def test_spawn_uses_injected_storage(self, mock_storage, mock_spawner):
        """spawn() がDIされたストレージを使用する"""
        usecase = WaitEssayUseCase(
            storage_port=mock_storage,
            spawner_port=mock_spawner
        )
        future_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")

        usecase.spawn(target_time=future_time)

        mock_storage.get_persistent_dir.assert_called()


class TestWaitEssayUseCaseDI:
    """DI必須化のテスト"""

    def test_usecase_requires_storage_port(self):
        """storage_portは必須"""
        with pytest.raises(TypeError):
            WaitEssayUseCase(spawner_port=Mock())

    def test_usecase_requires_spawner_port(self):
        """spawner_portは必須"""
        with pytest.raises(TypeError):
            WaitEssayUseCase(storage_port=Mock())

    def test_usecase_works_with_both_ports(self):
        """両方指定で正常動作"""
        usecase = WaitEssayUseCase(
            storage_port=Mock(),
            spawner_port=Mock()
        )
        assert usecase is not None


class TestGetPersistentDir:
    """get_persistent_dir() のテスト"""

    def test_persistent_dir_uses_claude_convention(self):
        """永続ディレクトリは ~/.claude/plugins/.emailingessay を使用する"""
        result = get_persistent_dir()
        # Claude Code plugin convention: ~/.claude/plugins/.emailingessay
        assert ".claude" in result and "plugins" in result and ".emailingessay" in result
