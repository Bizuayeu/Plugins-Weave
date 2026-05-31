"""Stage 3/4: self-contained CLI helpers (stdlib only, no EpisodicRAG imports).

- resolve_urls: build raw URLs for public load files.
- extract_token: pull a token out of a tar.gz / tgz / tar / gz / zip archive
  (claude.ai forbids nested zip inside a skill zip, but allows tar.gz — so the
  engine supports the whole family and picks by extension).
- CLI security invariant: on failure the token never reaches stdout/stderr.
"""
import gzip
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

from domain.models import LoadFile, RepoRef
from interfaces.wakeup_engine import extract_token, resolve_urls

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


# --- archive builders -------------------------------------------------------

def _gz(tmp_path, content):
    p = tmp_path / "token.gz"
    with gzip.open(p, "wt", encoding="utf-8") as f:
        f.write(content)
    return p


def _tar(tmp_path, content, gz=False):
    inner = tmp_path / "token.txt"
    inner.write_text(content, encoding="utf-8")
    p = tmp_path / ("token.tar.gz" if gz else "token.tar")
    with tarfile.open(p, "w:gz" if gz else "w:") as tf:
        tf.add(inner, arcname="token.txt")
    return p


def _zip(tmp_path, content):
    p = tmp_path / "token.zip"
    with zipfile.ZipFile(p, "w") as zf:
        zf.writestr("token.txt", content)
    return p


class TestExtractTokenAllFormats:
    def test_gz(self, tmp_path):
        assert extract_token(str(_gz(tmp_path, "github_pat_GZ\n"))) == "github_pat_GZ"

    def test_tar(self, tmp_path):
        assert extract_token(str(_tar(tmp_path, "github_pat_TAR\n"))) == "github_pat_TAR"

    def test_tar_gz(self, tmp_path):
        assert extract_token(str(_tar(tmp_path, "github_pat_TGZ\n", gz=True))) == "github_pat_TGZ"

    def test_zip(self, tmp_path):
        assert extract_token(str(_zip(tmp_path, "github_pat_ZIP\n"))) == "github_pat_ZIP"

    def test_unsupported_format_raises(self, tmp_path):
        p = tmp_path / "token.bin"
        p.write_bytes(b"\x00\x01")
        with pytest.raises(Exception):
            extract_token(str(p))

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(Exception):
            extract_token(str(tmp_path / "nope.tar.gz"))


class TestCliTokenNeverLeaks:
    """extract-token: token ONLY on success stdout (for $(...)); nothing tokenish on failure."""

    def test_failure_leaks_nothing(self, tmp_path):
        result = subprocess.run(
            [sys.executable, str(ENGINE), "extract-token", "--archive", str(tmp_path / "nope.tar.gz")],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
        assert result.stdout.strip() == ""
        assert "github_pat_" not in result.stdout
        assert "github_pat_" not in result.stderr
        assert "Traceback" not in result.stderr

    def test_success_stdout_is_token_only(self, tmp_path):
        arc = _tar(tmp_path, "github_pat_TGZ789\n", gz=True)
        result = subprocess.run(
            [sys.executable, str(ENGINE), "extract-token", "--archive", str(arc)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "github_pat_TGZ789"
        assert result.stderr == ""
