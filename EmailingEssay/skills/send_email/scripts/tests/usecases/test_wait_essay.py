# tests/usecases/test_wait_essay.py
"""
待機処理のテスト

parse_target_time と spawn_waiter のテスト。
"""

import os
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from usecases.wait_essay import WaiterError, WaitEssayUseCase, get_persistent_dir, parse_target_time


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
    def mock_waiter_storage(self):
        """WaiterStoragePort用モック"""
        storage = Mock()
        storage.register_waiter.return_value = None
        storage.get_active_waiters.return_value = []
        return storage

    @pytest.fixture
    def mock_path_resolver(self, tmp_path):
        """PathResolverPort用モック"""
        resolver = Mock()
        resolver.get_persistent_dir.return_value = str(tmp_path)
        return resolver

    @pytest.fixture
    def mock_spawner(self):
        """モックスポーナーを作成"""
        spawner = Mock()
        spawner.spawn_detached.return_value = 12345
        return spawner

    @pytest.fixture
    def usecase(self, mock_waiter_storage, mock_path_resolver, mock_spawner):
        """DI済みユースケースを作成"""
        return WaitEssayUseCase(
            waiter_storage=mock_waiter_storage,
            path_resolver=mock_path_resolver,
            spawner_port=mock_spawner,
        )

    def test_spawn_creates_script_file(self, usecase, tmp_path):
        """spawn() がスクリプトファイルを作成"""
        # 1時間後の時刻
        future_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")

        usecase.spawn(
            target_time=future_time, theme="test_theme", context="", file_list="", lang="ja"
        )

        # スクリプトファイルが作成されたことを確認
        script_file = tmp_path / "essay_waiter_temp.py"
        assert script_file.exists()

    def test_spawn_starts_detached_process(self, usecase, mock_spawner):
        """spawn() がデタッチドプロセスを起動"""
        future_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")

        usecase.spawn(target_time=future_time, theme="", context="", file_list="", lang="")

        mock_spawner.spawn_detached.assert_called_once()

    def test_spawn_includes_theme_in_script(self, usecase, tmp_path):
        """spawn() がテーマをスクリプトに含める"""
        future_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")

        usecase.spawn(
            target_time=future_time, theme="朝の振り返り", context="", file_list="", lang=""
        )

        script_file = tmp_path / "essay_waiter_temp.py"
        content = script_file.read_text(encoding="utf-8")
        assert "朝の振り返り" in content

    def test_spawn_returns_pid(self, usecase, mock_spawner):
        """spawn() がプロセスIDを返す"""
        future_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")

        pid = usecase.spawn(target_time=future_time)

        assert pid == 12345

    def test_spawn_uses_injected_path_resolver(self, mock_waiter_storage, mock_path_resolver, mock_spawner):
        """spawn() がDIされたPathResolverを使用する"""
        usecase = WaitEssayUseCase(
            waiter_storage=mock_waiter_storage,
            path_resolver=mock_path_resolver,
            spawner_port=mock_spawner,
        )
        future_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")

        usecase.spawn(target_time=future_time)

        mock_path_resolver.get_persistent_dir.assert_called()


class TestWaitEssayUseCaseDI:
    """DI必須化のテスト"""

    def test_usecase_requires_waiter_storage(self):
        """waiter_storageは必須"""
        with pytest.raises(TypeError):
            WaitEssayUseCase(path_resolver=Mock(), spawner_port=Mock())

    def test_usecase_requires_path_resolver(self):
        """path_resolverは必須"""
        with pytest.raises(TypeError):
            WaitEssayUseCase(waiter_storage=Mock(), spawner_port=Mock())

    def test_usecase_requires_spawner_port(self):
        """spawner_portは必須"""
        with pytest.raises(TypeError):
            WaitEssayUseCase(waiter_storage=Mock(), path_resolver=Mock())

    def test_usecase_works_with_all_ports(self):
        """全て指定で正常動作"""
        usecase = WaitEssayUseCase(
            waiter_storage=Mock(),
            path_resolver=Mock(),
            spawner_port=Mock(),
        )
        assert usecase is not None


class TestWaitEssayUseCaseSeparatedPorts:
    """分離Port使用のテスト（Phase C: StoragePort除去）"""

    @pytest.fixture
    def mock_waiter_storage(self):
        """WaiterStoragePort用モック"""
        storage = Mock()
        storage.register_waiter.return_value = None
        storage.get_active_waiters.return_value = []
        return storage

    @pytest.fixture
    def mock_path_resolver(self, tmp_path):
        """PathResolverPort用モック"""
        resolver = Mock()
        resolver.get_persistent_dir.return_value = str(tmp_path)
        resolver.get_runners_dir.return_value = str(tmp_path / "runners")
        return resolver

    @pytest.fixture
    def mock_spawner(self):
        """ProcessSpawnerPort用モック"""
        spawner = Mock()
        spawner.spawn_detached.return_value = 12345
        return spawner

    def test_constructor_accepts_separated_ports(
        self, mock_waiter_storage, mock_path_resolver, mock_spawner
    ):
        """コンストラクタが分離されたポートを受け取る"""
        usecase = WaitEssayUseCase(
            waiter_storage=mock_waiter_storage,
            path_resolver=mock_path_resolver,
            spawner_port=mock_spawner,
        )
        assert usecase is not None

    def test_spawn_uses_path_resolver(
        self, mock_waiter_storage, mock_path_resolver, mock_spawner
    ):
        """spawn()がPathResolverPortを使用する"""
        usecase = WaitEssayUseCase(
            waiter_storage=mock_waiter_storage,
            path_resolver=mock_path_resolver,
            spawner_port=mock_spawner,
        )
        future_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")
        usecase.spawn(target_time=future_time)
        mock_path_resolver.get_persistent_dir.assert_called()

    def test_spawn_uses_waiter_storage(
        self, mock_waiter_storage, mock_path_resolver, mock_spawner
    ):
        """spawn()がWaiterStoragePortを使用する"""
        usecase = WaitEssayUseCase(
            waiter_storage=mock_waiter_storage,
            path_resolver=mock_path_resolver,
            spawner_port=mock_spawner,
        )
        future_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")
        usecase.spawn(target_time=future_time, theme="test")
        mock_waiter_storage.register_waiter.assert_called_once()

    def test_list_waiters_uses_waiter_storage(
        self, mock_waiter_storage, mock_path_resolver, mock_spawner
    ):
        """list_waiters()がWaiterStoragePortを使用する"""
        usecase = WaitEssayUseCase(
            waiter_storage=mock_waiter_storage,
            path_resolver=mock_path_resolver,
            spawner_port=mock_spawner,
        )
        usecase.list_waiters()
        mock_waiter_storage.get_active_waiters.assert_called_once()


class TestGetPersistentDir:
    """get_persistent_dir() のテスト"""

    def test_persistent_dir_uses_claude_convention(self):
        """永続ディレクトリは ~/.claude/plugins/.emailingessay を使用する"""
        result = get_persistent_dir()
        # Claude Code plugin convention: ~/.claude/plugins/.emailingessay
        assert ".claude" in result and "plugins" in result and ".emailingessay" in result
