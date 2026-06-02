from __future__ import annotations

import json

import httpx
import pytest

from adapters.telegram import api_gateway as gateway_module
from adapters.telegram.api_gateway import TelegramApiGateway
from domain.exceptions import AuthFailureError, TelegramSecretaryError
from domain.models import OutboundMessage
from domain.offset import UpdateOffset
from domain.outbound import OutboundAttachment


def _gateway(handler, retry_count: int = 2, max_retry_after: int = 60) -> TelegramApiGateway:
    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, headers={"User-Agent": "test"})
    return TelegramApiGateway(
        bot_token="TEST_TOKEN",
        client=client,
        retry_count=retry_count,
        max_retry_after_seconds=max_retry_after,
    )


def test_fetch_parses_updates():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "getUpdates" in str(request.url)
        assert "TEST_TOKEN" in str(request.url)
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": [
                    {
                        "update_id": 7,
                        "message": {
                            "chat": {"id": 100},
                            "from": {"id": 200, "username": "test_user"},
                            "text": "hi",
                        },
                    }
                ],
            },
        )

    gw = _gateway(handler)
    updates = gw.fetch(UpdateOffset.initial(), timeout_seconds=30)
    assert len(updates) == 1
    assert updates[0].update_id == 7
    assert updates[0].text == "hi"


def test_fetch_empty_result():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": []})

    gw = _gateway(handler)
    assert gw.fetch(UpdateOffset.initial()) == []


def test_fetch_raises_auth_failure_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="Unauthorized")

    gw = _gateway(handler)
    with pytest.raises(AuthFailureError):
        gw.fetch(UpdateOffset.initial())


def test_send_message_success():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert "sendMessage" in str(request.url)
        captured["body"] = json.loads(request.read())
        return httpx.Response(200, json={"ok": True, "result": {}})

    gw = _gateway(handler)
    gw.send(OutboundMessage(chat_id=100, text="hi"))
    assert captured["body"]["chat_id"] == 100
    assert captured["body"]["text"] == "hi"


def test_send_message_with_reply_to():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.read())
        return httpx.Response(200, json={"ok": True, "result": {}})

    gw = _gateway(handler)
    gw.send(OutboundMessage(chat_id=100, text="reply", reply_to_message_id=42))
    assert captured["body"]["reply_to_message_id"] == 42


def test_5xx_is_retried_until_success():
    attempts: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) < 3:
            return httpx.Response(503, text="bad gateway")
        return httpx.Response(200, json={"ok": True, "result": []})

    gw = _gateway(handler, retry_count=2)
    updates = gw.fetch(UpdateOffset.initial())
    assert updates == []
    assert len(attempts) == 3


def test_5xx_fails_after_retries_exhausted():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="bad gateway")

    gw = _gateway(handler, retry_count=2)
    with pytest.raises(TelegramSecretaryError):
        gw.fetch(UpdateOffset.initial())


def test_4xx_client_error_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text="bad request")

    gw = _gateway(handler)
    with pytest.raises(TelegramSecretaryError):
        gw.fetch(UpdateOffset.initial())


def test_send_failure_raises_on_ok_false():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": False, "description": "chat not found"})

    gw = _gateway(handler)
    with pytest.raises(TelegramSecretaryError):
        gw.send(OutboundMessage(chat_id=999, text="x"))


# --- 429 / Retry-After ---


def test_429_is_retried_until_success(monkeypatch):
    sleep_calls: list[float] = []
    monkeypatch.setattr(gateway_module.time, "sleep", lambda s: sleep_calls.append(s))

    attempts: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) < 3:
            return httpx.Response(429, headers={"Retry-After": "1"})
        return httpx.Response(200, json={"ok": True, "result": []})

    gw = _gateway(handler, retry_count=2)
    updates = gw.fetch(UpdateOffset.initial())
    assert updates == []
    assert len(attempts) == 3
    # Retry-After を尊重して 2 回 sleep（最後の成功時は sleep しない）
    assert sleep_calls == [1, 1]


