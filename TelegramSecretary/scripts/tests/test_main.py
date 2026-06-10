from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

import adapters.telegram.api_gateway as gateway_module
from infrastructure.exit_codes import EXIT_FETCH_FAILED
from main import (
    EXIT_AUTH_FAILED,
    EXIT_CONFIG_INVALID,
    EXIT_LEASE_CONFLICT,
    EXIT_OK,
    main,
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for k in [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_SECRETARY_AUTHORIZED_CHATS",
        "TELEGRAM_SECRETARY_STATE_DIR",
        "TELEGRAM_SECRETARY_SESSION_ID",
    ]:
        monkeypatch.delenv(k, raising=False)


@pytest.fixture
def env_ready(monkeypatch, tmp_path):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "TEST_TOKEN")
    monkeypatch.setenv("TELEGRAM_SECRETARY_AUTHORIZED_CHATS", "[100]")
    monkeypatch.setenv("TELEGRAM_SECRETARY_STATE_DIR", str(tmp_path))
    # config.json（非秘匿の正典、session_duration_sec 必須）を tmp に用意し決め打ちパスを差し替え
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"session_duration_sec": 7200}), encoding="utf-8")
    monkeypatch.setattr("infrastructure.config._default_config_path", lambda: cfg)
    return tmp_path


# --- validate-config ---


def test_validate_config_fails_when_env_missing(capsys):
    assert main(["validate-config"]) == EXIT_CONFIG_INVALID
    assert "TELEGRAM_BOT_TOKEN" in capsys.readouterr().err


def test_validate_config_succeeds(env_ready, capsys):
    assert main(["validate-config"]) == EXIT_OK
    assert "ok" in capsys.readouterr().out


def test_validate_config_invalid_json_chats(monkeypatch, tmp_path):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "TEST")
    monkeypatch.setenv("TELEGRAM_SECRETARY_AUTHORIZED_CHATS", "not json")
    monkeypatch.setenv("TELEGRAM_SECRETARY_STATE_DIR", str(tmp_path))
    assert main(["validate-config"]) == EXIT_CONFIG_INVALID


def test_validate_config_shows_session_duration(env_ready, capsys):
    """validate-config 出力に session_duration_sec が含まれる（config.json 由来）。"""
    assert main(["validate-config"]) == EXIT_OK
    assert "session_duration_sec=7200" in capsys.readouterr().out


# --- show-config ---


