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
    result.success  # True if all steps succeeded
    result.steps    # List[CascadeStepResult] with step_name and status
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

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
    details: Dict[str, Any] = field(default_factory=dict)
    # details の内容（ステップ別）:
    #   promote: {"source_files_count": int}
    #   detect:  {"new_files_count": int, "sample_files": str}
    #   add:     {"added_count": int}
    #   clear:   {}


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
        result.success  # True if cascade completed successfully
        result.total_files_processed  # Total number of files processed
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

        Example:
            >>> result = orchestrator.execute_cascade("weekly")
            >>> result.success
            True
            >>> len(result.steps)
            4
        """
        _logger.info(f"[Orchestrator] カスケード処理を開始: レベル {level}")

        steps: List[CascadeStepResult] = []
        success = True
        next_level = self.level_hierarchy[level]["next"]

        # === 4ステップ制御フロー ===
        # Step 1: promote - 常に実行（Shadow → Grand 確定）
        # Step 2: detect  - next_level 存在時のみ（次階層の新規ファイル検出）
        # Step 3: add     - next_level + 新規ファイル存在時のみ（Shadow追加）
        # Step 4: clear   - 常に実行（現階層 Shadow クリア）

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
                    message=f"{level}に上位レベルなし（最上位）",
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
                    message="追加ファイルなし" if next_level else "上位レベルなし",
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
            f"[Orchestrator] カスケード処理完了: レベル {level}、"
            f"処理ファイル数: {result.total_files_processed}"
        )

        return result

    def _step_promote(self, level: str) -> CascadeStepResult:
        """
        Step 1: Shadow → Grand 昇格確認

        Shadowダイジェストの存在を確認し、昇格準備状態をレポート。
        実際の昇格処理はfinalize_from_shadow.pyで実行される。

        Args:
            level: 確認対象のレベル名

        Returns:
            CascadeStepResult: 昇格準備状態（SUCCESS/NO_DATA）
        """
        _logger.info(f"[Step 1/4] Shadow昇格確認: {level}")
        _logger.state("step_promote", level=level)

        digest = self.cascade_processor.get_shadow_digest_for_level(level)

        if not digest:
            _logger.decision("promote_result", has_digest=False)
            return CascadeStepResult(
                step_name="promote",
                status=CascadeStepStatus.NO_DATA,
                message=f"昇格対象のShadowダイジェストなし: レベル {level}",
            )

        file_count = len(digest.get("source_files", []))
        _logger.decision("promote_result", has_digest=True, file_count=file_count)
        return CascadeStepResult(
            step_name="promote",
            status=CascadeStepStatus.SUCCESS,
            message=f"昇格準備完了: {file_count}ファイル",
            files_processed=file_count,
            details={"source_files_count": file_count},
        )

    def _step_detect(self, next_level: str) -> tuple[CascadeStepResult, List[Path]]:
        """
        Step 2: 次レベルの新規ファイル検出

        上位レベルに追加すべき新規ファイルを検出する。

        Args:
            next_level: 検出対象の上位レベル名

        Returns:
            tuple[CascadeStepResult, List[Path]]:
                ステップ結果と検出された新規ファイルのリスト
        """
        _logger.info(f"[Step 2/4] 新規ファイル検出: {next_level}")
        _logger.state("step_detect", next_level=next_level)

        new_files = self.file_detector.find_new_files(next_level)

        if not new_files:
            _logger.file_op("detect_result", count=0)
            result = CascadeStepResult(
                step_name="detect",
                status=CascadeStepStatus.NO_DATA,
                message=f"新規ファイルなし: レベル {next_level}",
            )
            return result, []

        file_names = [f.name for f in new_files[:5]]
        suffix = "..." if len(new_files) > 5 else ""

        _logger.file_op("detect_result", count=len(new_files))
        result = CascadeStepResult(
            step_name="detect",
            status=CascadeStepStatus.SUCCESS,
            message=f"新規ファイル {len(new_files)}件検出: {next_level}",
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

        検出された新規ファイルを上位レベルのShadowダイジェストに追加する。

        Args:
            next_level: 追加先の上位レベル名
            new_files: 追加するファイルのリスト

        Returns:
            CascadeStepResult: 追加処理の結果
        """
        _logger.info(f"[Step 3/4] Shadowにファイル追加中: {len(new_files)}件 → {next_level}")
        _logger.state("step_add", next_level=next_level, file_count=len(new_files))

        self.file_appender.add_files_to_shadow(next_level, new_files)

        _logger.file_op("add_result", added=len(new_files))
        return CascadeStepResult(
            step_name="add",
            status=CascadeStepStatus.SUCCESS,
            message=f"Shadowにファイル追加完了: {len(new_files)}件 → {next_level}",
            files_processed=len(new_files),
            details={"added_count": len(new_files)},
        )

    def _step_clear(self, level: str) -> CascadeStepResult:
        """
        Step 4: 現在レベルのShadowをクリア

        確定済みレベルのShadowダイジェストを初期化する。

        Args:
            level: クリア対象のレベル名

        Returns:
            CascadeStepResult: クリア処理の結果
        """
        _logger.info(f"[Step 4/4] Shadowクリア: {level}")
        _logger.state("step_clear", level=level)

        self.cascade_processor.clear_shadow_level(level)

        _logger.file_op("clear_result", cleared=True)
        return CascadeStepResult(
            step_name="clear",
            status=CascadeStepStatus.SUCCESS,
            message=f"Shadowクリア完了: レベル {level}",
        )
