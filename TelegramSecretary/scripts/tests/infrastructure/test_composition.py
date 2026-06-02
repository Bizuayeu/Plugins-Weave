"""Composition Root の単体テスト（Stage 3）。

load_config の fail-fast（union 廃止）と build_media_stack の配線（pdf cap 注入・
optional transcriber/pdf の None フォールバック）を pin する。重い renderer 構築は
stub に置換して軽量に検証する（実 markitdown/moonshine は test_main の E2E が担う）。
"""
from __future__ import annotations

import json
import sys

import pytest

from domain.authorization import AuthorizedChats
from infrastructure.composition import MediaStack, build_media_stack, load_config
from infrastructure.config import Config
from usecases.download_authorized_media import DownloadAuthorizedMedia
from usecases.render_authorized_media import RenderAuthorizedMedia


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for k in [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_SECRETARY_AUTHORIZED_CHATS",
        "TELEGRAM_SECRETARY_STATE_DIR",
    ]:
        monkeypatch.delenv(k, raising=False)


def test_load_config_raises_on_missing_env():
    """env 欠損で EnvironmentError を raise（union int を返さない＝fail-fast）。

    token チェックが config.json 読込より先なので、env 欠損で（config.json の有無に関わらず）raise。
    """
    with pytest.raises(EnvironmentError):
        load_config()


def test_load_config_returns_config_when_env_ready(monkeypatch, tmp_path):
    """env が揃い config.json があれば Config を返す。"""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "TEST")
    monkeypatch.setenv("TELEGRAM_SECRETARY_AUTHORIZED_CHATS", "[100]")
    monkeypatch.setenv("TELEGRAM_SECRETARY_STATE_DIR", str(tmp_path))
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"session_duration_sec": 7200}), encoding="utf-8")
    monkeypatch.setattr("infrastructure.config._default_config_path", lambda: cfg)

    config = load_config()
    assert config.bot_token == "TEST"
    assert config.authorized_chats.is_authorized(100)
    assert config.session_duration_sec == 7200


def test_build_media_stack_wires_pdf_cap_and_optional_none(monkeypatch, tmp_path):
    """pdf cap が PdfRenderer に渡り、moonshine 未導入なら transcriber=None で組む。"""
    import adapters.render.markitdown_renderer as mr_mod
    import adapters.render.pdf_renderer as pdf_mod

    monkeypatch.setattr(mr_mod, "MarkitdownRenderer", lambda: object())

    captured: dict = {}
    real_pdf = pdf_mod.PdfRenderer

    def spy(image_max_pages=20):
        captured["cap"] = image_max_pages
        return real_pdf(image_max_pages=image_max_pages)

    monkeypatch.setattr(pdf_mod, "PdfRenderer", spy)
    # moonshine を未導入として模す（from ... import で ImportError）
    monkeypatch.setitem(sys.modules, "adapters.transcribe.moonshine_transcriber", None)

    config = Config(
        bot_token="t",
        authorized_chats=AuthorizedChats(frozenset({1})),
        state_dir=tmp_path,
        session_duration_sec=7200,
        pdf_image_max_pages=9,
    )
    stack = build_media_stack(config, gateway=object())
    try:
        assert isinstance(stack, MediaStack)
        assert captured["cap"] == 9
        assert isinstance(stack.download_uc, DownloadAuthorizedMedia)
        assert isinstance(stack.render_uc, RenderAuthorizedMedia)
        # moonshine 未導入 → transcriber=None フォールバックを配線結果として確認
        # （音声 media を流す E2E は test_main 側、ここは組み立て結果を直接 pin）
        assert stack.render_uc._transcriber is None
    finally:
        stack.downloader.close()