def test_show_config_displays_settings(env_ready, capsys):
    """現設定を表示し、秘匿（token）は値を出さずキー存在のみ。"""
    assert main(["show-config"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "session_duration_sec: 7200" in out
    assert "bot_token: set" in out
    assert "TEST_TOKEN" not in out  # 秘匿マスク（値が漏れない）


def test_show_config_when_not_ready_returns_ok(capsys):
    """env/config.json 未設定でも exit 0（read-only パネル、未設定を表示）。"""
    assert main(["show-config"]) == EXIT_OK
    assert "config not ready" in capsys.readouterr().out


# --- init-config ---


def test_init_config_writes_file(monkeypatch, tmp_path):
    """引数から config.json を生成（config ロード不要、書くだけ）。"""
    target = tmp_path / "config.json"
    monkeypatch.setattr("infrastructure.config._default_config_path", lambda: target)
    rc = main(["init-config", "--session-duration-sec", "3600", "--agent-name", "Iris"])
    assert rc == EXIT_OK
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["session_duration_sec"] == 3600
    assert data["agent_name"] == "Iris"


def test_init_config_refuses_overwrite_without_force(monkeypatch, tmp_path):
    """既存 config.json は --force 無しで上書きしない（exit 2）。"""
    target = tmp_path / "config.json"
    target.write_text("{}", encoding="utf-8")
    monkeypatch.setattr("infrastructure.config._default_config_path", lambda: target)
    assert main(["init-config", "--session-duration-sec", "3600"]) == EXIT_CONFIG_INVALID


def test_init_config_force_overwrites(monkeypatch, tmp_path):
    """--force で既存を上書き。"""
    target = tmp_path / "config.json"
    target.write_text("{}", encoding="utf-8")
    monkeypatch.setattr("infrastructure.config._default_config_path", lambda: target)
    assert main(["init-config", "--session-duration-sec", "3600", "--force"]) == EXIT_OK
    assert json.loads(target.read_text(encoding="utf-8"))["session_duration_sec"] == 3600


def test_init_config_rejects_out_of_range(monkeypatch, tmp_path):
    """範囲外（>86400）は生成前に弾く（ファイルを作らない）。"""
    target = tmp_path / "config.json"
    monkeypatch.setattr("infrastructure.config._default_config_path", lambda: target)
    assert main(["init-config", "--session-duration-sec", "99999"]) == EXIT_CONFIG_INVALID
    assert not target.exists()


def test_init_config_default_matches_template(monkeypatch, tmp_path):
    """フラグ省略時の既定値は雛型既定 14400（=4h）と一致する（v1.2.1 統一の取りこぼし防止）。"""
    target = tmp_path / "config.json"
    monkeypatch.setattr("infrastructure.config._default_config_path", lambda: target)
    assert main(["init-config"]) == EXIT_OK
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["session_duration_sec"] == 14400


# --- lease ---


def test_lease_acquire_then_release(env_ready, capsys):
    assert main(["lease", "acquire", "--owner", "S1", "--ttl", "120"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "acquired" in out

    assert main(["lease", "release", "--owner", "S1"]) == EXIT_OK


def test_lease_acquire_conflict(env_ready):
    assert main(["lease", "acquire", "--owner", "S1", "--ttl", "120"]) == EXIT_OK
    # 別 owner が fresh lease を奪取しようとすると conflict
    rc = main(["lease", "acquire", "--owner", "S2", "--ttl", "120"])
    assert rc == EXIT_LEASE_CONFLICT


def test_lease_renew_without_existing_lease(env_ready):
    rc = main(["lease", "renew", "--owner", "S1"])
    assert rc == EXIT_LEASE_CONFLICT


# --- poll (TelegramApiGateway をモック) ---


def _install_mock_transport(monkeypatch, handler):
    """TelegramApiGateway が内部で作る httpx.Client を MockTransport で置換。"""
    original_init = gateway_module.TelegramApiGateway.__init__

    def patched_init(
        self,
        bot_token,
        base_url=gateway_module.TelegramApiGateway.DEFAULT_BASE_URL,
        client=None,
        retry_count=2,
        request_timeout=40.0,
    ):
        if client is None:
            client = httpx.Client(transport=httpx.MockTransport(handler))
        original_init(
            self,
            bot_token=bot_token,
            base_url=base_url,
            client=client,
            retry_count=retry_count,
            request_timeout=request_timeout,
        )

    monkeypatch.setattr(gateway_module.TelegramApiGateway, "__init__", patched_init)


def test_poll_emits_authorized_updates(env_ready, monkeypatch, capsys):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": [
                    {
                        "update_id": 1,
                        "message": {
                            "chat": {"id": 100},
                            "from": {"id": 200, "username": "test_user"},
                            "text": "hi",
                        },
                    },
                    {
                        "update_id": 2,
                        "message": {
                            "chat": {"id": 999},  # 未認可
                            "from": {"id": 300, "username": "stranger"},
                            "text": "nope",
                        },
                    },
                ],
            },
        )

    _install_mock_transport(monkeypatch, handler)
    rc = main(["poll", "--timeout", "1"])
    assert rc == EXIT_OK
    out = capsys.readouterr().out.strip().split("\n")
    assert len(out) == 1  # 認可済みのみ
    payload = json.loads(out[0])
    assert payload["chat_id"] == 100
    assert payload["text"] == "hi"


def test_poll_returns_auth_failed_on_401(env_ready, monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="Unauthorized")

    _install_mock_transport(monkeypatch, handler)
    assert main(["poll", "--timeout", "1"]) == EXIT_AUTH_FAILED


# --- watch (max-iterations=1 で停止) ---


def test_watch_runs_one_iteration_and_exits(env_ready, monkeypatch, capsys):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": []})

    _install_mock_transport(monkeypatch, handler)
    # watch はサイクル末尾で lease renew するため、事前 acquire が必要
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    rc = main(["watch", "--timeout", "1", "--max-iterations", "1", "--owner", "S1"])
    assert rc == EXIT_OK


def test_watch_exits_4_when_no_lease(env_ready, monkeypatch):
    """事前 acquire 無しで watch を回すと、renew 段階で exit 4 を返す（並走奪取の自己治癒経路の入口）。"""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": []})

    _install_mock_transport(monkeypatch, handler)
    rc = main(["watch", "--timeout", "1", "--max-iterations", "1", "--owner", "S1"])
    assert rc == EXIT_LEASE_CONFLICT


def test_watch_exits_4_when_lease_stolen(env_ready, monkeypatch):
    """watch 中に lease が他人に奪われていた場合、renew で exit 4。"""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": []})

    _install_mock_transport(monkeypatch, handler)
    # 別 owner が lease を保持している状態を作る
    assert main(["lease", "acquire", "--owner", "OTHER"]) == EXIT_OK
    # 自分の owner で watch を回そうとすると renew が刺さる
    rc = main(["watch", "--timeout", "1", "--max-iterations", "1", "--owner", "S1"])
    assert rc == EXIT_LEASE_CONFLICT


# --- watch (--max-duration で wall-clock 自然停止) ---


def test_watch_stops_after_max_duration(env_ready, monkeypatch):
    """--max-duration 経過で wall-clock 自然終了（exit 0）。max-iterations 未指定でも時間で止まる。

    RenewLease は owner 一致のみ確認し is_stale を見ない（renew_lease.py）ため、
    acquire を実時刻で行い watch だけ fake clock にしても renew は成功する。
    """
    import itertools
    from datetime import datetime, timedelta, timezone

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": []})

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    # acquire 後に patch（acquire の utc_now を汚染しない）。
    # watch 内の utc_now: window生成(base+0) → renew(base+1000) → is_expired(base+2000)。
    # 2000s > 窓 580s ゆえ 1 サイクル後に break。
    base = datetime(2026, 5, 26, 12, 0, 0, tzinfo=timezone.utc)
    counter = itertools.count()
    monkeypatch.setattr(
        "main.utc_now", lambda: base + timedelta(seconds=1000 * next(counter))
    )
    rc = main(["watch", "--timeout", "1", "--max-duration", "580", "--owner", "S1"])
    assert rc == EXIT_OK


def test_watch_max_duration_zero_is_infinite_backward_compat(env_ready, monkeypatch):
    """--max-duration 0（既定）は無限窓。--max-iterations 1 で従来どおり 1 周（後方互換）。"""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": []})

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    rc = main(
        [
            "watch",
            "--timeout",
            "1",
            "--max-iterations",
            "1",
            "--max-duration",
            "0",
            "--owner",
            "S1",
        ]
    )
    assert rc == EXIT_OK


# --- watch (--exit-on-message で early-exit→返信→再起動 運用) ---


def test_watch_exit_on_message_breaks_after_emit(env_ready, monkeypatch):
    """--exit-on-message: 認可済みメッセージを emit したサイクルで exit 0。

    D 運用（メッセージ受信で foreground watch を畳む→返信→再起動）の核。
    max-iterations 5 は無限ループ保険。early-exit が効けば 1 サイクル目の emit で
    break するため getUpdates は 1 回しか呼ばれない。
    """
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": [
                    {
                        "update_id": 1,
                        "message": {
                            "chat": {"id": 100},
                            "from": {"id": 200, "username": "test_user"},
                            "text": "hi",
                        },
                    }
                ],
            },
        )

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    rc = main(
        [
            "watch",
            "--timeout",
            "1",
            "--exit-on-message",
            "--max-iterations",
            "5",
            "--owner",
            "S1",
        ]
    )
    assert rc == EXIT_OK
    assert calls["n"] == 1  # 1 サイクル目の emit で break（max-iterations 5 に達しない）


