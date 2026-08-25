#!/usr/bin/env python3
"""
domain/auto_dream/defrag_types.py のユニットテスト
================================================

Defrag 型定義の構造検証（dream-defrag = 引く dream の決定論的「事実」型）。
判断ロジックは持たず、Claude が後で埋める候補の器であることを確認する。
"""

import pytest

from domain.auto_dream.defrag_types import (
    DEFRAG_THRESHOLD,
    VALID_DEFRAG_KINDS,
    DefragCandidate,
    DefragScanResult,
)

# =============================================================================
# DEFRAG_THRESHOLD テスト
# =============================================================================


class TestDefragThreshold:
    """DEFRAG_THRESHOLD 定数の検証"""

    @pytest.mark.unit
    def test_DEFRAG_THRESHOLDが50(self) -> None:
        """commands/digest.md Step 11 が名指した変曲点 = 50"""
        assert DEFRAG_THRESHOLD == 50


# =============================================================================
# DefragKind テスト
# =============================================================================


class TestDefragKind:
    """DefragKind Literal 型の検証"""

    @pytest.mark.unit
    def test_kindは3種(self) -> None:
        """dedup, upper_dry, graduate の3種別"""
        assert {"dedup", "upper_dry", "graduate"} == VALID_DEFRAG_KINDS

    @pytest.mark.unit
    def test_VALID_DEFRAG_KINDSはset(self) -> None:
        """検証用セットが set であること（VALID_MEMORY_TYPES と同型）"""
        assert isinstance(VALID_DEFRAG_KINDS, set)


# =============================================================================
# DefragCandidate テスト
# =============================================================================


class TestDefragCandidate:
    """DefragCandidate TypedDict の検証"""

    @pytest.mark.unit
    def test_必須フィールドで構築可能(self) -> None:
        """kind, targets, reason の3フィールドで構築"""
        c: DefragCandidate = {
            "kind": "dedup",
            "targets": [
                "project_telegram_secretary.md",
                "project_secretary_plugin_port.md",
            ],
            "reason": "TelegramSecretary 関連の重複エントリ",
        }
        assert c["kind"] == "dedup"
        assert len(c["targets"]) == 2

    @pytest.mark.unit
    def test_3種のkindで構築可能(self) -> None:
        """dedup / upper_dry / graduate いずれの kind でも構築できる"""
        for kind in VALID_DEFRAG_KINDS:
            c: DefragCandidate = {
                "kind": kind,  # type: ignore[typeddict-item]
                "targets": [],
                "reason": "r",
            }
            assert c["kind"] in VALID_DEFRAG_KINDS


# =============================================================================
# DefragScanResult テスト
# =============================================================================


class TestDefragScanResult:
    """DefragScanResult TypedDict の検証"""

    @pytest.mark.unit
    def test_必須キーで構築可能(self) -> None:
        """status / memory_dir / file_count / over_threshold / threshold / error"""
        result: DefragScanResult = {
            "status": "ok",
            "memory_dir": "/home/.claude/projects/X/memory",
            "file_count": 57,
            "over_threshold": True,
            "threshold": 50,
            "error": None,
        }
        assert result["status"] == "ok"
        assert result["over_threshold"] is True
        assert result["file_count"] == 57

    @pytest.mark.unit
    def test_no_memory状態で構築可能(self) -> None:
        """status="no_memory" の自動スキップ経路"""
        result: DefragScanResult = {
            "status": "no_memory",
            "memory_dir": None,
            "file_count": 0,
            "over_threshold": False,
            "threshold": 50,
            "error": None,
        }
        assert result["status"] == "no_memory"
        assert result["memory_dir"] is None
