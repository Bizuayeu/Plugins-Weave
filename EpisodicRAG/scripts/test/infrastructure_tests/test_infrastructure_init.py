#!/usr/bin/env python3
"""
infrastructure/__init__.py のユニットテスト
=============================================

Infrastructureモジュールのエクスポートと統合を検証。
"""

from pathlib import Path

import pytest

# =============================================================================
# エクスポートテスト
# =============================================================================


class TestInfrastructureExports:
    """infrastructure/__init__.py エクスポートのテスト"""

    @pytest.mark.unit
    def test_all_json_exports_importable(self) -> None:

        """JSON関連のエクスポートがインポート可能"""
        from infrastructure import (
            confirm_file_overwrite,
            ensure_directory,
            file_exists,
            load_json,
            load_json_with_template,
            save_json,
            try_load_json,
            try_read_json_from_file,
        )

        # 全てがcallable
        assert callable(load_json)
        assert callable(save_json)
        assert callable(load_json_with_template)
        assert callable(file_exists)
        assert callable(ensure_directory)
        assert callable(try_load_json)
        assert callable(confirm_file_overwrite)
        assert callable(try_read_json_from_file)

    @pytest.mark.unit
    def test_all_file_scanner_exports_importable(self) -> None:

        """ファイルスキャナー関連のエクスポートがインポート可能"""
        from infrastructure import (
            count_files,
            filter_files_after_number,
            get_files_by_pattern,
            get_max_numbered_file,
            scan_files,
        )

        assert callable(scan_files)
        assert callable(get_files_by_pattern)
        assert callable(get_max_numbered_file)
        assert callable(filter_files_after_number)
        assert callable(count_files)

    @pytest.mark.unit
    def test_all_logging_exports_importable(self) -> None:

        """ロギング関連のエクスポートがインポート可能"""
        from infrastructure import (
            get_logger,
            log_debug,
            log_error,
            log_info,
            log_warning,
            setup_logging,
        )

        assert callable(get_logger)
        assert callable(setup_logging)
        assert callable(log_info)
        assert callable(log_warning)
        assert callable(log_error)
        assert callable(log_debug)

    @pytest.mark.unit
    def test_user_interaction_exports_importable(self) -> None:

        """ユーザーインタラクション関連のエクスポートがインポート可能"""
        from infrastructure import get_default_confirm_callback

        assert callable(get_default_confirm_callback)

    @pytest.mark.unit
    def test_exports_match_all_list(self) -> None:

        """__all__の全項目がインポート可能"""
        import infrastructure

        for name in infrastructure.__all__:
            assert hasattr(infrastructure, name), f"Missing export: {name}"
            item = getattr(infrastructure, name)
            assert item is not None, f"Export {name} is None"

    @pytest.mark.unit
    def test_all_list_completeness(self) -> None:

        """__all__に必要な全項目が含まれている"""
        import infrastructure

        expected_exports = [
            # JSON Repository
            "load_json",
            "save_json",
            "load_json_with_template",
            "file_exists",
            "ensure_directory",
            "try_load_json",
            "confirm_file_overwrite",
            "try_read_json_from_file",
            # File Scanner
            "scan_files",
            "get_files_by_pattern",
            "get_max_numbered_file",
            "filter_files_after_number",
            "count_files",
            # Logging
            "get_logger",
            "setup_logging",
            "log_info",
            "log_warning",
            "log_error",
            "log_debug",
            # User Interaction
            "get_default_confirm_callback",
        ]

        for name in expected_exports:
            assert name in infrastructure.__all__, f"{name} not in __all__"


# =============================================================================
# 統合テスト
# =============================================================================


class TestInfrastructureIntegration:
    """Infrastructureモジュールの統合テスト"""

    @pytest.mark.integration
    def test_json_roundtrip(self, tmp_path: Path) -> None:

        """JSON保存・読み込みのラウンドトリップ"""
        from infrastructure import load_json, save_json

        test_file = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42, "list": [1, 2, 3]}

        save_json(test_file, test_data)
        loaded = load_json(test_file)

        assert loaded == test_data

    @pytest.mark.integration
    def test_file_scanner_with_pattern(self, tmp_path: Path) -> None:

        """パターンによるファイルスキャン"""
        from infrastructure import scan_files

        # テストファイル作成
        (tmp_path / "Loop0001.txt").touch()
        (tmp_path / "Loop0002.txt").touch()
        (tmp_path / "other.json").touch()

        # txtファイルのみスキャン
        txt_files = scan_files(tmp_path, "*.txt")
        assert len(txt_files) == 2

        # jsonファイルのみスキャン
        json_files = scan_files(tmp_path, "*.json")
        assert len(json_files) == 1

    @pytest.mark.integration
    def test_logging_functions(self, caplog: pytest.LogCaptureFixture) -> None:

        """ロギング関数の動作確認"""
        import logging

        from infrastructure import log_debug, log_error, log_info, log_warning

        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            log_debug("Debug message")
            log_info("Info message")
            log_warning("Warning message")
            log_error("Error message")

        assert "Debug message" in caplog.text
        assert "Info message" in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text

    @pytest.mark.integration
    def test_user_interaction_callback(self, monkeypatch: pytest.MonkeyPatch) -> None:

        """ユーザーインタラクションコールバックの動作確認"""
        from infrastructure import get_default_confirm_callback

        monkeypatch.setattr("builtins.input", lambda _: "y")

        callback = get_default_confirm_callback()
        assert callback("Test?") is True
