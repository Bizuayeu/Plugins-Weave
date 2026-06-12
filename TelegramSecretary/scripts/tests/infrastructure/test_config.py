from __future__ import annotations

import json

import pytest

from infrastructure.config import Config


@pytest.fixture(autouse=True)
def base_env(monkeypatch, tmp_path):
    """最低限の env を揃え、config.json（非秘匿の正典）を tmp に用意して決め打ちパスを差し替える。

    media/outbound 系は各テストで env 上書きする。config.json を渡さない呼び出し
    （`Config.from_sources()`）は、ここで monkeypatch した `_default_config_path` 経由で
    この tmp config.json（session_duration_sec=7200）を読む。
    """
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "TEST")
    monkeypatch.setenv("TELEGRAM_SECRETARY_AUTHORIZED_CHATS", "[100]")
    monkeypatch.setenv("TELEGRAM_SECRETARY_STATE_DIR", str(tmp_path))
    for k in [
        "TELEGRAM_SECRETARY_MEDIA_MAX_SIZE_BYTES",
        "TELEGRAM_SECRETARY_MEDIA_RETENTION_HOURS",
        "TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD",
        "TELEGRAM_SECRETARY_OUTBOUND_MAX_SIZE_BYTES",
        "TELEGRAM_SECRETARY_PDF_IMAGE_MAX_PAGES",
        "TELEGRAM_SECRETARY_REGISTRY_DIR",
    ]:
        monkeypatch.delenv(k, raising=False)
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"session_duration_sec": 7200}), encoding="utf-8")
    monkeypatch.setattr("infrastructure.config._default_config_path", lambda: cfg)


def test_config_defaults_when_media_env_missing():
    cfg = Config.from_sources()
    assert cfg.media_max_size_bytes == 20 * 1024 * 1024
    assert cfg.media_retention_hours == 24
    assert cfg.media_enable_download is True


def test_config_new_table_paths():
    """P/A 軸の3表（PROFILE/GOALS/STEPS）も registry_root 配下の既存4表と同型のパス規約。"""
    cfg = Config.from_sources()
    assert cfg.profile_path == cfg.registry_root / "profile" / "PROFILE.json"
    assert cfg.goals_path == cfg.registry_root / "goals" / "GOALS.json"
    assert cfg.steps_path == cfg.registry_root / "steps" / "STEPS.json"


def test_config_parses_max_size_bytes(monkeypatch):
    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_MAX_SIZE_BYTES", "5242880")
    cfg = Config.from_sources()
    assert cfg.media_max_size_bytes == 5 * 1024 * 1024


def test_config_rejects_non_positive_max_size(monkeypatch):
    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_MAX_SIZE_BYTES", "0")
    with pytest.raises(EnvironmentError):
        Config.from_sources()


def test_config_rejects_invalid_max_size(monkeypatch):
    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_MAX_SIZE_BYTES", "not-a-number")
    with pytest.raises(EnvironmentError):
        Config.from_sources()


def test_config_parses_retention_hours(monkeypatch):
    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_RETENTION_HOURS", "6")
    cfg = Config.from_sources()
    assert cfg.media_retention_hours == 6


def test_config_rejects_non_positive_retention(monkeypatch):
    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_RETENTION_HOURS", "-1")
    with pytest.raises(EnvironmentError):
        Config.from_sources()


@pytest.mark.parametrize("value", ["true", "1", "yes", "TRUE", "Yes"])
def test_config_enable_download_truthy_values(monkeypatch, value):
    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD", value)
    assert Config.from_sources().media_enable_download is True


@pytest.mark.parametrize("value", ["false", "0", "no", "FALSE", "No"])
def test_config_enable_download_falsy_values(monkeypatch, value):
    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD", value)
    assert Config.from_sources().media_enable_download is False


def test_config_enable_download_invalid_value(monkeypatch):
    monkeypatch.setenv("TELEGRAM_SECRETARY_MEDIA_ENABLE_DOWNLOAD", "maybe")
    with pytest.raises(EnvironmentError):
        Config.from_sources()


# === Stage 8.4: outbound media size ===


def test_config_default_outbound_max_size():
    cfg = Config.from_sources()
    assert cfg.outbound_max_size_bytes == 50 * 1024 * 1024


def test_config_parses_outbound_max_size(monkeypatch):
    monkeypatch.setenv("TELEGRAM_SECRETARY_OUTBOUND_MAX_SIZE_BYTES", "10485760")
    cfg = Config.from_sources()
    assert cfg.outbound_max_size_bytes == 10 * 1024 * 1024


def test_config_rejects_non_positive_outbound_max_size(monkeypatch):
    monkeypatch.setenv("TELEGRAM_SECRETARY_OUTBOUND_MAX_SIZE_BYTES", "0")
    with pytest.raises(EnvironmentError):
        Config.from_sources()


