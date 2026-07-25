"""VerifyDeployment — the pre-boot deployment contract (Step 1 of the SKILL.md flow).

Step 2 (memory load) already fails loudly via :class:`BootSequence`, but Step 3
(apply the directive) is a Markdown read, so a config/directive/token that was
never placed at the skill root used to pass silently. This use case turns those
deployed artifacts into checked preconditions and fingerprints the load repo —
one deployed skill holds one config, so a stale config from another persona is a
real hazard worth naming before boot.

Pure orchestration: all filesystem and archive access arrives via
:class:`~usecases.ports.DeploymentProbePort`.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.exceptions import WakeupError
from usecases.ports import DeploymentProbePort

_SKIPPED = "skipped (config unreadable)"


@dataclass(frozen=True)
class CheckResult:
    """One deployment precondition and what was found."""

    name: str
    ok: bool
    detail: str

    def line(self) -> str:
        """Human-readable single line (never carries secrets — only names and sizes)."""
        return f"{self.name:<10}: {'ok' if self.ok else 'FAIL'}  ({self.detail})"


@dataclass(frozen=True)
class VerificationReport:
    checks: tuple[CheckResult, ...]

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)

    def lines(self) -> list[str]:
        return [c.line() for c in self.checks]


class VerifyDeployment:
    def __init__(self, probe: DeploymentProbePort) -> None:
        self._probe = probe

    def run(self) -> VerificationReport:
        """Check config, directive and token; never raise for a failed check."""
        try:
            config = self._probe.load_config()
        except WakeupError as exc:
            # Report and carry on: the token check does not depend on the config.
            return VerificationReport(
                (
                    CheckResult("config", False, str(exc)),
                    CheckResult("directive", False, _SKIPPED),
                    self._token_check(),
                )
            )

        repo = config.load_repo
        required = sum(1 for f in config.load_files if f.required)
        optional = len(config.load_files) - required
        config_check = CheckResult(
            "config",
            True,
            f"load_repo={repo.owner}/{repo.name}@{repo.branch} ({repo.visibility}), "
            f"load_files={len(config.load_files)} (required {required} / optional {optional})",
        )

        rel = config.directive_path
        size = self._probe.directive_size(rel)
        if size is None:
            directive_check = CheckResult("directive", False, f"{rel} not found under skill root")
        elif size == 0:
            directive_check = CheckResult("directive", False, f"{rel} is empty")
        else:
            directive_check = CheckResult("directive", True, f"{rel}, {size} bytes")

        return VerificationReport((config_check, directive_check, self._token_check()))

    def _token_check(self) -> CheckResult:
        """A token is required even for public repos: the SHA fetch needs auth."""
        archives = self._probe.token_archives()
        if not archives:
            return CheckResult("token", False, "no token archive at skill root")
        readable = [name for name in archives if self._probe.token_readable(name)]
        if not readable:
            return CheckResult("token", False, f"unreadable: {', '.join(archives)}")
        return CheckResult("token", True, f"{', '.join(readable)} readable")


__all__ = ["CheckResult", "VerificationReport", "VerifyDeployment"]
