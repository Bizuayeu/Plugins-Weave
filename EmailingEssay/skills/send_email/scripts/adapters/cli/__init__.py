# adapters/cli/__init__.py
"""
CLIアダプター

コマンドラインインターフェースのパースとディスパッチを提供。
"""

from .handlers import HANDLERS, dispatch
from .parser import create_parser

__all__ = ["HANDLERS", "create_parser", "dispatch"]