def test_watch_exit_on_message_continues_when_no_message(env_ready, monkeypatch):
    """--exit-on-message でもメッセージが無いサイクルでは早期終了しない（誤発火しない）。

    空 result が続く間は窓/回数まで回り続ける。max-iterations 2 まで getUpdates が呼ばれる。
    """
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={"ok": True, "result": []})

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    rc = main(
        [
            "watch",
            "--timeout",
            "1",
            "--exit-on-message",
            "--max-iterations",
            "2",
            "--owner",
            "S1",
        ]
    )
    assert rc == EXIT_OK
    assert calls["n"] == 2  # メッセージ無しでは exit-on-message 発火せず 2 サイクル回る


# --- watch (Heavy モード media stack の遅延構築 / FINDING A) ---


def test_watch_heavy_mode_no_media_does_not_build_renderer(env_ready, monkeypatch):
    """Heavy モードでも media を受けないサイクルでは renderer/transcriber を構築しない（遅延構築）。

    fresh container では bootstrap が httpx しか入れない。watch が起動時に renderer を eager 構築すると
    markitdown / moonshine を import して ModuleNotFoundError で落ちる（FINDING A、E2E Phase 0 で顕在化）。
    media を実際に受けるまで構築を遅延すれば、media 無しの常駐は httpx だけで起動できる。
    """
    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD", "true")
    import adapters.render.markitdown_renderer as mr_mod

    def _boom(*args, **kwargs):
        raise AssertionError("renderer must not be constructed without media (lazy)")

    monkeypatch.setattr(mr_mod, "MarkitdownRenderer", _boom)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": [
                    {
                        "update_id": 1,
                        "message": {
                            "chat": {"id": 100},
                            "from": {"id": 200, "username": "test_user"},
                            "text": "hi",
                        },
                    }
                ],
            },
        )

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    rc = main(["watch", "--timeout", "1", "--max-iterations", "1", "--owner", "S1"])
    assert rc == EXIT_OK


def test_watch_heavy_without_moonshine_does_not_crash(env_ready, monkeypatch):
    """moonshine 未導入（BUNDLE_VOICE=false 相当）でも Heavy watch は落ちない（FINDING B: moonshine opt-out）。

    _ensure_media_stack は transcriber(moonshine) を optional に try-import する。未導入なら
    transcriber=None で render stack を構築し、音声だけ skipped にフォールバック（markitdown render は維持）。
    photo は size 超過で download skip させ getFile を回避（_ensure 自体は media 受信サイクルで発火）。
    """
    import sys

    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD", "true")
    # moonshine を未導入として模す（from ... import で ImportError）
    monkeypatch.setitem(sys.modules, "adapters.transcribe.moonshine_transcriber", None)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": [
                    {
                        "update_id": 1,
                        "message": {
                            "chat": {"id": 100},
                            "from": {"id": 200, "username": "test_user"},
                            "photo": [{"file_id": "X", "file_size": 99999999}],
                        },
                    }
                ],
            },
        )

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    rc = main(["watch", "--timeout", "1", "--max-iterations", "1", "--owner", "S1"])
    assert rc == EXIT_OK


# --- watch (FINDING C: 最終サイクルの long-poll を残り窓に丸める) ---


def test_watch_caps_poll_timeout_to_remaining_window(env_ready, monkeypatch):
    """残り窓 < --timeout の最終サイクルでは long-poll timeout を残り窓に丸める（FINDING C）。

    max_duration + timeout が bash timeout(600s) を超えると、厳密 foreground では window 満了を
    超えて回り SIGTERM(143) される（Phase 2 で実測 603s）。最終 long-poll を残り窓に丸めることで
    満了が max_duration をほぼ超えず、値(580/30)に依存せず max_duration + timeout < bash_timeout を保つ。
    """
    import itertools
    from datetime import datetime, timedelta, timezone

    import usecases.fetch_authorized_updates as fau

    captured: list[int] = []

    def spy_execute(self, timeout_seconds):
        captured.append(timeout_seconds)
        return []

    monkeypatch.setattr(fau.FetchAuthorizedUpdates, "execute", spy_execute)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": []})

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    # window=10s, --timeout=30s。fake clock は呼び出し毎に +5s 進む。
    # window生成(base) → poll_timeout 計算(base+5, remaining=5) ゆえ残り窓5 < 30 で丸まる。
    base = datetime(2026, 5, 29, 12, 0, 0, tzinfo=timezone.utc)
    counter = itertools.count()
    monkeypatch.setattr(
        "main.utc_now", lambda: base + timedelta(seconds=5 * next(counter))
    )
    rc = main(["watch", "--timeout", "30", "--max-duration", "10", "--owner", "S1"])
    assert rc == EXIT_OK
    # 最初の long-poll は残り窓(≈5s)に丸められ、--timeout(30) 未満になる
    assert captured[0] < 30
    assert captured[0] >= 1


# --- send-reply ---


