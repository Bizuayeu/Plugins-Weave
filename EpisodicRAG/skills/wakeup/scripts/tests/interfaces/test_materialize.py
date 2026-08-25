"""materialize: place the ★ artifacts into a skill root deterministically, then verify.

The drift this kills: config and directive are hand-copied per zip, so a persona
ends up deployed with a fresh directive and a months-old config (stale coauthor,
stale repo). The source of truth is the persona's own config *wherever it lives* —
never this repo's examples/ — so the command takes paths, never a persona name.
"""

import json
import subprocess
import sys
import tarfile
from pathlib import Path

# tests/interfaces/ -> parents[2] == scripts/
ENGINE = Path(__file__).resolve().parents[2] / "interfaces" / "wakeup_engine.py"


def _source(
    tmp_path, directive_path="Directive.md", with_private=True, write_directive=True
):
    """A persona's own staging area: config + the directive beside it."""
    src = tmp_path / "persona-src"
    src.mkdir(parents=True, exist_ok=True)
    config = {
        "public_repo": {"owner": "acme", "name": "memo"},
        "load_files": [{"path": "Identities/A.txt"}],
        "commit_identity": {
            "author_name": "P",
            "author_email": "1+u@users.noreply.github.com",
            "coauthor": "Some Model <noreply@anthropic.com>",
        },
        "directive_path": directive_path,
    }
    if with_private:
        config["private_repo"] = {
            "owner": "acme",
            "name": "secret",
            "visibility": "private",
        }
    cfg = src / "mypersona.config.json"
    cfg.write_text(json.dumps(config), encoding="utf-8")
    if write_directive:
        target = src / directive_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# directive\n", encoding="utf-8")
    return cfg


def _token(tmp_path, name="token.tar.gz"):
    inner = tmp_path / "token.txt"
    inner.write_text("github_pat_SRC123\n", encoding="utf-8")
    arc = tmp_path / name
    with tarfile.open(arc, "w:gz") as tf:
        tf.add(inner, arcname="token.txt")
    return arc


def _run(config, out, token=None):
    argv = [
        sys.executable,
        str(ENGINE),
        "materialize",
        "--config",
        str(config),
        "--out",
        str(out),
    ]
    if token is not None:
        argv += ["--token", str(token)]
    return subprocess.run(argv, capture_output=True, text=True)


class TestPlacesArtifacts:
    def test_config_lands_under_the_generic_name(self, tmp_path):
        out = tmp_path / "wakeup"
        _run(_source(tmp_path), out, _token(tmp_path))
        assert (out / "wakeup.config.json").is_file()

    def test_config_content_is_copied_verbatim(self, tmp_path):
        """Single source of truth: the deployed config must not drift from the source."""
        src = _source(tmp_path)
        out = tmp_path / "wakeup"
        _run(src, out, _token(tmp_path))
        assert json.loads(
            (out / "wakeup.config.json").read_text(encoding="utf-8")
        ) == json.loads(src.read_text(encoding="utf-8"))

    def test_directive_lands_at_the_configured_relative_path(self, tmp_path):
        out = tmp_path / "wakeup"
        _run(
            _source(tmp_path, directive_path="personas/foo/D.md"), out, _token(tmp_path)
        )
        assert (out / "personas" / "foo" / "D.md").is_file()

    def test_token_lands_under_its_own_basename(self, tmp_path):
        """The printed name is what goes into the SKILL.md curl — no silent renaming."""
        out = tmp_path / "wakeup"
        _run(_source(tmp_path), out, _token(tmp_path, name="token-read.tar.gz"))
        assert (out / "token-read.tar.gz").is_file()

    def test_creates_the_out_directory(self, tmp_path):
        out = tmp_path / "nested" / "wakeup"
        assert _run(_source(tmp_path), out, _token(tmp_path)).returncode == 0

    def test_reports_what_was_placed(self, tmp_path):
        result = _run(_source(tmp_path), tmp_path / "wakeup", _token(tmp_path))
        assert "wakeup.config.json" in result.stdout
        assert "Directive.md" in result.stdout
        assert "token.tar.gz" in result.stdout


