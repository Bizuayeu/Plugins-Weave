#!/usr/bin/env python3
"""
Property-Based Tests for Shadow I/O
====================================

Using hypothesis to test invariants in application/shadow/shadow_io.py

Note:
    Due to Hypothesis limitation with pytest fixtures, we use
    tempfile.TemporaryDirectory() inside tests instead of tmp_path fixture.
"""

import tempfile
import time
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from application.shadow.shadow_io import ShadowIO
from application.shadow.template import ShadowTemplate
from domain.constants import LEVEL_NAMES

# =============================================================================
# Strategies for generating test data
# =============================================================================

# Source file names
source_file_names = st.lists(
    st.text(
        alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
        min_size=5,
        max_size=20,
    ).map(lambda s: f"L{s}.txt"),
    min_size=0,
    max_size=10,
    unique=True,
)


# =============================================================================
# ShadowIO Load/Save Roundtrip Properties
# =============================================================================


class TestShadowIORoundtripProperties:
    """Property-based tests for load/save roundtrip"""

    @pytest.mark.property
    @given(source_files=source_file_names)
    @settings(max_examples=50, deadline=None)
    def test_save_load_roundtrip_preserves_source_files(self, source_files) -> None:
        """save→loadでsource_filesが保持される"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            template = ShadowTemplate(LEVEL_NAMES)
            shadow_file = tmp_path / "ShadowGrandDigest.txt"
            io = ShadowIO(shadow_file, template.get_template)

            # 初回作成
            data1 = io.load_or_create()

            # source_files設定
            data1["latest_digests"]["weekly"]["overall_digest"]["source_files"] = source_files
            io.save(data1)

            # 再読み込み
            data2 = io.load_or_create()
            loaded_files = data2["latest_digests"]["weekly"]["overall_digest"]["source_files"]

            assert loaded_files == source_files

    @pytest.mark.property
    @given(
        abstract_text=st.text(min_size=1, max_size=500),
        impression_text=st.text(min_size=1, max_size=200),
    )
    @settings(max_examples=50, deadline=None)
    def test_save_load_roundtrip_preserves_text_fields(
        self, abstract_text, impression_text
    ) -> None:
        """save→loadでテキストフィールドが保持される"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            template = ShadowTemplate(LEVEL_NAMES)
            shadow_file = tmp_path / "ShadowGrandDigest.txt"
            io = ShadowIO(shadow_file, template.get_template)

            # 初回作成
            data1 = io.load_or_create()

            # テキストフィールド設定
            data1["latest_digests"]["weekly"]["overall_digest"]["abstract"] = abstract_text
            data1["latest_digests"]["weekly"]["overall_digest"]["impression"] = impression_text
            io.save(data1)

            # 再読み込み
            data2 = io.load_or_create()
            loaded_abstract = data2["latest_digests"]["weekly"]["overall_digest"]["abstract"]
            loaded_impression = data2["latest_digests"]["weekly"]["overall_digest"]["impression"]

            assert loaded_abstract == abstract_text
            assert loaded_impression == impression_text

    @pytest.mark.property
    @given(level=st.sampled_from(LEVEL_NAMES))
    @settings(max_examples=len(LEVEL_NAMES), deadline=None)
    def test_each_level_can_be_updated(self, level) -> None:
        """各レベルを個別に更新できる"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            template = ShadowTemplate(LEVEL_NAMES)
            shadow_file = tmp_path / "ShadowGrandDigest.txt"
            io = ShadowIO(shadow_file, template.get_template)

            # 初回作成
            data1 = io.load_or_create()

            # 指定レベルを更新
            test_files = [f"test_file_for_{level}.txt"]
            data1["latest_digests"][level]["overall_digest"]["source_files"] = test_files
            io.save(data1)

            # 再読み込み
            data2 = io.load_or_create()
            loaded_files = data2["latest_digests"][level]["overall_digest"]["source_files"]

            assert loaded_files == test_files


# =============================================================================
# ShadowIO Timestamp Properties
# =============================================================================


class TestShadowIOTimestampProperties:
    """Property-based tests for timestamp handling"""

    @pytest.mark.property
    def test_save_updates_timestamp(self) -> None:
        """saveでlast_updatedが更新される"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            template = ShadowTemplate(LEVEL_NAMES)
            shadow_file = tmp_path / "ShadowGrandDigest.txt"
            io = ShadowIO(shadow_file, template.get_template)

            # 初回作成
            data1 = io.load_or_create()
            old_timestamp = data1["metadata"]["last_updated"]

            # 確実に時刻差を出す
            time.sleep(0.02)

            # 再保存
            io.save(data1)

            # 再読み込み
            data2 = io.load_or_create()
            new_timestamp = data2["metadata"]["last_updated"]

            assert new_timestamp != old_timestamp

    @pytest.mark.property
    def test_multiple_saves_increment_timestamp(self) -> None:
        """複数回のsaveでタイムスタンプが順次更新される"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            template = ShadowTemplate(LEVEL_NAMES)
            shadow_file = tmp_path / "ShadowGrandDigest.txt"
            io = ShadowIO(shadow_file, template.get_template)

            timestamps = []
            data = io.load_or_create()

            for _ in range(3):
                time.sleep(0.02)
                io.save(data)
                data = io.load_or_create()
                timestamps.append(data["metadata"]["last_updated"])

            # タイムスタンプは全て異なる
            assert len(set(timestamps)) == 3


# =============================================================================
# ShadowIO Creation Properties
# =============================================================================


class TestShadowIOCreationProperties:
    """Property-based tests for file creation"""

    @pytest.mark.property
    def test_load_or_create_creates_file_if_missing(self) -> None:
        """ファイルがなければ作成する"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            template = ShadowTemplate(LEVEL_NAMES)
            shadow_file = tmp_path / "new_shadow.txt"
            io = ShadowIO(shadow_file, template.get_template)

            assert not shadow_file.exists()

            data = io.load_or_create()

            assert shadow_file.exists()
            assert "metadata" in data
            assert "latest_digests" in data

    @pytest.mark.property
    def test_load_or_create_preserves_existing_file(self) -> None:
        """既存ファイルの内容を保持する"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            template = ShadowTemplate(LEVEL_NAMES)
            shadow_file = tmp_path / "existing_shadow.txt"
            io = ShadowIO(shadow_file, template.get_template)

            # 初回作成と変更
            data1 = io.load_or_create()
            data1["latest_digests"]["weekly"]["overall_digest"]["source_files"] = ["existing.txt"]
            io.save(data1)

            # 新しいIOインスタンスで読み込み
            io2 = ShadowIO(shadow_file, template.get_template)
            data2 = io2.load_or_create()

            assert data2["latest_digests"]["weekly"]["overall_digest"]["source_files"] == [
                "existing.txt"
            ]


# =============================================================================
# ShadowIO Structure Invariants
# =============================================================================


class TestShadowIOStructureInvariants:
    """Property-based tests for structural invariants"""

    @pytest.mark.property
    def test_all_levels_present_after_load(self) -> None:
        """load後に全レベルが存在する"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            template = ShadowTemplate(LEVEL_NAMES)
            shadow_file = tmp_path / "ShadowGrandDigest.txt"
            io = ShadowIO(shadow_file, template.get_template)

            data = io.load_or_create()

            for level in LEVEL_NAMES:
                assert level in data["latest_digests"]
                assert "overall_digest" in data["latest_digests"][level]

    @pytest.mark.property
    def test_metadata_always_present(self) -> None:
        """metadataセクションが常に存在する"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            template = ShadowTemplate(LEVEL_NAMES)
            shadow_file = tmp_path / "ShadowGrandDigest.txt"
            io = ShadowIO(shadow_file, template.get_template)

            data = io.load_or_create()

            assert "metadata" in data
            assert "last_updated" in data["metadata"]
            assert "version" in data["metadata"]
