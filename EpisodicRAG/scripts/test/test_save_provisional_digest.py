#!/usr/bin/env python3
"""
ProvisionalDigestSaver 統合テスト
==================================

一時ディレクトリを使用したファイルI/Oテスト
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# Interfaces層
from domain.exceptions import ValidationError
from interfaces import ProvisionalDigestSaver


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


class TestProvisionalDigestSaver:
    """ProvisionalDigestSaver の統合テスト"""

    @pytest.mark.integration
    def test_load_individual_digests_from_list(self, provisional_saver):
        """JSON文字列（リスト形式）からの読み込み"""
        json_str = '[{"source_file": "Loop0001.txt", "keywords": ["test"]}]'
        result = provisional_saver.load_individual_digests(json_str)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["source_file"] == "Loop0001.txt"

    @pytest.mark.integration
    def test_load_individual_digests_from_dict(self, provisional_saver):
        """JSON文字列（dict形式）からの読み込み"""
        json_str = '{"individual_digests": [{"source_file": "Loop0001.txt"}]}'
        result = provisional_saver.load_individual_digests(json_str)

        assert isinstance(result, list)
        assert len(result) == 1

    @pytest.mark.integration
    def test_load_individual_digests_empty_raises(self, provisional_saver):
        """空文字列でValidationError"""
        with pytest.raises(ValidationError):
            provisional_saver.load_individual_digests("")

    @pytest.mark.integration
    def test_merge_individual_digests(self, provisional_saver):
        """マージ処理（重複は上書き）"""
        existing = [
            {"source_file": "Loop0001.txt", "keywords": ["old"]},
            {"source_file": "Loop0002.txt", "keywords": ["keep"]},
        ]
        new = [
            {"source_file": "Loop0001.txt", "keywords": ["new"]},
            {"source_file": "Loop0003.txt", "keywords": ["added"]},
        ]

        result = provisional_saver.merge_individual_digests(existing, new)

        assert len(result) == 3
        # Loop0001は上書きされる
        loop1 = next(d for d in result if d["source_file"] == "Loop0001.txt")
        assert loop1["keywords"] == ["new"]

    @pytest.mark.integration
    def test_merge_individual_digests_missing_filename_raises(self, provisional_saver):
        """source_fileキーがない場合ValidationError"""
        existing = [{"keywords": ["test"]}]  # source_fileなし
        new = [{"source_file": "Loop0001.txt"}]

        with pytest.raises(ValidationError):
            provisional_saver.merge_individual_digests(existing, new)

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
