#!/usr/bin/env python3
"""
finalize/provisional_loader.py のユニットテスト
===============================================

ProvisionalLoaderクラスの動作を検証。
- load_or_generate: Provisionalの読み込みまたは自動生成
- generate_from_source: ソースファイルからの自動生成
"""
import json
import pytest
from pathlib import Path

from finalize.provisional_loader import ProvisionalLoader
from config import DigestConfig
from shadow_grand_digest import ShadowGrandDigestManager
from exceptions import DigestError, FileIOError
from test_helpers import create_test_loop_file


# =============================================================================
# フィクスチャ
# =============================================================================

@pytest.fixture
def config(temp_plugin_env):
    """テスト用DigestConfig"""
    return DigestConfig(plugin_root=temp_plugin_env.plugin_root)


@pytest.fixture
def shadow_manager(config):
    """テスト用ShadowGrandDigestManager"""
    return ShadowGrandDigestManager(config)


@pytest.fixture
def loader(config, shadow_manager):
    """テスト用ProvisionalLoader"""
    return ProvisionalLoader(config, shadow_manager)


# =============================================================================
# ProvisionalLoader.load_or_generate テスト
# =============================================================================

class TestProvisionalLoaderLoadOrGenerate:
    """load_or_generate メソッドのテスト"""

    @pytest.mark.integration
    def test_loads_existing_provisional_file(self, loader, config):
        """既存のProvisionalファイルを読み込む"""
        # Provisionalファイルを作成
        provisional_dir = config.get_provisional_dir("weekly")
        provisional_path = provisional_dir / "W0001_Individual.txt"

        provisional_data = {
            "individual_digests": [
                {"filename": "Loop0001.txt", "content": "Test 1"},
                {"filename": "Loop0002.txt", "content": "Test 2"}
            ]
        }
        with open(provisional_path, 'w', encoding='utf-8') as f:
            json.dump(provisional_data, f)

        shadow_digest = {"source_files": ["Loop0001.txt", "Loop0002.txt"]}
        individual_digests, provisional_file = loader.load_or_generate("weekly", shadow_digest, "0001")

        assert len(individual_digests) == 2
        assert provisional_file == provisional_path

    @pytest.mark.integration
    def test_generates_from_source_when_no_provisional(self, loader, temp_plugin_env):
        """Provisionalがない場合はソースから生成"""
        # Loopファイルを作成
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)

        shadow_digest = {"source_files": [loop1.name]}
        individual_digests, provisional_file = loader.load_or_generate("weekly", shadow_digest, "0001")

        # 自動生成されたindividual_digestsがある
        assert len(individual_digests) == 1
        assert provisional_file is None  # Provisionalファイルは存在しない

    @pytest.mark.integration
    def test_raises_on_invalid_json(self, loader, config):
        """無効なJSONの場合はFileIOError"""
        provisional_dir = config.get_provisional_dir("weekly")
        provisional_path = provisional_dir / "W0001_Individual.txt"

        with open(provisional_path, 'w', encoding='utf-8') as f:
            f.write("{ invalid json }")

        shadow_digest = {"source_files": []}

        with pytest.raises(FileIOError) as exc_info:
            loader.load_or_generate("weekly", shadow_digest, "0001")
        assert "Invalid JSON" in str(exc_info.value)

    @pytest.mark.integration
    def test_raises_on_non_dict_provisional(self, loader, config):
        """Provisionalがdict以外の場合はDigestError"""
        provisional_dir = config.get_provisional_dir("weekly")
        provisional_path = provisional_dir / "W0001_Individual.txt"

        with open(provisional_path, 'w', encoding='utf-8') as f:
            json.dump(["list", "not", "dict"], f)

        shadow_digest = {"source_files": []}

        with pytest.raises(DigestError) as exc_info:
            loader.load_or_generate("weekly", shadow_digest, "0001")
        assert "Invalid format" in str(exc_info.value)


# =============================================================================
# ProvisionalLoader.generate_from_source テスト
# =============================================================================

class TestProvisionalLoaderGenerateFromSource:
    """generate_from_source メソッドのテスト"""

    @pytest.mark.integration
    def test_generates_from_loop_files(self, loader, temp_plugin_env):
        """Loopファイルからindividual_digestsを生成"""
        # Loopファイルを作成
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)
        loop2 = create_test_loop_file(temp_plugin_env.loops_path, 2)

        shadow_digest = {"source_files": [loop1.name, loop2.name]}
        result = loader.generate_from_source("weekly", shadow_digest)

        assert len(result) == 2
        assert result[0]["filename"] == loop1.name
        assert result[1]["filename"] == loop2.name

    @pytest.mark.integration
    def test_handles_missing_source_files(self, loader):
        """存在しないソースファイルはスキップ"""
        shadow_digest = {"source_files": ["NonExistent.txt"]}
        result = loader.generate_from_source("weekly", shadow_digest)

        assert len(result) == 0

    @pytest.mark.integration
    def test_extracts_overall_digest_fields(self, loader, temp_plugin_env):
        """overall_digestの各フィールドを抽出"""
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)

        shadow_digest = {"source_files": [loop1.name]}
        result = loader.generate_from_source("weekly", shadow_digest)

        assert len(result) == 1
        entry = result[0]
        assert "filename" in entry
        assert "timestamp" in entry
        assert "digest_type" in entry
        assert "keywords" in entry
        assert "abstract" in entry
        assert "impression" in entry

    @pytest.mark.integration
    def test_returns_empty_for_empty_source_files(self, loader):
        """source_filesが空の場合は空リスト"""
        shadow_digest = {"source_files": []}
        result = loader.generate_from_source("weekly", shadow_digest)

        assert result == []


# =============================================================================
# ProvisionalLoader 初期化テスト
# =============================================================================

class TestProvisionalLoaderInit:
    """ProvisionalLoader 初期化のテスト"""

    @pytest.mark.unit
    def test_stores_dependencies(self, config, shadow_manager):
        """依存関係が正しく保存される"""
        loader = ProvisionalLoader(config, shadow_manager)
        assert loader.config is config
        assert loader.shadow_manager is shadow_manager
