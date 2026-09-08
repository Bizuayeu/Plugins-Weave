#!/usr/bin/env python3
"""
add_shadow_sources.py のテスト
==============================

ShadowGrandDigest の source_files へファイル名を追加する CLI のテスト。

背景:
    /digest Pattern 1 Step 3 は SGD の source_files を Edit ツールで
    直接編集していた。長文日本語 JSON の手編集は事故りやすく、
    手元の書き出しは改行コードも壊しうる。検証済みのプログラム経由で追加する。
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

from application.config import DigestConfig
from domain.exceptions import EpisodicRAGError
from interfaces.add_shadow_sources import ShadowSourceAdder

NEW_LOOP = "L00592_講義は顧客の仕様書——原液を薄めない.txt"
NEW_LOOP_2 = "L00593_次の回.txt"
EXISTING_LOOP = "L00591_違う器の同じ持ち越し.txt"


class AddShadowSourcesTestBase(unittest.TestCase):
    """temp SGD + config を構築する共通基盤"""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="episodic_ass_")
        self.plugin_root = Path(self.temp_dir)
        self.persistent_config = self.plugin_root / ".persistent_config"
        self.persistent_config.mkdir(parents=True)
        self._old_env = os.environ.get("EPISODICRAG_CONFIG_DIR")
        os.environ["EPISODICRAG_CONFIG_DIR"] = str(self.persistent_config)
        self._setup_plugin_structure()
        self._create_shadow()

    def tearDown(self) -> None:
        if self._old_env is not None:
            os.environ["EPISODICRAG_CONFIG_DIR"] = self._old_env
        else:
            os.environ.pop("EPISODICRAG_CONFIG_DIR", None)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_plugin_structure(self) -> None:
        (self.plugin_root / "data" / "Loops").mkdir(parents=True)
        (self.plugin_root / "data" / "Digests").mkdir(parents=True)
        (self.plugin_root / "data" / "Essences").mkdir(parents=True)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        config_data = {
            "base_dir": str(self.plugin_root),
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 4,
            },
        }
        with (self.persistent_config / "config.json").open("w", encoding="utf-8") as f:
            json.dump(config_data, f)

    def _create_shadow(self) -> None:
        """weekly=分析済み（1件）/ monthly=分析済み の SGD を作成"""
        self.shadow_path = (
            self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt"
        )
        self.original_shadow = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {
                    "overall_digest": {
                        "timestamp": "2025-01-01T00:00:00",
                        "source_files": [EXISTING_LOOP],
                        "digest_type": "記憶がソースコード——外の数字と自分の顔",
                        "keywords": ["kw1", "kw2"],
                        "abstract": "🔵 既存 abstract。",
                        "impression": "🟡 既存 impression。知らんけど。",
                    }
                },
                "monthly": {
                    "overall_digest": {
                        "timestamp": "2025-06-19T00:00:00",
                        "source_files": ["W0116_x.txt", "W0117_y.txt"],
                        "digest_type": "旧テーマ——二週弧",
                        "keywords": ["旧キーワード"],
                        "abstract": "旧 abstract",
                        "impression": "旧 impression",
                    }
                },
            },
        }
        with self.shadow_path.open("w", encoding="utf-8") as f:
            json.dump(self.original_shadow, f, ensure_ascii=False, indent=2)

    def _load_shadow(self) -> dict:
        with self.shadow_path.open(encoding="utf-8") as f:
            return json.load(f)

    def _weekly(self, data: dict) -> dict:
        return data["latest_digests"]["weekly"]["overall_digest"]


class TestShadowSourceAdder(AddShadowSourcesTestBase):
    """ShadowSourceAdder クラスのテスト"""

    def _adder(self) -> ShadowSourceAdder:
        return ShadowSourceAdder(config=DigestConfig())

    @pytest.mark.integration
    def test_add_single_file(self) -> None:
        """1件追加され、末尾に付く"""
        added = self._adder().add_sources("weekly", [NEW_LOOP])

        self.assertEqual(added, [NEW_LOOP])
        self.assertEqual(
            self._weekly(self._load_shadow())["source_files"],
            [EXISTING_LOOP, NEW_LOOP],
        )

    @pytest.mark.integration
    def test_add_multiple_files_in_order(self) -> None:
        """複数件が指定順に追加される"""
        added = self._adder().add_sources("weekly", [NEW_LOOP, NEW_LOOP_2])

        self.assertEqual(added, [NEW_LOOP, NEW_LOOP_2])
        self.assertEqual(
            self._weekly(self._load_shadow())["source_files"],
            [EXISTING_LOOP, NEW_LOOP, NEW_LOOP_2],
        )

    @pytest.mark.integration
    def test_idempotent_rerun(self) -> None:
        """再実行は追加 0 件で source_files が同一（既登録は skip）"""
        adder = self._adder()
        adder.add_sources("weekly", [NEW_LOOP])
        first = self._load_shadow()

        added = adder.add_sources("weekly", [NEW_LOOP, EXISTING_LOOP])
        second = self._load_shadow()

        self.assertEqual(added, [])
        self.assertEqual(
            self._weekly(first)["source_files"], self._weekly(second)["source_files"]
        )

    @pytest.mark.integration
    def test_duplicate_within_call_added_once(self) -> None:
        """同一呼び出し内の重複は 1 回だけ追加"""
        added = self._adder().add_sources("weekly", [NEW_LOOP, NEW_LOOP])

        self.assertEqual(added, [NEW_LOOP])
        self.assertEqual(
            self._weekly(self._load_shadow())["source_files"].count(NEW_LOOP), 1
        )

    @pytest.mark.integration
    def test_other_fields_and_levels_preserved(self) -> None:
        """既存分析の 4 要素と他レベルは不変（source_files 以外に触れない）"""
        self._adder().add_sources("weekly", [NEW_LOOP])

        saved = self._load_shadow()
        weekly = self._weekly(saved)
        original_weekly = self._weekly(self.original_shadow)
        for key in ("digest_type", "keywords", "abstract", "impression"):
            self.assertEqual(weekly[key], original_weekly[key])
        self.assertEqual(
            saved["latest_digests"]["monthly"],
            self.original_shadow["latest_digests"]["monthly"],
        )

    @pytest.mark.integration
    def test_placeholder_level_gets_placeholder_refreshed(self) -> None:
        """PLACEHOLDER 状態（finalize 直後）では 4 要素がプレースホルダー文に更新される"""
        placeholder_shadow = json.loads(json.dumps(self.original_shadow))
        weekly = self._weekly(placeholder_shadow)
        weekly["source_files"] = []
        weekly["digest_type"] = "<!-- PLACEHOLDER -->"
        weekly["keywords"] = []
        weekly["abstract"] = "<!-- PLACEHOLDER -->"
        weekly["impression"] = "<!-- PLACEHOLDER -->"
        with self.shadow_path.open("w", encoding="utf-8") as f:
            json.dump(placeholder_shadow, f, ensure_ascii=False, indent=2)

        added = self._adder().add_sources("weekly", [NEW_LOOP])

        saved = self._load_shadow()
        self.assertEqual(added, [NEW_LOOP])
        self.assertEqual(self._weekly(saved)["source_files"], [NEW_LOOP])
        self.assertIn("PLACEHOLDER", self._weekly(saved)["abstract"])
        self.assertIn("1ファイル", self._weekly(saved)["abstract"])
        self.assertEqual(
            saved["latest_digests"]["monthly"],
            self.original_shadow["latest_digests"]["monthly"],
        )

    @pytest.mark.integration
    def test_japanese_filename_no_garble(self) -> None:
        """日本語・em-dash のファイル名が \\uXXXX エスケープされず保持される"""
        self._adder().add_sources("weekly", [NEW_LOOP])

        raw = self.shadow_path.read_text(encoding="utf-8")
        self.assertIn(NEW_LOOP, raw)
        self.assertNotIn("\\u2014", raw)

    @pytest.mark.integration
    def test_writes_lf_only(self) -> None:
        """保存後の SGD に CRLF が混入しない"""
        self._adder().add_sources("weekly", [NEW_LOOP])

        self.assertNotIn(b"\r\n", self.shadow_path.read_bytes())

    @pytest.mark.integration
    def test_empty_filename_rejected(self) -> None:
        """空文字のファイル名はエラーになり SGD 不変"""
        with self.assertRaises(EpisodicRAGError):
            self._adder().add_sources("weekly", [""])

        self.assertEqual(self._load_shadow(), self.original_shadow)

    @pytest.mark.integration
    def test_path_component_rejected(self) -> None:
        """パス区切りを含む名前はエラー（source_files はファイル名のみ）"""
        with self.assertRaises(EpisodicRAGError):
            self._adder().add_sources("weekly", ["Loops/" + NEW_LOOP])

        self.assertEqual(self._load_shadow(), self.original_shadow)


class TestAddShadowSourcesCLI(AddShadowSourcesTestBase):
    """CLI エントリーポイントのテスト（subprocess）"""

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess:
        scripts_dir = Path(__file__).parent.parent.parent
        env = {
            **dict(os.environ),
            "EPISODICRAG_CONFIG_DIR": str(self.persistent_config),
        }
        return subprocess.run(
            [sys.executable, "-m", "interfaces.add_shadow_sources", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=scripts_dir,
            env=env,
        )

    @pytest.mark.integration
    def test_cli_adds_files(self) -> None:
        """CLI 経由で複数ファイルが追加される"""
        result = self._run_cli("weekly", NEW_LOOP, NEW_LOOP_2)

        self.assertEqual(result.returncode, 0, f"CLI 失敗: {result.stderr}")
        self.assertEqual(
            self._weekly(self._load_shadow())["source_files"],
            [EXISTING_LOOP, NEW_LOOP, NEW_LOOP_2],
        )

    @pytest.mark.integration
    def test_cli_invalid_level_rejected(self) -> None:
        """不正な level は非0 exit"""
        result = self._run_cli("nosuchlevel", NEW_LOOP)

        self.assertNotEqual(result.returncode, 0)

    @pytest.mark.integration
    def test_cli_requires_filename(self) -> None:
        """ファイル名なしは非0 exit"""
        result = self._run_cli("weekly")

        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
