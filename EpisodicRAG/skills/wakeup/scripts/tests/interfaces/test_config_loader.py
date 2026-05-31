"""Stage 3: config dict -> WakeupConfig mapping + required-key validation.

Dummy values only (acme/memo) — the loader must not assume any persona.
"""
import pytest

from domain.exceptions import ConfigError
from domain.models import WakeupConfig
from interfaces.config_loader import load_config


def _valid_data():
    return {
        "public_repo": {"owner": "acme", "name": "memo"},
        "load_files": [
            {"path": "dir/A.txt", "label": "skeleton", "required": True},
            {"path": "dir/B.md", "required": False},
        ],
        "commit_identity": {
            "author_name": "Persona",
            "author_email": "1+u@users.noreply.github.com",
            "coauthor": "Some Model <noreply@anthropic.com>",
        },
        "directive_path": "dir/Directive.md",
    }


class TestLoadConfig:
    def test_builds_wakeup_config(self):
        cfg = load_config(_valid_data())
        assert isinstance(cfg, WakeupConfig)
        assert cfg.public_repo.owner == "acme"
        assert cfg.public_repo.branch == "main"  # default applied
        assert len(cfg.load_files) == 2
        assert cfg.load_files[0].required is True
        assert cfg.load_files[1].required is False

    def test_load_files_is_tuple(self):
        # frozen WakeupConfig needs a hashable/immutable sequence
        assert isinstance(load_config(_valid_data()).load_files, tuple)

    def test_optional_private_repo(self):
        data = _valid_data()
        data["private_repo"] = {"owner": "acme", "name": "secret", "visibility": "private"}
        cfg = load_config(data)
        assert cfg.private_repo is not None
        assert cfg.private_repo.visibility == "private"

    def test_absent_private_repo_is_none(self):
        assert load_config(_valid_data()).private_repo is None

    @pytest.mark.parametrize(
        "missing", ["public_repo", "load_files", "commit_identity", "directive_path"]
    )
    def test_missing_required_key_raises_config_error(self, missing):
        data = _valid_data()
        del data[missing]
        with pytest.raises(ConfigError):
            load_config(data)

    def test_invalid_email_raises_config_error(self):
        # domain raises ValueError; loader wraps it as ConfigError for a uniform surface
        data = _valid_data()
        data["commit_identity"]["author_email"] = "raw@gmail.com"
        with pytest.raises(ConfigError):
            load_config(data)
