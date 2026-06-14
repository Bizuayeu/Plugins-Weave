#!/usr/bin/env python3
"""
Defrag Scanner
==============

dream-defrag（引く dream＝memory GC）の件数診断 Facade。

既存 MemoryScanner を再利用してメモリ件数を集計し、DEFRAG_THRESHOLD 超過を
決定論的に判定する読み取り専用オーケストレータ。**判断（何を剪定するか）は
行わない**——それは Claude=LLM がコマンドフロー内で担う。

Usage:
    from application.auto_dream.defrag_scanner import DefragScanner

    scanner = DefragScanner()
    result = scanner.scan()
"""

from typing import Optional

from application.auto_dream.memory_scanner import MemoryScanner
from domain.auto_dream.defrag_types import DEFRAG_THRESHOLD, DefragScanResult


class DefragScanner:
    """
    メモリ件数診断のオーケストレータ

    MemoryScanner（足す dream の所在スキャン）を内部利用して件数を読み、
    threshold 超過のみを返す。剪定候補の検出はしない。
    """

    def __init__(self, project_path: Optional[str] = None) -> None:
        self._project_path = project_path

    def scan(self) -> DefragScanResult:
        """
        メモリ件数を集計し threshold 超過を判定する

        Returns:
            DefragScanResult:
                status="ok"        — 集計成功
                status="no_memory" — メモリディレクトリなし（自動スキップ用）
                status="error"     — エラー発生
        """
        try:
            return self._do_scan()
        except Exception as e:
            return DefragScanResult(
                status="error",
                memory_dir=None,
                file_count=0,
                over_threshold=False,
                threshold=DEFRAG_THRESHOLD,
                error=str(e),
            )

    def _do_scan(self) -> DefragScanResult:
        """スキャン本体（MemoryScanner に委譲して件数を読む）"""
        inner = MemoryScanner(self._project_path).scan()

        # no_memory / error は件数判定不能 → そのまま伝播
        if inner["status"] != "ok":
            return DefragScanResult(
                status=inner["status"],
                memory_dir=inner["memory_dir"],
                file_count=inner["file_count"],
                over_threshold=False,
                threshold=DEFRAG_THRESHOLD,
                error=inner["error"],
            )

        file_count = inner["file_count"]
        return DefragScanResult(
            status="ok",
            memory_dir=inner["memory_dir"],
            file_count=file_count,
            over_threshold=file_count > DEFRAG_THRESHOLD,
            threshold=DEFRAG_THRESHOLD,
            error=None,
        )