def test_send_reply_requires_lease(env_ready, monkeypatch, tmp_path):
    text_file = tmp_path / "reply.txt"
    text_file.write_text("hello", encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": {}})

    _install_mock_transport(monkeypatch, handler)
    rc = main(
        [
            "send-reply",
            "--chat-id",
            "100",
            "--update-id",
            "1",
            "--text-file",
            str(text_file),
        ]
    )
    assert rc == EXIT_LEASE_CONFLICT


def test_send_reply_after_lease_acquire(env_ready, monkeypatch, tmp_path, capsys):
    text_file = tmp_path / "reply.txt"
    text_file.write_text("hello", encoding="utf-8")

    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if "sendMessage" in str(request.url):
            captured["body"] = json.loads(request.read())
        return httpx.Response(200, json={"ok": True, "result": {}})

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    rc = main(
        [
            "send-reply",
            "--chat-id",
            "100",
            "--update-id",
            "1",
            "--text-file",
            str(text_file),
            "--owner",
            "S1",
        ]
    )
    assert rc == EXIT_OK
    assert captured["body"]["chat_id"] == 100
    assert captured["body"]["text"] == "hello"


def test_send_reply_fails_when_owner_mismatch(env_ready, monkeypatch, tmp_path):
    """別 owner の lease で send-reply は exit 4（CLI 層の防御）。"""
    text_file = tmp_path / "reply.txt"
    text_file.write_text("hello", encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": {}})

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    rc = main(
        [
            "send-reply",
            "--chat-id",
            "100",
            "--update-id",
            "1",
            "--text-file",
            str(text_file),
            "--owner",
            "S2",
        ]
    )
    assert rc == EXIT_LEASE_CONFLICT


def test_send_reply_uses_env_owner(env_ready, monkeypatch, tmp_path):
    """env で TELEGRAM_SECRETARY_SESSION_ID を export すれば --owner 省略可 (運用律 B 案)。"""
    text_file = tmp_path / "reply.txt"
    text_file.write_text("hello", encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": {}})

    _install_mock_transport(monkeypatch, handler)
    # bootstrap.sh が export する状況を再現
    monkeypatch.setenv("TELEGRAM_SECRETARY_SESSION_ID", "S-env")
    # --owner 省略、env 経由で同じ owner を共有
    assert main(["lease", "acquire"]) == EXIT_OK
    rc = main(
        [
            "send-reply",
            "--chat-id",
            "100",
            "--update-id",
            "1",
            "--text-file",
            str(text_file),
        ]
    )
    assert rc == EXIT_OK


# --- Stage 8.4: send-reply --file / --reply-to ---


def test_send_reply_with_file_uses_sendphoto(env_ready, monkeypatch, tmp_path):
    text_file = tmp_path / "reply.txt"
    text_file.write_text("caption", encoding="utf-8")
    img = tmp_path / "fig.png"
    img.write_bytes(b"\x89PNG\r\n")
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200, json={"ok": True, "result": {}})

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    rc = main(
        [
            "send-reply",
            "--chat-id",
            "100",
            "--update-id",
            "1",
            "--text-file",
            str(text_file),
            "--owner",
            "S1",
            "--file",
            str(img),
        ]
    )
    assert rc == EXIT_OK
    assert any("sendPhoto" in c for c in calls)


def test_send_reply_missing_file_exits_config_invalid(env_ready, monkeypatch, tmp_path):
    text_file = tmp_path / "reply.txt"
    text_file.write_text("x", encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": {}})

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    rc = main(
        [
            "send-reply",
            "--chat-id",
            "100",
            "--update-id",
            "1",
            "--text-file",
            str(text_file),
            "--owner",
            "S1",
            "--file",
            str(tmp_path / "nonexistent.png"),
        ]
    )
    # 存在しない添付は送信前に弾く（入力不正 = exit 2）
    assert rc == EXIT_CONFIG_INVALID


def test_send_reply_missing_text_file_exits_config_invalid(env_ready, capsys, tmp_path):
    """--text-file 不在は traceback でなく stderr 1 行＋exit 2（入力不正）。

    lease 検証・API 呼び出しの前に読むため、transport モックも lease も不要。
    """
    rc = main(
        [
            "send-reply",
            "--chat-id",
            "100",
            "--update-id",
            "1",
            "--text-file",
            str(tmp_path / "missing.txt"),
        ]
    )
    assert rc == EXIT_CONFIG_INVALID
    assert "text-file" in capsys.readouterr().err


def test_proactive_send_missing_text_file_exits_config_invalid(
    env_ready, capsys, tmp_path
):
    """proactive-send も同じ共有ヘルパで --text-file 不在を exit 2 に翻訳する。"""
    rc = main(
        [
            "proactive-send",
            "--chat-id",
            "100",
            "--text-file",
            str(tmp_path / "missing.txt"),
        ]
    )
    assert rc == EXIT_CONFIG_INVALID
    assert "text-file" in capsys.readouterr().err


def test_send_reply_with_reply_to(env_ready, monkeypatch, tmp_path):
    text_file = tmp_path / "reply.txt"
    text_file.write_text("threaded", encoding="utf-8")
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if "sendMessage" in str(request.url):
            captured["body"] = json.loads(request.read())
        return httpx.Response(200, json={"ok": True, "result": {}})

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    rc = main(
        [
            "send-reply",
            "--chat-id",
            "100",
            "--update-id",
            "1",
            "--text-file",
            str(text_file),
            "--owner",
            "S1",
            "--reply-to",
            "42",
        ]
    )
    assert rc == EXIT_OK
    assert captured["body"]["reply_to_message_id"] == 42


def test_watch_uses_env_owner(env_ready, monkeypatch):
    """env で session_id を export しておけば watch も同じ owner で renew する。"""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": []})

    _install_mock_transport(monkeypatch, handler)
    monkeypatch.setenv("TELEGRAM_SECRETARY_SESSION_ID", "S-env-watch")
    # --owner 省略、env 経由で acquire→watch が同じ owner を共有
    assert main(["lease", "acquire"]) == EXIT_OK
    rc = main(["watch", "--timeout", "1", "--max-iterations", "1"])
    assert rc == EXIT_OK


# --- Stage 6.4: Medium モード（download 無効）切替 ---


def test_poll_medium_mode_emits_media_without_local_path(
    env_ready, monkeypatch, capsys
):
    """media_enable_download=false: photo 付き update が来ても download せず、
    emit に local_path=None の media[] が乗る。getFile も呼ばれない。"""
    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD", "false")

    def handler(request: httpx.Request) -> httpx.Response:
        # Medium モードでは getFile は絶対呼ばれない
        assert "getFile" not in str(request.url)
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": [
                    {
                        "update_id": 1,
                        "message": {
                            "chat": {"id": 100},
                            "from": {"id": 200, "username": "test_user"},
                            "photo": [{"file_id": "AgACphoto", "file_size": 4096}],
                            "caption": "見て",
                        },
                    },
                ],
            },
        )

    _install_mock_transport(monkeypatch, handler)
    rc = main(["poll", "--timeout", "1"])
    assert rc == EXIT_OK
    out = capsys.readouterr().out.strip()
    payload = json.loads(out)
    # caption は text に統合
    assert payload["text"] == "見て"
    # media は出るが local_path は None（Medium モード）
    assert len(payload["media"]) == 1
    assert payload["media"][0]["kind"] == "photo"
    assert payload["media"][0]["file_id"] == "AgACphoto"
    assert payload["media"][0]["local_path"] is None
    assert payload["media"][0]["skip_reason"] is None