def test_429_fails_after_retries_exhausted(monkeypatch):
    monkeypatch.setattr(gateway_module.time, "sleep", lambda s: None)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "1"})

    gw = _gateway(handler, retry_count=2)
    with pytest.raises(TelegramSecretaryError) as excinfo:
        gw.fetch(UpdateOffset.initial())
    assert "429" in str(excinfo.value)


def test_429_caps_sleep_at_max_retry_after(monkeypatch):
    sleep_calls: list[float] = []
    monkeypatch.setattr(gateway_module.time, "sleep", lambda s: sleep_calls.append(s))

    attempts: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) < 2:
            # 攻撃的に大きな Retry-After を返すケース（自損防止のため上限で丸める）
            return httpx.Response(429, headers={"Retry-After": "3600"})
        return httpx.Response(200, json={"ok": True, "result": []})

    gw = _gateway(handler, retry_count=2, max_retry_after=10)
    gw.fetch(UpdateOffset.initial())
    assert sleep_calls == [10]  # 3600 → 10 に丸められる


def test_429_without_retry_after_does_not_sleep(monkeypatch):
    sleep_calls: list[float] = []
    monkeypatch.setattr(gateway_module.time, "sleep", lambda s: sleep_calls.append(s))

    attempts: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) < 2:
            return httpx.Response(429)  # Retry-After ヘッダ無し
        return httpx.Response(200, json={"ok": True, "result": []})

    gw = _gateway(handler, retry_count=2)
    gw.fetch(UpdateOffset.initial())
    # Retry-After 無しなら sleep せず即 retry
    assert sleep_calls == []
    assert len(attempts) == 2


def test_429_invalid_retry_after_does_not_sleep(monkeypatch):
    sleep_calls: list[float] = []
    monkeypatch.setattr(gateway_module.time, "sleep", lambda s: sleep_calls.append(s))

    attempts: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) < 2:
            return httpx.Response(429, headers={"Retry-After": "not-a-number"})
        return httpx.Response(200, json={"ok": True, "result": []})

    gw = _gateway(handler, retry_count=2)
    gw.fetch(UpdateOffset.initial())
    assert sleep_calls == []


# === Stage 6.3: get_file ===


def test_get_file_returns_file_path():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "getFile" in str(request.url)
        assert "file_id=AgACAg" in str(request.url)
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": {
                    "file_id": "AgACAg",
                    "file_unique_id": "AQADxxxx",
                    "file_size": 102400,
                    "file_path": "photos/file_42.jpg",
                },
            },
        )

    gw = _gateway(handler)
    file_path = gw.get_file("AgACAg")
    assert file_path == "photos/file_42.jpg"


def test_get_file_raises_auth_failure_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="Unauthorized")

    gw = _gateway(handler)
    with pytest.raises(AuthFailureError):
        gw.get_file("AgACAg")


def test_get_file_retries_on_5xx():
    attempts: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) < 3:
            return httpx.Response(503, text="bad gateway")
        return httpx.Response(
            200,
            json={"ok": True, "result": {"file_path": "photos/x.jpg"}},
        )

    gw = _gateway(handler, retry_count=2)
    assert gw.get_file("x") == "photos/x.jpg"
    assert len(attempts) == 3


def test_get_file_raises_when_ok_false():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": False, "description": "file not found"})

    gw = _gateway(handler)
    with pytest.raises(TelegramSecretaryError):
        gw.get_file("missing")


# === Stage 8.3: outbound media（sendPhoto / sendDocument / sendChatAction） ===


def test_send_no_attachment_uses_sendmessage():
    # 後方互換: 添付なしは従来 sendMessage（json）
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["content_type"] = request.headers.get("content-type", "")
        return httpx.Response(200, json={"ok": True, "result": {}})

    gw = _gateway(handler)
    gw.send(OutboundMessage(chat_id=100, text="hi"))
    assert "sendMessage" in captured["url"]
    assert "application/json" in captured["content_type"]


