#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_digest_times.py CLI統合テスト

TDD Phase 1-2: update_direct() CLIの統合テスト
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest
from test_helpers import create_default_config, create_standard_test_structure


class TestUpdateDigestTimesCLI(unittest.TestCase):
    """update_digest_times.py CLI統合テスト"""

    def setUp(self) -> None:
        """テスト用の一時ディレクトリを作成"""
        self.temp_dir = Path(tempfile.mkdtemp())
        # 標準テスト構造を作成（helper関数使用）
        paths = create_standard_test_structure(self.temp_dir)
        self.plugin_dir = paths["config_dir"]
        # config.json作成（正しいフォーマット）
        create_default_config(self.plugin_dir)

    def tearDown(self) -> None:
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.integration
    def test_update_loop_last_processed(self) -> None:
        """loopレベルのlast_processedを更新"""
        from interfaces.update_digest_times import main

        with patch(
            "sys.argv",
            ["update_digest_times.py", "loop", "259", "--plugin-root", str(self.temp_dir)],
        ):
            with patch("builtins.print") as mock_print:
                main()
                # 出力確認
                mock_print.assert_called()
                output = str(mock_print.call_args)
                assert "259" in output or "更新完了" in output

        # ファイル内容確認
        times_file = self.plugin_dir / "last_digest_times.json"
        assert times_file.exists()
        data = json.loads(times_file.read_text(encoding="utf-8"))
        assert data["loop"]["last_processed"] == 259

    @pytest.mark.integration
    def test_update_weekly_last_processed(self) -> None:
        """weeklyレベルのlast_processedを更新"""
        from interfaces.update_digest_times import main

        with patch(
            "sys.argv",
            ["update_digest_times.py", "weekly", "51", "--plugin-root", str(self.temp_dir)],
        ):
            with patch("builtins.print"):
                main()

        times_file = self.plugin_dir / "last_digest_times.json"
        data = json.loads(times_file.read_text(encoding="utf-8"))
        assert data["weekly"]["last_processed"] == 51

    @pytest.mark.integration
    def test_invalid_level_raises_error(self) -> None:
        """無効なレベル指定でエラー"""
        from interfaces.update_digest_times import main

        with patch(
            "sys.argv",
            ["update_digest_times.py", "invalid_level", "259", "--plugin-root", str(self.temp_dir)],
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
            "sys.argv", ["update_digest_times.py", "loop", "--plugin-root", str(self.temp_dir)]
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0

    @pytest.mark.integration
    def test_preserves_existing_levels(self) -> None:
        """既存レベルのデータを保持"""
        # 事前データ作成
        times_file = self.plugin_dir / "last_digest_times.json"
        initial_data = {"weekly": {"timestamp": "2025-01-01T00:00:00", "last_processed": 40}}
        times_file.write_text(json.dumps(initial_data, ensure_ascii=False), encoding="utf-8")

        from interfaces.update_digest_times import main

        with patch(
            "sys.argv",
            ["update_digest_times.py", "loop", "259", "--plugin-root", str(self.temp_dir)],
        ):
            with patch("builtins.print"):
                main()

        data = json.loads(times_file.read_text(encoding="utf-8"))
        assert data["loop"]["last_processed"] == 259
        assert data["weekly"]["last_processed"] == 40  # 既存データ保持


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
