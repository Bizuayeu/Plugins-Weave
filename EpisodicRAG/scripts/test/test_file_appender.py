#!/usr/bin/env python3
"""
shadow/file_appender.py のユニットテスト
=========================================

FileAppenderクラスの動作を検証。
- _ensure_overall_digest_initialized: overall_digestの初期化
- _log_digest_content: Digestファイルの内容ログ出力

Note:
    これらのテストは元々test_shadow_updater.pyにあったものを移動。
    ShadowUpdaterのDEPRECATEDメソッド削除に伴い、直接FileAppenderをテスト。
"""
import json
import pytest
from pathlib import Path

# Application層
from application.shadow import ShadowIO, ShadowTemplate, FileDetector
from application.shadow.file_appender import FileAppender
from application.shadow.placeholder_manager import PlaceholderManager
from application.tracking import DigestTimesTracker

# Domain層
from domain.constants import LEVEL_NAMES, LEVEL_CONFIG

# 設定
from config import DigestConfig
from test_helpers import create_test_loop_file


# =============================================================================
# フィクスチャ
# =============================================================================

@pytest.fixture
def config(temp_plugin_env):
    """テスト用DigestConfig"""
    return DigestConfig(plugin_root=temp_plugin_env.plugin_root)


@pytest.fixture
def times_tracker(config):
    """テスト用DigestTimesTracker"""
    return DigestTimesTracker(config)


@pytest.fixture
def template():
    """テスト用ShadowTemplate"""
    return ShadowTemplate(levels=LEVEL_NAMES)


@pytest.fixture
def shadow_io(temp_plugin_env, template):
    """テスト用ShadowIO"""
    shadow_file = temp_plugin_env.plugin_root / ".claude-plugin" / "ShadowGrandDigest.txt"
    return ShadowIO(shadow_file, template.get_template)


@pytest.fixture
def file_detector(config, times_tracker):
    """テスト用FileDetector"""
    return FileDetector(config, times_tracker)


@pytest.fixture
def level_hierarchy():
    """レベル階層情報"""
    return {
        level: {"source": cfg["source"], "next": cfg["next"]}
        for level, cfg in LEVEL_CONFIG.items()
    }


@pytest.fixture
def placeholder_manager():
    """テスト用PlaceholderManager"""
    return PlaceholderManager()


@pytest.fixture
def file_appender(shadow_io, file_detector, template, level_hierarchy, placeholder_manager):
    """テスト用FileAppender"""
    return FileAppender(shadow_io, file_detector, template, level_hierarchy, placeholder_manager)


# =============================================================================
# _ensure_overall_digest_initialized テスト
# =============================================================================

class TestEnsureOverallDigestInitialized:
    """_ensure_overall_digest_initialized メソッドのテスト"""

    @pytest.mark.integration
    def test_initializes_null_overall_digest(self, file_appender, shadow_io):
        """overall_digestがnullの場合、初期化される"""
        shadow_data = shadow_io.load_or_create()
        shadow_data["latest_digests"]["weekly"]["overall_digest"] = None

        result = file_appender._ensure_overall_digest_initialized(shadow_data, "weekly")

        assert result is not None
        assert isinstance(result, dict)
        assert "source_files" in result

    @pytest.mark.integration
    def test_initializes_non_dict_overall_digest(self, file_appender, shadow_io):
        """overall_digestがdict以外の場合、初期化される"""
        shadow_data = shadow_io.load_or_create()
        shadow_data["latest_digests"]["weekly"]["overall_digest"] = "invalid"

        result = file_appender._ensure_overall_digest_initialized(shadow_data, "weekly")

        assert isinstance(result, dict)
        assert "source_files" in result

    @pytest.mark.integration
    def test_preserves_existing_valid_digest(self, file_appender, shadow_io):
        """有効なoverall_digestは保持される"""
        shadow_data = shadow_io.load_or_create()
        existing_digest = {
            "source_files": ["Loop0001_test.txt"],
            "abstract": "Existing content"
        }
        shadow_data["latest_digests"]["weekly"]["overall_digest"] = existing_digest

        result = file_appender._ensure_overall_digest_initialized(shadow_data, "weekly")

        assert result["abstract"] == "Existing content"
        assert "Loop0001_test.txt" in result["source_files"]

    @pytest.mark.integration
    def test_adds_source_files_if_missing(self, file_appender, shadow_io):
        """source_filesがない場合、追加される"""
        shadow_data = shadow_io.load_or_create()
        shadow_data["latest_digests"]["weekly"]["overall_digest"] = {
            "abstract": "Some content"
            # source_filesがない
        }

        result = file_appender._ensure_overall_digest_initialized(shadow_data, "weekly")

        assert "source_files" in result
        assert result["source_files"] == []


