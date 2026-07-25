"""Tests for interfaces/stop_hook_handler — lock-based block/approve."""

import json
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from scripts.domain.models import HookLock
from scripts.interfaces.stop_hook_handler import handle_stop


def _capture_output(
    stdin_payload: dict[str, object], lock: HookLock | None = None
) -> dict[str, object]:
    """Run handle_stop with mocked stdin and optional lock, capture JSON output."""
    captured: list[str] = []

    with (
        patch("sys.stdin", StringIO(json.dumps(stdin_payload))),
        patch("scripts.interfaces.stop_hook_handler._read_lock", return_value=lock),
        patch("scripts.interfaces.stop_hook_handler._write_lock") as mock_write,
        patch("scripts.interfaces.stop_hook_handler._delete_lock") as mock_delete,
        patch("builtins.print", side_effect=lambda s: captured.append(s)),
    ):
        handle_stop()

    result = json.loads(captured[0])
    return {
        "output": result,
        "write_called": mock_write.called,
        "delete_called": mock_delete.called,
    }


class TestHandleStop:
    def test_no_lock_blocks(self) -> None:
        """初回stop（ロックなし）→ block + systemMessage."""
        result = _capture_output({"session_id": "s1"}, lock=None)
        assert result["output"]["decision"] == "block"
        assert "systemMessage" in result["output"]
        assert "emotion_writer" in result["output"]["systemMessage"]
        assert result["write_called"] is True
        assert result["delete_called"] is False

    def test_no_lock_blocks_includes_reason(self) -> None:
        """reason fallback (#34600 silent mode迂回): prefixが期待文言で始まる."""
        result = _capture_output({"session_id": "s1"}, lock=None)
        assert "reason" in result["output"]
        assert result["output"]["reason"].startswith("EmotionPulse: evaluating emotions.")

    def test_no_lock_blocks_reason_includes_system_message(self) -> None:
        """silent mode下でもreasonだけで実行可能なよう、systemMessage全文がreasonに埋め込まれる."""
        result = _capture_output({"session_id": "s1"}, lock=None)
        assert result["output"]["systemMessage"] in result["output"]["reason"]

    def test_no_lock_blocks_reason_and_system_message_consistent(self) -> None:
        """reason末尾 == systemMessage（prefix + 改行 + system_message構造の保証）."""
        result = _capture_output({"session_id": "s1"}, lock=None)
        assert result["output"]["reason"].endswith(result["output"]["systemMessage"])

    def test_fresh_lock_same_session_approves(self) -> None:
        """2回目stop（同session + fresh lock）→ approve + ロック削除."""
        now = datetime.now(timezone.utc).isoformat()
        lock = HookLock(session_id="s1", blocked_at=now)
        result = _capture_output({"session_id": "s1"}, lock=lock)
        assert result["output"]["decision"] == "approve"
        assert result["delete_called"] is True
        assert result["write_called"] is False

    def test_expired_lock_blocks(self) -> None:
        """期限切れロック → 初回扱いでblock."""
        old = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
        lock = HookLock(session_id="s1", blocked_at=old)
        result = _capture_output({"session_id": "s1"}, lock=lock)
        assert result["output"]["decision"] == "block"
        assert result["write_called"] is True

    def test_different_session_blocks(self) -> None:
        """別sessionのロック → 無視してblock."""
        now = datetime.now(timezone.utc).isoformat()
        lock = HookLock(session_id="other-session", blocked_at=now)
        result = _capture_output({"session_id": "s1"}, lock=lock)
        assert result["output"]["decision"] == "block"
        assert result["write_called"] is True

    def test_invalid_stdin_approves(self) -> None:
        """ペイロード不正 → approve（安全策）."""
        captured: list[str] = []
        with (
            patch("sys.stdin", StringIO("not json")),
            patch("builtins.print", side_effect=lambda s: captured.append(s)),
        ):
            handle_stop()
        result = json.loads(captured[0])
        assert result["decision"] == "approve"

    def test_empty_stdin_approves(self) -> None:
        """空stdin → approve（安全策）."""
        captured: list[str] = []
        with (
            patch("sys.stdin", StringIO("")),
            patch("builtins.print", side_effect=lambda s: captured.append(s)),
        ):
            handle_stop()
        result = json.loads(captured[0])
        assert result["decision"] == "approve"
