#!/usr/bin/env python3
"""
Infrastructure Config パッケージ
================================

設定ファイルI/O操作を提供。

Usage:
    from infrastructure.config import ConfigLoader, PathResolver, load_config
    from infrastructure.config import PathValidatorChain, PluginRootValidator
"""

from infrastructure.config.config_loader import ConfigLoader
from infrastructure.config.config_repository import load_config
from infrastructure.config.path_resolver import PathResolver
from infrastructure.config.path_validators import (
    PathValidator,
    PathValidatorChain,
    PluginRootValidator,
    TrustedExternalPathValidator,
    ValidationContext,
    ValidationResult,
)
from infrastructure.config.persistent_path import get_persistent_config_dir

__all__ = [
    "ConfigLoader",
    "PathResolver",
    "get_persistent_config_dir",
    "load_config",
    # Path validators
    "PathValidator",
    "PathValidatorChain",
    "PluginRootValidator",
    "TrustedExternalPathValidator",
    "ValidationContext",
    "ValidationResult",
]
