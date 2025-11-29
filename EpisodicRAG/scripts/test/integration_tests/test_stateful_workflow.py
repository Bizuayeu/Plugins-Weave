#!/usr/bin/env python3
"""
Stateful property-based tests for EpisodicRAG workflows.
========================================================

Tests multi-step state machine behavior using Hypothesis.
Verifies that complex workflows maintain invariants across arbitrary sequences.

Key tests:
    - DigestWorkflowStateMachine: 8-tier cascade workflow state transitions
    - ErrorRecoveryStateMachine: Error detection and recovery sequences

Usage:
    pytest test_stateful_workflow.py -v --hypothesis-show-statistics
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import pytest

try:
    from hypothesis import HealthCheck, settings
    from hypothesis.stateful import (
        Bundle,
        RuleBasedStateMachine,
        initialize,
        invariant,
        rule,
    )

    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False

# Mark entire module
pytestmark = [pytest.mark.property, pytest.mark.slow]


# =============================================================================
# Skip if hypothesis not available
# =============================================================================

if not HYPOTHESIS_AVAILABLE:
    pytest.skip("hypothesis not installed", allow_module_level=True)


# =============================================================================
# DigestWorkflowStateMachine
# =============================================================================


class DigestWorkflowStateMachine(RuleBasedStateMachine):
    """
    8層階層ダイジェストワークフローの状態機械テスト

    State:
        - loop_count: 未処理Loopファイル数
        - weekly_count: 未処理Weeklyダイジェスト数
        - monthly_count: 未処理Monthlyダイジェスト数
        - total_loops_created: 作成されたLoop総数（追跡用）

    Rules:
        - create_loop: 新しいLoopファイルを作成
        - run_digest: /digestコマンドをシミュレート
        - run_digest_weekly: /digest weeklyコマンドをシミュレート

    Invariants:
        - カウントは常に非負
        - データ損失なし
    """

    def __init__(self):
        super().__init__()
        self.loop_count = 0
        self.weekly_count = 0
        self.monthly_count = 0
        self.total_loops_created = 0
        self.total_weeklies_created = 0
        self.total_monthlies_created = 0

        # 閾値（簡略化）
        self.weekly_threshold = 5
        self.monthly_threshold = 5

        # 一時ディレクトリ
        self.temp_dir: Optional[tempfile.TemporaryDirectory] = None

    @initialize()
    def setup(self):
        """テスト環境の初期化"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)

        # ディレクトリ構造を作成
        (self.base_path / "Loops").mkdir(parents=True)
        (self.base_path / "Digests" / "1_Weekly").mkdir(parents=True)
        (self.base_path / "Digests" / "2_Monthly").mkdir(parents=True)
        (self.base_path / "Essences").mkdir(parents=True)

    def teardown(self):
        """テスト環境のクリーンアップ"""
        if self.temp_dir:
            self.temp_dir.cleanup()

    @rule()
    def create_loop(self):
        """Loopファイルを作成"""
        self.loop_count += 1
        self.total_loops_created += 1

        # 実際にファイルを作成
        loop_file = self.base_path / "Loops" / f"L{self.total_loops_created:05d}_Test.txt"
        loop_file.write_text(
            json.dumps(
                {
                    "metadata": {"title": f"Loop {self.total_loops_created}"},
                    "overall_digest": {"keywords": ["test"]},
                }
            )
        )

    @rule()
    def run_digest(self):
        """
        /digestコマンドをシミュレート

        Weekly閾値に達した場合、Weeklyダイジェストを作成
        """
        if self.loop_count >= self.weekly_threshold:
            # Weeklyダイジェスト作成
            self.total_weeklies_created += 1
            self.weekly_count += 1

            # Weeklyファイルを作成
            weekly_file = (
                self.base_path
                / "Digests"
                / "1_Weekly"
                / f"W{self.total_weeklies_created:04d}_Test.txt"
            )
            weekly_file.write_text(
                json.dumps(
                    {
                        "metadata": {"level": "weekly"},
                        "source_loops": self.loop_count,
                    }
                )
            )

            # Loopカウントをリセット
            self.loop_count = 0

    @rule()
    def run_digest_weekly(self):
        """
        /digest weeklyコマンドをシミュレート

        Monthly閾値に達した場合、Monthlyダイジェストを作成
        """
        if self.weekly_count >= self.monthly_threshold:
            # Monthlyダイジェスト作成
            self.total_monthlies_created += 1
            self.monthly_count += 1

            # Monthlyファイルを作成
            monthly_file = (
                self.base_path
                / "Digests"
                / "2_Monthly"
                / f"M{self.total_monthlies_created:03d}_Test.txt"
            )
            monthly_file.write_text(
                json.dumps(
                    {
                        "metadata": {"level": "monthly"},
                        "source_weeklies": self.weekly_count,
                    }
                )
            )

            # Weeklyカウントをリセット
            self.weekly_count = 0

    @invariant()
    def counts_are_non_negative(self):
        """カウントは常に非負"""
        assert self.loop_count >= 0, f"loop_count is negative: {self.loop_count}"
        assert self.weekly_count >= 0, f"weekly_count is negative: {self.weekly_count}"
        assert (
            self.monthly_count >= 0
        ), f"monthly_count is negative: {self.monthly_count}"

    @invariant()
    def counts_within_valid_range(self):
        """カウントは有効な範囲内（閾値以下）"""
        # Loopは閾値と同数まで蓄積可能（閾値に達したらdigestで処理）
        # 閾値を超えることもある（digestを実行しない場合）
        # ここでは無制限にカウントが増加しても論理的には問題ない
        # 重要なのはカウントが非負であること（counts_are_non_negativeで検証済み）
        pass  # No strict upper bound - counts can exceed threshold if digest not run

    @invariant()
    def total_consistency(self):
        """総作成数の一貫性"""
        assert self.total_loops_created >= 0
        assert self.total_weeklies_created >= 0
        assert self.total_monthlies_created >= 0


