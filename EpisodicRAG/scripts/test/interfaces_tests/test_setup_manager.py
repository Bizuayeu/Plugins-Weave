#!/usr/bin/env python3
"""
SetupManager クラスのテスト
===========================

SetupManager クラスの基本機能とエッジケースのテスト。
test_digest_setup.py から分割。
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import pytest


class TestSetupManager(unittest.TestCase):
    """SetupManager クラスのテスト"""

    def setUp(self) -> None:
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        # .claude-plugin ディレクトリを作成
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        # 永続化設定ディレクトリを作成
        self.persistent_config = self.plugin_root / ".persistent_config"
        self.persistent_config.mkdir(parents=True)
        # 環境変数を設定（get_persistent_config_dir()がこれを使用）
        self._old_env = os.environ.get("EPISODICRAG_CONFIG_DIR")
        os.environ["EPISODICRAG_CONFIG_DIR"] = str(self.persistent_config)

    def tearDown(self) -> None:
        """一時ディレクトリを削除"""
        # 環境変数をリセット
        if self._old_env is not None:
            os.environ["EPISODICRAG_CONFIG_DIR"] = self._old_env
        else:
            os.environ.pop("EPISODICRAG_CONFIG_DIR", None)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_templates(self) -> None:
        """テンプレートファイルを作成"""
        template_dir = self.plugin_root / ".claude-plugin"

        # GrandDigest.template.txt
        grand_template = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "major_digests": {},
        }
        with open(template_dir / "GrandDigest.template.txt", "w", encoding="utf-8") as f:
            json.dump(grand_template, f)

        # ShadowGrandDigest.template.txt
        shadow_template = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {},
        }
        with open(template_dir / "ShadowGrandDigest.template.txt", "w", encoding="utf-8") as f:
            json.dump(shadow_template, f)

        # last_digest_times.template.json
        times_template = {"weekly": {"timestamp": "", "last_processed": None}}
        with open(template_dir / "last_digest_times.template.json", "w", encoding="utf-8") as f:
            json.dump(times_template, f)

    @pytest.mark.unit
    def test_check_returns_not_configured_when_no_config(self) -> None:
        """設定ファイルがない場合、not_configured を返す"""
        from interfaces.digest_setup import SetupManager

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.check()

        assert result["status"] == "not_configured"
        assert result["config_exists"] is False
        assert result["directories_exist"] is False

    @pytest.mark.unit
    def test_check_returns_configured_when_setup_complete(self) -> None:
        """セットアップ完了時に configured を返す"""
        from interfaces.digest_setup import SetupManager

        # 設定ファイルを作成
        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4,
            },
        }
        with open(self.persistent_config / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        # ディレクトリを作成
        (self.plugin_root / "data" / "Loops").mkdir(parents=True)

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.check()

        assert result["status"] == "configured"
        assert result["config_exists"] is True
        assert result["directories_exist"] is True

    @pytest.mark.unit
    def test_init_creates_config_file(self) -> None:
        """init が設定ファイルを作成する"""
        from interfaces.digest_setup import SetupManager

        self._create_templates()

        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4,
            },
        }

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.init(config_data)

        assert result.status == "ok"
        # config.json は永続化ディレクトリに作成される
        assert self.persistent_config.exists()
        assert (self.persistent_config / "config.json").exists()

    @pytest.mark.unit
    def test_init_creates_directories(self) -> None:
        """init がディレクトリを作成する"""
        from interfaces.digest_setup import SetupManager

        self._create_templates()

        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4,
            },
        }

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.init(config_data)

        assert result.status == "ok"
        assert (self.plugin_root / "data" / "Loops").exists()
        assert (self.plugin_root / "data" / "Digests" / "1_Weekly").exists()
        assert (self.plugin_root / "data" / "Digests" / "1_Weekly" / "Provisional").exists()
        assert (self.plugin_root / "data" / "Essences").exists()

    @pytest.mark.unit
    def test_init_creates_initial_files(self) -> None:
        """init が初期ファイルを作成する"""
        from interfaces.digest_setup import SetupManager

        self._create_templates()

        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4,
            },
        }

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.init(config_data)

        assert result.status == "ok"
        assert "GrandDigest.txt" in result.created["files"]
        assert "ShadowGrandDigest.txt" in result.created["files"]
        assert "last_digest_times.json" in result.created["files"]
        assert (self.plugin_root / "data" / "Essences" / "GrandDigest.txt").exists()
        # last_digest_times.json は永続化ディレクトリに作成される
        assert (self.persistent_config / "last_digest_times.json").exists()

    @pytest.mark.unit
    def test_init_fails_without_force_when_config_exists(self) -> None:
        """既存設定がある場合、force なしで失敗する"""
        from interfaces.digest_setup import SetupManager

        # 既存の設定ファイルを作成（永続化ディレクトリに）
        with open(self.persistent_config / "config.json", "w", encoding="utf-8") as f:
            json.dump({}, f)

        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4,
            },
        }

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.init(config_data)

        assert result.status == "already_configured"

    @pytest.mark.unit
    def test_init_succeeds_with_force_when_config_exists(self) -> None:
        """既存設定がある場合でも force で成功する"""
        from interfaces.digest_setup import SetupManager

        self._create_templates()

        # 既存の設定ファイルを作成（永続化ディレクトリに）
        with open(self.persistent_config / "config.json", "w", encoding="utf-8") as f:
            json.dump({}, f)

        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4,
            },
        }

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.init(config_data, force=True)

        assert result.status == "ok"

    @pytest.mark.unit
    def test_init_validates_config_data(self) -> None:
        """init が設定データをバリデーションする"""
        from interfaces.digest_setup import SetupManager

        # 必須フィールドがない設定
        config_data = {"base_dir": "."}

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.init(config_data)

        assert result.status == "error"
        assert "paths" in result.error

    @pytest.mark.unit
    def test_init_detects_external_paths(self) -> None:
        """init が外部パスを検出する"""
        from interfaces.digest_setup import SetupManager

        self._create_templates()

        config_data = {
            "base_dir": "~/external/path",  # 外部パス
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4,
            },
        }

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.init(config_data)

        assert result.status == "ok"
        assert len(result.external_paths_detected) > 0
        assert any("base_dir" in p for p in result.external_paths_detected)


class TestSetupManagerCheckEdgeCases(unittest.TestCase):
    """SetupManager check() のエッジケーステスト"""

    def setUp(self) -> None:
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        # 永続化設定ディレクトリを作成
        self.persistent_config = self.plugin_root / ".persistent_config"
        self.persistent_config.mkdir(parents=True)
        # 環境変数を設定（get_persistent_config_dir()がこれを使用）
        self._old_env = os.environ.get("EPISODICRAG_CONFIG_DIR")
        os.environ["EPISODICRAG_CONFIG_DIR"] = str(self.persistent_config)

    def tearDown(self) -> None:
        """一時ディレクトリを削除"""
        # 環境変数をリセット
        if self._old_env is not None:
            os.environ["EPISODICRAG_CONFIG_DIR"] = self._old_env
        else:
            os.environ.pop("EPISODICRAG_CONFIG_DIR", None)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_check_returns_partial_when_config_exists_but_dirs_missing(self) -> None:
        """設定ファイルがあるがディレクトリがない場合、partial を返す"""
        from interfaces.digest_setup import SetupManager

        # 設定ファイルを作成（永続化ディレクトリに、ディレクトリは作成しない）
        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
        }
        with open(self.persistent_config / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.check()

        assert result["status"] == "partial"
        assert result["config_exists"] is True
        assert result["directories_exist"] is False

    @pytest.mark.unit
    def test_check_handles_corrupt_json(self) -> None:
        """破損したJSONファイルを処理する"""
        from interfaces.digest_setup import SetupManager

        # 破損したJSONファイルを作成（永続化ディレクトリに）
        with open(self.persistent_config / "config.json", "w", encoding="utf-8") as f:
            f.write("{ invalid json content")

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.check()

        # JSONDecodeErrorをキャッチしてpartialまたはnot_configuredを返す
        # 設定ファイルは存在するがパースできないので結果はpartial相当
        assert result["status"] in ["partial", "not_configured"]
        assert result["config_exists"] is True

    @pytest.mark.unit
    def test_check_handles_missing_keys_in_config(self) -> None:
        """設定にpathsキーがない場合を処理する"""
        from interfaces.digest_setup import SetupManager

        # pathsキーがない設定ファイルを作成（永続化ディレクトリに）
        config_data = {"base_dir": "."}  # pathsがない
        with open(self.persistent_config / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        manager = SetupManager(plugin_root=self.plugin_root)
        result = manager.check()

        # KeyErrorをキャッチして処理
        assert result["status"] in ["partial", "not_configured"]
        assert result["config_exists"] is True


if __name__ == "__main__":
    unittest.main()
