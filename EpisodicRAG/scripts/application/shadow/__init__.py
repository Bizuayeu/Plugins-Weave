"""
Shadow Package - ShadowGrandDigest management components
=========================================================

ShadowGrandDigestの管理コンポーネント群

Components:
    - ShadowTemplate: テンプレート生成
    - FileDetector: 新規ファイル検出
    - ShadowIO: Shadow I/O処理
    - ShadowUpdater: Shadow更新・カスケード処理
    - CascadeProcessor: カスケードデータ操作
    - CascadeOrchestrator: カスケードワークフロー制御
    - CascadeComponents: カスケード処理用パラメータオブジェクト
"""

from .cascade_orchestrator import (
    CascadeOrchestrator,
    CascadeResult,
    CascadeStepResult,
    CascadeStepStatus,
)
from .cascade_processor import CascadeProcessor
from .components import CascadeComponents
from .file_detector import FileDetector
from .provisional_appender import ProvisionalAppender
from .shadow_io import ShadowIO
from .shadow_updater import ShadowUpdater
from .template import ShadowTemplate

__all__ = [
    "ShadowTemplate",
    "FileDetector",
    "ShadowIO",
    "ShadowUpdater",
    "CascadeProcessor",
    "CascadeOrchestrator",
    "CascadeResult",
    "CascadeStepResult",
    "CascadeStepStatus",
    "CascadeComponents",
    "ProvisionalAppender",
]
