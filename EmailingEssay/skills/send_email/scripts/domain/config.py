# domain/config.py
"""
アプリケーション設定

環境変数と.envファイルから設定を読み込む。
シングルトンパターンで一度だけ読み込み、以降は同じインスタンスを返す。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar


@dataclass(frozen=True)
class EmailConfig:
    """メール設定"""

    sender: str
    password: str
    recipient: str


@dataclass(frozen=True)
class Config:
    """
    アプリケーション設定

    シングルトンパターンで実装。
    環境変数と.envファイルから設定を読み込む。
    """

    email: EmailConfig
    log_json: bool = False
    log_level: str = "INFO"

    # シングルトンインスタンス
    _instance: ClassVar[Config | None] = None

    @classmethod
    def load(cls, env_file: Path | None = None) -> Config:
        """
        設定を読み込む。

        シングルトンパターンにより、2回目以降の呼び出しは
        同じインスタンスを返す。

        Args:
            env_file: .envファイルのパス（省略時はカレントディレクトリ）

        Returns:
            Config インスタンス
        """
        if cls._instance is not None:
            return cls._instance

        # .envファイルの読み込み
        if env_file is None:
            env_file = Path.cwd() / ".env"
        if env_file.exists():
            cls._load_env_file(env_file)

        # 環境変数から設定を構築
        cls._instance = cls(
            email=EmailConfig(
                sender=os.environ.get("ESSAY_SENDER_EMAIL", ""),
                password=os.environ.get("ESSAY_APP_PASSWORD", ""),
                recipient=os.environ.get("ESSAY_RECIPIENT_EMAIL", ""),
            ),
            log_json=os.environ.get("ESSAY_LOG_JSON", "").lower() == "true",
            log_level=os.environ.get("ESSAY_LOG_LEVEL", "INFO"),
        )
        return cls._instance

    @staticmethod
    def _load_env_file(path: Path) -> None:
        """
        .envファイルを読み込んで環境変数に設定する。

        - コメント行（#で始まる行）は無視
        - 空行は無視
        - クォート（"と'）は除去
        - 既存の環境変数は上書きしない（setdefault）

        Args:
            path: .envファイルのパス
        """
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            # 空行とコメント行をスキップ
            if not line or line.startswith("#"):
                continue
            # KEY=VALUE形式をパース
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                # クォートを除去
                value = value.strip('"\'')
                # 既存の環境変数は上書きしない
                os.environ.setdefault(key, value)

    def validate(self) -> list[str]:
        """
        設定を検証する。

        Returns:
            エラーメッセージのリスト（空なら検証成功）
        """
        errors = []
        if not self.email.sender:
            errors.append("ESSAY_SENDER_EMAIL is required")
        if not self.email.password:
            errors.append("ESSAY_APP_PASSWORD is required")
        if not self.email.recipient:
            errors.append("ESSAY_RECIPIENT_EMAIL is required")
        return errors

    @classmethod
    def reset(cls) -> None:
        """
        シングルトンをリセットする。

        テスト用。本番コードでは使用しない。
        """
        cls._instance = None


__all__ = ["Config", "EmailConfig"]
