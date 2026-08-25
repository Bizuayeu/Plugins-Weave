#!/usr/bin/env python3
"""
Snapshot Writer
===============

dream-defrag（引く dream）の安全要件: 剪定を適用する**前**に memory dir 全体の
スナップショットを作成する。auto-memory は git 非追跡で revert 不能なため、
これが唯一の復元手段。コマンドフローは必ず snapshot 成功後にのみ剪定へ進む。

格納先は走査対象の memory dir の **外**（既定では永続化 dir 配下 snapshots/）。
memory dir 内や兄弟に置くと将来のスキャン対象に紛れる懸念を避けるため。

Usage:
    from infrastructure.auto_dream.snapshot_writer import create_snapshot

    dest = create_snapshot(memory_dir)  # → ~/.claude/plugins/.episodicrag/snapshots/memory.snapshot-<ts>
"""

import shutil
from datetime import datetime, timezone
from pathlib import Path

from infrastructure.config import get_persistent_config_dir


def _utc_timestamp() -> str:
    """UTC タイムスタンプ文字列（例: 20260614T103000123456Z）"""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def default_snapshot_root() -> Path:
    """既定のスナップショット格納先（永続化 dir 配下、走査対象の外）"""
    return get_persistent_config_dir() / "snapshots"


def create_snapshot(
    memory_dir: Path,
    snapshot_root: Path | None = None,
    timestamp: str | None = None,
) -> Path:
    """
    memory dir 全体を timestamp 付きでコピーし、コピー先パスを返す

    Args:
        memory_dir: スナップショット対象（auto-memory ディレクトリ）
        snapshot_root: 格納先ルート（省略時は永続化 dir 配下 snapshots/）
        timestamp: タイムスタンプ文字列（省略時は現在 UTC。テスト用に注入可能）

    Returns:
        作成したスナップショットディレクトリの絶対パス

    Raises:
        FileNotFoundError: memory_dir が存在しない場合
    """
    if not memory_dir.exists():
        raise FileNotFoundError(f"memory_dir not found: {memory_dir}")

    root = snapshot_root if snapshot_root is not None else default_snapshot_root()
    root.mkdir(parents=True, exist_ok=True)

    ts = timestamp if timestamp is not None else _utc_timestamp()

    # 同一 timestamp 衝突時は連番サフィックスで上書きを回避
    dest = root / f"memory.snapshot-{ts}"
    counter = 1
    while dest.exists():
        dest = root / f"memory.snapshot-{ts}-{counter}"
        counter += 1

    shutil.copytree(memory_dir, dest)
    return dest
