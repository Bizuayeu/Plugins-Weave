# adapters/storage/__init__.py
"""
ストレージアダプター

スケジュール情報の永続化を管理する。
"""
from .json_adapter import JsonStorageAdapter

__all__ = ["JsonStorageAdapter"]
