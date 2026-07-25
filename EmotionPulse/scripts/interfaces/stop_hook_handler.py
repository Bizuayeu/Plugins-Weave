"""Stop hook logic: lock-based block/approve to prevent infinite loops."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from scripts.application.hook_config import build_system_message
from scripts.domain.constants import LOCK_MAX_AGE_SECONDS
from scripts.domain.models import HookLock, StopHookPayload
from scripts.infrastructure.file_io import read_json_safe, write_json_atomic
from scripts.infrastructure.path_resolver import get_lock_file_path


def _read_lock() -> HookLock | None:
    """Read lock file, return None if missing or corrupt."""
    data = read_json_safe(get_lock_file_path())
    if data is None:
        return None
    return HookLock.from_dict(data)


def _write_lock(session_id: str) -> None:
    """Write lock file with current timestamp."""
    lock = HookLock(
        session_id=session_id,
        blocked_at=datetime.now(timezone.utc).isoformat(),
    )
    write_json_atomic(get_lock_file_path(), lock.to_dict())


def _delete_lock() -> None:
    """Delete lock file if it exists."""
    import contextlib

    with contextlib.suppress(OSError):
        get_lock_file_path().unlink(missing_ok=True)


def handle_stop() -> None:
    """Read Stop hook payload and decide block/approve using lock file.

    Lock-based decision (ralph-loop準拠):
    - Lock exists + same session + fresh (< 60s) → approve + delete lock
    - Otherwise → block + write lock + systemMessage
    - Parse failure → approve (never block Claude Code)
    """
    try:
        raw_input = sys.stdin.read()
        payload = StopHookPayload.from_json(raw_input)
    except Exception:
        print(json.dumps({"decision": "approve"}))
        return

    lock = _read_lock()

    if (
        lock is not None
        and lock.session_id == payload.session_id
        and lock.is_fresh(max_age_seconds=LOCK_MAX_AGE_SECONDS)
    ):
        _delete_lock()
        print(json.dumps({"decision": "approve"}))
        return

    _write_lock(payload.session_id)
    system_message = build_system_message()
    fallback_reason = f"EmotionPulse: evaluating emotions.\n\n{system_message}"
    print(
        json.dumps(
            {
                "decision": "block",
                "reason": fallback_reason,
                "systemMessage": system_message,
            }
        )
    )
