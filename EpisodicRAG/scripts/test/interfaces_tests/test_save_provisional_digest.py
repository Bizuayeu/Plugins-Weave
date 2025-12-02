#!/usr/bin/env python3
"""
ProvisionalDigestSaver 統合テスト
==================================

一時ディレクトリを使用したファイルI/Oテスト
"""

import io
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Interfaces層
from domain.exceptions import ValidationError
from interfaces import ProvisionalDigestSaver
from interfaces.provisional import DigestMerger, InputLoader


@pytest.fixture
def provisional_saver(temp_plugin_env):
    """ProvisionalDigestSaverインスタンスを提供"""
    # Provisionalディレクトリを作成
    weekly_provisional = temp_plugin_env.digests_path / "1_Weekly" / "Provisional"
    weekly_provisional.mkdir(parents=True, exist_ok=True)

    with patch('interfaces.save_provisional_digest.DigestConfig') as mock_config_class:
        mock_config = MagicMock()
        mock_config.digests_path = temp_plugin_env.digests_path
        mock_config.get_provisional_dir.return_value = weekly_provisional
        mock_config_class.return_value = mock_config
        saver = ProvisionalDigestSaver()
        saver._weekly_provisional = weekly_provisional  # テストからアクセス可能に
        yield saver


class TestInputLoader:
    """InputLoader のテスト"""

    @pytest.mark.integration
    def test_load_individual_digests_from_list(self, temp_plugin_env):
        """JSON文字列（リスト形式）からの読み込み"""
        json_str = '[{"source_file": "Loop0001.txt", "keywords": ["test"]}]'
        result = InputLoader.load(json_str)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["source_file"] == "Loop0001.txt"

    @pytest.mark.integration
    def test_load_individual_digests_from_dict(self, temp_plugin_env):
        """JSON文字列（dict形式）からの読み込み"""
        json_str = '{"individual_digests": [{"source_file": "Loop0001.txt"}]}'
        result = InputLoader.load(json_str)

        assert isinstance(result, list)
        assert len(result) == 1

    @pytest.mark.integration
    def test_load_individual_digests_empty_raises(self, temp_plugin_env):
        """空文字列でValidationError"""
        with pytest.raises(ValidationError):
            InputLoader.load("")


class TestDigestMerger:
    """DigestMerger のテスト"""

    @pytest.mark.integration
    def test_merge_individual_digests(self, temp_plugin_env):
        """マージ処理（重複は上書き）"""
        existing = [
            {"source_file": "Loop0001.txt", "keywords": ["old"]},
            {"source_file": "Loop0002.txt", "keywords": ["keep"]},
        ]
        new = [
            {"source_file": "Loop0001.txt", "keywords": ["new"]},
            {"source_file": "Loop0003.txt", "keywords": ["added"]},
        ]

        result = DigestMerger.merge(existing, new)

        assert len(result) == 3
        # Loop0001は上書きされる
        loop1 = next(d for d in result if d["source_file"] == "Loop0001.txt")
        assert loop1["keywords"] == ["new"]

    @pytest.mark.integration
    def test_merge_individual_digests_missing_filename_raises(self, temp_plugin_env):
        """source_fileキーがない場合ValidationError"""
        existing = [{"keywords": ["test"]}]  # source_fileなし
        new = [{"source_file": "Loop0001.txt"}]

        with pytest.raises(ValidationError):
            DigestMerger.merge(existing, new)


class TestProvisionalDigestSaver:
    """ProvisionalDigestSaver の統合テスト"""

    @pytest.mark.integration
    def test_save_provisional_new_file(self, provisional_saver):
        """新規Provisionalファイルの保存"""
        individual_digests = [{"source_file": "Loop0001.txt", "keywords": ["test"]}]

        saved_path = provisional_saver.save_provisional("weekly", individual_digests)

        assert saved_path.exists()
        assert "W0001_Individual.txt" in saved_path.name

        # 保存内容を検証
        with open(saved_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert "metadata" in data
        assert "individual_digests" in data
        assert len(data["individual_digests"]) == 1

    @pytest.mark.integration
    def test_save_provisional_append_mode(self, provisional_saver):
        """追加モードでの保存"""
        # 最初の保存
        first_digests = [{"source_file": "Loop0001.txt", "keywords": ["first"]}]
        first_path = provisional_saver.save_provisional("weekly", first_digests)

        # 追加保存
        second_digests = [{"source_file": "Loop0002.txt", "keywords": ["second"]}]
        second_path = provisional_saver.save_provisional("weekly", second_digests, append=True)

        # 同じファイルに追加されている
        assert first_path == second_path

        with open(second_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert len(data["individual_digests"]) == 2


class TestCLIStdinOption:
    """--stdin オプションのテスト"""

    @pytest.mark.integration
    def test_stdin_option_reads_from_stdin(self, temp_plugin_env, monkeypatch):
        """--stdin オプションで標準入力からJSONを読み込む"""
        from interfaces.save_provisional_digest import main

        # テスト用JSON
        test_json = json.dumps({
            "individual_digests": {
                "Loop0001.txt": {
                    "digest_type": "test",
                    "keywords": ["keyword1"],
                    "abstract": {"long": "long text", "short": "short"},
                    "impression": {"long": "impression long", "short": "short"}
                }
            }
        })

        # 標準入力をモック
        monkeypatch.setattr('sys.stdin', io.StringIO(test_json))

        # コマンドライン引数をモック
        test_args = ['save_provisional_digest.py', 'weekly', '--stdin']
        monkeypatch.setattr('sys.argv', test_args)

        # DigestConfigをモック
        with patch('interfaces.save_provisional_digest.DigestConfig') as mock_config_class:
            mock_config = MagicMock()
            mock_config.digests_path = temp_plugin_env.digests_path
            provisional_dir = temp_plugin_env.digests_path / "1_Weekly" / "Provisional"
            provisional_dir.mkdir(parents=True, exist_ok=True)
            mock_config.get_provisional_dir.return_value = provisional_dir
            mock_config_class.return_value = mock_config

            # main() 実行（例外なく完了すればOK）
            main()

        # Provisionalファイルが作成されたことを確認
        provisional_files = list(provisional_dir.glob("*.txt"))
        assert len(provisional_files) == 1

    @pytest.mark.integration
    def test_error_when_no_input_and_no_stdin(self, temp_plugin_env, monkeypatch):
        """input_dataも--stdinもない場合はエラー"""
        from interfaces.save_provisional_digest import main

        # コマンドライン引数（input_dataなし、--stdinなし）
        test_args = ['save_provisional_digest.py', 'weekly']
        monkeypatch.setattr('sys.argv', test_args)

        # argparse.error() は SystemExit を発生させる
        with pytest.raises(SystemExit) as exc_info:
            main()

        # エラーコード2（argparseのエラー）
        assert exc_info.value.code == 2
