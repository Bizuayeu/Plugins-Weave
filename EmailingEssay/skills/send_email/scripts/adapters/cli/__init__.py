# adapters/cli/__init__.py
"""
CLIアダプター

コマンドラインインターフェースのパースとディスパッチを提供。
"""
from .handlers import dispatch, HANDLERS
from .parser import create_parser

__all__ = ["dispatch", "HANDLERS", "create_parser"]
