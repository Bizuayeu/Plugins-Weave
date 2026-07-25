"""Stage 3/4: self-contained CLI helpers (stdlib only, no EpisodicRAG imports).

- resolve_urls: build raw URLs for public load files.
- extract_token: pull a token out of a tar.gz / tgz / tar / gz / zip archive
  (claude.ai forbids nested zip inside a skill zip, but allows tar.gz — so the
  engine supports the whole family and picks by extension).
- CLI security invariant: on failure the token never reaches stdout/stderr.
"""

import gzip
import json
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

from domain.models import LoadFile, RepoRef
from interfaces.wakeup_engine import SKILL_ROOT, extract_token, resolve_urls

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
            [
                sys.executable,
                str(ENGINE),
                "extract-token",
                "--archive",
                str(tmp_path / "nope.tar.gz"),
            ],
            capture_output=True,
            text=True,
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
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "github_pat_TGZ789"
        assert result.stderr == ""


def _deployment(
    tmp_path, directive_path="Directive.md", directive_text="# directive\n", token=True
):
    """Build a deployed skill root: config + directive + token archive."""
    root = tmp_path / "wakeup"
    root.mkdir(exist_ok=True)
    config = {
        "public_repo": {"owner": "acme", "name": "memo"},
        "load_files": [
            {"path": "Identities/A.txt"},
            {"path": "Identities/B.md", "required": False},
        ],
        "commit_identity": {"author_name": "P", "author_email": "1+u@users.noreply.github.com"},
        "directive_path": directive_path,
        "private_repo": {"owner": "acme", "name": "secret", "visibility": "private"},
    }
    (root / "wakeup.config.json").write_text(json.dumps(config), encoding="utf-8")
    if directive_text is not None:
        target = root / directive_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(directive_text, encoding="utf-8")
    if token:
        inner = tmp_path / "token.txt"
        inner.write_text("github_pat_DEPLOY\n", encoding="utf-8")
        with tarfile.open(root / "token.tar.gz", "w:gz") as tf:
            tf.add(inner, arcname="token.txt")
    return root


def _verify(root=None):
    argv = [sys.executable, str(ENGINE), "verify"]
    if root is not None:
        argv += ["--root", str(root)]
    return subprocess.run(argv, capture_output=True, text=True)


class TestVerifyCommand:
    """Step 1 must fail loudly: a missing directive used to slip through silently."""

    def test_complete_deployment_passes(self, tmp_path):
        result = _verify(_deployment(tmp_path))
        assert result.returncode == 0
        assert "FAIL" not in result.stdout

    def test_reports_every_check(self, tmp_path):
        out = _verify(_deployment(tmp_path)).stdout
        assert "config" in out and "directive" in out and "token" in out

    def test_fingerprints_the_persona_being_woken(self, tmp_path):
        out = _verify(_deployment(tmp_path)).stdout
        assert "acme/secret" in out  # private repo wins as load_repo

    def test_missing_directive_fails_with_the_expected_path(self, tmp_path):
        root = _deployment(tmp_path, directive_path="personas/foo/D.md", directive_text=None)
        result = _verify(root)
        assert result.returncode != 0
        assert "personas/foo/D.md" in result.stdout
        assert "FAIL" in result.stdout

    def test_missing_token_fails(self, tmp_path):
        result = _verify(_deployment(tmp_path, token=False))
        assert result.returncode != 0

    def test_broken_config_fails_without_traceback(self, tmp_path):
        root = _deployment(tmp_path)
        (root / "wakeup.config.json").write_text("{ not json", encoding="utf-8")
        result = _verify(root)
        assert result.returncode != 0
        assert "Traceback" not in result.stderr

    def test_unsafe_directive_path_in_config_fails(self, tmp_path):
        root = _deployment(tmp_path)
        cfg = json.loads((root / "wakeup.config.json").read_text(encoding="utf-8"))
        cfg["directive_path"] = "../outside.md"
        (root / "wakeup.config.json").write_text(json.dumps(cfg), encoding="utf-8")
        assert _verify(root).returncode != 0

    def test_never_prints_token_contents(self, tmp_path):
        result = _verify(_deployment(tmp_path))
        assert "github_pat_" not in result.stdout
        assert "github_pat_" not in result.stderr

    def test_root_defaults_to_the_deployed_skill_root(self):
        """No --root: identical report to an explicit --root at the skill's own root.

        Comparing the two runs keeps the assertion true whether or not this tree has
        been materialized. The earlier version asserted on the *missing config* error
        message, which silently depended on the dev tree never holding a deployment —
        an assumption `materialize` turned into the normal state.
        """
        default_run = _verify(root=None)
        explicit_run = _verify(root=SKILL_ROOT)
        assert default_run.stdout == explicit_run.stdout
        assert default_run.returncode == explicit_run.returncode

    def test_skill_root_resolves_to_the_directory_holding_skill_md(self):
        """SKILL_ROOT is derived from the engine's own location, so it travels with the zip."""
        assert (Path(SKILL_ROOT) / "SKILL.md").is_file()


class TestResolveUrlsCommand:
    """resolve-urls resolves boot memory against the private repo when configured.

    Memory (GrandDigest etc.) moved to the private repo under private-by-default,
    so load_files must resolve there; public-only personas still fall back.
    """

    def _write_config(self, tmp_path, with_private):
        config = {
            "public_repo": {"owner": "acme", "name": "memo"},
            "load_files": [{"path": "Identities/GrandDigest.txt"}],
            "commit_identity": {
                "author_name": "P",
                "author_email": "1+u@users.noreply.github.com",
            },
            "directive_path": "Directive.md",
        }
        if with_private:
            config["private_repo"] = {"owner": "acme", "name": "secret", "visibility": "private"}
        p = tmp_path / "wakeup.config.json"
        p.write_text(json.dumps(config), encoding="utf-8")
        return p

    def test_resolves_against_private_repo(self, tmp_path):
        cfg = self._write_config(tmp_path, with_private=True)
        result = subprocess.run(
            [sys.executable, str(ENGINE), "resolve-urls", "--config", str(cfg), "--sha", "sha123"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert json.loads(result.stdout) == [
            "https://raw.githubusercontent.com/acme/secret/sha123/Identities/GrandDigest.txt"
        ]

    def test_falls_back_to_public_repo(self, tmp_path):
        cfg = self._write_config(tmp_path, with_private=False)
        result = subprocess.run(
            [sys.executable, str(ENGINE), "resolve-urls", "--config", str(cfg), "--sha", "sha123"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert json.loads(result.stdout) == [
            "https://raw.githubusercontent.com/acme/memo/sha123/Identities/GrandDigest.txt"
        ]
