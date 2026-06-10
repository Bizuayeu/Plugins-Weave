"""Telegram Bot API への HTTP クライアント。getUpdates / sendMessage を提供。"""
from __future__ import annotations

from typing import Any, List, Optional

import httpx

from adapters.telegram import http_retry
from domain.exceptions import AuthFailureError, TelegramSecretaryError
from domain.models import OutboundMessage, TelegramUpdate
from domain.offset import UpdateOffset
from domain.outbound import OutboundAttachment


class TelegramApiGateway:
    """Telegram Bot API の getUpdates / sendMessage を呼ぶ実装。

    - 5xx / 429 は retry_count 回まで自動再試行（retry ループは http_retry と共有）
    - 429 は `Retry-After` ヘッダを尊重して sleep（最大 `max_retry_after_seconds` 秒）
    - 401 は AuthFailureError（exit 3 系の決定打）
    - その他 4xx は TelegramSecretaryError
    - ネットワークエラーは retry 後に TelegramSecretaryError
    """

    DEFAULT_BASE_URL = http_retry.DEFAULT_BASE_URL
    DEFAULT_USER_AGENT = http_retry.DEFAULT_USER_AGENT
    DEFAULT_MAX_RETRY_AFTER_SECONDS = http_retry.DEFAULT_MAX_RETRY_AFTER_SECONDS

    def __init__(
        self,
        bot_token: str,
        base_url: str = DEFAULT_BASE_URL,
        client: Optional[httpx.Client] = None,
        retry_count: int = 2,
        request_timeout: float = 40.0,
        max_retry_after_seconds: int = DEFAULT_MAX_RETRY_AFTER_SECONDS,
    ) -> None:
        self._bot_token = bot_token
        self._base_url = base_url.rstrip("/")
        self._retry_count = retry_count
        self._request_timeout = request_timeout
        self._max_retry_after_seconds = max_retry_after_seconds
        if client is None:
            client = httpx.Client(
                timeout=request_timeout,
                headers={"User-Agent": self.DEFAULT_USER_AGENT},
            )
        self._client = client

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "TelegramApiGateway":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def fetch(self, offset: UpdateOffset, timeout_seconds: int = 30) -> List[TelegramUpdate]:
        url = f"{self._base_url}/bot{self._bot_token}/getUpdates"
        params = {"offset": offset.value, "timeout": timeout_seconds}
        response = self._request_with_retry("GET", url, params=params)
        data = response.json()
        if not data.get("ok"):
            raise TelegramSecretaryError(f"getUpdates failed: {data}")
        return [TelegramUpdate.from_api(u) for u in data.get("result", [])]

    # Telegram の photo/document caption 上限（超過分は text を別 sendMessage で先送り）
    CAPTION_LIMIT = 1024

    def send(self, message: OutboundMessage) -> None:
        """添付の有無で分岐。添付なしは sendMessage、ありは sendPhoto/sendDocument。"""
        if not message.attachments:
            self._send_text(message.chat_id, message.text, message.reply_to_message_id)
            return
        self._send_with_attachments(message)

    def _send_text(
        self, chat_id: int, text: str, reply_to_message_id: Optional[int]
    ) -> None:
        url = f"{self._base_url}/bot{self._bot_token}/sendMessage"
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
        response = self._request_with_retry("POST", url, json=payload)
        data = response.json()
        if not data.get("ok"):
            raise TelegramSecretaryError(f"sendMessage failed: {data}")

    def _send_with_attachments(self, message: OutboundMessage) -> None:
        """各添付を sendPhoto/sendDocument で送る。

        - 添付1件かつ caption 上限内なら本文を caption に載せる
        - それ以外（複数 or 上限超）は本文を sendMessage で先送りしてから添付を送る
        - reply_to は最初の送信のみに付与（二重 reply 回避）
        """
        text = message.text or ""
        attachments = message.attachments
        single_caption = len(attachments) == 1 and len(text) <= self.CAPTION_LIMIT
        reply_to = message.reply_to_message_id

        if text and not single_caption:
            self._send_text(message.chat_id, text, reply_to)
            reply_to = None  # 先送り済み。以降の添付には付けない

        for index, attachment in enumerate(attachments):
            caption = text if (single_caption and index == 0) else None
            self._send_one_attachment(
                message.chat_id,
                attachment,
                caption=caption,
                reply_to_message_id=reply_to if index == 0 else None,
            )

    def _send_one_attachment(
        self,
        chat_id: int,
        attachment: OutboundAttachment,
        caption: Optional[str],
        reply_to_message_id: Optional[int],
    ) -> None:
        method = "sendPhoto" if attachment.is_photo() else "sendDocument"
        field = "photo" if attachment.is_photo() else "document"
        url = f"{self._base_url}/bot{self._bot_token}/{method}"
        # retry で再利用できるよう bytes に読み切る（file handle 消費済み問題の回避）
        file_bytes = attachment.path.read_bytes()
        files = {field: (attachment.path.name, file_bytes)}
        data: dict[str, Any] = {"chat_id": chat_id}
        if caption is not None:
            data["caption"] = caption
        if reply_to_message_id is not None:
            data["reply_to_message_id"] = reply_to_message_id
        response = self._request_with_retry("POST", url, files=files, data=data)
        payload = response.json()
        if not payload.get("ok"):
            # token 込み URL は載せず、method/chat_id/file 名のみ（redact）
            raise TelegramSecretaryError(
                f"{method} failed (chat_id={chat_id}, file={attachment.path.name}): {payload}"
            )

    def send_chat_action(self, chat_id: int, action: str = "typing") -> None:
        """typing 等のチャットアクションを送る（best-effort、失敗は本応答を妨げない）。"""
        url = f"{self._base_url}/bot{self._bot_token}/sendChatAction"
        try:
            self._request_with_retry(
                "POST", url, json={"chat_id": chat_id, "action": action}
            )
        except TelegramSecretaryError:
            pass  # best-effort

    def get_file(self, file_id: str) -> str:
        """Telegram /getFile で file_id から file_path を取得（Stage 6.3）。

        Bot API の File オブジェクトは `file_path` を含む（例: `photos/file_42.jpg`）。
        この相対パスを `/file/bot<TOKEN>/<file_path>` の組み立てに使う。
        """
        url = f"{self._base_url}/bot{self._bot_token}/getFile"
        params = {"file_id": file_id}
        response = self._request_with_retry("GET", url, params=params)
        data = response.json()
        if not data.get("ok"):
            raise TelegramSecretaryError(f"getFile failed: {data}")
        result = data.get("result") or {}
        file_path = result.get("file_path")
        if not file_path:
            raise TelegramSecretaryError(
                f"getFile response missing file_path: {data}"
            )
        return str(file_path)

    def _request_with_retry(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        # network error の固定文言: exc には token 込み URL が混入し得るため、ヘルパ側が
        # from None で chain を切り、この文言だけを raise する（redact）
        return http_retry.request_with_retry(
            lambda: self._client.request(method, url, **kwargs),
            self._classify_status,
            retry_count=self._retry_count,
            network_error_message=(
                "network error after retries (request to Telegram API failed)"
            ),
            max_retry_after_seconds=self._max_retry_after_seconds,
        )

    @staticmethod
    def _classify_status(response: httpx.Response) -> Optional[str]:
        """Bot API 応答の status 分類（http_retry.request_with_retry の callback 契約）。

        - 401 → AuthFailureError（致命、retry しない）
        - 429 / 5xx → transient 文言を返す（retry、尽きたらその文言で raise）
        - その他 4xx → TelegramSecretaryError（致命）
        - 2xx 系 → None（成功）
        """
        if response.status_code == 401:
            raise AuthFailureError(f"401 Unauthorized: {response.text[:200]}")
        if response.status_code == 429:
            # Telegram のレート制限。Retry-After 尊重の sleep はヘルパ側が担う
            return (
                "rate limited after retries (429), "
                f"Retry-After={response.headers.get('Retry-After')!r}"
            )
        if response.status_code >= 500:
            return f"server error after retries: {response.status_code}"
        if response.status_code >= 400:
            raise TelegramSecretaryError(
                f"client error: {response.status_code} {response.text[:200]}"
            )
        return None
