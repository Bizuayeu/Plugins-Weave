#!/usr/bin/env python3
"""
shadow/shadow_io.py のユニットテスト
====================================

ShadowIOクラスの動作を検証。
- load_or_create: 読み込みまたは新規作成
- save: 保存とタイムスタンプ更新
"""
import json
import pytest
from datetime import datetime
from pathlib import Path

# Application層
from application.shadow import ShadowIO, ShadowTemplate

# Domain層
from domain.constants import LEVEL_NAMES


# =============================================================================
# ShadowIO.load_or_create テスト
# =============================================================================

class TestShadowIOLoadOrCreate:
    """load_or_create メソッドのテスト"""

    @pytest.fixture
    def template_factory(self):
        """テスト用テンプレートファクトリ"""
        def factory():
            template = ShadowTemplate(levels=LEVEL_NAMES)
            return template.get_template()
        return factory

    @pytest.mark.integration
    def test_creates_new_file_when_not_exists(self, temp_plugin_env, template_factory):
        """ファイルが存在しない場合、新規作成する"""
        shadow_file = temp_plugin_env.plugin_root / "ShadowGrandDigest.txt"
        assert not shadow_file.exists()

        io = ShadowIO(shadow_file, template_factory)
        result = io.load_or_create()

        assert shadow_file.exists()
        assert isinstance(result, dict)
        assert "metadata" in result
        assert "latest_digests" in result

    @pytest.mark.integration
    def test_loads_existing_file(self, temp_plugin_env, template_factory):
        """既存ファイルがある場合、それを読み込む"""
        shadow_file = temp_plugin_env.plugin_root / "ShadowGrandDigest.txt"

        # 既存ファイルを作成
        existing_data = {
            "metadata": {
                "last_updated": "2024-01-01T00:00:00",
                "version": "1.0.0"
            },
            "latest_digests": {
                "weekly": {"overall_digest": {"custom": "data"}}
            }
        }
        with open(shadow_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f)

        io = ShadowIO(shadow_file, template_factory)
        result = io.load_or_create()

        assert result == existing_data
        assert result["metadata"]["last_updated"] == "2024-01-01T00:00:00"
        assert result["latest_digests"]["weekly"]["overall_digest"]["custom"] == "data"

    @pytest.mark.integration
    def test_created_file_has_template_structure(self, temp_plugin_env, template_factory):
        """新規作成されたファイルはテンプレート構造を持つ"""
        shadow_file = temp_plugin_env.plugin_root / "ShadowGrandDigest.txt"

        io = ShadowIO(shadow_file, template_factory)
        result = io.load_or_create()

        # テンプレート構造を検証
        assert "metadata" in result
        assert "version" in result["metadata"]
        assert "latest_digests" in result
        for level in LEVEL_NAMES:
            assert level in result["latest_digests"]

    @pytest.mark.integration
    def test_template_factory_called_only_when_needed(self, temp_plugin_env):
        """テンプレートファクトリは必要な場合のみ呼ばれる"""
        shadow_file = temp_plugin_env.plugin_root / "ShadowGrandDigest.txt"

        # 既存ファイルを作成
        existing_data = {"metadata": {"version": "1.0.0"}, "latest_digests": {}}
        with open(shadow_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f)

        call_count = 0
        def counting_factory():
            nonlocal call_count
            call_count += 1
            return {"metadata": {}, "latest_digests": {}}

        io = ShadowIO(shadow_file, counting_factory)
        io.load_or_create()

        assert call_count == 0  # 既存ファイルがあるのでファクトリは呼ばれない


# =============================================================================
# ShadowIO.save テスト
# =============================================================================

class TestShadowIOSave:
    """save メソッドのテスト"""

    @pytest.fixture
    def template_factory(self):
        """テスト用テンプレートファクトリ"""
        def factory():
            template = ShadowTemplate(levels=LEVEL_NAMES)
            return template.get_template()
        return factory

    @pytest.mark.integration
    def test_saves_data_to_file(self, temp_plugin_env, template_factory):
        """データがファイルに保存される"""
        shadow_file = temp_plugin_env.plugin_root / "ShadowGrandDigest.txt"

        io = ShadowIO(shadow_file, template_factory)
        data = {
            "metadata": {"version": "1.0.0"},
            "latest_digests": {"weekly": {"test": "data"}}
        }
        io.save(data)

        assert shadow_file.exists()
        with open(shadow_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        assert saved_data["latest_digests"]["weekly"]["test"] == "data"

    @pytest.mark.integration
    def test_updates_last_updated_timestamp(self, temp_plugin_env, template_factory):
        """保存時にlast_updatedが更新される"""
        shadow_file = temp_plugin_env.plugin_root / "ShadowGrandDigest.txt"

        io = ShadowIO(shadow_file, template_factory)
        before_save = datetime.now()
        data = {
            "metadata": {"last_updated": "2020-01-01T00:00:00", "version": "1.0.0"},
            "latest_digests": {}
        }
        io.save(data)
        after_save = datetime.now()

        # 保存後のデータを読み込んで確認
        with open(shadow_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        last_updated = datetime.fromisoformat(saved_data["metadata"]["last_updated"])
        assert before_save <= last_updated <= after_save

    @pytest.mark.integration
    def test_save_overwrites_existing_file(self, temp_plugin_env, template_factory):
        """既存ファイルを上書きする"""
        shadow_file = temp_plugin_env.plugin_root / "ShadowGrandDigest.txt"

        # 既存ファイルを作成
        with open(shadow_file, 'w', encoding='utf-8') as f:
            json.dump({"old": "data", "metadata": {}}, f)

        io = ShadowIO(shadow_file, template_factory)
        new_data = {
            "metadata": {"version": "2.0.0"},
            "latest_digests": {"new": "content"}
        }
        io.save(new_data)

        with open(shadow_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        assert "old" not in saved_data
        assert saved_data["latest_digests"]["new"] == "content"

    @pytest.mark.integration
    def test_save_preserves_other_metadata_fields(self, temp_plugin_env, template_factory):
        """save時に他のmetadataフィールドは保持される"""
        shadow_file = temp_plugin_env.plugin_root / "ShadowGrandDigest.txt"

        io = ShadowIO(shadow_file, template_factory)
        data = {
            "metadata": {
                "version": "1.0.0",
                "description": "Test description",
                "last_updated": "old_value"
            },
            "latest_digests": {}
        }
        io.save(data)

        with open(shadow_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        assert saved_data["metadata"]["version"] == "1.0.0"
        assert saved_data["metadata"]["description"] == "Test description"
        assert saved_data["metadata"]["last_updated"] != "old_value"  # 更新されている


# =============================================================================
# ShadowIO 初期化テスト
# =============================================================================

class TestShadowIOInit:
    """ShadowIO 初期化のテスト"""

    @pytest.mark.unit
    def test_stores_shadow_digest_file(self, temp_plugin_env):
        """shadow_digest_fileが正しく保存される"""
        shadow_file = temp_plugin_env.plugin_root / "ShadowGrandDigest.txt"
        factory = lambda: {}
        io = ShadowIO(shadow_file, factory)
        assert io.shadow_digest_file == shadow_file

    @pytest.mark.unit
    def test_stores_template_factory(self, temp_plugin_env):
        """template_factoryが正しく保存される"""
        shadow_file = temp_plugin_env.plugin_root / "ShadowGrandDigest.txt"
        factory = lambda: {"test": "template"}
        io = ShadowIO(shadow_file, factory)
        assert io.template_factory is factory