def test_poll_medium_mode_text_only_unchanged(env_ready, monkeypatch, capsys):
    """media なし text-only update でも Medium モードで Stage 5 と同等に動く。"""
    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD", "false")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": [
                    {
                        "update_id": 1,
                        "message": {
                            "chat": {"id": 100},
                            "from": {"id": 200, "username": "test_user"},
                            "text": "hi",
                        },
                    },
                ],
            },
        )

    _install_mock_transport(monkeypatch, handler)
    rc = main(["poll", "--timeout", "1"])
    assert rc == EXIT_OK
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["text"] == "hi"
    assert payload["media"] == []


def test_watch_medium_mode_does_not_call_getfile(env_ready, monkeypatch):
    """watch の Medium モードでも getFile を呼ばない（fetch のみ）。"""
    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD", "false")
    monkeypatch.setenv("TELEGRAM_SECRETARY_SESSION_ID", "S-medium-watch")

    def handler(request: httpx.Request) -> httpx.Response:
        assert "getFile" not in str(request.url)
        return httpx.Response(200, json={"ok": True, "result": []})

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire"]) == EXIT_OK
    rc = main(["watch", "--timeout", "1", "--max-iterations", "1"])
    assert rc == EXIT_OK


# --- Stage 6.5 follow-up: caption が CLI 層を通って emit text に乗る E2E ---


def test_poll_emits_caption_in_text_with_photo(env_ready, monkeypatch, capsys):
    """photo + caption の payload で emit `text` に caption が統合されることを CLI 経由で検証。

    Stage 6.5 follow-up: ユニットテスト（test_caption_is_merged_into_normalized_text）は
    通っていたが、CLI 層を通した end-to-end は欠けていた。Live E2E で "text:\"\"" だった
    報告（caption "見える？" 送信疑い）の切り分け用ベースラインを明示。
    """
    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD", "false")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": [
                    {
                        "update_id": 1,
                        "message": {
                            "chat": {"id": 100},
                            "from": {"id": 200, "username": "test_user"},
                            "photo": [{"file_id": "photo1", "file_size": 4096}],
                            "caption": "見える？",
                        },
                    },
                ],
            },
        )

    _install_mock_transport(monkeypatch, handler)
    rc = main(["poll", "--timeout", "1"])
    assert rc == EXIT_OK
    payload = json.loads(capsys.readouterr().out.strip())
    # caption も text と同じ NFKC 正規化を通る（全角「？」→ 半角「?」）
    assert payload["text"] == "見える?"
    assert len(payload["media"]) == 1
    assert payload["media"][0]["kind"] == "photo"


def test_poll_caption_above_text_for_text_message_with_caption(
    env_ready, monkeypatch, capsys
):
    """text + caption 両方ある稀ケースでも caption が上段、text が下段で結合される。"""
    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD", "false")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": [
                    {
                        "update_id": 1,
                        "message": {
                            "chat": {"id": 100},
                            "from": {"id": 200},
                            "text": "本文",
                            "caption": "見出し",
                        },
                    },
                ],
            },
        )

    _install_mock_transport(monkeypatch, handler)
    assert main(["poll", "--timeout", "1"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["text"] == "見出し\n本文"


# --- Stage 6.5 follow-up: cleanup-media subcommand + watch cleanup hook ---


def test_cleanup_media_subcommand_removes_expired_files(
    env_ready, monkeypatch, capsys, tmp_path
):
    """cleanup-media subcommand が retention 超過のファイルを削除し、新しいファイルは残す。"""
    import os
    import time

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    old = media_dir / "old.jpg"
    fresh = media_dir / "fresh.jpg"
    old.write_bytes(b"a")
    fresh.write_bytes(b"b")
    # default retention=24h、old は 2日前にする
    two_days_ago = time.time() - 2 * 86400
    os.utime(old, (two_days_ago, two_days_ago))

    rc = main(["cleanup-media"])
    assert rc == EXIT_OK
    assert not old.exists()
    assert fresh.exists()
    assert "cleaned 1" in capsys.readouterr().out


def test_cleanup_media_subcommand_no_op_when_media_dir_missing(
    env_ready, monkeypatch, capsys, tmp_path
):
    """state_dir/media/ が存在しない時は 0 件で正常終了。"""
    # media/ を意図的に作らない
    rc = main(["cleanup-media"])
    assert rc == EXIT_OK
    assert "cleaned 0" in capsys.readouterr().out


def test_watch_runs_cleanup_hook_at_interval(env_ready, monkeypatch, tmp_path):
    """watch ループが cleanup_interval サイクル毎に cleanup_media_dir を呼ぶ。"""
    import os
    import time

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    old = media_dir / "old.jpg"
    old.write_bytes(b"x")
    two_days_ago = time.time() - 2 * 86400
    os.utime(old, (two_days_ago, two_days_ago))

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": []})

    _install_mock_transport(monkeypatch, handler)
    monkeypatch.setenv("TELEGRAM_SECRETARY_SESSION_ID", "S-cleanup-hook")
    assert main(["lease", "acquire"]) == EXIT_OK
    # cleanup-interval=1 で 1 サイクル目に即 cleanup 発火
    rc = main(
        [
            "watch",
            "--timeout",
            "1",
            "--max-iterations",
            "1",
            "--cleanup-interval",
            "1",
        ]
    )
    assert rc == EXIT_OK
    # 古いファイルは消えている
    assert not old.exists()


# --- Stage 7.4: Medium モードで render フィールドが null で出る後方互換 ---


def test_poll_medium_mode_renders_null_for_photo(env_ready, monkeypatch, capsys):
    """Medium モード + photo: render_status / rendered_text が null（render は呼ばれない）。"""
    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD", "false")

    def handler(request: httpx.Request) -> httpx.Response:
        # Medium モードでは render 配線も skip されるため、markitdown 関連 API は呼ばれない
        assert "getFile" not in str(request.url)
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": [
                    {
                        "update_id": 1,
                        "message": {
                            "chat": {"id": 100},
                            "from": {"id": 200},
                            "photo": [{"file_id": "P", "file_size": 4096}],
                        },
                    },
                ],
            },
        )

    _install_mock_transport(monkeypatch, handler)
    rc = main(["poll", "--timeout", "1"])
    assert rc == EXIT_OK
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["media"][0]["render_status"] is None
    assert payload["media"][0]["rendered_text"] is None
    # file_name は MediaAttachment から、photo は None（Stage 7.1）
    assert payload["media"][0]["file_name"] is None


