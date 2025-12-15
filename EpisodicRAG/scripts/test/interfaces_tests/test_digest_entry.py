#!/usr/bin/env python3
"""
digest_entry テスト
===================

/digest コマンドエントリポイントのTDDテスト。
"""

import json
import os
from pathlib import Path
from typing import Dict
from unittest.mock import MagicMock, patch

import pytest

from interfaces.digest_entry import (
    DigestEntryResult,
    format_text_output,
    get_paths_from_config,
    run_pattern1,
    run_pattern2,
)
from interfaces.shadow_state_checker import ShadowStateResult


@pytest.fixture
def persistent_config_env(tmp_path: Path):
    """永続化設定ディレクトリを設定してテストに提供するフィクスチャ"""
    persistent_config = tmp_path / ".persistent_config"
    persistent_config.mkdir(parents=True)
    (tmp_path / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    old_env = os.environ.get("EPISODICRAG_CONFIG_DIR")
    os.environ["EPISODICRAG_CONFIG_DIR"] = str(persistent_config)
    yield {"tmp_path": tmp_path, "persistent_config": persistent_config}
    # Cleanup
    if old_env is not None:
        os.environ["EPISODICRAG_CONFIG_DIR"] = old_env
    else:
        os.environ.pop("EPISODICRAG_CONFIG_DIR", None)


# =============================================================================
# DigestEntryResult データクラステスト
# =============================================================================


class TestDigestEntryResult:
    """DigestEntryResult のテスト"""

    def test_result_with_minimal_args(self) -> None:
        """最小限の引数で初期化"""
        result = DigestEntryResult(status="ok", pattern=1)
        assert result.status == "ok"
        assert result.pattern == 1
        assert result.base_dir is None
        assert result.new_loops == []
        assert result.error is None

    def test_result_pattern1_success(self) -> None:
        """Pattern 1 成功時の構造"""
        result = DigestEntryResult(
            status="ok",
            pattern=1,
            base_dir="/path/to/plugin",
            loops_path="/path/to/loops",
            digests_path="/path/to/digests",
            essences_path="/path/to/essences",
            new_loops=["Loop_0001", "Loop_0002"],
            new_loops_count=2,
            weekly_source_count=3,
            weekly_threshold=5,
            message="新規Loop 2個を検出",
        )
        assert result.status == "ok"
        assert result.pattern == 1
        assert len(result.new_loops) == 2
        assert result.new_loops_count == 2

    def test_result_pattern2_success(self) -> None:
        """Pattern 2 成功時の構造"""
        result = DigestEntryResult(
            status="ok",
            pattern=2,
            base_dir="/path/to/plugin",
            level="weekly",
            shadow_state={"source_count": 5, "analyzed": True},
            message="weekly 確定準備",
        )
        assert result.status == "ok"
        assert result.pattern == 2
        assert result.level == "weekly"
        assert result.shadow_state is not None

    def test_result_error(self) -> None:
        """エラー時の構造"""
        result = DigestEntryResult(
            status="error",
            pattern=1,
            error="EpisodicRAG plugin not found",
        )
        assert result.status == "error"
        assert result.error is not None


# =============================================================================
# get_paths_from_config テスト
# =============================================================================


class TestGetPathsFromConfig:
    """get_paths_from_config のテスト"""

    def test_loads_paths_from_config(self, persistent_config_env) -> None:
        """config.jsonからパスを読み込む"""
        tmp_path = persistent_config_env["tmp_path"]
        persistent_config = persistent_config_env["persistent_config"]
        # テスト用config.jsonを作成（永続化ディレクトリに）
        config_file = persistent_config / "config.json"
        config_file.write_text(
            json.dumps(
                {
                    "base_dir": str(tmp_path),
                    "paths": {
                        "loops_dir": "data/Loops",
                        "digests_dir": "data/Digests",
                        "essences_dir": "data/Essences",
                    },
                    "levels": {"weekly_threshold": 7},
                }
            )
        )

        paths = get_paths_from_config()

        assert "loops_path" in paths
        assert "digests_path" in paths
        assert "essences_path" in paths
        assert paths["weekly_threshold"] == 7

    def test_uses_defaults_when_keys_missing(self, persistent_config_env) -> None:
        """キーがない場合はデフォルト値を使用"""
        tmp_path = persistent_config_env["tmp_path"]
        persistent_config = persistent_config_env["persistent_config"]
        # config.jsonを作成（永続化ディレクトリに、base_dirは必須）
        config_file = persistent_config / "config.json"
        config_file.write_text(json.dumps({"base_dir": str(tmp_path)}))

        paths = get_paths_from_config()

        assert "loops_path" in paths
        assert paths["weekly_threshold"] == 5  # デフォルト値


# =============================================================================
# run_pattern1 テスト
# =============================================================================


class TestRunPattern1:
    """run_pattern1 (新Loop検出) のテスト"""

    def test_returns_result_with_new_loops(self, persistent_config_env) -> None:
        """新規Loopがある場合の結果"""
        tmp_path = persistent_config_env["tmp_path"]
        persistent_config = persistent_config_env["persistent_config"]
        # テスト用の環境をセットアップ（永続化ディレクトリに）
        config_file = persistent_config / "config.json"
        config_file.write_text(
            json.dumps(
                {
                    "base_dir": str(tmp_path),
                    "paths": {},
                    "levels": {"weekly_threshold": 5},
                }
            )
        )

        paths = {
            "base_dir": tmp_path,
            "loops_path": tmp_path / "data" / "Loops",
            "digests_path": tmp_path / "data" / "Digests",
            "essences_path": tmp_path / "data" / "Essences",
            "weekly_threshold": 5,
        }

        with patch("interfaces.digest_entry.get_new_loops") as mock_new_loops:
            mock_new_loops.return_value = ["Loop_0001", "Loop_0002"]
            with patch("interfaces.digest_entry.get_weekly_source_count") as mock_count:
                mock_count.return_value = 3

                result = run_pattern1(paths)

        assert result.status == "ok"
        assert result.pattern == 1
        assert result.new_loops_count == 2
        assert "2個を検出" in result.message

    def test_returns_result_with_no_new_loops(self, tmp_path: Path) -> None:
        """新規Loopがない場合の結果"""
        paths = {
            "base_dir": tmp_path,
            "loops_path": tmp_path / "data" / "Loops",
            "digests_path": tmp_path / "data" / "Digests",
            "essences_path": tmp_path / "data" / "Essences",
            "weekly_threshold": 5,
        }

        with patch("interfaces.digest_entry.get_new_loops") as mock_new_loops:
            mock_new_loops.return_value = []
            with patch("interfaces.digest_entry.get_weekly_source_count") as mock_count:
                mock_count.return_value = 0

                result = run_pattern1(paths)

        assert result.status == "ok"
        assert result.new_loops_count == 0
        assert "なし" in result.message


# =============================================================================
# run_pattern2 テスト
# =============================================================================


class TestRunPattern2:
    """run_pattern2 (階層確定準備) のテスト"""

    def test_returns_result_for_weekly(self, tmp_path: Path) -> None:
        """weekly レベルの結果"""
        paths = {
            "base_dir": tmp_path,
            "loops_path": tmp_path / "data" / "Loops",
            "digests_path": tmp_path / "data" / "Digests",
            "essences_path": tmp_path / "data" / "Essences",
            "weekly_threshold": 5,
        }

        # 実際のデータクラスを使用
        shadow_result = ShadowStateResult(
            status="ok",
            level="weekly",
            analyzed=True,
            source_files=["Loop_0001.json", "Loop_0002.json"],
            source_count=5,
            placeholder_fields=[],
            message="分析済み",
        )

        with patch("interfaces.shadow_state_checker.ShadowStateChecker") as mock_checker:
            mock_instance = MagicMock()
            mock_instance.check.return_value = shadow_result
            mock_checker.return_value = mock_instance
            with patch("interfaces.digest_entry.get_weekly_source_count") as mock_count:
                mock_count.return_value = 3

                result = run_pattern2(paths, "weekly")

        assert result.status == "ok"
        assert result.pattern == 2
        assert result.level == "weekly"

    def test_returns_error_on_shadow_error(self, tmp_path: Path) -> None:
        """Shadow状態エラー時"""
        paths = {
            "base_dir": tmp_path,
            "loops_path": tmp_path / "data" / "Loops",
            "digests_path": tmp_path / "data" / "Digests",
            "essences_path": tmp_path / "data" / "Essences",
            "weekly_threshold": 5,
        }

        # エラー状態のデータクラス
        shadow_result = ShadowStateResult(
            status="error",
            level="weekly",
            analyzed=False,
            error="Shadow file not found",
        )

        with patch("interfaces.shadow_state_checker.ShadowStateChecker") as mock_checker:
            mock_instance = MagicMock()
            mock_instance.check.return_value = shadow_result
            mock_checker.return_value = mock_instance

            result = run_pattern2(paths, "weekly")

        assert result.status == "error"
        assert result.error is not None


# =============================================================================
# format_text_output テスト
# =============================================================================


class TestFormatTextOutput:
    """format_text_output のテスト"""

    def test_formats_pattern1_result(self) -> None:
        """Pattern 1 の結果をフォーマット"""
        result = DigestEntryResult(
            status="ok",
            pattern=1,
            base_dir="/path/to/plugin",
            loops_path="/path/to/loops",
            digests_path="/path/to/digests",
            essences_path="/path/to/essences",
            new_loops=["Loop_0001"],
            new_loops_count=1,
            weekly_source_count=3,
            weekly_threshold=5,
            message="新規Loop 1個を検出",
        )

        output = format_text_output(result)

        assert "```text" in output
        assert "新Loop検出" in output
        assert "Loop_0001" in output
        assert "3/5" in output

    def test_formats_pattern2_result(self) -> None:
        """Pattern 2 の結果をフォーマット"""
        result = DigestEntryResult(
            status="ok",
            pattern=2,
            base_dir="/path/to/plugin",
            loops_path="/path/to/loops",
            digests_path="/path/to/digests",
            essences_path="/path/to/essences",
            level="weekly",
            shadow_state={"source_count": 5, "analyzed": True},
            weekly_source_count=5,
            weekly_threshold=5,
            message="weekly 確定準備",
        )

        output = format_text_output(result)

        assert "```text" in output
        assert "weekly" in output
        assert "階層確定準備" in output

    def test_formats_error_result(self) -> None:
        """エラー結果をフォーマット"""
        result = DigestEntryResult(
            status="error",
            pattern=1,
            error="Plugin not found",
        )

        output = format_text_output(result)

        assert "```text" in output
        assert "エラー" in output
        assert "Plugin not found" in output

    def test_truncates_long_loop_list(self) -> None:
        """10個以上のループを切り詰める"""
        result = DigestEntryResult(
            status="ok",
            pattern=1,
            base_dir="/path/to/plugin",
            loops_path="/path/to/loops",
            digests_path="/path/to/digests",
            essences_path="/path/to/essences",
            new_loops=[f"Loop_{i:04d}" for i in range(15)],
            new_loops_count=15,
            weekly_source_count=3,
            weekly_threshold=5,
            message="新規Loop 15個を検出",
        )

        output = format_text_output(result)

        assert "他5個" in output


# =============================================================================
# CLI統合テスト
# =============================================================================


class TestDigestEntryMain:
    """main() CLI統合テスト"""

    def test_json_output_pattern1(self, tmp_path: Path) -> None:
        """Pattern 1 のJSON出力"""
        from interfaces.digest_entry import main

        with patch("interfaces.digest_entry.get_paths_from_config") as mock_paths:
            mock_paths.return_value = {
                "base_dir": tmp_path,
                "loops_path": tmp_path / "Loops",
                "digests_path": tmp_path / "Digests",
                "essences_path": tmp_path / "Essences",
                "weekly_threshold": 5,
            }

            with patch("interfaces.digest_entry.get_new_loops") as mock_new:
                mock_new.return_value = []

                with patch("interfaces.digest_entry.get_weekly_source_count") as mock_count:
                    mock_count.return_value = 0

                    with patch("sys.argv", ["digest_entry.py"]):
                        with patch("builtins.print") as mock_print:
                            main()

                            output = mock_print.call_args[0][0]
                            parsed = json.loads(output)
                            assert parsed["status"] == "ok"
                            assert parsed["pattern"] == 1

    def test_error_when_config_not_found(self) -> None:
        """config.json未検出時のエラー"""
        from interfaces.digest_entry import main

        with patch("interfaces.digest_entry.get_paths_from_config") as mock_paths:
            mock_paths.side_effect = FileNotFoundError("config.json not found")

            with patch("sys.argv", ["digest_entry.py"]):
                with patch("builtins.print") as mock_print:
                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    assert exc_info.value.code == 1
                    output = mock_print.call_args[0][0]
                    parsed = json.loads(output)
                    assert parsed["status"] == "error"
