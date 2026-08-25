"""Stage 1: Domain value-object tests.

CRITICAL: no persona-specific values here. We use dummy owners/repos (acme/memo)
so these tests also prove the engine hardcodes nothing Weave-specific.
"""

import pytest

from domain.models import CommitIdentity, LoadFile, RepoRef, WakeupConfig


class TestRepoRef:
    def test_defaults(self):
        r = RepoRef(owner="acme", name="memo")
        assert r.branch == "main"
        assert r.visibility == "public"

    def test_frozen(self):
        r = RepoRef(owner="acme", name="memo")
        with pytest.raises(AttributeError):
            r.owner = "changed"  # type: ignore[misc]

    def test_private_visibility(self):
        r = RepoRef(owner="acme", name="secret", visibility="private")
        assert r.visibility == "private"


class TestLoadFile:
    def test_required_defaults_true(self):
        assert LoadFile(path="dir/A.txt").required is True

    def test_optional(self):
        assert LoadFile(path="dir/B.md", required=False).required is False

    def test_label(self):
        assert LoadFile(path="dir/A.txt", label="skeleton").label == "skeleton"

    def test_frozen(self):
        f = LoadFile(path="dir/A.txt")
        with pytest.raises(AttributeError):
            f.path = "x"  # type: ignore[misc]


class TestCommitIdentity:
    def test_accepts_noreply(self):
        c = CommitIdentity(
            author_name="Persona", author_email="123+user@users.noreply.github.com"
        )
        assert c.author_name == "Persona"
        assert c.coauthor == ""

    def test_accepts_hyphenated_username(self):
        c = CommitIdentity(
            author_name="P", author_email="42+weaving-futurity@users.noreply.github.com"
        )
        assert c.author_email.startswith("42+")

    def test_rejects_raw_gmail(self):
        with pytest.raises(ValueError):
            CommitIdentity(author_name="P", author_email="user@gmail.com")

    def test_rejects_plain_email(self):
        with pytest.raises(ValueError):
            CommitIdentity(author_name="P", author_email="p@example.com")

    def test_rejects_noreply_without_id(self):
        with pytest.raises(ValueError):
            CommitIdentity(
                author_name="P", author_email="user@users.noreply.github.com"
            )

    def test_coauthor_kept(self):
        c = CommitIdentity(
            author_name="P",
            author_email="1+u@users.noreply.github.com",
            coauthor="Some Model <noreply@anthropic.com>",
        )
        assert "anthropic" in c.coauthor


class TestWakeupConfig:
    def _identity(self):
        return CommitIdentity(
            author_name="P", author_email="1+u@users.noreply.github.com"
        )

    def test_construction_public_only(self):
        cfg = WakeupConfig(
            public_repo=RepoRef(owner="acme", name="memo"),
            load_files=(LoadFile(path="dir/A.txt"),),
            commit_identity=self._identity(),
            directive_path="dir/Directive.md",
        )
        assert cfg.public_repo.owner == "acme"
        assert len(cfg.load_files) == 1
        assert cfg.private_repo is None

    def test_construction_with_private(self):
        cfg = WakeupConfig(
            public_repo=RepoRef(owner="acme", name="memo"),
            load_files=(
                LoadFile(path="dir/A.txt"),
                LoadFile(path="dir/B.md", required=False),
            ),
            commit_identity=self._identity(),
            directive_path="dir/Directive.md",
            private_repo=RepoRef(owner="acme", name="private", visibility="private"),
        )
        assert cfg.private_repo is not None
        assert cfg.private_repo.visibility == "private"
        assert len(cfg.load_files) == 2

    def test_load_repo_prefers_private(self):
        """Boot memory lives in the private repo under private-by-default."""
        cfg = WakeupConfig(
            public_repo=RepoRef(owner="acme", name="memo"),
            load_files=(LoadFile(path="dir/A.txt"),),
            commit_identity=self._identity(),
            directive_path="dir/Directive.md",
            private_repo=RepoRef(owner="acme", name="private", visibility="private"),
        )
        assert cfg.load_repo == cfg.private_repo

    def test_load_repo_falls_back_to_public_when_no_private(self):
        """Public-only personas keep resolving boot files against the public repo."""
        cfg = WakeupConfig(
            public_repo=RepoRef(owner="acme", name="memo"),
            load_files=(LoadFile(path="dir/A.txt"),),
            commit_identity=self._identity(),
            directive_path="dir/Directive.md",
        )
        assert cfg.load_repo == cfg.public_repo


class TestDirectivePathValidation:
    """``directive_path`` is joined onto the deployed skill root, so it must stay inside it.

    Personas name their own directive (any name, any depth), hence the rule is
    structural — relative, POSIX, no parent escape — never a fixed filename.
    """

    def _cfg(self, directive_path):
        return WakeupConfig(
            public_repo=RepoRef(owner="acme", name="memo"),
            load_files=(LoadFile(path="dir/A.txt"),),
            commit_identity=CommitIdentity(
                author_name="P", author_email="1+u@users.noreply.github.com"
            ),
            directive_path=directive_path,
        )

    @pytest.mark.parametrize(
        "good", ["directive.md", "personas/foo/directive.md", "A.md"]
    )
    def test_accepts_relative_paths_of_any_depth(self, good):
        assert self._cfg(good).directive_path == good

    @pytest.mark.parametrize(
        "bad",
        [
            "",  # unset
            "   ",  # blank
            "/etc/passwd",  # absolute (POSIX)
            "C:/dir/d.md",  # absolute (Windows drive)
            "sub\\d.md",  # backslash separator: breaks on the Linux sandbox
            "../d.md",  # parent escape
            "sub/../../d.md",  # parent escape mid-path
            "..",  # bare parent
            "sub//d.md",  # empty segment
            "sub/",  # directory, not a file
        ],
    )
    def test_rejects_unsafe_or_unusable_paths(self, bad):
        with pytest.raises(ValueError):
            self._cfg(bad)