# === Stage 11.4: PDF image max pages (cap) ===


def test_config_default_pdf_image_max_pages():
    """欠損時は default 20（超多ページ画像化の安全弁）。"""
    cfg = Config.from_sources()
    assert cfg.pdf_image_max_pages == 20


def test_config_parses_pdf_image_max_pages(monkeypatch):
    monkeypatch.setenv("TELEGRAM_SECRETARY_PDF_IMAGE_MAX_PAGES", "5")
    cfg = Config.from_sources()
    assert cfg.pdf_image_max_pages == 5


def test_config_rejects_non_positive_pdf_image_max_pages(monkeypatch):
    monkeypatch.setenv("TELEGRAM_SECRETARY_PDF_IMAGE_MAX_PAGES", "0")
    with pytest.raises(EnvironmentError):
        Config.from_sources()


def test_config_rejects_invalid_pdf_image_max_pages(monkeypatch):
    monkeypatch.setenv("TELEGRAM_SECRETARY_PDF_IMAGE_MAX_PAGES", "lots")
    with pytest.raises(EnvironmentError):
        Config.from_sources()


# === Stage 2: session_duration_sec（config.json 必須・範囲検証・純2層） ===


def _write_config(tmp_path, data: dict):
    p = tmp_path / "explicit_config.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_session_duration_read_from_config_json(tmp_path):
    """config.json の session_duration_sec が Config に反映される。"""
    path = _write_config(tmp_path, {"session_duration_sec": 3600})
    assert Config.from_sources(config_path=path).session_duration_sec == 3600


def test_session_duration_missing_key_raises(tmp_path):
    """session_duration_sec キー欠落は必須エラー（デフォルトに落ちない）。"""
    path = _write_config(tmp_path, {})
    with pytest.raises(EnvironmentError):
        Config.from_sources(config_path=path)


def test_config_json_missing_file_raises(tmp_path):
    """config.json 自体が無ければ EnvironmentError（init-config を促す）。"""
    with pytest.raises(EnvironmentError):
        Config.from_sources(config_path=tmp_path / "nonexistent.json")


def test_session_duration_out_of_range_raises(tmp_path):
    """範囲外（>86400）は EnvironmentError（Domain の ValueError を翻訳）。"""
    path = _write_config(tmp_path, {"session_duration_sec": 99999})
    with pytest.raises(EnvironmentError):
        Config.from_sources(config_path=path)


def test_session_duration_zero_raises(tmp_path):
    """0 は不正（session 総枠で 0 は無効）。"""
    path = _write_config(tmp_path, {"session_duration_sec": 0})
    with pytest.raises(EnvironmentError):
        Config.from_sources(config_path=path)


def test_session_duration_non_numeric_raises(tmp_path):
    """数値でない値は EnvironmentError。"""
    path = _write_config(tmp_path, {"session_duration_sec": "abc"})
    with pytest.raises(EnvironmentError):
        Config.from_sources(config_path=path)


def test_config_json_invalid_json_raises(tmp_path):
    """壊れた JSON は EnvironmentError。"""
    path = tmp_path / "broken.json"
    path.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(EnvironmentError):
        Config.from_sources(config_path=path)


def test_agent_name_and_private_dir_are_optional(tmp_path):
    """agent_name / private_dir は Optional（あれば読む、無くても fail しない）。"""
    path = _write_config(
        tmp_path,
        {"session_duration_sec": 7200, "agent_name": "Iris", "private_dir": "/secret"},
    )
    cfg = Config.from_sources(config_path=path)
    assert cfg.agent_name == "Iris"
    assert cfg.private_dir == "/secret"


def test_agent_name_defaults_to_none_when_absent(tmp_path):
    """agent_name 未指定なら None（必須ではない）。"""
    path = _write_config(tmp_path, {"session_duration_sec": 7200})
    cfg = Config.from_sources(config_path=path)
    assert cfg.agent_name is None
    assert cfg.private_dir is None


def test_agent_name_non_string_raises(tmp_path):
    """数値 agent_name は型不正で fail-fast（他キーと同じ EnvironmentError）。"""
    path = _write_config(tmp_path, {"session_duration_sec": 7200, "agent_name": 123})
    with pytest.raises(EnvironmentError):
        Config.from_sources(config_path=path)


def test_private_dir_non_string_raises(tmp_path):
    """非 str の private_dir も型不正で fail-fast（agent_name と対称）。"""
    path = _write_config(
        tmp_path, {"session_duration_sec": 7200, "private_dir": ["Private"]}
    )
    with pytest.raises(EnvironmentError):
        Config.from_sources(config_path=path)


