"""Stage 1: pure URL / branch-name builders.

Security invariant under test: a raw URL never embeds a token
(the engine authenticates via the Authorization header instead).
"""

from domain.models import RepoRef
from domain.urls import build_pr_branch_name, build_raw_url


class TestBuildRawUrl:
    def test_basic(self):
        repo = RepoRef(owner="acme", name="memo")
        url = build_raw_url(repo, "abc123", "dir/A.txt")
        assert url == "https://raw.githubusercontent.com/acme/memo/abc123/dir/A.txt"

    def test_nested_path(self):
        repo = RepoRef(owner="acme", name="memo")
        assert build_raw_url(repo, "sha", "a/b/c.md").endswith("/sha/a/b/c.md")

    def test_no_token_embedded(self):
        repo = RepoRef(owner="acme", name="memo")
        url = build_raw_url(repo, "main", "dir/A.txt")
        assert "token" not in url.lower()
        assert "@" not in url  # never the user:token@host form


class TestBuildPrBranchName:
    def test_default_prefix(self):
        assert build_pr_branch_name("update-log") == "claude/update-log"

    def test_custom_prefix(self):
        assert build_pr_branch_name("topic", prefix="bot") == "bot/topic"

    def test_slugifies_spaces_and_case(self):
        assert build_pr_branch_name("Update WORKLOG") == "claude/update-worklog"
