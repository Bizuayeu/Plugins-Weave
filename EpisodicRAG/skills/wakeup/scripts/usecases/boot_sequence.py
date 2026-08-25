"""BootSequence — the boot ordering contract: load public memory with required/optional policy.

Private reference and write-back are on-demand (handled by the SKILL.md procedure),
so they are deliberately not part of ``run()``. This class is the testable SSoT for
the load order and the required/optional boot policy only (YAGNI).
"""

from __future__ import annotations

from domain.exceptions import WakeupError
from domain.models import WakeupConfig
from usecases.ports import MemoryLoaderPort


class BootSequence:
    def __init__(
        self,
        config: WakeupConfig,
        memory_loader: MemoryLoaderPort,
    ) -> None:
        self._config = config
        self._loader = memory_loader

    def run(self) -> dict[str, str]:
        """Load public memory and enforce the required-file policy.

        Returns the loaded ``{path: content}``. Raises :class:`WakeupError` if any
        *required* file could not be loaded; missing *optional* files are tolerated.
        """
        loaded = self._loader.load_public(
            self._config.public_repo, self._config.load_files
        )
        missing_required = [
            f.path
            for f in self._config.load_files
            if f.required and f.path not in loaded
        ]
        if missing_required:
            raise WakeupError(f"required boot files unavailable: {missing_required}")
        return loaded
