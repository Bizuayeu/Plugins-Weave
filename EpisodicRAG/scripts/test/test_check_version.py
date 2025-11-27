#!/usr/bin/env python3
"""
check_version.py のユニットテスト
=================================

バージョン整合性チェックスクリプトのテスト。
- 全バージョン一致時に0を返す
- 不一致時に1を返す
- ファイル欠如時のエラー処理
- 不正なJSON時のエラー処理
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest


class TestCheckVersion:
    """check_version.py のテスト"""

    @pytest.fixture
    def temp_version_env(self, tmp_path):
        """
        バージョンチェック用の一時環境を構築

        構造:
            tmp_path/
            ├── scripts/
            │   ├── check_version.py  (コピー)
            │   └── domain/
            │       └── version.py
            ├── .claude-plugin/
            │   └── plugin.json
            └── pyproject.toml
        """
        # ディレクトリ構造作成
        scripts_dir = tmp_path / "scripts"
        domain_dir = scripts_dir / "domain"
        plugin_dir = tmp_path / ".claude-plugin"

        scripts_dir.mkdir()
        domain_dir.mkdir()
        plugin_dir.mkdir()

        # check_version.py をコピー
        original_script = Path(__file__).parent.parent / "check_version.py"
        target_script = scripts_dir / "check_version.py"
        target_script.write_text(original_script.read_text(encoding="utf-8"), encoding="utf-8")

        return {
            "root": tmp_path,
            "scripts_dir": scripts_dir,
            "domain_dir": domain_dir,
            "plugin_dir": plugin_dir,
            "check_version_script": target_script,
            "version_file": domain_dir / "version.py",
            "plugin_json": plugin_dir / "plugin.json",
            "pyproject": tmp_path / "pyproject.toml",
        }

    def _create_version_py(self, path: Path, version: str) -> None:
        """version.py を作成"""
        path.write_text(f'__version__ = "{version}"\n', encoding="utf-8")

    def _create_plugin_json(self, path: Path, version: str) -> None:
        """plugin.json を作成"""
        data = {"name": "test-plugin", "version": version}
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _create_pyproject(self, path: Path, version: str) -> None:
        """pyproject.toml を作成"""
        content = f'''[project]
name = "test-project"
version = "{version}"
'''
        path.write_text(content, encoding="utf-8")

    def _run_check_version(self, script_path: Path) -> tuple[int, str]:
        """check_version.py を実行して終了コードと出力を返す"""
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        return result.returncode, result.stdout + result.stderr

    @pytest.mark.unit
    def test_all_versions_match(self, temp_version_env):
        """全バージョン一致時に0を返す"""
        env = temp_version_env
        version = "2.1.0"

        self._create_version_py(env["version_file"], version)
        self._create_plugin_json(env["plugin_json"], version)
        self._create_pyproject(env["pyproject"], version)

        returncode, output = self._run_check_version(env["check_version_script"])

        assert returncode == 0
        assert "All versions match" in output
        assert version in output

    @pytest.mark.unit
    def test_version_mismatch_detected(self, temp_version_env):
        """不一致時に1を返す"""
        env = temp_version_env

        self._create_version_py(env["version_file"], "2.1.0")
        self._create_plugin_json(env["plugin_json"], "2.0.0")  # 異なるバージョン
        self._create_pyproject(env["pyproject"], "2.1.0")

        returncode, output = self._run_check_version(env["check_version_script"])

        assert returncode == 1
        assert "mismatch" in output.lower()

    @pytest.mark.unit
    def test_missing_version_py(self, temp_version_env):
        """version.pyがない場合に1を返す"""
        env = temp_version_env

        # version.py を作成しない
        self._create_plugin_json(env["plugin_json"], "2.1.0")
        self._create_pyproject(env["pyproject"], "2.1.0")

        returncode, output = self._run_check_version(env["check_version_script"])

        assert returncode == 1
        assert "not found" in output.lower()

    @pytest.mark.unit
    def test_missing_plugin_json(self, temp_version_env):
        """plugin.jsonがない場合に1を返す"""
        env = temp_version_env

        self._create_version_py(env["version_file"], "2.1.0")
        # plugin.json を作成しない
        self._create_pyproject(env["pyproject"], "2.1.0")

        returncode, output = self._run_check_version(env["check_version_script"])

        assert returncode == 1
        assert "not found" in output.lower()

    @pytest.mark.unit
    def test_invalid_json_in_plugin_json(self, temp_version_env):
        """不正なJSONの場合に1を返す"""
        env = temp_version_env

        self._create_version_py(env["version_file"], "2.1.0")
        env["plugin_json"].write_text("{ invalid json }", encoding="utf-8")
        self._create_pyproject(env["pyproject"], "2.1.0")

        returncode, output = self._run_check_version(env["check_version_script"])

        assert returncode == 1
        assert "invalid json" in output.lower()

    @pytest.mark.unit
    def test_missing_pyproject_toml(self, temp_version_env):
        """pyproject.tomlがない場合に1を返す"""
        env = temp_version_env

        self._create_version_py(env["version_file"], "2.1.0")
        self._create_plugin_json(env["plugin_json"], "2.1.0")
        # pyproject.toml を作成しない

        returncode, output = self._run_check_version(env["check_version_script"])

        assert returncode == 1
        assert "not found" in output.lower()