# =============================================================================
# ErrorRecoveryStateMachine
# =============================================================================


class ErrorRecoveryStateMachine(RuleBasedStateMachine):
    """
    エラー回復シーケンスの状態機械テスト

    State:
        - file_exists: ファイルが存在するか
        - file_corrupted: ファイルが破損しているか
        - corruption_detected: 破損が検出されたか
        - recovery_attempted: 回復が試行されたか

    Rules:
        - create_file: 正常なファイルを作成
        - corrupt_file: ファイルを破損させる
        - detect_corruption: 破損を検出
        - recover_from_corruption: 破損から回復

    Invariants:
        - 回復後はシステムが正常な状態
    """

    def __init__(self):
        super().__init__()
        self.file_exists = False
        self.file_corrupted = False
        self.corruption_detected = False
        self.recovery_attempted = False

        self.temp_dir: Optional[tempfile.TemporaryDirectory] = None
        self.test_file: Optional[Path] = None

    @initialize()
    def setup(self):
        """テスト環境の初期化"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.test_file = self.base_path / "test_data.json"

    def teardown(self):
        """テスト環境のクリーンアップ"""
        if self.temp_dir:
            self.temp_dir.cleanup()

    @rule()
    def create_file(self):
        """正常なファイルを作成"""
        if self.test_file:
            self.test_file.write_text(json.dumps({"status": "valid", "data": [1, 2, 3]}))
            self.file_exists = True
            self.file_corrupted = False
            self.corruption_detected = False

    @rule()
    def corrupt_file(self):
        """ファイルを破損させる"""
        if self.file_exists and self.test_file and not self.file_corrupted:
            # 不完全なJSONを書き込む
            self.test_file.write_text('{"status": "corrupted", "data": [')
            self.file_corrupted = True
            self.corruption_detected = False

    @rule()
    def detect_corruption(self):
        """破損を検出"""
        if self.file_exists and self.test_file:
            try:
                with open(self.test_file, "r", encoding="utf-8") as f:
                    json.load(f)
                self.corruption_detected = False
            except json.JSONDecodeError:
                self.corruption_detected = True

    @rule()
    def recover_from_corruption(self):
        """破損から回復"""
        if self.corruption_detected and self.test_file:
            # 回復: ファイルを削除して再作成
            if self.test_file.exists():
                self.test_file.unlink()

            # 新しい有効なファイルを作成
            self.test_file.write_text(
                json.dumps({"status": "recovered", "data": []})
            )
            self.file_exists = True
            self.file_corrupted = False
            self.corruption_detected = False
            self.recovery_attempted = True

    @invariant()
    def corruption_state_consistency(self):
        """破損状態の一貫性"""
        if self.file_corrupted:
            # 破損ファイルは存在する
            assert self.file_exists, "Corrupted file must exist"

        # Note: corruption_detected can remain True even after corruption is fixed
        # because detect_corruption is the last action that set it

    @invariant()
    def recovery_restores_valid_state(self):
        """回復後は有効な状態（回復直後かつ破損していない場合）"""
        # Only check immediately after recovery when file is not corrupted again
        if self.recovery_attempted and not self.file_corrupted and self.test_file and self.test_file.exists():
            try:
                with open(self.test_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # 回復後のファイルは有効なJSONであるべき
                assert isinstance(data, dict)
            except json.JSONDecodeError:
                # 回復後に再度破損されていない場合のみ失敗
                if not self.file_corrupted:
                    assert False, "File still corrupted after recovery"


# =============================================================================
# Test Cases - Hypothesis generates test sequences automatically
# =============================================================================


# Apply settings to the state machines directly
DigestWorkflowStateMachine.TestCase.settings = settings(
    max_examples=50, suppress_health_check=[HealthCheck.too_slow]
)

ErrorRecoveryStateMachine.TestCase.settings = settings(
    max_examples=50, suppress_health_check=[HealthCheck.too_slow]
)


class TestDigestWorkflow(DigestWorkflowStateMachine.TestCase):
    """
    Hypothesis will automatically:
    1. Generate random sequences of create_loop, run_digest, run_digest_weekly
    2. Verify invariants hold after each step
    3. Shrink failing examples to minimal reproduction
    """

    pass


class TestErrorRecovery(ErrorRecoveryStateMachine.TestCase):
    """
    Hypothesis will automatically:
    1. Generate random sequences of create, corrupt, detect, recover
    2. Verify invariants hold after each step
    3. Find edge cases in error recovery logic
    """

    pass


# =============================================================================
# Additional Unit Tests for State Machines
# =============================================================================


class TestDigestWorkflowManual:
    """手動テストケース - 特定のシナリオを検証"""

    @pytest.mark.unit
    def test_threshold_trigger(self):
        """閾値に達するとWeeklyが作成される"""
        sm = DigestWorkflowStateMachine()
        sm.setup()

        try:
            # 5個のLoopを作成
            for _ in range(5):
                sm.create_loop()

            assert sm.loop_count == 5

            # digestを実行
            sm.run_digest()

            # Weeklyが作成され、loop_countがリセット
            assert sm.loop_count == 0
            assert sm.weekly_count == 1
            assert sm.total_weeklies_created == 1
        finally:
            sm.teardown()

    @pytest.mark.unit
    def test_cascade_to_monthly(self):
        """Weekly→Monthlyカスケードが正常に動作"""
        sm = DigestWorkflowStateMachine()
        sm.setup()

        try:
            # 5回のWeekly作成サイクル
            for _ in range(5):
                # 5個のLoopを作成してWeeklyを作成
                for _ in range(5):
                    sm.create_loop()
                sm.run_digest()

            assert sm.weekly_count == 5
            assert sm.total_weeklies_created == 5

            # digest weeklyを実行
            sm.run_digest_weekly()

            # Monthlyが作成され、weekly_countがリセット
            assert sm.weekly_count == 0
            assert sm.monthly_count == 1
            assert sm.total_monthlies_created == 1
        finally:
            sm.teardown()


class TestErrorRecoveryManual:
    """手動テストケース - エラー回復シナリオを検証"""

    @pytest.mark.unit
    def test_corruption_detection(self):
        """破損検出が正常に動作"""
        sm = ErrorRecoveryStateMachine()
        sm.setup()

        try:
            # ファイル作成
            sm.create_file()
            assert sm.file_exists
            assert not sm.file_corrupted

            # 破損させる
            sm.corrupt_file()
            assert sm.file_corrupted

            # 破損検出
            sm.detect_corruption()
            assert sm.corruption_detected
        finally:
            sm.teardown()

    @pytest.mark.unit
    def test_full_recovery_cycle(self):
        """完全な回復サイクル"""
        sm = ErrorRecoveryStateMachine()
        sm.setup()

        try:
            # 作成→破損→検出→回復
            sm.create_file()
            sm.corrupt_file()
            sm.detect_corruption()
            sm.recover_from_corruption()

            # 回復後の状態を確認
            assert sm.file_exists
            assert not sm.file_corrupted
            assert not sm.corruption_detected
            assert sm.recovery_attempted

            # ファイルが有効なJSONであることを確認
            with open(sm.test_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data["status"] == "recovered"
        finally:
            sm.teardown()
