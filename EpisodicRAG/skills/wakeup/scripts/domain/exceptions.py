"""Domain exceptions for the wakeup engine (generic, persona-agnostic)."""


class WakeupError(Exception):
    """Base exception for the wakeup engine."""


class ConfigError(WakeupError):
    """Configuration is missing required keys or holds invalid values."""
