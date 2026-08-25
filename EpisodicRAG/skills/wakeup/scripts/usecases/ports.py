"""Use Case port interfaces — the abstractions the Infrastructure/SKILL layer implements.

Protocols are runtime_checkable so fakes can be asserted in tests. No persona values.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, TypeVar, runtime_checkable

from domain.models import LoadFile, RepoRef, WakeupConfig

T = TypeVar("T")


@runtime_checkable
class MemoryLoaderPort(Protocol):
    """Loads public files at boot (public repos need no auth)."""

    def load_public(self, repo: RepoRef, files: tuple[LoadFile, ...]) -> dict[str, str]:
        """Return ``{path: content}`` for the files that could be fetched.

        Missing files are simply absent from the dict; this port never decides
        whether that is fatal — the required/optional policy lives in BootSequence.
        """
        ...


@runtime_checkable
class SecretProviderPort(Protocol):
    """Hands a short-lived token to a callback, then drops it (no residency)."""

    def with_token(self, scope: str, fn: Callable[[str], T]) -> T:
        """Call ``fn(token)`` and return its result; release the token afterward."""
        ...


@runtime_checkable
class DeploymentProbePort(Protocol):
    """Inspects the deployed skill root (config / directive / token) before boot.

    All paths are resolved by the implementation against its own root, so the
    use case never does path math — and never sees a token's contents.
    """

    def load_config(self) -> WakeupConfig:
        """Return the deployed config, raising ``ConfigError`` if unusable."""
        ...

    def directive_size(self, rel_path: str) -> int | None:
        """Size in bytes of ``rel_path`` under the root, or ``None`` if absent."""
        ...

    def token_archives(self) -> tuple[str, ...]:
        """Names of candidate token archives at the root (names only, no contents)."""
        ...

    def token_readable(self, name: str) -> bool:
        """Whether a token can actually be extracted from ``name`` (contents discarded)."""
        ...


@runtime_checkable
class VcsPort(Protocol):
    """Write-back via a feature branch + PR — never a direct push to the default branch."""

    def push_branch(self, branch: str, message: str) -> None:
        """Commit staged changes and push to ``branch`` (e.g. ``claude/...``)."""
        ...

    def open_pr(self, branch: str, title: str) -> str:
        """Open a PR from ``branch`` into the default branch; return its URL."""
        ...


__all__ = ["DeploymentProbePort", "MemoryLoaderPort", "SecretProviderPort", "VcsPort"]
