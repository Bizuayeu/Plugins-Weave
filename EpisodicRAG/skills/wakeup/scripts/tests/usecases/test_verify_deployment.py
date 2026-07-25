"""VerifyDeployment: the pre-boot deployment contract (Step 1), exercised with fakes.

Rationale: Step 3 (apply the directive) is a Markdown read, so a missing directive
used to pass silently — fail-open. This use case makes the deployed artifacts a
checked precondition, and prints a fingerprint of *which* persona is about to wake
(one deployed skill = one config = one persona, so a stale config is a real hazard).

Dummy values only (acme/memo) — no persona coupling.
"""

import pytest

from domain.exceptions import ConfigError
from domain.models import CommitIdentity, LoadFile, RepoRef, WakeupConfig
from usecases.verify_deployment import VerifyDeployment


def _config(directive_path="Directive.md", with_private=True, load_files=None):
    return WakeupConfig(
        public_repo=RepoRef(owner="acme", name="memo"),
        load_files=load_files
        or (LoadFile(path="dir/A.txt"), LoadFile(path="dir/B.md", required=False)),
        commit_identity=CommitIdentity(
            author_name="P", author_email="1+u@users.noreply.github.com"
        ),
        directive_path=directive_path,
        private_repo=RepoRef(owner="acme", name="secret", visibility="private")
        if with_private
        else None,
    )


class _FakeProbe:
    """Filesystem stand-in: sizes by relative path, archives by name."""

    def __init__(self, config=None, error=None, sizes=None, archives=None, readable=None):
        self._config = config if config is not None else _config()
        self._error = error
        self._sizes = sizes if sizes is not None else {"Directive.md": 826}
        # None = "use the happy default"; () = "genuinely none" (must not be defaulted away)
        self._archives = ("token.tar.gz",) if archives is None else tuple(archives)
        self._readable = {"token.tar.gz"} if readable is None else set(readable)

    def load_config(self):
        if self._error:
            raise self._error
        return self._config

    def directive_size(self, rel_path):
        return self._sizes.get(rel_path)

    def token_archives(self):
        return self._archives

    def token_readable(self, name):
        return name in self._readable


def _check(report, name):
    return next(c for c in report.checks if c.name == name)


class TestAllGreen:
    def test_report_is_ok(self):
        report = VerifyDeployment(_FakeProbe()).run()
        assert report.ok is True

    def test_config_check_fingerprints_the_load_repo(self):
        """Which persona am I about to wake? The load repo answers it."""
        detail = _check(VerifyDeployment(_FakeProbe()).run(), "config").detail
        assert "acme/secret" in detail
        assert "main" in detail
        assert "private" in detail

    def test_config_check_reports_required_optional_split(self):
        detail = _check(VerifyDeployment(_FakeProbe()).run(), "config").detail
        assert "2" in detail  # 2 load files: 1 required / 1 optional
        assert "required 1" in detail
        assert "optional 1" in detail

    def test_public_only_persona_fingerprints_the_public_repo(self):
        probe = _FakeProbe(config=_config(with_private=False))
        detail = _check(VerifyDeployment(probe).run(), "config").detail
        assert "acme/memo" in detail
        assert "public" in detail

    def test_directive_check_reports_path_and_size(self):
        detail = _check(VerifyDeployment(_FakeProbe()).run(), "directive").detail
        assert "Directive.md" in detail
        assert "826" in detail

    def test_token_check_names_the_archive(self):
        detail = _check(VerifyDeployment(_FakeProbe()).run(), "token").detail
        assert "token.tar.gz" in detail


class TestDirectiveFailures:
    def test_missing_directive_fails(self):
        report = VerifyDeployment(_FakeProbe(sizes={})).run()
        assert report.ok is False
        assert _check(report, "directive").ok is False

    def test_missing_directive_names_the_expected_path(self):
        """The whole point: say which file to place, not just 'failed'."""
        probe = _FakeProbe(config=_config(directive_path="personas/foo/D.md"), sizes={})
        detail = _check(VerifyDeployment(probe).run(), "directive").detail
        assert "personas/foo/D.md" in detail

    def test_empty_directive_fails(self):
        report = VerifyDeployment(_FakeProbe(sizes={"Directive.md": 0})).run()
        assert _check(report, "directive").ok is False

    def test_nested_directive_of_another_persona_is_accepted(self):
        probe = _FakeProbe(
            config=_config(directive_path="personas/foo/D.md"),
            sizes={"personas/foo/D.md": 12},
        )
        assert VerifyDeployment(probe).run().ok is True


class TestTokenFailures:
    def test_no_archive_fails(self):
        # A token is required even for public repos (SHA fetch needs auth).
        report = VerifyDeployment(_FakeProbe(archives=())).run()
        assert report.ok is False
        assert _check(report, "token").ok is False

    def test_unreadable_archive_fails(self):
        report = VerifyDeployment(_FakeProbe(archives=("token.zip",), readable=())).run()
        assert _check(report, "token").ok is False

    def test_any_readable_archive_passes(self):
        """Read/Write tokens may be split across archives; one readable is enough."""
        probe = _FakeProbe(
            archives=("token-read.tar.gz", "token-write.tar.gz"),
            readable=("token-write.tar.gz",),
        )
        assert _check(VerifyDeployment(probe).run(), "token").ok is True


class TestConfigFailure:
    def test_config_error_fails_without_crashing(self):
        report = VerifyDeployment(_FakeProbe(error=ConfigError("missing keys"))).run()
        assert report.ok is False
        assert _check(report, "config").ok is False

    def test_dependent_checks_are_reported_as_skipped(self):
        """Without a config the directive path is unknown — report it, don't guess."""
        report = VerifyDeployment(_FakeProbe(error=ConfigError("boom"))).run()
        directive = _check(report, "directive")
        assert directive.ok is False
        assert "skipped" in directive.detail

    def test_token_is_still_checked_without_a_config(self):
        report = VerifyDeployment(_FakeProbe(error=ConfigError("boom"))).run()
        assert _check(report, "token").ok is True


class TestReportRendering:
    def test_lines_cover_every_check(self):
        lines = VerifyDeployment(_FakeProbe()).run().lines()
        assert len(lines) == 3
        assert any(line.startswith("config") for line in lines)
        assert any(line.startswith("directive") for line in lines)
        assert any(line.startswith("token") for line in lines)

    def test_failure_is_visibly_marked(self):
        lines = VerifyDeployment(_FakeProbe(sizes={})).run().lines()
        assert any("FAIL" in line for line in lines)

    def test_success_lines_carry_no_fail_marker(self):
        assert not any("FAIL" in line for line in VerifyDeployment(_FakeProbe()).run().lines())


class TestPortContract:
    def test_fake_satisfies_the_port(self):
        from usecases.ports import DeploymentProbePort

        assert isinstance(_FakeProbe(), DeploymentProbePort)


@pytest.mark.parametrize("bad_directive", ["", "../escape.md"])
def test_config_with_unsafe_directive_never_reaches_the_use_case(bad_directive):
    """Path safety is domain-enforced, so VerifyDeployment can trust the config."""
    with pytest.raises(ValueError):
        _config(directive_path=bad_directive)
