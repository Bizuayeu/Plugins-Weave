"""Domain exceptions for ContextPreloader."""


class ContextPreloaderError(Exception):
    """Base exception for ContextPreloader."""


class ConfigError(ContextPreloaderError):
    """Configuration-related errors."""


class SourceError(ContextPreloaderError):
    """Source loading errors (file not found, read failure)."""


class FetchError(ContextPreloaderError):
    """URL fetch errors (timeout, network, HTTP errors)."""