def test_poll_medium_mode_file_name_for_document(env_ready, monkeypatch, capsys):
    """Medium モード + document: file_name が乗る、render は null。"""
    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD", "false")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": [
                    {
                        "update_id": 1,
                        "message": {
                            "chat": {"id": 100},
                            "from": {"id": 200},
                            "document": {
                                "file_id": "D",
                                "mime_type": "application/pdf",
                                "file_size": 4096,
                                "file_name": "report.pdf",
                            },
                        },
                    },
                ],
            },
        )

    _install_mock_transport(monkeypatch, handler)
    assert main(["poll", "--timeout", "1"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["media"][0]["file_name"] == "report.pdf"
    assert payload["media"][0]["render_status"] is None  # Medium モード


def test_watch_skips_cleanup_when_interval_zero(env_ready, monkeypatch, tmp_path):
    """--cleanup-interval=0 で cleanup hook を無効化。"""
    import os
    import time

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    old = media_dir / "old.jpg"
    old.write_bytes(b"x")
    os.utime(old, (time.time() - 2 * 86400, time.time() - 2 * 86400))

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": []})

    _install_mock_transport(monkeypatch, handler)
    monkeypatch.setenv("TELEGRAM_SECRETARY_SESSION_ID", "S-no-cleanup")
    assert main(["lease", "acquire"]) == EXIT_OK
    rc = main(
        [
            "watch",
            "--timeout",
            "1",
            "--max-iterations",
            "1",
            "--cleanup-interval",
            "0",
        ]
    )
    assert rc == EXIT_OK
    # cleanup 無効なのでファイルは残る
    assert old.exists()


# --- Stage 9.3: 受信基盤 CLI 実証（voice / video が emit に kind 付きで乗る）---


def test_poll_medium_mode_emits_voice(env_ready, monkeypatch, capsys):
    """Medium モード: voice update が kind=voice で emit に乗る（受信基盤・公式同等）。

    Heavy モードの transcribe は adapter テスト（9.5b）＋実 E2E で検証するため、
    ここでは download/transcribe を起動しない Medium モードで受信認識のみを固める。
    """
    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD", "false")

    def handler(request: httpx.Request) -> httpx.Response:
        assert "getFile" not in str(request.url)  # Medium モードは download しない
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": [
                    {
                        "update_id": 1,
                        "message": {
                            "chat": {"id": 100},
                            "from": {"id": 200, "username": "test_user"},
                            "voice": {
                                "file_id": "AwACvoice",
                                "duration": 5,
                                "mime_type": "audio/ogg",
                                "file_size": 8192,
                            },
                            "caption": "聞いて",
                        },
                    },
                ],
            },
        )

    _install_mock_transport(monkeypatch, handler)
    rc = main(["poll", "--timeout", "1"])
    assert rc == EXIT_OK
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["text"] == "聞いて"  # caption が text に統合
    assert len(payload["media"]) == 1
    assert payload["media"][0]["kind"] == "voice"
    assert payload["media"][0]["file_id"] == "AwACvoice"
    assert payload["media"][0]["mime_type"] == "audio/ogg"
    assert payload["media"][0]["local_path"] is None  # Medium
    assert payload["media"][0]["render_status"] is None  # Medium は render/transcribe しない


def test_poll_medium_mode_emits_video(env_ready, monkeypatch, capsys):
    """Medium モード: video update が kind=video で emit（音声 transcript は Heavy/9.6）。"""
    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD", "false")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": [
                    {
                        "update_id": 1,
                        "message": {
                            "chat": {"id": 100},
                            "from": {"id": 200},
                            "video": {
                                "file_id": "BAADvideo",
                                "duration": 30,
                                "mime_type": "video/mp4",
                                "file_size": 1000000,
                            },
                        },
                    },
                ],
            },
        )

    _install_mock_transport(monkeypatch, handler)
    assert main(["poll", "--timeout", "1"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["media"][0]["kind"] == "video"
    assert payload["media"][0]["mime_type"] == "video/mp4"
    assert payload["media"][0]["local_path"] is None


# --- Stage 11.4: cmd_poll が PDF cap を PdfRenderer に渡す配線 ---


def test_poll_heavy_passes_pdf_cap_to_renderer(env_ready, monkeypatch):
    """cmd_poll の Heavy 分岐で PdfRenderer が config.pdf_image_max_pages 付きで構築される。

    markitdown/moonshine の重い __init__（magika 等）は軽量 stub に置換し、PdfRenderer の
    構築引数だけをスパイ。photo を size 超過にして download skip させ getFile/render を回避。
    """
    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD", "true")
    monkeypatch.setenv("TELEGRAM_SECRETARY_PDF_IMAGE_MAX_PAGES", "7")

    import adapters.render.markitdown_renderer as mr_mod
    import adapters.transcribe.moonshine_transcriber as mt_mod
    import adapters.render.pdf_renderer as pdf_mod

    monkeypatch.setattr(mr_mod, "MarkitdownRenderer", lambda: object())
    monkeypatch.setattr(mt_mod, "MoonshineTranscriber", lambda: object())

    captured: dict = {}
    real_pdf_renderer = pdf_mod.PdfRenderer

    def spy(image_max_pages=20):
        captured["cap"] = image_max_pages
        return real_pdf_renderer(image_max_pages=image_max_pages)

    monkeypatch.setattr(pdf_mod, "PdfRenderer", spy)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": [
                    {
                        "update_id": 1,
                        "message": {
                            "chat": {"id": 100},
                            "from": {"id": 200},
                            "photo": [{"file_id": "X", "file_size": 99999999}],
                        },
                    }
                ],
            },
        )

    _install_mock_transport(monkeypatch, handler)
    assert main(["poll", "--timeout", "1"]) == EXIT_OK
    assert captured["cap"] == 7


