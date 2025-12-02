#!/usr/bin/env python3
"""
Infrastructure Config パッケージ
================================

設定ファイルI/O操作を提供。

Usage:
    from infrastructure.config import ConfigLoader, PathResolver, find_plugin_root, load_config
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
from infrastructure.config.plugin_root_resolver import find_plugin_root

__all__ = [
    "ConfigLoader",
    "PathResolver",
    "find_plugin_root",
    "load_config",
    # Path validators
    "PathValidator",
    "PathValidatorChain",
    "PluginRootValidator",
    "TrustedExternalPathValidator",
    "ValidationContext",
    "ValidationResult",
]
