"""Domain models: EmotionVector, StopHookPayload, HookLock, DisplayConfig."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone

from scripts.domain.constants import EMOTION_KEYS, MAX_INTENSITY, MIN_INTENSITY


@dataclass(frozen=True)
class EmotionVector:
    """Immutable emotion state with 7 dimensions scored 0-3."""

    emotions: dict[str, int]
    session_id: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> EmotionVector:
        """Construct from a state file dict."""
        raw_emotions = data.get("emotions", {})
        if not isinstance(raw_emotions, dict):
            raw_emotions = {}
        emotions = cls._validate_emotions(raw_emotions)
        session_id = str(data.get("session_id", ""))
        timestamp = str(data.get("timestamp", datetime.now(timezone.utc).isoformat()))
        return cls(emotions=emotions, session_id=session_id, timestamp=timestamp)

    @classmethod
    def from_raw_scores(
        cls, scores: dict[str, int], session_id: str = ""
    ) -> EmotionVector:
        """Construct from raw scores, clamping to 0-3."""
        emotions = cls._validate_emotions(scores)
        return cls(emotions=emotions, session_id=session_id)

    @staticmethod
    def _validate_emotions(raw: Mapping[str, object]) -> dict[str, int]:
        """Validate and clamp emotion scores to [0, 3]."""
        result: dict[str, int] = {}
        for key in EMOTION_KEYS:
            val = raw.get(key, 0)
            try:
                int_val = int(val)  # type: ignore[call-overload]
            except (TypeError, ValueError):
                int_val = 0
            result[key] = max(MIN_INTENSITY, min(MAX_INTENSITY, int_val))
        return result

    def to_dict(self) -> dict[str, object]:
        """Serialize to dict for JSON storage."""
        return {
            "version": "1.0.0",
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "emotions": dict(self.emotions),
        }


@dataclass(frozen=True)
class StopHookPayload:
    """Stop hook stdin payload (actual Claude Code fields)."""

    session_id: str

    @classmethod
    def from_json(cls, raw: str) -> StopHookPayload:
        """Parse stdin JSON into StopHookPayload."""
        data = json.loads(raw)
        return cls(session_id=str(data.get("session_id", "")))


@dataclass(frozen=True)
class HookLock:
    """Lock file state for Stop hook 二重発火防止."""

    session_id: str
    blocked_at: str  # ISO 8601

    def is_fresh(self, max_age_seconds: int = 60) -> bool:
        """Check if lock is within max age (not expired)."""
        try:
            locked_time = datetime.fromisoformat(self.blocked_at)
            now = datetime.now(timezone.utc)
            # Ensure locked_time is timezone-aware
            if locked_time.tzinfo is None:
                locked_time = locked_time.replace(tzinfo=timezone.utc)
            elapsed = (now - locked_time).total_seconds()
            return elapsed < max_age_seconds
        except (ValueError, TypeError):
            return False

    def to_dict(self) -> dict[str, str]:
        """Serialize for JSON storage."""
        return {"session_id": self.session_id, "blocked_at": self.blocked_at}

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> HookLock:
        """Construct from lock file dict."""
        return cls(
            session_id=str(data.get("session_id", "")),
            blocked_at=str(data.get("blocked_at", "")),
        )


@dataclass(frozen=True)
class DisplayConfig:
    """Display settings for statusline output."""

    show_labels: bool = True
    language: str = "ja"

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> DisplayConfig:
        """Construct from config.json display section."""
        show_labels = data.get("show_labels", True)
        language = data.get("language", "ja")
        if language not in ("ja", "en"):
            language = "ja"
        return cls(
            show_labels=bool(show_labels),
            language=str(language),
        )