# --- Stage 11.5: render-pdf オンデマンドコマンド（--text 全文 / --pages 個別画像）---


def _write_text_pdf(path: Path, lines) -> None:
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path))
    c.setFont("Helvetica", 14)
    y = 800
    for ln in lines:
        c.drawString(50, y, ln)
        y -= 24
    c.showPage()
    c.save()


def _write_blank_pdf(path: Path, n: int) -> None:
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path))
    for _ in range(n):
        c.showPage()
    c.save()


def test_render_pdf_text_mode_outputs_json(env_ready, tmp_path, capsys):
    """render-pdf --text → JSON 1行で全文テキスト + page_count。"""
    pdf = tmp_path / "doc.pdf"
    _write_text_pdf(pdf, ["Hello render-pdf text"])
    assert main(["render-pdf", "--path", str(pdf), "--text"]) == EXIT_OK
    out = json.loads(capsys.readouterr().out.strip())
    assert out["mode"] == "text"
    assert out["render_status"] == "ok"
    assert out["page_count"] == 1
    assert "Hello render-pdf text" in out["rendered_text"]


def test_render_pdf_pages_mode_outputs_paths(env_ready, tmp_path, capsys):
    """render-pdf --pages 1-2 → JSON 1行で derived_image_paths（実在 png）。"""
    pdf = tmp_path / "scan.pdf"
    _write_blank_pdf(pdf, 3)
    assert main(["render-pdf", "--path", str(pdf), "--pages", "1-2"]) == EXIT_OK
    out = json.loads(capsys.readouterr().out.strip())
    assert out["mode"] == "pages"
    assert len(out["derived_image_paths"]) == 2
    for p in out["derived_image_paths"]:
        assert Path(p).exists()


def test_render_pdf_missing_file_returns_config_invalid(env_ready, tmp_path):
    """存在しない PDF → EXIT_CONFIG_INVALID（クラッシュさせない）。"""
    assert (
        main(["render-pdf", "--path", str(tmp_path / "nope.pdf"), "--text"])
        == EXIT_CONFIG_INVALID
    )


def test_render_pdf_invalid_pages_format_exits_config_invalid(
    env_ready, capsys, tmp_path
):
    """--pages 不正書式（abc）は traceback でなく stderr 1 行＋exit 2（入力不正）。"""
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4")  # 存在チェック通過用ダミー（parse で弾かれ rasterize 不到達）
    rc = main(["render-pdf", "--path", str(pdf), "--pages", "abc"])
    assert rc == EXIT_CONFIG_INVALID
    assert "pages" in capsys.readouterr().err


def test_render_pdf_requires_text_or_pages(tmp_path):
    """--text も --pages も無い → mutually exclusive required で SystemExit。"""
    pdf = tmp_path / "doc.pdf"
    _write_text_pdf(pdf, ["x"])
    with pytest.raises(SystemExit):
        main(["render-pdf", "--path", str(pdf)])


def test_parse_page_range():
    """_parse_page_range: 1-indexed inclusive → 0-indexed [start, end)。"""
    from main import _parse_page_range

    assert _parse_page_range("21-22") == (20, 22)
    assert _parse_page_range("21") == (20, 21)
    assert _parse_page_range("1-3") == (0, 3)
    start, end = _parse_page_range("21-")
    assert start == 20 and end >= 22


# --- proactive-send（offset 非干渉の能動 outbound）---


def test_proactive_send_wal_gate_then_send_then_settle(env_ready, monkeypatch):
    """WAL ライフサイクル内包: append（送信前ゲート）→ 送信 → settle（happy-path）の順序で配線する。"""
    calls: list = []

    def fake_append(*a, **k):
        calls.append("append")
        return True, "K1"

    def fake_settle(config, key, **k):
        calls.append(("settle", key))

    monkeypatch.setattr("main.run_wal_append_outbound", fake_append)
    monkeypatch.setattr("main.run_wal_settle_outbound", fake_settle)

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append("send")
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    text_file = env_ready / "push.txt"
    text_file.write_text("能動メッセージ", encoding="utf-8")
    rc = main(
        ["proactive-send", "--chat-id", "100", "--text-file", str(text_file), "--owner", "S1"]
    )
    assert rc == EXIT_OK
    # append が先頭・settle が末尾（送信は両者の間）、settle に append の created_at キーが渡る
    assert calls[0] == "append"
    assert calls[-1] == ("settle", "K1")
    assert "send" in calls