# === R1: registry_dir（揮発 state と永続管理表のパス分離） ===


def test_registry_paths_default_to_state_dir_when_registry_unset(tmp_path):
    """REGISTRY_DIR 未設定なら管理表 path は state_dir 配下（後方互換）。"""
    path = _write_config(tmp_path, {"session_duration_sec": 7200})
    cfg = Config.from_sources(config_path=path)
    assert cfg.individuals_path == cfg.state_dir / "individuals" / "INDIVIDUALS.json"
    assert cfg.tasks_path == cfg.state_dir / "tasks" / "TASKS.json"
    assert cfg.knowledge_path == cfg.state_dir / "knowledge" / "KNOWLEDGE.json"


def test_registry_dir_config_separates_registry_from_state(tmp_path, monkeypatch):
    """config.json の registry_dir 設定時、管理表 path は registry_dir 配下へ分離（state_dir とは別系統）。"""
    state = tmp_path / "volatile"
    reg = tmp_path / "registry"
    monkeypatch.setenv("TELEGRAM_SECRETARY_STATE_DIR", str(state))
    path = _write_config(tmp_path, {"session_duration_sec": 7200, "registry_dir": str(reg)})
    cfg = Config.from_sources(config_path=path)
    assert cfg.state_dir == state.resolve()
    assert reg.resolve() in cfg.individuals_path.parents
    assert cfg.knowledge_path == reg.resolve() / "knowledge" / "KNOWLEDGE.json"
    # 揮発 state とは別の根に分離されている（R1 の核心）
    assert cfg.state_dir not in cfg.individuals_path.parents


# === R2-3: registry_sync 設定（イベント駆動 git 同期のオプトイン） ===


def test_registry_sync_disabled_by_default(tmp_path):
    """REGISTRY_SYNC 未設定なら無効（ローカル CRUD は git に触れない、後方互換）。"""
    path = _write_config(tmp_path, {"session_duration_sec": 7200})
    cfg = Config.from_sources(config_path=path)
    assert cfg.registry_sync_enabled is False


def test_registry_sync_enabled_via_config(tmp_path):
    path = _write_config(tmp_path, {"session_duration_sec": 7200, "registry_sync": True})
    cfg = Config.from_sources(config_path=path)
    assert cfg.registry_sync_enabled is True


def test_registry_remote_and_branch_defaults(tmp_path):
    path = _write_config(tmp_path, {"session_duration_sec": 7200})
    cfg = Config.from_sources(config_path=path)
    assert cfg.registry_remote == "origin"
    assert cfg.registry_branch == "claude/ts-registry"


def test_registry_branch_from_config(tmp_path):
    path = _write_config(tmp_path, {"session_duration_sec": 7200, "registry_branch": "claude/custom-reg"})
    cfg = Config.from_sources(config_path=path)
    assert cfg.registry_branch == "claude/custom-reg"


# === R3: registry_dir の env 優先（bootstrap 絶対化のキャリア、cwd 依存 .resolve() 回避） ===


def test_registry_dir_env_overrides_config(tmp_path, monkeypatch):
    """TELEGRAM_SECRETARY_REGISTRY_DIR env 設定時、config.json の registry_dir より env を優先する。

    config.json の registry_dir は cwd（=2リポ親）起点の相対だが、registry コマンドは
    ROUTINE_PROMPT で `cd $INSTALL_DIR`（skill root）してから走るため、config.py の
    `.resolve()`（cwd 基準）では二重ネストの幽霊パスに解決される（FINDING 3 同型、R3 物証）。
    bootstrap が source 時の cwd（=2リポ親）基準で絶対化して env 注入し、config.py は
    その絶対パスをそのまま信頼する（再 resolve しない＝state_dir と同型の Z 案）。
    """
    abs_reg = (tmp_path / "abs_registry").resolve()
    monkeypatch.setenv("TELEGRAM_SECRETARY_REGISTRY_DIR", str(abs_reg))
    path = _write_config(tmp_path, {"session_duration_sec": 7200, "registry_dir": "relative/ignored"})
    cfg = Config.from_sources(config_path=path)
    assert cfg.registry_dir == abs_reg
    assert cfg.registry_root == abs_reg
    assert cfg.knowledge_path == abs_reg / "knowledge" / "KNOWLEDGE.json"


def test_registry_dir_falls_back_to_config_when_env_absent(tmp_path):
    """REGISTRY_DIR env が無ければ config.json の registry_dir を従来通り解決（後方互換・ローカル運用）。"""
    reg = tmp_path / "registry"
    path = _write_config(tmp_path, {"session_duration_sec": 7200, "registry_dir": str(reg)})
    cfg = Config.from_sources(config_path=path)
    assert cfg.registry_dir == reg.resolve()
