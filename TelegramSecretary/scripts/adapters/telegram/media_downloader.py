"""Telegram の file_id から実ファイルを download する Adapter（Stage 6.3）。

bot token 込み URL（`/file/bot<TOKEN>/<file_path>`）を使うため、
例外メッセージ・ログに URL/token を残さない（redact）。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import httpx

from adapters.telegram import http_retry
from adapters.telegram.api_gateway import TelegramApiGateway
from domain.exceptions import TelegramSecretaryError

# 保存名 `{file_id[:FILE_ID_PREFIX_LEN]}_{basename}` のプレフィックス長。
# pdf_renderer が派生画像の命名で同じ長さを stem から切り出して一致させるため共有する
# （どちらかが独断で変えると derived_image_paths の対応が静かに崩れる）。
FILE_ID_PREFIX_LEN = 16


class TelegramMediaDownloader:
    """`getFile` → file_path 取得 → `/file/bot<TOKEN>/<file_path>` から bytes 取得 → 保存。

    別 client を使う理由: file CDN の base URL が `api.telegram.org/file/bot<TOKEN>/`
    で API base と異なり、token が URL path に入る。
    """

    DEFAULT_BASE_URL = http_retry.DEFAULT_BASE_URL
    DEFAULT_USER_AGENT = http_retry.DEFAULT_USER_AGENT

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
        - file CDN は別 client。retry ポリシー（5xx retry / 429 Retry-After 尊重）は
          http_retry を Bot API 経路と共有し、token は例外メッセージに残さない
        """
        file_path = self._gateway.get_file(file_id)
        url = f"{self._file_base_url}/file/bot{self._bot_token}/{file_path}"
        safe_id = file_id[:8]  # 例外メッセージ用の短縮 id（token redact 文脈）

        # network error の固定文言: exc には URL（token 込み）が含まれる可能性があるため、
        # ヘルパ側が from None で chain を切り、この文言だけを raise する（redact）
        response = http_retry.request_with_retry(
            lambda: self._file_client.get(url),
            lambda res: self._classify_cdn_status(res, safe_id),
            retry_count=self._retry_count,
            network_error_message=(
                f"network error during media download (file_id={safe_id})"
            ),
        )
        return self._save_to_target(file_id, file_path, response.content, target_dir)

    @staticmethod
    def _classify_cdn_status(response: httpx.Response, safe_id: str) -> Optional[str]:
        """file CDN 応答の status 分類（http_retry.request_with_retry の callback 契約）。

        429 を transient に分類することで Retry-After 尊重の retry を Bot API 経路から
        継承する（旧実装は `>=400` 分岐で即死し Retry-After を無視していた）。
        文言は safe_id のみ載せ、URL/token は含めない（redact）。
        """
        if response.status_code == 429:
            return (
                f"media CDN rate limited after retries "
                f"(file_id={safe_id}, status=429)"
            )
        if response.status_code >= 500:
            return (
                f"media CDN server error after retries "
                f"(file_id={safe_id}, status={response.status_code})"
            )
        if response.status_code >= 400:
            raise TelegramSecretaryError(
                f"media CDN client error "
                f"(file_id={safe_id}, status={response.status_code})"
            )
        return None

    def _save_to_target(
        self,
        file_id: str,
        file_path: str,
        content: bytes,
        target_dir: Path,
    ) -> Path:
        """target_dir / "<file_id 先頭 FILE_ID_PREFIX_LEN 文字>_<basename>" に bytes を保存。

        file_id プレフィックスで衝突回避と追跡性を両立。
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        basename = Path(file_path).name
        prefix = file_id[:FILE_ID_PREFIX_LEN]
        save_path = target_dir / f"{prefix}_{basename}"
        save_path.write_bytes(content)
        return save_path