def test_proactive_send_aborts_when_wal_push_fails(env_ready, monkeypatch):
    """WAL push 失敗（送信前ゲート）→ 送信せず・settle せず exit 非0（push できないなら送らない）。"""
    monkeypatch.setattr("main.run_wal_append_outbound", lambda *a, **k: (False, "K1"))
    settled: list = []
    monkeypatch.setattr("main.run_wal_settle_outbound", lambda *a, **k: settled.append(1))
    sent: list = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(1)
        return httpx.Response(200, json={"ok": True, "result": {}})

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    text_file = env_ready / "push.txt"
    text_file.write_text("hi", encoding="utf-8")
    rc = main(
        ["proactive-send", "--chat-id", "100", "--text-file", str(text_file), "--owner", "S1"]
    )
    assert rc == EXIT_FETCH_FAILED
    assert sent == []  # 送信されない（送信前ゲートで止まる）
    assert settled == []  # settle も呼ばれない


def test_proactive_send_requires_lease(env_ready, monkeypatch, tmp_path):
    """lease 無しでは送信せず exit 4（send-reply と同じ CLI 層防御）。"""
    text_file = tmp_path / "push.txt"
    text_file.write_text("最近の Loop で面白い話が", encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": {}})

    _install_mock_transport(monkeypatch, handler)
    rc = main(["proactive-send", "--chat-id", "100", "--text-file", str(text_file)])
    assert rc == EXIT_LEASE_CONFLICT


def test_proactive_send_after_lease_acquire_omits_update_id(
    env_ready, monkeypatch, tmp_path, capsys
):
    """acquire 後に能動送信 → exit 0、body に chat_id/text、stdout に update_id を出さない。"""
    text_file = tmp_path / "push.txt"
    text_file.write_text("能動発信", encoding="utf-8")
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if "sendMessage" in str(request.url):
            captured["body"] = json.loads(request.read())
        return httpx.Response(200, json={"ok": True, "result": {}})

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    rc = main(
        [
            "proactive-send",
            "--chat-id",
            "100",
            "--text-file",
            str(text_file),
            "--owner",
            "S1",
        ]
    )
    assert rc == EXIT_OK
    assert captured["body"]["chat_id"] == 100
    assert captured["body"]["text"] == "能動発信"
    out = capsys.readouterr().out
    assert "sent chat_id=100" in out
    assert "update_id" not in out  # inbound セマンティクスを持ち込まない


def test_proactive_send_fails_when_owner_mismatch(env_ready, monkeypatch, tmp_path):
    """別 owner の lease で proactive-send は exit 4（並走奪取の二重 push 防止）。"""
    text_file = tmp_path / "push.txt"
    text_file.write_text("x", encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": {}})

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    rc = main(
        [
            "proactive-send",
            "--chat-id",
            "100",
            "--text-file",
            str(text_file),
            "--owner",
            "S2",
        ]
    )
    assert rc == EXIT_LEASE_CONFLICT


def test_proactive_send_missing_file_exits_config_invalid(
    env_ready, monkeypatch, tmp_path
):
    """存在しない添付は送信前に弾く（入力不正 = exit 2、send-reply と共通）。"""
    text_file = tmp_path / "push.txt"
    text_file.write_text("x", encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": {}})

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    rc = main(
        [
            "proactive-send",
            "--chat-id",
            "100",
            "--text-file",
            str(text_file),
            "--owner",
            "S1",
            "--file",
            str(tmp_path / "nonexistent.png"),
        ]
    )
    assert rc == EXIT_CONFIG_INVALID


def test_proactive_send_with_file_uses_sendphoto(env_ready, monkeypatch, tmp_path):
    """--file 添付の richness は send-reply と共通（画像は sendPhoto）。"""
    text_file = tmp_path / "push.txt"
    text_file.write_text("caption", encoding="utf-8")
    img = tmp_path / "fig.png"
    img.write_bytes(b"\x89PNG\r\n")
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200, json={"ok": True, "result": {}})

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    rc = main(
        [
            "proactive-send",
            "--chat-id",
            "100",
            "--text-file",
            str(text_file),
            "--owner",
            "S1",
            "--file",
            str(img),
        ]
    )
    assert rc == EXIT_OK
    assert any("sendPhoto" in c for c in calls)


def test_proactive_send_with_reply_to(env_ready, monkeypatch, tmp_path):
    """--reply-to も send-reply と共通で配線される。"""
    text_file = tmp_path / "push.txt"
    text_file.write_text("threaded", encoding="utf-8")
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if "sendMessage" in str(request.url):
            captured["body"] = json.loads(request.read())
        return httpx.Response(200, json={"ok": True, "result": {}})

    _install_mock_transport(monkeypatch, handler)
    assert main(["lease", "acquire", "--owner", "S1"]) == EXIT_OK
    rc = main(
        [
            "proactive-send",
            "--chat-id",
            "100",
            "--text-file",
            str(text_file),
            "--owner",
            "S1",
            "--reply-to",
            "42",
        ]
    )
    assert rc == EXIT_OK
    assert captured["body"]["reply_to_message_id"] == 42


def test_proactive_send_rejects_update_id_flag(env_ready, tmp_path):
    """proactive-send は --update-id を受け付けない（send-reply との差分の明示検証）。

    offset 非干渉ゆえ inbound の update_id セマンティクスを CLI からも排除する。
    argparse は未知フラグで SystemExit を出す。
    """
    text_file = tmp_path / "push.txt"
    text_file.write_text("x", encoding="utf-8")
    with pytest.raises(SystemExit):
        main(
            [
                "proactive-send",
                "--chat-id",
                "100",
                "--text-file",
                str(text_file),
                "--update-id",
                "1",
            ]
        )


# --- wal-append --kind outbound（proactive-send WAL 配線の parser 入口）---


def test_wal_append_accepts_outbound_kind(env_ready):
    """parser が --kind outbound を受け付ける（registry_sync 無効ゆえ no-op で exit 0）。

    outbound 送信ロスト対策で wal-append --kind outbound を ROUTINE_PROMPT が叩くための入口。
    registry_sync 無効環境では run_wal_append が no-op で素通り（後方互換）。
    """
    rc = main(
        ["wal-append", "--kind", "outbound", "--json", '{"chat_id": 100, "text": "hi"}']
    )
    assert rc == EXIT_OK
