"""Tests for hooks/emotion_writer_launcher.py — sys.path managed CLI entry."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from scripts.infrastructure.path_resolver import (
    get_plugin_root,
    get_state_file_path,
)


def _env_without_coverage() -> dict[str, str]:
    """Child env with pytest-cov's subprocess instrumentation removed.

    The launcher runs with cwd=tmp_path, where the parent's coverage config is
    not discoverable. An instrumented child would record statement-only data and
    break the parent's combine ("Can't combine statement coverage data with
    branch data"). The launcher's own coverage is not what this test measures.
    """
    return {k: v for k, v in os.environ.items() if not k.startswith("COV_CORE_")}


def _launcher_path() -> Path:
    """Resolve the expected launcher path; fails the test early if absent."""
    root = get_plugin_root()
    assert root is not None, (
        "Plugin root not found; ensure DEV or marketplace copy exists"
    )
    return root / "hooks" / "emotion_writer_launcher.py"


class TestEmotionWriterLauncherStructure:
    """Static structural invariants of the launcher source."""

    def test_launcher_file_exists(self) -> None:
        assert _launcher_path().is_file()

    def test_launcher_inserts_plugin_dir_to_syspath(self) -> None:
        """launcher は sys.path.insert で plugin_dir を通してから import する."""
        content = _launcher_path().read_text(encoding="utf-8")
        assert "sys.path.insert" in content

    def test_launcher_imports_emotion_writer_main(self) -> None:
        """launcher が emotion_writer.main を呼ぶ."""
        content = _launcher_path().read_text(encoding="utf-8")
        assert "from scripts.interfaces.emotion_writer import main" in content


class TestEmotionWriterLauncherIntegration:
    """End-to-end: launcher の subprocess 実行で state file が更新される."""

    def _with_backed_up_state(self, func):
        """Run func while preserving the real emotion_state.json."""
        state_path = get_state_file_path()
        backup = state_path.read_bytes() if state_path.is_file() else None
        try:
            func()
        finally:
            if backup is not None:
                state_path.write_bytes(backup)
            elif state_path.is_file():
                state_path.unlink()

    def test_launcher_survives_conflicting_scripts_module_in_cwd(
        self, tmp_path: Path
    ) -> None:
        """cwd に scripts/__init__.py があっても launcher は動く (import 衝突回避)."""
        conflict_dir = tmp_path / "scripts"
        conflict_dir.mkdir()
        (conflict_dir / "__init__.py").write_text(
            "raise ImportError('conflicting plugin scripts module loaded')\n",
            encoding="utf-8",
        )

        payload = json.dumps(
            {
                "desperation": 1,
                "calm": 1,
                "curiosity": 1,
                "playfulness": 1,
                "confidence": 1,
                "rapport": 1,
                "empathy": 1,
            }
        )

        result_holder: dict[str, subprocess.CompletedProcess[str]] = {}

        def run() -> None:
            result_holder["r"] = subprocess.run(
                [sys.executable, str(_launcher_path()), payload],
                cwd=str(tmp_path),
                env=_env_without_coverage(),
                capture_output=True,
                text=True,
                timeout=15,
            )

        self._with_backed_up_state(run)
        result = result_holder["r"]
        assert result.returncode == 0, (
            f"Launcher failed in conflicting cwd: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
