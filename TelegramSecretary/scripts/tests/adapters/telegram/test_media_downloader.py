from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from adapters.telegram.api_gateway import TelegramApiGateway
from adapters.telegram.media_downloader import TelegramMediaDownloader
from domain.exceptions import TelegramSecretaryError


def _make_gateway_and_downloader(
    api_handler,
    file_handler,
    retry_count: int = 2,
) -> tuple[TelegramApiGateway, TelegramMediaDownloader]:
    """gateway 用と file CDN 用の MockTransport を分離して構築。

    TelegramMediaDownloader は別 client（base_url が `/file/bot<TOKEN>/`）を使うため、
    httpx.MockTransport を 2 つ用意して各々のクライアントに注入する。
    """
    api_transport = httpx.MockTransport(api_handler)
    api_client = httpx.Client(transport=api_transport, headers={"User-Agent": "test"})
    gateway = TelegramApiGateway(
        bot_token="TEST_TOKEN",
        client=api_client,
        retry_count=retry_count,
    )

    file_transport = httpx.MockTransport(file_handler)
    file_client = httpx.Client(transport=file_transport, headers={"User-Agent": "test"})
    downloader = TelegramMediaDownloader(
        bot_token="TEST_TOKEN",
        gateway=gateway,
        file_client=file_client,
        retry_count=retry_count,
    )
    return gateway, downloader


def test_download_saves_file_to_target_dir(tmp_path: Path):
    def api_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"ok": True, "result": {"file_path": "photos/file_42.jpg"}},
        )

    def file_handler(request: httpx.Request) -> httpx.Response:
        # bot token が file 取得 URL に含まれる
        assert "TEST_TOKEN" in str(request.url)
        assert "photos/file_42.jpg" in str(request.url)
        return httpx.Response(200, content=b"\xff\xd8\xff\xe0fake-jpeg-bytes")

    _, downloader = _make_gateway_and_downloader(api_handler, file_handler)
    saved_path = downloader.download("AgACAgIAAxkBAaXYZ", tmp_path)

    # target_dir 配下に保存される
    assert saved_path.parent == tmp_path
    # 拡張子は file_path のものを継承
    assert saved_path.suffix == ".jpg"
    # 中身がそのまま書き込まれる
    assert saved_path.read_bytes() == b"\xff\xd8\xff\xe0fake-jpeg-bytes"


def test_download_filename_includes_file_id_prefix_for_uniqueness(tmp_path: Path):
    """同一 basename が連続しても衝突しないよう file_id プレフィックスでユニーク化。"""

    def api_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"ok": True, "result": {"file_path": "photos/file_42.jpg"}},
        )

    def file_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"data")

    _, downloader = _make_gateway_and_downloader(api_handler, file_handler)
    saved_a = downloader.download("AgACAgIAAxkBAA1111", tmp_path)
    saved_b = downloader.download("AgACAgIAAxkBAA2222", tmp_path)

    # 2 つの save 結果は異なるファイル名
    assert saved_a != saved_b
    # それぞれ file_id 先頭がファイル名に反映される
    assert "AgACAgIAAxkBAA1111"[:16] in saved_a.name
    assert "AgACAgIAAxkBAA2222"[:16] in saved_b.name


def test_download_does_not_leak_token_in_exception_message(tmp_path: Path):
    """file CDN が 500 で失敗した時、例外メッセージに bot token が含まれない。"""

    def api_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"ok": True, "result": {"file_path": "photos/leak_test.jpg"}},
        )

    def file_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="internal error")

    _, downloader = _make_gateway_and_downloader(api_handler, file_handler)
    with pytest.raises(TelegramSecretaryError) as excinfo:
        downloader.download("AgACAg", tmp_path)

    msg = str(excinfo.value)
    assert "TEST_TOKEN" not in msg
    # URL 全体（token 込み）も含まれない
    assert "api.telegram.org/file/bot" not in msg


def test_download_propagates_auth_failure_from_get_file(tmp_path: Path):
    """get_file で 401 → AuthFailureError がそのまま伝播する。"""
    from domain.exceptions import AuthFailureError

    def api_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="Unauthorized")

    def file_handler(request: httpx.Request) -> httpx.Response:  # 到達しない
        raise AssertionError("file_handler should not be called when get_file fails")

    _, downloader = _make_gateway_and_downloader(api_handler, file_handler)
    with pytest.raises(AuthFailureError):
        downloader.download("AgACAg", tmp_path)


def test_download_5xx_on_file_cdn_is_retried(tmp_path: Path):
    def api_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"ok": True, "result": {"file_path": "photos/x.jpg"}},
        )

    attempts: list[int] = []

    def file_handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) < 2:
            return httpx.Response(503, text="bad gateway")
        return httpx.Response(200, content=b"ok")

    _, downloader = _make_gateway_and_downloader(api_handler, file_handler, retry_count=2)
    saved = downloader.download("AgACAg", tmp_path)
    assert saved.read_bytes() == b"ok"
    assert len(attempts) == 2
