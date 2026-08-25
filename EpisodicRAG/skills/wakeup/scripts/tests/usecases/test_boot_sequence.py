"""Stage 2: BootSequence orchestration.

The required/optional *policy* lives in BootSequence (UseCase); the loader only
fetches. Exercised with fakes — dummy values only (acme/memo), no persona coupling.
"""

import pytest

from domain.exceptions import WakeupError
from domain.models import CommitIdentity, LoadFile, RepoRef, WakeupConfig
from usecases.boot_sequence import BootSequence


def _config(load_files):
    return WakeupConfig(
        public_repo=RepoRef(owner="acme", name="memo"),
        load_files=load_files,
        commit_identity=CommitIdentity(
            author_name="P", author_email="1+u@users.noreply.github.com"
        ),
        directive_path="dir/Directive.md",
    )


class _RecordingLoader:
    """Returns only fetchable files; missing ones are simply absent (never raises).
    The required/optional decision is BootSequence's job, not the loader's."""

    def __init__(self, log, missing_paths=()):
        self.log = log
        self.missing = set(missing_paths)

    def load_public(self, repo, files):
        self.log.append("load_public")
        return {
            f.path: f"content-of-{f.path}" for f in files if f.path not in self.missing
        }


class TestBootOrder:
    def test_loads_public_memory(self):
        log = []
        cfg = _config((LoadFile(path="dir/A.txt"),))
        BootSequence(cfg, _RecordingLoader(log)).run()
        assert log == ["load_public"]

    def test_returns_loaded_contents(self):
        cfg = _config((LoadFile(path="dir/A.txt"), LoadFile(path="dir/B.md")))
        result = BootSequence(cfg, _RecordingLoader([])).run()
        assert result["dir/A.txt"] == "content-of-dir/A.txt"
        assert result["dir/B.md"] == "content-of-dir/B.md"


class TestRequiredOptional:
    def test_required_missing_aborts(self):
        log = []
        cfg = _config((LoadFile(path="dir/A.txt", required=True),))
        loader = _RecordingLoader(log, missing_paths=["dir/A.txt"])
        with pytest.raises(WakeupError):
            BootSequence(cfg, loader).run()

    def test_optional_missing_continues(self):
        log = []
        cfg = _config((LoadFile(path="dir/opt.md", required=False),))
        loader = _RecordingLoader(log, missing_paths=["dir/opt.md"])
        result = BootSequence(cfg, loader).run()
        assert (
            "dir/opt.md" not in result
        )  # optional missing tolerated; returns what loaded
