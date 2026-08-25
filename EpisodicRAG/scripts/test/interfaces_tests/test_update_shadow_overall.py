#!/usr/bin/env python3
"""
update_shadow_overall.py のテスト
==================================

ShadowGrandDigest の overall_digest 5要素更新 CLI のテスト。

背景:
    SGD の overall_digest（digest_type/keywords/abstract/impression）は
    2400字級の日本語文字列を含む JSON であり、Edit ツールの exact-match
    置換は事故りやすい。検証済みのプログラム経由で更新する。
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
from interfaces.update_shadow_overall import OverallDigestUpdater

EMDASH_TYPE = "診断学→方法論→実装鋳造——三週弧"

UPDATE_PAYLOAD = {
    "digest_type": EMDASH_TYPE,
    "keywords": [
        "キーワード一——長文の統合分析を含む",
        "キーワード二",
        "キーワード三",
        "キーワード四",
        "キーワード五",
    ],
    "abstract": "🔵 三週統合の abstract——em-dash と絵文字を含む長文。\n\n第二段落。",
    "impression": "🟡💜 三週統合の impression。知らんけど。",
}


class UpdateShadowOverallTestBase(unittest.TestCase):
    """temp SGD + config を構築する共通基盤"""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="episodic_uso_")
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
        with (self.persistent_config / 'config.json').open('w', encoding='utf-8') as f:
            json.dump(config_data, f)

    def _create_shadow(self) -> None:
        """weekly=PLACEHOLDER / monthly=分析済み の SGD を作成"""
        self.shadow_path = self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt"
        self.original_shadow = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {
                    "overall_digest": {
                        "timestamp": "2025-01-01T00:00:00",
                        "source_files": [],
                        "digest_type": "<!-- PLACEHOLDER -->",
                        "keywords": [],
                        "abstract": "<!-- PLACEHOLDER -->",
                        "impression": "<!-- PLACEHOLDER -->",
                    }
                },
                "monthly": {
                    "overall_digest": {
                        "timestamp": "2025-06-19T00:00:00",
                        "source_files": [
                            "W0106_合成の誤謬から検証の規律へ.txt",
                            "W0107_変異と淘汰圧が揃う週：方法の前景化.txt",
                            "W0108_受注者能力を持った発注者：基質が決める最安コーナー.txt",
                        ],
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


class TestOverallDigestUpdater(UpdateShadowOverallTestBase):
    """OverallDigestUpdater クラスのテスト"""

    def _updater(self) -> OverallDigestUpdater:
        return OverallDigestUpdater(config=DigestConfig())

    @pytest.mark.integration
    def test_update_monthly_overall(self) -> None:
        """monthly の4要素が更新され、weekly が不変"""
        self._updater().update_overall("monthly", UPDATE_PAYLOAD)

        saved = self._load_shadow()
        monthly = saved["latest_digests"]["monthly"]["overall_digest"]
        self.assertEqual(monthly["digest_type"], EMDASH_TYPE)
        self.assertEqual(len(monthly["keywords"]), 5)
        self.assertEqual(monthly["abstract"], UPDATE_PAYLOAD["abstract"])
        self.assertEqual(monthly["impression"], UPDATE_PAYLOAD["impression"])

        # weekly は完全不変
        self.assertEqual(
            saved["latest_digests"]["weekly"],
            self.original_shadow["latest_digests"]["weekly"],
        )

    @pytest.mark.integration
    def test_source_files_preserved(self) -> None:
        """source_files が更新前後で不変"""
        self._updater().update_overall("monthly", UPDATE_PAYLOAD)

        saved = self._load_shadow()
        self.assertEqual(
            saved["latest_digests"]["monthly"]["overall_digest"]["source_files"],
            self.original_shadow["latest_digests"]["monthly"]["overall_digest"]["source_files"],
        )

    @pytest.mark.integration
    def test_japanese_no_garble(self) -> None:
        """em-dash・日本語・絵文字が保持され \\uXXXX エスケープが出ない"""
        self._updater().update_overall("monthly", UPDATE_PAYLOAD)

        raw = self.shadow_path.read_text(encoding="utf-8")
        self.assertIn(EMDASH_TYPE, raw)
        self.assertIn("🔵", raw)
        self.assertNotIn("\\u2014", raw)  # ensure_ascii=False の検証

    @pytest.mark.integration
    def test_timestamps_updated(self) -> None:
        """overall.timestamp と metadata.last_updated が更新される"""
        self._updater().update_overall("monthly", UPDATE_PAYLOAD)

        saved = self._load_shadow()
        self.assertNotEqual(
            saved["latest_digests"]["monthly"]["overall_digest"]["timestamp"],
            "2025-06-19T00:00:00",
        )
        self.assertNotEqual(saved["metadata"]["last_updated"], "2025-01-01T00:00:00")

    @pytest.mark.integration
    def test_idempotent(self) -> None:
        """同一入力の再実行で内容が同一（timestamp 以外）"""
        updater = self._updater()
        updater.update_overall("monthly", UPDATE_PAYLOAD)
        first = self._load_shadow()
        updater.update_overall("monthly", UPDATE_PAYLOAD)
        second = self._load_shadow()

        for snapshot in (first, second):
            snapshot["metadata"]["last_updated"] = "X"
            snapshot["latest_digests"]["monthly"]["overall_digest"]["timestamp"] = "X"
        self.assertEqual(first, second)

    @pytest.mark.integration
    def test_missing_key_rejected(self) -> None:
        """必須キー欠落（abstract なし）はエラーになり SGD 不変"""
        broken = {k: v for k, v in UPDATE_PAYLOAD.items() if k != "abstract"}
        with self.assertRaises(EpisodicRAGError):
            self._updater().update_overall("monthly", broken)

        self.assertEqual(self._load_shadow(), self.original_shadow)

    @pytest.mark.integration
    def test_keywords_must_be_list(self) -> None:
        """keywords が文字列（リストでない）はエラー"""
        broken = dict(UPDATE_PAYLOAD, keywords="not-a-list")
        with self.assertRaises(EpisodicRAGError):
            self._updater().update_overall("monthly", broken)


class TestUpdateShadowOverallCLI(UpdateShadowOverallTestBase):
    """CLI エントリーポイントのテスト（subprocess）"""

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess:
        scripts_dir = Path(__file__).parent.parent.parent
        env = {**dict(os.environ), "EPISODICRAG_CONFIG_DIR": str(self.persistent_config)}
        return subprocess.run(
            [sys.executable, "-m", "interfaces.update_shadow_overall", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=scripts_dir,
            env=env,
        )

    @pytest.mark.integration
    def test_cli_updates_from_json_file(self) -> None:
        """JSON ファイル経由で CLI 更新が成功する"""
        payload_file = self.plugin_root / "payload.json"
        payload_file.write_text(json.dumps(UPDATE_PAYLOAD, ensure_ascii=False), encoding="utf-8")

        result = self._run_cli("monthly", str(payload_file))

        self.assertEqual(result.returncode, 0, f"CLI 失敗: {result.stderr}")
        saved = self._load_shadow()
        self.assertEqual(
            saved["latest_digests"]["monthly"]["overall_digest"]["digest_type"],
            EMDASH_TYPE,
        )

    @pytest.mark.integration
    def test_cli_invalid_level_rejected(self) -> None:
        """不正な level は非0 exit"""
        payload_file = self.plugin_root / "payload.json"
        payload_file.write_text(json.dumps(UPDATE_PAYLOAD, ensure_ascii=False), encoding="utf-8")

        result = self._run_cli("nosuchlevel", str(payload_file))

        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
