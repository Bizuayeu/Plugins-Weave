"""Pure builders for raw-content URLs and PR branch names. No I/O, no secrets."""

from __future__ import annotations

from domain.models import RepoRef


def build_raw_url(repo: RepoRef, ref: str, path: str) -> str:
    """raw.githubusercontent.com URL for ``path`` at ``ref`` (a sha or branch).

    A token is NEVER embedded in the URL; callers authenticate with an
    Authorization header so the secret cannot leak via logs or referrers.
    """
    return f"https://raw.githubusercontent.com/{repo.owner}/{repo.name}/{ref}/{path}"


def build_pr_branch_name(topic: str, prefix: str = "claude") -> str:
    """Deterministic branch name ``'<prefix>/<slug>'`` (spaces->hyphens, lowercased)."""
    slug = "-".join(topic.split()).lower()
    return f"{prefix}/{slug}"
