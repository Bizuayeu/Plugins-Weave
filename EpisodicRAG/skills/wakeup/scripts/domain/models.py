"""Domain value objects describing a session-boot spec.

Pure data + validation only. The engine hardcodes nothing persona-specific;
every concrete value (repos, files, commit identity) arrives via config.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# GitHub noreply form: "<numeric-id>+<login>@users.noreply.github.com".
# Enforced so a raw address (e.g. Gmail) is never committed into a public repo.
_NOREPLY_RE = re.compile(r"^\d+\+[A-Za-z0-9-]+@users\.noreply\.github\.com$")

# Windows drive prefix ("C:/..."), rejected together with POSIX absolute paths.
_DRIVE_RE = re.compile(r"^[A-Za-z]:")


def _validate_directive_path(path: str) -> None:
    """Reject a ``directive_path`` that cannot resolve inside the deployed skill root.

    The name is the persona's choice (any name, any depth), so the rule is
    structural: a relative POSIX path with no parent escape and no empty segment.
    Deployment is Linux, hence a backslash is a separator typo, not a filename.
    """
    if not path.strip():
        raise ValueError("directive_path must not be empty")
    if "\\" in path:
        raise ValueError(f"directive_path must use '/' separators (deployment is Linux): {path!r}")
    if path.startswith("/") or _DRIVE_RE.match(path):
        raise ValueError(f"directive_path must be relative to the config, not absolute: {path!r}")
    segments = path.split("/")
    if ".." in segments:
        raise ValueError(f"directive_path must not escape the skill root: {path!r}")
    if any(not s for s in segments):
        raise ValueError(f"directive_path must name a file, with no empty segment: {path!r}")


@dataclass(frozen=True)
class RepoRef:
    """A GitHub repository reference."""

    owner: str
    name: str
    branch: str = "main"
    visibility: str = "public"  # "public" | "private"


@dataclass(frozen=True)
class LoadFile:
    """A file to load at boot. A ``required`` file aborts boot on failure."""

    path: str
    label: str = ""
    required: bool = True


@dataclass(frozen=True)
class CommitIdentity:
    """Authorship of write-back commits. ``author_email`` must be a GitHub noreply."""

    author_name: str
    author_email: str
    coauthor: str = ""

    def __post_init__(self) -> None:
        if not _NOREPLY_RE.match(self.author_email):
            raise ValueError(
                "author_email must be a GitHub noreply address "
                "('<id>+<login>@users.noreply.github.com'); "
                f"refusing raw address {self.author_email!r}"
            )


@dataclass(frozen=True)
class WakeupConfig:
    """Complete boot spec. ``private_repo`` is optional (public-only setups)."""

    public_repo: RepoRef
    load_files: tuple[LoadFile, ...]
    commit_identity: CommitIdentity
    directive_path: str
    private_repo: RepoRef | None = None

    def __post_init__(self) -> None:
        _validate_directive_path(self.directive_path)

    @property
    def load_repo(self) -> RepoRef:
        """Repo to load boot memory from: private if configured, else public.

        Under private-by-default, boot memory (GrandDigest etc.) lives only in
        the private repo; public-only personas fall back to the public repo.
        """
        return self.private_repo or self.public_repo
