from __future__ import annotations

import argparse
import json
from pathlib import Path

from domain.authorization import AuthorizedChats
from infrastructure.config import Config
from infrastructure.registry_cli import run_registry_command


def _config(tmp_path: Path) -> Config:
    return Config(
        bot_token="x",
        authorized_chats=AuthorizedChats.from_iterable([1]),
        state_dir=tmp_path,
        session_duration_sec=7200,
    )


def _ns(**kw) -> argparse.Namespace:
    base = {"key": None, "json": None, "json_file": None}
    base.update(kw)
    return argparse.Namespace(**base)


_INDIVIDUAL = {
    "uuid": "u1", "display_name": "yamada", "role": "associate",
    "status": "active", "created_at": "t", "updated_at": "t",
}


def test_add_then_get_individual(tmp_path, capsys):
    config = _config(tmp_path)
    assert run_registry_command(config, "individuals", "add", _ns(json=json.dumps(_INDIVIDUAL))) == 0
    assert run_registry_command(config, "individuals", "get", _ns(key="u1")) == 0
    assert "yamada" in capsys.readouterr().out


def test_add_invalid_role_returns_2(tmp_path):
    config = _config(tmp_path)
    bad = dict(_INDIVIDUAL, role="boss")
    assert run_registry_command(config, "individuals", "add", _ns(json=json.dumps(bad))) == 2


def test_list_empty_prints_empty_array(tmp_path, capsys):
    config = _config(tmp_path)
    assert run_registry_command(config, "individuals", "list", _ns()) == 0
    assert capsys.readouterr().out.strip() == "[]"


def test_get_missing_returns_2(tmp_path):
    config = _config(tmp_path)
    assert run_registry_command(config, "tasks", "get", _ns(key="zzz")) == 2


def test_remove_individual(tmp_path):
    config = _config(tmp_path)
    run_registry_command(config, "individuals", "add", _ns(json=json.dumps(_INDIVIDUAL)))
    assert run_registry_command(config, "individuals", "remove", _ns(key="u1")) == 0
    assert run_registry_command(config, "individuals", "get", _ns(key="u1")) == 2


def test_add_persists_to_correct_path(tmp_path):
    config = _config(tmp_path)
    run_registry_command(config, "individuals", "add", _ns(json=json.dumps(_INDIVIDUAL)))
    assert config.individuals_path.exists()