def test_send_photo_attachment_uses_sendphoto(tmp_path):
    img = tmp_path / "fig.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["content_type"] = request.headers.get("content-type", "")
        captured["body"] = request.read()
        return httpx.Response(200, json={"ok": True, "result": {}})

    gw = _gateway(handler)
    gw.send(
        OutboundMessage(
            chat_id=100,
            text="caption text",
            attachments=[OutboundAttachment(path=img)],
        )
    )
    assert "sendPhoto" in captured["url"]
    assert "multipart/form-data" in captured["content_type"]
    # 本文は caption として、chat_id は data field として multipart body に乗る
    assert b"caption text" in captured["body"]
    assert b'name="chat_id"' in captured["body"]


def test_send_document_attachment_uses_senddocument(tmp_path):
    doc = tmp_path / "report.pdf"
    doc.write_bytes(b"%PDF-1.4")
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(200, json={"ok": True, "result": {}})

    gw = _gateway(handler)
    gw.send(
        OutboundMessage(
            chat_id=100,
            text="",
            attachments=[OutboundAttachment(path=doc)],
        )
    )
    assert "sendDocument" in captured["url"]


def test_long_text_with_attachment_sends_text_separately(tmp_path):
    # caption 上限（1024）超の text は sendMessage で先送り、添付は後続
    img = tmp_path / "fig.png"
    img.write_bytes(b"\x89PNG\r\n")
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200, json={"ok": True, "result": {}})

    gw = _gateway(handler)
    gw.send(
        OutboundMessage(
            chat_id=100,
            text="x" * 2000,
            attachments=[OutboundAttachment(path=img)],
        )
    )
    assert any("sendMessage" in c for c in calls)
    assert any("sendPhoto" in c for c in calls)


def test_send_chat_action_calls_api():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.read())
        return httpx.Response(200, json={"ok": True, "result": True})

    gw = _gateway(handler)
    gw.send_chat_action(100, "typing")
    assert "sendChatAction" in captured["url"]
    assert captured["body"]["action"] == "typing"
    assert captured["body"]["chat_id"] == 100


def test_send_chat_action_is_best_effort_on_error():
    # typing は best-effort: API エラーでも例外を投げず本応答を妨げない
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="err")

    gw = _gateway(handler, retry_count=0)
    gw.send_chat_action(100, "typing")  # 例外が出ないこと


def test_send_photo_failure_does_not_leak_token(tmp_path):
    # 送信失敗例外に bot token が混入しない（media_downloader と同型の redact）
    img = tmp_path / "fig.png"
    img.write_bytes(b"\x89PNG")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": False, "description": "bad request"})

    gw = _gateway(handler)
    with pytest.raises(TelegramSecretaryError) as excinfo:
        gw.send(
            OutboundMessage(
                chat_id=100,
                text="x",
                attachments=[OutboundAttachment(path=img)],
            )
        )
    assert "TEST_TOKEN" not in str(excinfo.value)


def test_network_error_does_not_leak_token():
    """network error（httpx.RequestError）時、例外に bot token / URL が漏れない。

    全メソッド共通の `_request_with_retry` の network error 経路を sendMessage で代表検証。
    実ライブラリが URL をエラーメッセージに含めても、`from None` で chain を切り redact する
    （media_downloader の network error 経路と同型）。
    """

    def handler(request: httpx.Request) -> httpx.Response:
        # 実ライブラリが URL（token 込み）をエラーメッセージに含めるケースを再現
        raise httpx.ConnectError(f"connect failed: {request.url}", request=request)

    gw = _gateway(handler, retry_count=0)
    with pytest.raises(TelegramSecretaryError) as excinfo:
        gw.send(OutboundMessage(chat_id=100, text="hi"))
    msg = str(excinfo.value)
    assert "TEST_TOKEN" not in msg
    assert "api.telegram.org/bot" not in msg
    # from None で chain を切り、traceback 経由の URL 露出も防ぐ
    assert excinfo.value.__cause__ is None
