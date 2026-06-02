"""Telegram の file_id から実ファイルを download する Adapter（Stage 6.3）。

bot token 込み URL（`/file/bot<TOKEN>/<file_path>`）を使うため、
例外メッセージ・ログに URL/token を残さない（redact）。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import httpx

from adapters.telegram.api_gateway import TelegramApiGateway
from domain.exceptions import TelegramSecretaryError


class TelegramMediaDownloader:
    """`getFile` → file_path 取得 → `/file/bot<TOKEN>/<file_path>` から bytes 取得 → 保存。

    別 client を使う理由: file CDN の base URL が `api.telegram.org/file/bot<TOKEN>/`
    で API base と異なり、token が URL path に入る。
    """

    DEFAULT_BASE_URL = "https://api.telegram.org"
    DEFAULT_USER_AGENT = "TelegramSecretary/0.1 (+bot)"

    def __init__(
        self,
        bot_token: str,
        gateway: TelegramApiGateway,
        file_base_url: str = DEFAULT_BASE_URL,
        file_client: Optional[httpx.Client] = None,
        retry_count: int = 2,
        request_timeout: float = 60.0,
    ) -> None:
        self._bot_token = bot_token
        self._gateway = gateway
        self._file_base_url = file_base_url.rstrip("/")
        self._retry_count = retry_count
        if file_client is None:
            file_client = httpx.Client(
                timeout=request_timeout,
                headers={"User-Agent": self.DEFAULT_USER_AGENT},
            )
        self._file_client = file_client

    def close(self) -> None:
        self._file_client.close()

    def __enter__(self) -> "TelegramMediaDownloader":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def download(self, file_id: str, target_dir: Path) -> Path:
        """file_id → getFile → file_path → bytes 取得 → target_dir に保存。

        - get_file は gateway 側の retry / 401 / 4xx ハンドリングを継承
        - file CDN は別 client、5xx は retry、token は例外メッセージに残さない
        """
        file_path = self._gateway.get_file(file_id)
        url = f"{self._file_base_url}/file/bot{self._bot_token}/{file_path}"
        safe_id = file_id[:8]  # 例外メッセージ用の短縮 id（token redact 文脈）

        for attempt in range(self._retry_count + 1):
            try:
                response = self._file_client.get(url)
            except httpx.RequestError:
                if attempt < self._retry_count:
                    continue
                # exc には URL が含まれる可能性 → from None で chain を切って token を秘匿
                raise TelegramSecretaryError(
                    f"network error during media download (file_id={safe_id})"
                ) from None

            if response.status_code >= 500:
                if attempt < self._retry_count:
                    continue
                raise TelegramSecretaryError(
                    f"media CDN server error after retries "
                    f"(file_id={safe_id}, status={response.status_code})"
                )
            if response.status_code >= 400:
                raise TelegramSecretaryError(
                    f"media CDN client error "
                    f"(file_id={safe_id}, status={response.status_code})"
                )

            return self._save_to_target(file_id, file_path, response.content, target_dir)

        # retry loop が完走しないケース（理論上到達しない）
        raise TelegramSecretaryError(
            f"media download unreachable path (file_id={safe_id})"
        )

    def _save_to_target(
        self,
        file_id: str,
        file_path: str,
        content: bytes,
        target_dir: Path,
    ) -> Path:
        """target_dir / "<file_id 先頭16>_<basename>" に bytes を保存。

        file_id プレフィックスで衝突回避と追跡性を両立。
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        basename = Path(file_path).name
        prefix = file_id[:16]
        save_path = target_dir / f"{prefix}_{basename}"
        save_path.write_bytes(content)
        return save_path
