#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_digest_times.py CLI統合テスト

TDD Phase 1-2: update_direct() CLIの統合テスト
"""

import json
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest
from test_helpers import TempPluginEnvironment


class TestUpdateDigestTimesCLI(unittest.TestCase):
    """update_digest_times.py CLI統合テスト"""

    def setUp(self) -> None:
        """テスト用の一時ディレクトリを作成"""
        self.env = TempPluginEnvironment()
        self.env.__enter__()
        self.temp_dir = self.env.plugin_root
        self.persistent_dir = self.env.persistent_config_dir

    def tearDown(self) -> None:
        """一時ディレクトリを削除"""
        self.env.__exit__(None, None, None)

    @pytest.mark.integration
    def test_update_loop_last_processed(self) -> None:
        """loopレベルのlast_processedを更新"""
        from interfaces.update_digest_times import main

        with patch(
            "sys.argv",
            ["update_digest_times.py", "loop", "259"],
        ):
            with patch("builtins.print") as mock_print:
                main()
                # 出力確認
                mock_print.assert_called()
                output = str(mock_print.call_args)
                assert "259" in output or "更新完了" in output

        # ファイル内容確認（永続化ディレクトリに保存される）
        times_file = self.persistent_dir / "last_digest_times.json"
        assert times_file.exists()
        data = json.loads(times_file.read_text(encoding="utf-8"))
        assert data["loop"]["last_processed"] == 259

    @pytest.mark.integration
    def test_update_weekly_last_processed(self) -> None:
        """weeklyレベルのlast_processedを更新"""
        from interfaces.update_digest_times import main

        with patch(
            "sys.argv",
            ["update_digest_times.py", "weekly", "51"],
        ):
            with patch("builtins.print"):
                main()

        # 永続化ディレクトリをチェック
        times_file = self.persistent_dir / "last_digest_times.json"
        data = json.loads(times_file.read_text(encoding="utf-8"))
        assert data["weekly"]["last_processed"] == 51

    @pytest.mark.integration
    def test_invalid_level_raises_error(self) -> None:
        """無効なレベル指定でエラー"""
        from interfaces.update_digest_times import main

        with patch(
            "sys.argv",
            ["update_digest_times.py", "invalid_level", "259"],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0

    @pytest.mark.integration
    def test_missing_arguments_shows_usage(self) -> None:
        """引数不足でエラー"""
        from interfaces.update_digest_times import main

        with patch("sys.argv", ["update_digest_times.py"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0

    @pytest.mark.integration
    def test_missing_last_processed_shows_usage(self) -> None:
        """last_processed引数不足でエラー"""
        from interfaces.update_digest_times import main

        with patch(
            "sys.argv", ["update_digest_times.py", "loop"]
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0

    @pytest.mark.integration
    def test_preserves_existing_levels(self) -> None:
        """既存レベルのデータを保持"""
        # 事前データ作成（永続化ディレクトリに保存）
        times_file = self.persistent_dir / "last_digest_times.json"
        initial_data = {"weekly": {"timestamp": "2025-01-01T00:00:00", "last_processed": 40}}
        times_file.write_text(json.dumps(initial_data, ensure_ascii=False), encoding="utf-8")

        from interfaces.update_digest_times import main

        with patch(
            "sys.argv",
            ["update_digest_times.py", "loop", "259"],
        ):
            with patch("builtins.print"):
                main()

        data = json.loads(times_file.read_text(encoding="utf-8"))
        assert data["loop"]["last_processed"] == 259
        assert data["weekly"]["last_processed"] == 40  # 既存データ保持


class TestUpdateDigestTimesErrorHandling(unittest.TestCase):
    """エラーハンドリングのテスト"""

    def setUp(self) -> None:
        """テスト用の一時ディレクトリを作成"""
        self.env = TempPluginEnvironment()
        self.env.__enter__()
        self.temp_dir = self.env.plugin_root
        self.persistent_dir = self.env.persistent_config_dir

    def tearDown(self) -> None:
        """一時ディレクトリを削除"""
        self.env.__exit__(None, None, None)

    @pytest.mark.integration
    def test_episodic_rag_error_handling(self) -> None:
        """EpisodicRAGErrorが発生した場合のエラーハンドリング"""
        from domain.exceptions import EpisodicRAGError
        from interfaces.update_digest_times import main

        with patch(
            "sys.argv",
            ["update_digest_times.py", "loop", "259"],
        ):
            with patch(
                "interfaces.update_digest_times.DigestTimesTracker.update_direct",
                side_effect=EpisodicRAGError("Test error"),
            ):
                with patch("interfaces.update_digest_times.log_error") as mock_log:
                    main()
                    mock_log.assert_called_once()
                    call_args = mock_log.call_args
                    assert "Test error" in str(call_args)

    @pytest.mark.integration
    def test_os_error_handling(self) -> None:
        """OSErrorが発生した場合のエラーハンドリング"""
        from interfaces.update_digest_times import main

        with patch(
            "sys.argv",
            ["update_digest_times.py", "loop", "259"],
        ):
            with patch(
                "interfaces.update_digest_times.DigestTimesTracker.update_direct",
                side_effect=OSError("Permission denied"),
            ):
                with patch("interfaces.update_digest_times.log_error") as mock_log:
                    main()
                    mock_log.assert_called_once()
                    call_args = mock_log.call_args
                    assert "File I/O error" in str(call_args)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
