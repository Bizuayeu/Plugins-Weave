#!/usr/bin/env python3
"""
finalize/provisional_loader.py のユニットテスト
===============================================

ProvisionalLoaderクラスの動作を検証。
- load_or_generate: Provisionalの読み込みまたは自動生成
- generate_from_source: ソースファイルからの自動生成
"""

import json
from pathlib import Path

import pytest

# slow マーカーを適用（ファイル全体）
pytestmark = pytest.mark.slow
from test_helpers import create_test_loop_file

# Application層
from application.finalize import ProvisionalLoader
from application.grand import ShadowGrandDigestManager

# 設定
from config import DigestConfig

# Domain層
from domain.exceptions import DigestError, FileIOError

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
                {"filename": "Loop0002.txt", "content": "Test 2"},
            ]
        }
        with open(provisional_path, 'w', encoding='utf-8') as f:
            json.dump(provisional_data, f)

        shadow_digest = {"source_files": ["Loop0001.txt", "Loop0002.txt"]}
        individual_digests, provisional_file = loader.load_or_generate(
            "weekly", shadow_digest, "0001"
        )

        assert len(individual_digests) == 2
        assert provisional_file == provisional_path

    @pytest.mark.integration
    def test_generates_from_source_when_no_provisional(self, loader, temp_plugin_env):
        """Provisionalがない場合はソースから生成"""
        # Loopファイルを作成
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)

        shadow_digest = {"source_files": [loop1.name]}
        individual_digests, provisional_file = loader.load_or_generate(
            "weekly", shadow_digest, "0001"
        )

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
        # Changed from "filename" to "source_file" to match IndividualDigestData TypedDict
        assert result[0]["source_file"] == loop1.name
        assert result[1]["source_file"] == loop2.name

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
        # Changed from "filename" to "source_file" to match IndividualDigestData TypedDict
        # Note: "timestamp" was also removed from IndividualDigestData
        assert "source_file" in entry
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


# =============================================================================
# エッジケーステスト
# =============================================================================


class TestProvisionalLoaderEdgeCases:
    """ProvisionalLoader エッジケースのテスト"""

    @pytest.mark.integration
    def test_source_file_with_invalid_json_skipped(self, loader, temp_plugin_env):
        """ソースファイルが不正なJSONの場合はスキップ（警告のみ）"""
        # 不正なJSONを持つLoopファイルを作成
        invalid_loop = temp_plugin_env.loops_path / "Loop0001_invalid.txt"
        invalid_loop.write_text("{ invalid json content }")

        # 正常なLoopファイルも作成
        valid_loop = create_test_loop_file(temp_plugin_env.loops_path, 2)

        shadow_digest = {"source_files": [invalid_loop.name, valid_loop.name]}
        result = loader.generate_from_source("weekly", shadow_digest)

        # 不正なファイルはスキップされ、正常なファイルのみ処理される
        assert len(result) == 1
        # Changed from "filename" to "source_file"
        assert result[0]["source_file"] == valid_loop.name

    @pytest.mark.integration
    def test_source_file_non_txt_extension_skipped(self, loader, temp_plugin_env):
        """txtでないソースファイルはスキップ"""
        # .jsonファイルを作成（txtではない）
        json_file = temp_plugin_env.loops_path / "Loop0001_test.json"
        json_file.write_text('{"overall_digest": {"abstract": "test"}}')

        shadow_digest = {"source_files": [json_file.name]}
        result = loader.generate_from_source("weekly", shadow_digest)

        # txtでないファイルはスキップ
        assert len(result) == 0

    @pytest.mark.integration
    def test_source_file_missing_overall_digest(self, loader, temp_plugin_env):
        """overall_digestがないソースファイルでもエラーにならない"""
        # overall_digestがないLoopファイル
        loop_file = temp_plugin_env.loops_path / "Loop0001_no_overall.txt"
        loop_file.write_text('{"metadata": {"version": "1.0"}}')

        shadow_digest = {"source_files": [loop_file.name]}
        result = loader.generate_from_source("weekly", shadow_digest)

        # 処理は成功するが、フィールドは空/デフォルト値
        assert len(result) == 1
        # Changed from "filename" to "source_file"
        assert result[0]["source_file"] == loop_file.name
        assert result[0]["abstract"] == ""
        assert result[0]["keywords"] == []


# =============================================================================
# skipped_count 集計テスト（Phase 6: カバレッジ向上）
# =============================================================================


class TestProvisionalLoaderSkippedCount:
    """generate_from_source の skipped_count 集計テスト"""

    @pytest.mark.integration
    def test_skipped_count_on_json_decode_error(self, loader, temp_plugin_env, caplog):
        """JSONDecodeError発生時にskipped_countが増加し、警告ログが出力される"""
        import logging

        caplog.set_level(logging.WARNING)

        # 不正なJSONファイルを作成
        invalid_loop = temp_plugin_env.loops_path / "Loop0001_invalid.txt"
        invalid_loop.write_text("{ invalid json }")

        shadow_digest = {"source_files": [invalid_loop.name]}
        result = loader.generate_from_source("weekly", shadow_digest)

        # 結果は空
        assert len(result) == 0

        # 警告ログが出力されている
        assert "Failed to parse" in caplog.text
        assert "(skipped)" in caplog.text

    @pytest.mark.integration
    def test_skipped_count_summary_log_on_multiple_errors(self, loader, temp_plugin_env, caplog):
        """複数エラー発生時に集計ログが出力される"""
        import logging

        caplog.set_level(logging.WARNING)

        # 複数の不正なJSONファイルを作成
        invalid1 = temp_plugin_env.loops_path / "Loop0001_bad1.txt"
        invalid1.write_text("{ bad json 1 }")

        invalid2 = temp_plugin_env.loops_path / "Loop0002_bad2.txt"
        invalid2.write_text("{ bad json 2 }")

        shadow_digest = {"source_files": [invalid1.name, invalid2.name]}
        result = loader.generate_from_source("weekly", shadow_digest)

        # 結果は空
        assert len(result) == 0

        # 集計ログが出力されている
        assert "Skipped 2/2 files due to errors" in caplog.text

    @pytest.mark.integration
    def test_skipped_count_partial_success(self, loader, temp_plugin_env, caplog):
        """一部成功、一部失敗の場合の集計ログ"""
        import logging

        caplog.set_level(logging.WARNING)

        # 不正なJSONファイル
        invalid_loop = temp_plugin_env.loops_path / "Loop0001_invalid.txt"
        invalid_loop.write_text("{ invalid }")

        # 正常なLoopファイル
        valid_loop = create_test_loop_file(temp_plugin_env.loops_path, 2)

        shadow_digest = {"source_files": [invalid_loop.name, valid_loop.name]}
        result = loader.generate_from_source("weekly", shadow_digest)

        # 正常なファイルのみ処理される
        assert len(result) == 1
        # Changed from "filename" to "source_file"
        assert result[0]["source_file"] == valid_loop.name

        # 1/2がスキップされた集計ログ
        assert "Skipped 1/2 files due to errors" in caplog.text

    @pytest.mark.integration
    def test_no_summary_log_when_no_errors(self, loader, temp_plugin_env, caplog):
        """エラーがない場合は集計ログが出力されない"""
        import logging

        caplog.set_level(logging.WARNING)

        # 正常なLoopファイルのみ
        valid_loop = create_test_loop_file(temp_plugin_env.loops_path, 1)

        shadow_digest = {"source_files": [valid_loop.name]}
        result = loader.generate_from_source("weekly", shadow_digest)

        assert len(result) == 1

        # "Skipped"という警告ログはない
        assert "Skipped" not in caplog.text
