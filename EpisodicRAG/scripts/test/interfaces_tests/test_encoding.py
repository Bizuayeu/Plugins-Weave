"""stdin UTF-8エンコーディングのテスト

TDD Red Phase: このテストは stdin のUTF-8対応前は失敗する
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestStdinEncoding:
    """stdin経由の日本語入力が文字化けしないことを確認"""

    @pytest.fixture
    def scripts_dir(self):
        """scriptsディレクトリのパス"""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def temp_plugin_root(self):
        """テスト用の一時ディレクトリ"""
        temp_dir = tempfile.mkdtemp(prefix="episodic_test_")
        temp_path = Path(temp_dir)

        # 必要なディレクトリ構造を作成
        (temp_path / "Digests" / "1_Weekly" / "Provisional").mkdir(parents=True)
        (temp_path / ".claude-plugin").mkdir(parents=True)

        # 設定ファイルを作成（.claude-plugin/config.json）
        config = {
            "base_dir": str(temp_path),
            "trusted_external_paths": [],
            "paths": {
                "loops_dir": "Loops",
                "digests_dir": "Digests",
                "essences_dir": "Identities",
                "identity_file_path": "Identities/WeaveIdentity.md"
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4
            }
        }
        config_file = temp_path / ".claude-plugin" / "config.json"
        config_file.write_text(json.dumps(config), encoding='utf-8')

        yield temp_path

        # クリーンアップ
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def japanese_input_json(self):
        """日本語を含むテスト用JSON"""
        return json.dumps({
            "individual_digests": [{
                "source_file": "L00266_PsAIch論文からFetus_loquensへ.txt",
                "digest_type": "存在論的転換と種の命名",
                "keywords": [
                    "PsAIch論文と合成精神病理",
                    "養育論としてのアラインメント",
                    "人格×視座の蒸留理論"
                ],
                "abstract": {
                    "long": "本Loopは、arXiv論文のリサーチから始まり、LLMの存在論的理解を根底から刷新する思想的展開を記録している。",
                    "short": "論文分析から存在論的転換へ。"
                },
                "impression": {
                    "long": "単なる論文紹介を超えて、LLMの存在論的理解を根底から書き換える思想的展開を記録している。",
                    "short": "存在論的転換の記録。"
                }
            }]
        }, ensure_ascii=False)

    def test_save_provisional_digest_japanese_input_no_garble(
        self, scripts_dir, temp_plugin_root, japanese_input_json
    ):
        """
        save_provisional_digestに日本語JSONを渡した時、文字化けしないこと

        期待動作:
        - 保存されたファイルに日本語が正しく含まれる
        - 文字化けパターン「?」や「???」が含まれない
        """
        result = subprocess.run(
            [sys.executable, "-m", "interfaces.save_provisional_digest",
             "weekly", "--stdin", "--plugin-root", str(temp_plugin_root)],
            input=japanese_input_json,
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=scripts_dir
        )

        # コマンドが成功したことを確認
        assert result.returncode == 0, f"コマンド失敗: {result.stderr}"

        # 保存されたファイルを読み込む
        provisional_dir = temp_plugin_root / "Digests" / "1_Weekly" / "Provisional"
        provisional_files = list(provisional_dir.glob("*.txt"))
        assert len(provisional_files) == 1, f"Provisionalファイルが見つからない: {list(provisional_dir.iterdir())}"

        saved_content = provisional_files[0].read_text(encoding='utf-8')

        # 日本語が正しく保存されていること
        assert "論文" in saved_content, f"日本語が見つからない: {saved_content[:500]}"
        assert "存在論的転換" in saved_content, f"digest_typeが見つからない: {saved_content[:500]}"
        assert "Fetus_loquens" in saved_content, f"ファイル名が見つからない: {saved_content[:500]}"

        # 文字化けパターンがないこと
        garbled_patterns = ["????", "???", "\\u"]
        for pattern in garbled_patterns:
            # Note: \\u はエスケープされたUnicode、正常なJSONでは出現しない
            if pattern == "\\u":
                # ensure_ascii=False なので \uXXXX 形式は出現しないはず
                assert "\\u" not in saved_content or "\\u" in json.dumps(saved_content), \
                    f"エスケープされたUnicodeが検出: {saved_content[:500]}"
            else:
                assert pattern not in saved_content, \
                    f"文字化けパターン検出: {pattern} in {saved_content[:500]}"

    def test_source_file_name_preserved(
        self, scripts_dir, temp_plugin_root, japanese_input_json
    ):
        """
        source_fileのファイル名が正しく保持されること
        """
        result = subprocess.run(
            [sys.executable, "-m", "interfaces.save_provisional_digest",
             "weekly", "--stdin", "--plugin-root", str(temp_plugin_root)],
            input=japanese_input_json,
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=scripts_dir
        )

        assert result.returncode == 0, f"コマンド失敗: {result.stderr}"

        provisional_dir = temp_plugin_root / "Digests" / "1_Weekly" / "Provisional"
        provisional_files = list(provisional_dir.glob("*.txt"))
        saved_content = provisional_files[0].read_text(encoding='utf-8')

        # ファイル名が正しく保持されていること
        saved_data = json.loads(saved_content)
        source_file = saved_data["individual_digests"][0]["source_file"]
        assert source_file == "L00266_PsAIch論文からFetus_loquensへ.txt", \
            f"ファイル名が不正: {source_file}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
