"""保持期限超過の media を削除する Infrastructure ユーティリティ（Stage 6.4）。

watch ループの cleanup hook（N サイクルに 1 回呼ぶ）と、単独実行 (CLI 起動) の
両方を意図した、純粋関数寄りの薄いラッパー。
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional


def cleanup_media_dir(
    target_dir: Path,
    retention_seconds: int,
    now: Optional[float] = None,
) -> int:
    """target_dir 内の mtime が retention_seconds 超過のファイルを削除。

    - target_dir が存在しなければ 0 を返す（no-op）
    - サブディレクトリは無視（フラット保存前提）
    - 削除に失敗したファイルはスキップして進む（best-effort、OSError は飲む）

    Args:
        target_dir: 検査対象ディレクトリ（通常 state_dir/media/）
        retention_seconds: 保持期限（秒）
        now: 現在時刻（テスト用に注入可、省略時は time.time()）

    Returns:
        削除に成功したファイル数。
    """
    if not target_dir.exists():
        return 0
    cutoff = (now if now is not None else time.time()) - retention_seconds
    removed = 0
    for path in target_dir.iterdir():
        if not path.is_file():
            continue
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
                removed += 1
        except OSError:
            # 個別の失敗は飲み込む（best-effort）
            continue
    return removed