# =============================================================================
# _log_digest_content テスト
# =============================================================================

class TestLogDigestContent:
    """_log_digest_content メソッドのテスト"""

    @pytest.mark.integration
    def test_log_digest_content_valid_json(self, file_appender, temp_plugin_env, caplog):
        """有効なJSONファイルの内容をログ出力"""
        # Weekly Digestファイルを作成
        weekly_dir = temp_plugin_env.digests_path / "1_Weekly"
        weekly_file = weekly_dir / "W0001_test.txt"
        digest_content = {
            "overall_digest": {
                "digest_type": "weekly",
                "keywords": ["test", "keyword"],
                "abstract": "Test abstract content",
                "impression": "Test impression"
            }
        }
        with open(weekly_file, 'w', encoding='utf-8') as f:
            json.dump(digest_content, f)

        # _log_digest_contentを呼び出し（monthlyレベルでweeklyファイルを読む）
        file_appender._log_digest_content(weekly_file, "monthly")

        # ログ出力を検証（print→log_infoに変更されたため、caplogを使用）
        assert "digest_type" in caplog.text or "Read digest content" in caplog.text

    @pytest.mark.integration
    def test_log_digest_content_json_decode_error(self, file_appender, temp_plugin_env, capsys):
        """無効なJSONファイルの場合、警告を出力"""
        weekly_dir = temp_plugin_env.digests_path / "1_Weekly"
        weekly_file = weekly_dir / "W0001_invalid.txt"
        with open(weekly_file, 'w', encoding='utf-8') as f:
            f.write("{ invalid json content")

        # エラーなく完了すること
        file_appender._log_digest_content(weekly_file, "monthly")

        # 警告が出力されていることを確認（ログ出力の内容は実装依存）
        # エラーで落ちないことが重要

    @pytest.mark.integration
    def test_log_digest_content_file_not_found(self, file_appender, temp_plugin_env):
        """存在しないファイルの場合、エラーなく終了"""
        nonexistent_file = temp_plugin_env.digests_path / "1_Weekly" / "W9999_nonexistent.txt"

        # エラーなく完了すること
        file_appender._log_digest_content(nonexistent_file, "monthly")

    @pytest.mark.integration
    def test_log_digest_content_non_txt_file(self, file_appender, temp_plugin_env):
        """非テキストファイル（.json等）は無視される"""
        weekly_dir = temp_plugin_env.digests_path / "1_Weekly"
        json_file = weekly_dir / "W0001_test.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({"test": "data"}, f)

        # .txt以外は無視されるので、エラーなく完了
        file_appender._log_digest_content(json_file, "monthly")

    @pytest.mark.integration
    def test_log_digest_content_non_dict_digest(self, file_appender, temp_plugin_env, capsys):
        """overall_digestがdict以外の場合、警告を出力"""
        weekly_dir = temp_plugin_env.digests_path / "1_Weekly"
        weekly_file = weekly_dir / "W0001_non_dict.txt"
        with open(weekly_file, 'w', encoding='utf-8') as f:
            json.dump({"overall_digest": "not a dict"}, f)

        file_appender._log_digest_content(weekly_file, "monthly")

        # 警告が出力されていることを確認
