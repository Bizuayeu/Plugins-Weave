#!/usr/bin/env python3
"""
test_directory_validator.py
===========================

config/directory_validator.py のテスト
"""

import shutil

import pytest

from config.directory_validator import DirectoryValidator
from config.level_path_service import LevelPathService
from domain.constants import LEVEL_NAMES


class TestDirectoryValidator:
    """DirectoryValidatorクラスのテスト"""

    @pytest.fixture
    def level_path_service(self, temp_plugin_env):
        """LevelPathServiceインスタンス"""
        return LevelPathService(temp_plugin_env.digests_path)

    @pytest.fixture
    def validator(self, temp_plugin_env, level_path_service):
        """DirectoryValidatorインスタンス"""
        return DirectoryValidator(
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
            level_path_service=level_path_service,
        )

    @pytest.mark.integration
    def test_validate_existing_directories(self, validator):
        """存在するディレクトリの検証（エラーなし）"""
        errors = validator.validate_directory_structure()

        assert errors == []

    @pytest.mark.integration
    def test_validate_missing_loops_directory(self, temp_plugin_env, level_path_service):
        """Loopsディレクトリ欠如検出"""
        # Loopsディレクトリを削除
        shutil.rmtree(temp_plugin_env.loops_path)

        validator = DirectoryValidator(
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
            level_path_service=level_path_service,
        )

        errors = validator.validate_directory_structure()

        assert len(errors) >= 1
        assert any("Loops" in error for error in errors)

    @pytest.mark.integration
    def test_validate_missing_digests_directory(self, temp_plugin_env, level_path_service):
        """Digestsディレクトリ欠如検出"""
        # Digestsディレクトリを削除
        shutil.rmtree(temp_plugin_env.digests_path)

        validator = DirectoryValidator(
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
            level_path_service=level_path_service,
        )

        errors = validator.validate_directory_structure()

        assert len(errors) >= 1
        assert any("Digests" in error for error in errors)

    @pytest.mark.integration
    def test_validate_missing_essences_directory(self, temp_plugin_env, level_path_service):
        """Essencesディレクトリ欠如検出"""
        # Essencesディレクトリを削除
        shutil.rmtree(temp_plugin_env.essences_path)

        validator = DirectoryValidator(
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
            level_path_service=level_path_service,
        )

        errors = validator.validate_directory_structure()

        assert len(errors) >= 1
        assert any("Essences" in error for error in errors)

    @pytest.mark.integration
    def test_validate_missing_level_directory(self, temp_plugin_env, level_path_service):
        """レベルディレクトリ欠如検出"""
        # 1_Weeklyディレクトリを削除
        weekly_dir = temp_plugin_env.digests_path / "1_Weekly"
        shutil.rmtree(weekly_dir)

        validator = DirectoryValidator(
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
            level_path_service=level_path_service,
        )

        errors = validator.validate_directory_structure()

        assert len(errors) >= 1
        assert any("weekly" in error.lower() for error in errors)

    @pytest.mark.integration
    def test_validate_missing_provisional_directory(self, temp_plugin_env, level_path_service):
        """Provisionalディレクトリ欠如検出"""
        # 1_Weekly/Provisionalを削除（レベルディレクトリは残す）
        provisional_dir = temp_plugin_env.digests_path / "1_Weekly" / "Provisional"
        shutil.rmtree(provisional_dir)

        validator = DirectoryValidator(
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
            level_path_service=level_path_service,
        )

        errors = validator.validate_directory_structure()

        assert len(errors) >= 1
        assert any("Provisional" in error for error in errors)

    @pytest.mark.integration
    def test_validate_all_levels_checked(self, temp_plugin_env, level_path_service):
        """全8レベルがチェックされる"""
        # 全レベルディレクトリを削除
        for level_dir in temp_plugin_env.digests_path.iterdir():
            if level_dir.is_dir():
                shutil.rmtree(level_dir)

        validator = DirectoryValidator(
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
            level_path_service=level_path_service,
        )

        errors = validator.validate_directory_structure()

        # 8レベル分のエラーが報告される
        assert len(errors) >= 8

    @pytest.mark.integration
    def test_validate_returns_list(self, validator):
        """戻り値がリスト"""
        result = validator.validate_directory_structure()

        assert isinstance(result, list)

    @pytest.mark.unit
    def test_validator_stores_paths(self, temp_plugin_env, level_path_service):
        """パスが正しく格納される"""
        validator = DirectoryValidator(
            loops_path=temp_plugin_env.loops_path,
            digests_path=temp_plugin_env.digests_path,
            essences_path=temp_plugin_env.essences_path,
            level_path_service=level_path_service,
        )

        assert validator.loops_path == temp_plugin_env.loops_path
        assert validator.digests_path == temp_plugin_env.digests_path
        assert validator.essences_path == temp_plugin_env.essences_path
