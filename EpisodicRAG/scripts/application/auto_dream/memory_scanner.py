#!/usr/bin/env python3
"""
Memory Scanner
==============

auto-memoryディレクトリの発見・読み込み・解析を統合するFacade。

Usage:
    from application.auto_dream.memory_scanner import MemoryScanner

    scanner = MemoryScanner()
    result = scanner.scan()
"""

from typing import List, Optional

from domain.auto_dream.types import AutoDreamScanResult, MemoryFile
from infrastructure.auto_dream.memory_discovery import discover_memory_dirs
from infrastructure.auto_dream.memory_reader import read_memory_file, read_memory_index
from infrastructure.file_scanner import scan_files


class MemoryScanner:
    """
    auto-memoryスキャンのオーケストレータ

    discover → read index → read files → return result
    """

    def __init__(self, project_path: Optional[str] = None) -> None:
        self._project_path = project_path

    def scan(self) -> AutoDreamScanResult:
        """
        auto-memoryをスキャンし構造化された結果を返す

        Returns:
            AutoDreamScanResult:
                status="ok"        — スキャン成功
                status="no_memory" — メモリディレクトリなし
                status="error"     — エラー発生
        """
        try:
            return self._do_scan()
        except Exception as e:
            return AutoDreamScanResult(
                status="error",
                project_path=None,
                memory_dir=None,
                memory_index=None,
                memory_files=[],
                file_count=0,
                error=str(e),
            )

    def _do_scan(self) -> AutoDreamScanResult:
        """スキャン本体"""
        # 1. メモリディレクトリを発見
        dirs = discover_memory_dirs(self._project_path)

        if not dirs:
            return AutoDreamScanResult(
                status="no_memory",
                project_path=None,
                memory_dir=None,
                memory_index=None,
                memory_files=[],
                file_count=0,
                error=None,
            )

        # 最初に見つかったディレクトリを使用
        memory_dir = dirs[0]
        project_name = memory_dir.parent.name

        # 2. MEMORY.md インデックスを読み込み
        index_path = memory_dir / "MEMORY.md"
        memory_index = read_memory_index(index_path)

        # 3. 全.mdファイルをスキャン（MEMORY.md自体は除外）
        md_files = scan_files(memory_dir, pattern="*.md")
        memory_files: List[MemoryFile] = []

        for md_path in md_files:
            if md_path.name == "MEMORY.md":
                continue
            mf = read_memory_file(md_path)
            if mf is not None:
                memory_files.append(mf)

        return AutoDreamScanResult(
            status="ok",
            project_path=project_name,
            memory_dir=str(memory_dir),
            memory_index=memory_index,
            memory_files=memory_files,
            file_count=len(memory_files),
            error=None,
        )
