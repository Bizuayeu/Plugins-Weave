"""Load a wakeup config dict into a validated WakeupConfig (Interface gateway).

Persona-agnostic: every value comes from the config; nothing is hardcoded.
All problems surface as ConfigError for a uniform error surface.
"""
from __future__ import annotations

import json
from typing import Any

from domain.exceptions import ConfigError
from domain.models import CommitIdentity, LoadFile, RepoRef, WakeupConfig

_REQUIRED_KEYS = ("public_repo", "load_files", "commit_identity", "directive_path")


def _repo(d: dict[str, Any]) -> RepoRef:
    return RepoRef(
        owner=d["owner"],
        name=d["name"],
        branch=d.get("branch", "main"),
        visibility=d.get("visibility", "public"),
    )


def load_config(data: dict[str, Any]) -> WakeupConfig:
    """Map a config dict to a WakeupConfig, raising ConfigError on any problem."""
    missing = [k for k in _REQUIRED_KEYS if k not in data]
    if missing:
        raise ConfigError(f"missing required config keys: {missing}")

    try:
        public_repo = _repo(data["public_repo"])
        private_repo = _repo(data["private_repo"]) if data.get("private_repo") else None
        load_files = tuple(
            LoadFile(
                path=f["path"],
                label=f.get("label", ""),
                required=f.get("required", True),
            )
            for f in data["load_files"]
        )
        ci = data["commit_identity"]
        commit_identity = CommitIdentity(
            author_name=ci["author_name"],
            author_email=ci["author_email"],
            coauthor=ci.get("coauthor", ""),
        )
    except (KeyError, TypeError, ValueError) as exc:
        # domain raises ValueError (e.g. non-noreply email); wrap uniformly.
        raise ConfigError(f"invalid config: {exc}") from exc

    return WakeupConfig(
        public_repo=public_repo,
        load_files=load_files,
        commit_identity=commit_identity,
        directive_path=data["directive_path"],
        private_repo=private_repo,
    )


def load_config_file(path: str) -> WakeupConfig:
    """Read a JSON config file from disk and load it."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot read config file {path!r}: {exc}") from exc
    return load_config(data)
