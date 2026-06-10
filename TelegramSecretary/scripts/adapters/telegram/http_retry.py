"""telegram パッケージ共通の HTTP 定数と retry ループ。

api_gateway（Bot API）と media_downloader（file CDN）で二重実装だった retry ループを
status 分類 callback 注入式で一本化する。429 の Retry-After 尊重 sleep は経路に依らず
ここが一律に担う（CDN 経路が 429 を `>=400` 分岐で即死させ Retry-After を無視していた
ポリシー乖離の解消）。`DEFAULT_BASE_URL` / `DEFAULT_USER_AGENT` の二重定義もここに集約。

redact 規律: httpx.RequestError には token 込み URL が混入し得るため、`from None` で
chain を切り、呼び出し側が用意した固定文言（token を含まない）だけを raise する。
"""
from __future__ import annotations

import time
from typing import Callable, Optional

import httpx

from domain.exceptions import TelegramSecretaryError

DEFAULT_BASE_URL = "https://api.telegram.org"
DEFAULT_USER_AGENT = "TelegramSecretary/0.1 (+bot)"
DEFAULT_MAX_RETRY_AFTER_SECONDS = 60


def request_with_retry(
    do_request: Callable[[], httpx.Response],
    classify_status: Callable[[httpx.Response], Optional[str]],
    retry_count: int,
    network_error_message: str,
    max_retry_after_seconds: int = DEFAULT_MAX_RETRY_AFTER_SECONDS,
) -> httpx.Response:
    """retry_count 回まで再試行しつつ do_request を実行する共有ループ。

    classify_status(response) の契約（status 分類 callback）:
    - None を返す → 成功。response をそのまま返す
    - 文言（str）を返す → transient（5xx / 429 等）。再試行し、尽きたらその文言で
      TelegramSecretaryError を raise（文言は呼び出し側責務で redact 済みであること）
    - 例外を raise → 致命（401 / その他 4xx 等）。再試行せずそのまま伝播

    429 を transient に分類した場合は Retry-After ヘッダを尊重して sleep してから
    再試行する（上限 max_retry_after_seconds、ヘッダ無し・不正値は即時 retry）。
    httpx.RequestError は network_error_message（固定文言）で raise し、token 込み URL が
    混入し得る元例外は `from None` で chain ごと切る。

    ループは全経路で return / raise に到達するため、旧実装の「到達不能 raise ＋
    last_exc 蓄積」は持たない。
    """
    attempt = 0
    while True:
        try:
            response = do_request()
        except httpx.RequestError:
            if attempt >= retry_count:
                raise TelegramSecretaryError(network_error_message) from None
            attempt += 1
            continue

        retry_message = classify_status(response)
        if retry_message is None:
            return response
        if attempt >= retry_count:
            raise TelegramSecretaryError(retry_message)
        if response.status_code == 429:
            _sleep_for_retry_after(
                response.headers.get("Retry-After"), max_retry_after_seconds
            )
        attempt += 1


def _sleep_for_retry_after(
    header_value: Optional[str], max_retry_after_seconds: int
) -> None:
    """`Retry-After` ヘッダの秒数だけ sleep（上限 max_retry_after_seconds）。

    - ヘッダ無しまたは parse 失敗時は sleep しない（即時 retry）
    - 上限を超える値は上限に丸める（DoS 自損防止）
    """
    if not header_value:
        return
    try:
        seconds = int(header_value)
    except (ValueError, TypeError):
        return
    if seconds <= 0:
        return
    time.sleep(min(seconds, max_retry_after_seconds))
