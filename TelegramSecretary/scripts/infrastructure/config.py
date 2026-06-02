"""env と config.json から設定を読み込むローダ。fail-fast：欠損は EnvironmentError。

純2層: 秘匿（token/chats）と state_dir は env、非秘匿の運用設定（session_duration_sec /
agent_name / private_dir）は config.json（<INSTALL_DIR>/config.json 決め打ち）。
media_* は env 任意上書き口を持つコード内蔵デフォルト（据え置き）。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from domain.authorization import AuthorizedChats
from domain.session_config import SessionDuration

DEFAULT_MEDIA_MAX_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
DEFAULT_MEDIA_RETENTION_HOURS = 24
DEFAULT_OUTBOUND_MAX_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB（Telegram bot API 送信上限）
DEFAULT_PDF_IMAGE_MAX_PAGES = 20  # 画像 PDF 全ページ画像化の安全弁（超多ページの disk/トークン暴走防止）


def _default_config_path() -> Path:
    """config.json の決め打ち場所（<INSTALL_DIR>/config.json）。

    config.py は <INSTALL_DIR>/scripts/infrastructure/config.py ゆえ parents[2]=<INSTALL_DIR>。
    env で場所を指さない（鶏卵問題の回避）。テストは from_sources(config_path=...) で差し替え。
    """
    return Path(__file__).resolve().parents[2] / "config.json"


@dataclass(frozen=True)
class Config:
    bot_token: str
    authorized_chats: AuthorizedChats
    state_dir: Path
    session_duration_sec: int
    media_max_size_bytes: int = DEFAULT_MEDIA_MAX_SIZE_BYTES
    media_retention_hours: int = DEFAULT_MEDIA_RETENTION_HOURS
    media_enable_download: bool = True
    outbound_max_size_bytes: int = DEFAULT_OUTBOUND_MAX_SIZE_BYTES
    pdf_image_max_pages: int = DEFAULT_PDF_IMAGE_MAX_PAGES
    agent_name: str | None = None
    private_dir: str | None = None

    @property
    def individuals_path(self) -> Path:
        return self.state_dir / "individuals" / "INDIVIDUALS.json"

    @property
    def tasks_path(self) -> Path:
        return self.state_dir / "tasks" / "TASKS.json"

    @property
    def knowledge_path(self) -> Path:
        return self.state_dir / "knowledge" / "KNOWLEDGE.json"

    @classmethod
    def from_sources(cls, config_path: Path | None = None) -> "Config":
        """env（秘匿 + state_dir + media 任意上書き）と config.json（非秘匿の正典）から構築。

        秘匿（token/chats）は env、session_duration_sec 等の運用設定は config.json。
        欠損・不正は EnvironmentError（fail-fast）。config.json の場所は決め打ち
        （<INSTALL_DIR>/config.json）、テストは config_path で差し替える。
        """
        # --- 秘匿: env（fail-fast） ---
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            raise EnvironmentError("TELEGRAM_BOT_TOKEN is not set")

        chats_raw = os.environ.get("TELEGRAM_SECRETARY_AUTHORIZED_CHATS", "").strip()
        if not chats_raw:
            raise EnvironmentError("TELEGRAM_SECRETARY_AUTHORIZED_CHATS is not set")
        try:
            parsed = json.loads(chats_raw)
        except json.JSONDecodeError as exc:
            raise EnvironmentError(
                f"TELEGRAM_SECRETARY_AUTHORIZED_CHATS must be JSON array of int: {exc}"
            )
        if not isinstance(parsed, list):
            raise EnvironmentError(
                "TELEGRAM_SECRETARY_AUTHORIZED_CHATS must be a JSON array of int"
            )
        try:
            chat_ids: Iterable[int] = [int(c) for c in parsed]
        except (TypeError, ValueError) as exc:
            raise EnvironmentError(
                f"TELEGRAM_SECRETARY_AUTHORIZED_CHATS elements must be ints: {exc}"
            )

        # --- state_dir: env 任意上書き（未設定なら ./state、bootstrap が絶対化） ---
        state_dir = Path(os.environ.get("TELEGRAM_SECRETARY_STATE_DIR", "./state")).resolve()

        # --- 非秘匿の運用設定: config.json（<INSTALL_DIR>/config.json 決め打ち、必須） ---
        path = config_path or _default_config_path()
        if not path.exists():
            raise EnvironmentError(
                f"config.json not found at {path}; run `init-config` to create it"
            )
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise EnvironmentError(f"config.json is not valid JSON ({path}): {exc}")
        if not isinstance(data, dict):
            raise EnvironmentError(f"config.json must be a JSON object ({path})")

        raw_duration = data.get("session_duration_sec")
        if raw_duration is None:
            raise EnvironmentError(
                "config.json: session_duration_sec is required (no default; see config.template.json)"
            )
        try:
            duration = SessionDuration.from_seconds(int(raw_duration))
        except (TypeError, ValueError) as exc:
            raise EnvironmentError(f"config.json: session_duration_sec invalid: {exc}")

        agent_name = data.get("agent_name")  # Optional（prompt 用、CLI fetch/send では未使用）
        private_dir = data.get("private_dir")  # Optional

        # --- media 系: env 任意上書き（未設定で DEFAULT、据え置き） ---
        max_size = cls._parse_positive_int(
            "TELEGRAM_SECRETARY_MEDIA_MAX_SIZE_BYTES",
            default=DEFAULT_MEDIA_MAX_SIZE_BYTES,
        )
        retention = cls._parse_positive_int(
            "TELEGRAM_SECRETARY_MEDIA_RETENTION_HOURS",
            default=DEFAULT_MEDIA_RETENTION_HOURS,
        )
        enable_download = cls._parse_bool(
            "TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD",
            default=True,
        )
        outbound_max_size = cls._parse_positive_int(
            "TELEGRAM_SECRETARY_OUTBOUND_MAX_SIZE_BYTES",
            default=DEFAULT_OUTBOUND_MAX_SIZE_BYTES,
        )
        pdf_image_max_pages = cls._parse_positive_int(
            "TELEGRAM_SECRETARY_PDF_IMAGE_MAX_PAGES",
            default=DEFAULT_PDF_IMAGE_MAX_PAGES,
        )

        return cls(
            bot_token=token,
            authorized_chats=AuthorizedChats.from_iterable(chat_ids),
            state_dir=state_dir,
            session_duration_sec=duration.seconds,
            media_max_size_bytes=max_size,
            media_retention_hours=retention,
            media_enable_download=enable_download,
            outbound_max_size_bytes=outbound_max_size,
            pdf_image_max_pages=pdf_image_max_pages,
            agent_name=agent_name,
            private_dir=private_dir,
        )

    @staticmethod
    def _parse_positive_int(env_name: str, default: int) -> int:
        raw = os.environ.get(env_name, "").strip()
        if not raw:
            return default
        try:
            value = int(raw)
        except ValueError as exc:
            raise EnvironmentError(
                f"{env_name} must be a positive integer: {exc}"
            )
        if value <= 0:
            raise EnvironmentError(
                f"{env_name} must be > 0 (got {value})"
            )
        return value

    @staticmethod
    def _parse_bool(env_name: str, default: bool) -> bool:
        raw = os.environ.get(env_name, "").strip().lower()
        if not raw:
            return default
        if raw in ("true", "1", "yes"):
            return True
        if raw in ("false", "0", "no"):
            return False
        raise EnvironmentError(
            f"{env_name} must be true/false (got {raw!r})"
        )
