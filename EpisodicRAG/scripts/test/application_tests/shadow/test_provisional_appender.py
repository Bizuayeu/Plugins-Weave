#!/usr/bin/env python3
"""
ProvisionalAppender テスト
==========================

provisional_appender.py のユニットテスト

カスケード処理時に、次レベルのProvisionalファイルへ
individual_digestを追加する機能をテスト。
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Dict, List

    from test_helpers import TempPluginEnvironment

    from application.config import DigestConfig
    from application.shadow import ShadowIO, ShadowTemplate
    from domain.types.level import LevelHierarchyEntry

import pytest

from domain.constants import LEVEL_CONFIG

# slow マーカーを適用（ファイル全体）
pytestmark = pytest.mark.slow

# =============================================================================
# フィクスチャ
# =============================================================================


@pytest.fixture
def level_hierarchy() -> "Dict[str, LevelHierarchyEntry]":
    """レベル階層情報"""
    return {
        level: {"source": cfg["source"], "next": cfg["next"]} for level, cfg in LEVEL_CONFIG.items()
    }


@pytest.fixture
def sample_finalized_digest() -> "Dict[str, Any]":
    """
    確定したRegularDigest（W0053相当）のサンプル

    finalize_from_shadow.pyが生成する形式。
    """
    return {
        "metadata": {
            "digest_level": "weekly",
            "digest_number": "0053",
            "created_at": "2025-12-08T00:00:00",
            "version": "1.0",
        },
        "overall_digest": {
            "name": "W0053_テストタイトル",  # フル名（RegularDigestBuilder.buildで生成）
            "timestamp": "2025-12-08T00:00:00",
            "source_files": ["L00261_test.txt", "L00262_test.txt"],
            "digest_type": "weekly",
            "keywords": ["test", "keyword"],
            "abstract": "Test abstract",
            "impression": "Test impression",
        },
        "individual_digests": [
            {
                "source_file": "L00261_test.txt",
                "digest_type": "テスト",
                "keywords": ["test1"],
                "abstract": {"long": "詳細1", "short": "簡潔1"},
                "impression": {"long": "所感1", "short": "短所感1"},
            },
            {
                "source_file": "L00262_test.txt",
                "digest_type": "開発",
                "keywords": ["test2"],
                "abstract": {"long": "詳細2", "short": "簡潔2"},
                "impression": {"long": "所感2", "short": "短所感2"},
            },
        ],
    }


@pytest.fixture
def provisional_appender(
    temp_plugin_env: "TempPluginEnvironment",
    level_hierarchy: "Dict[str, LevelHierarchyEntry]",
):
    """テスト用ProvisionalAppender"""
    from application.config import DigestConfig
    from application.shadow.provisional_appender import ProvisionalAppender

    config = DigestConfig()
    return ProvisionalAppender(config, level_hierarchy)


# =============================================================================
# append_to_next_provisional テスト
# =============================================================================


class TestAppendToEmptyProvisional:
    """Provisionalファイルが存在しない場合のテスト"""

    @pytest.mark.integration
    def test_creates_provisional_file_when_not_exists(
        self,
        provisional_appender,
        temp_plugin_env: "TempPluginEnvironment",
        sample_finalized_digest: "Dict[str, Any]",
    ) -> None:
        """Provisionalファイルが存在しない場合、新規作成される"""
        # weekly確定 → monthlyのProvisionalに追加
        provisional_appender.append_to_next_provisional("weekly", sample_finalized_digest)

        # M0001_Individual.txt が作成されているか確認
        monthly_provisional_dir = temp_plugin_env.digests_path / "2_Monthly" / "Provisional"
        provisional_files = list(monthly_provisional_dir.glob("M*_Individual.txt"))

        assert len(provisional_files) == 1
        assert provisional_files[0].exists()

    @pytest.mark.integration
    def test_new_provisional_contains_individual_digests(
        self,
        provisional_appender,
        temp_plugin_env: "TempPluginEnvironment",
        sample_finalized_digest: "Dict[str, Any]",
    ) -> None:
        """新規作成されたProvisionalに確定ダイジェストのindividual_digestsが含まれる"""
        provisional_appender.append_to_next_provisional("weekly", sample_finalized_digest)

        # ファイルの内容を確認
        monthly_provisional_dir = temp_plugin_env.digests_path / "2_Monthly" / "Provisional"
        provisional_file = list(monthly_provisional_dir.glob("M*_Individual.txt"))[0]

        with open(provisional_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # W0053からの情報が追加されていることを確認
        assert "individual_digests" in data
        # W0053全体を1エントリとして追加（source_fileはW0053_xxx.txt）
        assert len(data["individual_digests"]) == 1


class TestAppendToExistingProvisional:
    """既存Provisionalファイルへの追加テスト"""

    @pytest.mark.integration
    def test_appends_to_existing_provisional(
        self,
        provisional_appender,
        temp_plugin_env: "TempPluginEnvironment",
        sample_finalized_digest: "Dict[str, Any]",
    ) -> None:
        """既存Provisionalに新しいindividual_digestが追加される"""
        # 既存のProvisionalファイルを作成
        monthly_provisional_dir = temp_plugin_env.digests_path / "2_Monthly" / "Provisional"
        monthly_provisional_dir.mkdir(parents=True, exist_ok=True)
        existing_provisional = monthly_provisional_dir / "M0011_Individual.txt"

        existing_data = {
            "metadata": {
                "digest_level": "monthly",
                "digest_number": "0011",
                "last_updated": "2025-11-30T00:00:00",
                "version": "1.0",
            },
            "individual_digests": [
                {
                    "filename": "W0051_existing.txt",
                    "digest_type": "既存",
                    "keywords": ["existing"],
                    "abstract": "既存のabstract",
                    "impression": "既存のimpression",
                }
            ],
        }
        with open(existing_provisional, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

        # 追加
        provisional_appender.append_to_next_provisional("weekly", sample_finalized_digest)

        # 確認
        with open(existing_provisional, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 既存1件 + 新規1件（W0053） = 2件
        assert len(data["individual_digests"]) == 2
        # 既存エントリが保持されている
        filenames = [d.get("filename") for d in data["individual_digests"]]
        assert "W0051_existing.txt" in filenames


class TestDuplicateSourceFileSkipped:
    """重複source_file スキップテスト"""

    @pytest.mark.integration
    def test_skips_duplicate_source_file(
        self,
        provisional_appender,
        temp_plugin_env: "TempPluginEnvironment",
        sample_finalized_digest: "Dict[str, Any]",
    ) -> None:
        """同じsource_fileが既に存在する場合、スキップされる"""
        # W0053を含む既存Provisionalファイルを作成
        monthly_provisional_dir = temp_plugin_env.digests_path / "2_Monthly" / "Provisional"
        monthly_provisional_dir.mkdir(parents=True, exist_ok=True)
        existing_provisional = monthly_provisional_dir / "M0011_Individual.txt"

        existing_data = {
            "metadata": {
                "digest_level": "monthly",
                "digest_number": "0011",
                "last_updated": "2025-11-30T00:00:00",
                "version": "1.0",
            },
            "individual_digests": [
                {
                    "filename": "W0053_test.txt",  # sample_finalized_digestと同じ
                    "digest_type": "重複",
                    "keywords": ["duplicate"],
                    "abstract": "重複のabstract",
                    "impression": "重複のimpression",
                }
            ],
        }
        with open(existing_provisional, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

        # 同じW0053を追加しようとする
        provisional_appender.append_to_next_provisional("weekly", sample_finalized_digest)

        # 確認：件数が増えていない
        with open(existing_provisional, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["individual_digests"]) == 1  # 重複なので追加されない


class TestProvisionalDirectoryCreation:
    """Provisionalディレクトリ作成テスト"""

    @pytest.mark.integration
    def test_creates_provisional_directory_if_missing(
        self,
        provisional_appender,
        temp_plugin_env: "TempPluginEnvironment",
        sample_finalized_digest: "Dict[str, Any]",
    ) -> None:
        """Provisionalディレクトリが存在しない場合、作成される"""
        # Provisionalディレクトリを削除
        monthly_provisional_dir = temp_plugin_env.digests_path / "2_Monthly" / "Provisional"
        if monthly_provisional_dir.exists():
            import shutil

            shutil.rmtree(monthly_provisional_dir)

        assert not monthly_provisional_dir.exists()

        # 追加処理（ディレクトリ作成が必要）
        provisional_appender.append_to_next_provisional("weekly", sample_finalized_digest)

        # ディレクトリが作成されている
        assert monthly_provisional_dir.exists()
        assert monthly_provisional_dir.is_dir()


# =============================================================================
# エッジケーステスト
# =============================================================================


class TestProvisionalAppenderEdgeCases:
    """ProvisionalAppender のエッジケーステスト"""

    @pytest.mark.unit
    def test_centurial_skips_provisional_append(
        self,
        provisional_appender,
        sample_finalized_digest: "Dict[str, Any]",
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """centurialは最上位のため、Provisional追加をスキップ"""
        # centurialには次レベルがない
        provisional_appender.append_to_next_provisional("centurial", sample_finalized_digest)

        # スキップメッセージがログに出力される
        assert "centurialに上位レベルなし" in caplog.text or "最上位" in caplog.text

    @pytest.mark.integration
    def test_updates_metadata_last_updated(
        self,
        provisional_appender,
        temp_plugin_env: "TempPluginEnvironment",
        sample_finalized_digest: "Dict[str, Any]",
    ) -> None:
        """Provisionalのmetadata.last_updatedが更新される"""
        # 既存Provisionalを作成（古いlast_updated）
        monthly_provisional_dir = temp_plugin_env.digests_path / "2_Monthly" / "Provisional"
        monthly_provisional_dir.mkdir(parents=True, exist_ok=True)
        existing_provisional = monthly_provisional_dir / "M0011_Individual.txt"

        old_timestamp = "2020-01-01T00:00:00"
        existing_data = {
            "metadata": {
                "digest_level": "monthly",
                "digest_number": "0011",
                "last_updated": old_timestamp,
                "version": "1.0",
            },
            "individual_digests": [],
        }
        with open(existing_provisional, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

        # 追加
        provisional_appender.append_to_next_provisional("weekly", sample_finalized_digest)

        # last_updatedが更新されている
        with open(existing_provisional, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["metadata"]["last_updated"] != old_timestamp


# =============================================================================
# filename フォーマットテスト（SGD source_files との整合性）
# =============================================================================


class TestProvisionalFilenameMatchesSGD:
    """Provisional filename が SGD source_files と一致するテスト

    digest_readiness.py は SGD.source_files と Provisional.filename を
    完全一致で比較するため、filename にはフル名（タイトル含む）が必要。
    """

    @pytest.mark.integration
    def test_filename_includes_full_digest_name(
        self,
        provisional_appender,
        temp_plugin_env: "TempPluginEnvironment",
        sample_finalized_digest: "Dict[str, Any]",
    ) -> None:
        """追加されるエントリのfilenameがoverall_digest.name + .txt形式であること"""
        provisional_appender.append_to_next_provisional("weekly", sample_finalized_digest)

        monthly_provisional_dir = temp_plugin_env.digests_path / "2_Monthly" / "Provisional"
        provisional_file = list(monthly_provisional_dir.glob("M*_Individual.txt"))[0]

        with open(provisional_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        entry = data["individual_digests"][0]
        # source_fileフィールドを使用（digest_readiness.pyとの整合性）
        assert "source_file" in entry
        # フル名 (W0053_テストタイトル.txt) であること
        assert entry["source_file"] == "W0053_テストタイトル.txt"
        # 短縮名 (W0053.txt) ではないこと
        assert entry["source_file"] != "W0053.txt"

    @pytest.mark.integration
    def test_filename_fallback_when_name_missing(
        self,
        provisional_appender,
        temp_plugin_env: "TempPluginEnvironment",
    ) -> None:
        """overall_digest.name がない場合、prefix+number.txt にフォールバック"""
        # nameフィールドなしのダイジェスト
        digest_without_name = {
            "metadata": {
                "digest_level": "weekly",
                "digest_number": "0099",
                "created_at": "2025-12-08T00:00:00",
                "version": "1.0",
            },
            "overall_digest": {
                # "name" フィールドなし（レガシーデータ対応）
                "timestamp": "2025-12-08T00:00:00",
                "source_files": [],
                "digest_type": "test",
                "keywords": [],
                "abstract": "",
                "impression": "",
            },
            "individual_digests": [],
        }

        provisional_appender.append_to_next_provisional("weekly", digest_without_name)

        monthly_provisional_dir = temp_plugin_env.digests_path / "2_Monthly" / "Provisional"
        provisional_file = list(monthly_provisional_dir.glob("M*_Individual.txt"))[0]

        with open(provisional_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        entry = data["individual_digests"][0]
        # フォールバック: W0099.txt
        assert entry["source_file"] == "W0099.txt"


# =============================================================================
# 既存RegularDigestからの番号決定テスト
# =============================================================================


class TestProvisionalNumberingFromExistingRegular:
    """既存RegularDigestから正しい番号を決定するテスト

    BUG FIX: 既存Provisionalがない場合でも、既存RegularDigestから
    次番号を決定すべき。0001ハードコードではなく。
    """

    @pytest.mark.integration
    def test_uses_next_number_after_existing_regular_digest(
        self,
        provisional_appender,
        temp_plugin_env: "TempPluginEnvironment",
        sample_finalized_digest: "Dict[str, Any]",
    ) -> None:
        """
        既存RegularDigest（M0011）がある場合、
        新規ProvisionalはM0012_Individual.txtで作成される
        """
        # Arrange: M0011のRegularDigestを作成
        monthly_dir = temp_plugin_env.digests_path / "2_Monthly"
        monthly_dir.mkdir(parents=True, exist_ok=True)
        (monthly_dir / "M0011_テスト.txt").write_text("{}", encoding="utf-8")

        # Act: weekly確定時のProvisional追加
        provisional_appender.append_to_next_provisional("weekly", sample_finalized_digest)

        # Assert: M0012_Individual.txtが作成される（M0001ではない）
        provisional_dir = monthly_dir / "Provisional"
        provisional_files = list(provisional_dir.glob("M*_Individual.txt"))
        assert len(provisional_files) == 1
        assert "M0012" in provisional_files[0].name, (
            f"Expected M0012 but got {provisional_files[0].name}"
        )

    @pytest.mark.integration
    def test_uses_next_number_when_no_provisional_but_regular_exists(
        self,
        provisional_appender,
        temp_plugin_env: "TempPluginEnvironment",
        sample_finalized_digest: "Dict[str, Any]",
    ) -> None:
        """
        Provisionalは空だがRegularが複数存在する場合、
        最大番号+1でProvisionalを作成
        """
        # Arrange: M0005, M0010のRegularDigestを作成（連番でない）
        monthly_dir = temp_plugin_env.digests_path / "2_Monthly"
        monthly_dir.mkdir(parents=True, exist_ok=True)
        (monthly_dir / "M0005_古い.txt").write_text("{}", encoding="utf-8")
        (monthly_dir / "M0010_新しい.txt").write_text("{}", encoding="utf-8")

        # Act
        provisional_appender.append_to_next_provisional("weekly", sample_finalized_digest)

        # Assert: M0011_Individual.txt（最大M0010の次）
        provisional_dir = monthly_dir / "Provisional"
        provisional_files = list(provisional_dir.glob("M*_Individual.txt"))
        assert len(provisional_files) == 1
        assert "M0011" in provisional_files[0].name, (
            f"Expected M0011 but got {provisional_files[0].name}"
        )

    @pytest.mark.integration
    def test_uses_0001_when_no_regular_and_no_provisional(
        self,
        provisional_appender,
        temp_plugin_env: "TempPluginEnvironment",
        sample_finalized_digest: "Dict[str, Any]",
    ) -> None:
        """
        RegularDigestもProvisionalも存在しない場合、
        M0001_Individual.txtで作成される（正しい動作）
        """
        # Arrange: 何もない状態（temp_plugin_envがクリーンな状態を提供）
        monthly_dir = temp_plugin_env.digests_path / "2_Monthly"
        # ディレクトリ自体も存在しない状態を確認
        if monthly_dir.exists():
            import shutil
            shutil.rmtree(monthly_dir)

        # Act
        provisional_appender.append_to_next_provisional("weekly", sample_finalized_digest)

        # Assert: M0001_Individual.txt
        monthly_dir = temp_plugin_env.digests_path / "2_Monthly"
        provisional_dir = monthly_dir / "Provisional"
        provisional_files = list(provisional_dir.glob("M*_Individual.txt"))
        assert len(provisional_files) == 1
        assert "M0001" in provisional_files[0].name, (
            f"Expected M0001 but got {provisional_files[0].name}"
        )
