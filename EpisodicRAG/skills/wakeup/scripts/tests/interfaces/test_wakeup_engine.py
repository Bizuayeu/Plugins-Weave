"""Stage 3: self-contained CLI helpers (stdlib only, no EpisodicRAG imports).

- resolve_urls: build raw URLs for public load files.
- extract_token_from_zip: pull a token out of a zip.
- CLI security invariant: on failure the token never reaches stdout/stderr.
"""
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from domain.models import LoadFile, RepoRef
from interfaces.wakeup_engine import extract_token_from_zip, resolve_urls

# tests/interfaces/ -> parents[2] == scripts/
ENGINE = Path(__file__).resolve().parents[2] / "interfaces" / "wakeup_engine.py"


class TestResolveUrls:
    def test_builds_raw_url_per_file(self):
        repo = RepoRef(owner="acme", name="memo")
        files = (LoadFile(path="dir/A.txt"), LoadFile(path="dir/B.md"))
        assert resolve_urls(repo, "sha123", files) == [
            "https://raw.githubusercontent.com/acme/memo/sha123/dir/A.txt",
            "https://raw.githubusercontent.com/acme/memo/sha123/dir/B.md",
        ]


class TestExtractTokenFromZip:
    def _make_zip(self, tmp_path, name, content):
        zpath = tmp_path / "pat.zip"
        with zipfile.ZipFile(zpath, "w") as z:
            z.writestr(name, content)
        return zpath

    def test_extracts_and_strips_token(self, tmp_path):
        z = self._make_zip(tmp_path, "token.txt", "github_pat_ABC123\n")
        assert extract_token_from_zip(str(z)) == "github_pat_ABC123"

    def test_missing_zip_raises(self, tmp_path):
        with pytest.raises(Exception):
            extract_token_from_zip(str(tmp_path / "nope.zip"))


class TestCliTokenNeverLeaks:
    """Security: extract-token must put the token ONLY on stdout (for $(...)),
    and on failure must leak nothing tokenish on either stream."""

    def test_failure_leaks_nothing(self, tmp_path):
        result = subprocess.run(
            [sys.executable, str(ENGINE), "extract-token", "--zip", str(tmp_path / "nope.zip")],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
        assert result.stdout.strip() == ""
        assert "github_pat_" not in result.stdout
        assert "github_pat_" not in result.stderr
        assert "Traceback" not in result.stderr  # masked, not a raw crash dump

    def test_success_stdout_is_token_only(self, tmp_path):
        z = tmp_path / "pat.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("token.txt", "github_pat_XYZ789\n")
        result = subprocess.run(
            [sys.executable, str(ENGINE), "extract-token", "--zip", str(z)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "github_pat_XYZ789"  # token only, for TOKEN=$(...)
        assert result.stderr == ""