class TestResync:
    def test_overwrites_a_stale_deployed_config(self, tmp_path):
        """The whole point: re-running must replace the old hand-copy."""
        out = tmp_path / "wakeup"
        out.mkdir()
        (out / "wakeup.config.json").write_text('{"stale": true}', encoding="utf-8")
        _run(_source(tmp_path), out, _token(tmp_path))
        assert "stale" not in (out / "wakeup.config.json").read_text(encoding="utf-8")

    def test_overwrites_a_stale_directive(self, tmp_path):
        out = tmp_path / "wakeup"
        out.mkdir()
        (out / "Directive.md").write_text("old generation\n", encoding="utf-8")
        _run(_source(tmp_path), out, _token(tmp_path))
        assert (out / "Directive.md").read_text(encoding="utf-8") == "# directive\n"

    def test_token_already_in_place_is_enough(self, tmp_path):
        """No --token: an archive already deployed keeps the deployment valid."""
        out = tmp_path / "wakeup"
        out.mkdir()
        _token(tmp_path)  # build once...
        (out / "token.tar.gz").write_bytes((tmp_path / "token.tar.gz").read_bytes())
        assert _run(_source(tmp_path), out).returncode == 0

    def test_in_place_source_is_not_a_failure(self, tmp_path):
        """out == source dir and the config is already named wakeup.config.json."""
        src = tmp_path / "persona-src"
        src.mkdir()
        cfg = _source(tmp_path)
        cfg.rename(src / "wakeup.config.json")
        _token(src)
        result = _run(src / "wakeup.config.json", src, src / "token.tar.gz")
        assert result.returncode == 0
        assert (src / "wakeup.config.json").is_file()


class TestVerifiesAfterPlacing:
    def test_exit_zero_on_a_complete_deployment(self, tmp_path):
        assert (
            _run(_source(tmp_path), tmp_path / "wakeup", _token(tmp_path)).returncode
            == 0
        )

    def test_prints_the_verify_report(self, tmp_path):
        out = _run(_source(tmp_path), tmp_path / "wakeup", _token(tmp_path)).stdout
        assert "config" in out and "directive" in out and "token" in out
        assert "acme/secret" in out  # fingerprint of the persona being deployed

    def test_missing_token_fails_verification(self, tmp_path):
        result = _run(_source(tmp_path), tmp_path / "wakeup")
        assert result.returncode != 0
        assert "FAIL" in result.stdout


class TestSourceProblems:
    def test_missing_directive_at_source_fails_and_names_it(self, tmp_path):
        src = _source(
            tmp_path, directive_path="personas/foo/D.md", write_directive=False
        )
        result = _run(src, tmp_path / "wakeup", _token(tmp_path))
        assert result.returncode != 0
        assert "personas/foo/D.md" in result.stdout + result.stderr

    def test_missing_directive_places_nothing(self, tmp_path):
        """Fail before deploying a half-materialized skill."""
        out = tmp_path / "wakeup"
        src = _source(tmp_path, write_directive=False)
        _run(src, out, _token(tmp_path))
        assert not (out / "wakeup.config.json").exists()

    def test_broken_source_config_fails_without_traceback(self, tmp_path):
        src = _source(tmp_path)
        src.write_text("{ not json", encoding="utf-8")
        result = _run(src, tmp_path / "wakeup", _token(tmp_path))
        assert result.returncode != 0
        assert "Traceback" not in result.stderr

    def test_unsafe_directive_path_is_refused(self, tmp_path):
        src = _source(tmp_path)
        data = json.loads(src.read_text(encoding="utf-8"))
        data["directive_path"] = "../outside.md"
        src.write_text(json.dumps(data), encoding="utf-8")
        assert _run(src, tmp_path / "wakeup", _token(tmp_path)).returncode != 0

    def test_missing_token_archive_fails(self, tmp_path):
        result = _run(_source(tmp_path), tmp_path / "wakeup", tmp_path / "nope.tar.gz")
        assert result.returncode != 0


class TestPersonaAgnostic:
    def test_public_only_persona_materializes(self, tmp_path):
        src = _source(tmp_path, with_private=False)
        result = _run(src, tmp_path / "wakeup", _token(tmp_path))
        assert result.returncode == 0
        assert "acme/memo" in result.stdout

    def test_arbitrary_directive_name(self, tmp_path):
        out = tmp_path / "wakeup"
        src = _source(tmp_path, directive_path="directive.md")
        assert _run(src, out, _token(tmp_path)).returncode == 0
        assert (out / "directive.md").is_file()


class TestNeverLeaksToken:
    def test_token_contents_absent_from_output(self, tmp_path):
        result = _run(_source(tmp_path), tmp_path / "wakeup", _token(tmp_path))
        assert "github_pat_" not in result.stdout
        assert "github_pat_" not in result.stderr
