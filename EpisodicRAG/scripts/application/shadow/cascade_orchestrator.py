#!/usr/bin/env python3
"""
CascadeOrchestrator - Orchestrator Pattern for Cascade Workflow
================================================================

ダイジェスト確定時のカスケード処理ワークフローをオーケストレートする。

## 使用デザインパターン

### Orchestrator Pattern
複数のステップからなるワークフローを制御し、
各ステップの実行結果を集約して返す。

### Chain of Responsibility
レベル間の連鎖的な処理を管理。

## SOLID原則の実践

### SRP (Single Responsibility Principle)
- CascadeOrchestrator: ワークフロー制御のみ
- CascadeProcessor: データ操作のみ

### OCP (Open/Closed Principle)
- 新しいステップを追加しても既存コードに影響なし
- ステップの順序変更も容易

Usage:
    from application.shadow.cascade_orchestrator import CascadeOrchestrator

    orchestrator = CascadeOrchestrator(
        cascade_processor=processor,
        file_detector=detector,
        file_appender=appender,
        level_hierarchy=hierarchy
    )

    result = orchestrator.execute_cascade("weekly")
    if result.success:
        for step in result.steps:
            print(f"{step.step_name}: {step.status}")
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from domain.types import LevelHierarchyEntry
from infrastructure import get_structured_logger

if TYPE_CHECKING:
    from .cascade_processor import CascadeProcessor
    from .file_appender import FileAppender
    from .file_detector import FileDetector

__all__ = ["CascadeOrchestrator", "CascadeResult", "CascadeStepResult", "CascadeStepStatus"]

# 構造化ロガー
_logger = get_structured_logger(__name__)


class CascadeStepStatus(Enum):
    """カスケードステップの実行状態"""

    SUCCESS = "success"
    SKIPPED = "skipped"
    NO_DATA = "no_data"
    ERROR = "error"


@dataclass
class CascadeStepResult:
    """カスケードステップの実行結果"""

    step_name: str
    status: CascadeStepStatus
    message: str
    files_processed: int = 0
    details: Dict = field(default_factory=dict)


@dataclass
class CascadeResult:
    """カスケード処理全体の結果"""

    level: str
    steps: List[CascadeStepResult]
    success: bool
    next_level: Optional[str] = None

    @property
    def total_files_processed(self) -> int:
        """処理されたファイルの合計数"""
        return sum(step.files_processed for step in self.steps)

    @property
    def step_summary(self) -> Dict[str, CascadeStepStatus]:
        """ステップ名とステータスのマッピング"""
        return {step.step_name: step.status for step in self.steps}


class CascadeOrchestrator:
    """
    カスケード処理ワークフローのオーケストレーター

    ダイジェスト確定時の4ステップ処理を制御し、
    各ステップの結果を集約して返す。

    ワークフロー:
    1. promote: Shadow → Grand 昇格確認
    2. detect: 次レベルの新規ファイル検出
    3. add: 次レベルのShadowにファイル追加
    4. clear: 現在レベルのShadowをクリア

    Attributes:
        cascade_processor: データ操作を担当するCascadeProcessor
        file_detector: 新規ファイル検出
        file_appender: ファイル追加処理
        level_hierarchy: レベル間の階層関係

    Example:
        result = orchestrator.execute_cascade("weekly")
        print(f"Success: {result.success}")
        print(f"Files processed: {result.total_files_processed}")
    """

    def __init__(
        self,
        cascade_processor: "CascadeProcessor",
        file_detector: "FileDetector",
        file_appender: "FileAppender",
        level_hierarchy: Dict[str, LevelHierarchyEntry],
    ):
        """
        初期化

        Args:
            cascade_processor: CascadeProcessor インスタンス
            file_detector: FileDetector インスタンス
            file_appender: FileAppender インスタンス
            level_hierarchy: レベル階層情報
        """
        self.cascade_processor = cascade_processor
        self.file_detector = file_detector
        self.file_appender = file_appender
        self.level_hierarchy = level_hierarchy

    def execute_cascade(self, level: str) -> CascadeResult:
        """
        カスケード処理を実行

        4ステップのワークフローを順次実行し、結果を集約。

        Args:
            level: 起点となるレベル名

        Returns:
            CascadeResult: 全ステップの結果を含む
        """
        _logger.info(f"[Orchestrator] Starting cascade for level: {level}")

        steps: List[CascadeStepResult] = []
        success = True
        next_level = self.level_hierarchy[level]["next"]

        # Step 1: Promote (Shadow → Grand 確認)
        promote_result = self._step_promote(level)
        steps.append(promote_result)

        # Step 2: Detect (次レベルの新規ファイル検出)
        new_files: List[Path] = []
        if next_level:
            detect_result, new_files = self._step_detect(next_level)
            steps.append(detect_result)
        else:
            steps.append(
                CascadeStepResult(
                    step_name="detect",
                    status=CascadeStepStatus.SKIPPED,
                    message=f"No next level for {level} (top level)",
                )
            )

        # Step 3: Add (次レベルのShadowにファイル追加)
        if next_level and new_files:
            add_result = self._step_add(next_level, new_files)
            steps.append(add_result)
        else:
            steps.append(
                CascadeStepResult(
                    step_name="add",
                    status=CascadeStepStatus.SKIPPED,
                    message="No files to add" if next_level else "No next level",
                )
            )

        # Step 4: Clear (現在レベルのShadowをクリア)
        clear_result = self._step_clear(level)
        steps.append(clear_result)

        # 結果集約
        result = CascadeResult(
            level=level,
            steps=steps,
            success=success,
            next_level=next_level,
        )

        _logger.info(
            f"[Orchestrator] Cascade completed for level: {level}, "
            f"files processed: {result.total_files_processed}"
        )

        return result

    def _step_promote(self, level: str) -> CascadeStepResult:
        """
        Step 1: Shadow → Grand 昇格確認

        Note: 実際の昇格処理はfinalize_from_shadow.pyで実行される。
        ここでは確認のみ。
        """
        _logger.info(f"[Step 1/4] Checking shadow promotion for: {level}")

        digest = self.cascade_processor.get_shadow_digest_for_level(level)

        if not digest:
            return CascadeStepResult(
                step_name="promote",
                status=CascadeStepStatus.NO_DATA,
                message=f"No shadow digest to promote for level: {level}",
            )

        file_count = len(digest.get("source_files", []))
        return CascadeStepResult(
            step_name="promote",
            status=CascadeStepStatus.SUCCESS,
            message=f"Shadow digest ready for promotion: {file_count} file(s)",
            files_processed=file_count,
            details={"source_files_count": file_count},
        )

    def _step_detect(self, next_level: str) -> tuple[CascadeStepResult, List[Path]]:
        """
        Step 2: 次レベルの新規ファイル検出

        Returns:
            Tuple of (step result, list of new files)
        """
        _logger.info(f"[Step 2/4] Detecting new files for: {next_level}")

        new_files = self.file_detector.find_new_files(next_level)

        if not new_files:
            result = CascadeStepResult(
                step_name="detect",
                status=CascadeStepStatus.NO_DATA,
                message=f"No new files found for level: {next_level}",
            )
            return result, []

        file_names = [f.name for f in new_files[:5]]
        suffix = "..." if len(new_files) > 5 else ""

        result = CascadeStepResult(
            step_name="detect",
            status=CascadeStepStatus.SUCCESS,
            message=f"Found {len(new_files)} new file(s) for {next_level}",
            files_processed=len(new_files),
            details={
                "new_files_count": len(new_files),
                "sample_files": f"{file_names}{suffix}",
            },
        )
        return result, new_files

    def _step_add(self, next_level: str, new_files: List[Path]) -> CascadeStepResult:
        """
        Step 3: 次レベルのShadowにファイル追加
        """
        _logger.info(f"[Step 3/4] Adding {len(new_files)} file(s) to shadow: {next_level}")

        self.file_appender.add_files_to_shadow(next_level, new_files)

        return CascadeStepResult(
            step_name="add",
            status=CascadeStepStatus.SUCCESS,
            message=f"Added {len(new_files)} file(s) to shadow for {next_level}",
            files_processed=len(new_files),
            details={"added_count": len(new_files)},
        )

    def _step_clear(self, level: str) -> CascadeStepResult:
        """
        Step 4: 現在レベルのShadowをクリア
        """
        _logger.info(f"[Step 4/4] Clearing shadow for: {level}")

        self.cascade_processor.clear_shadow_level(level)

        return CascadeStepResult(
            step_name="clear",
            status=CascadeStepStatus.SUCCESS,
            message=f"Cleared shadow for level: {level}",
        )
