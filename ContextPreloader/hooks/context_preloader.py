"""ContextPreloader hook launcher - delegates to installed plugin.

Place this file at ~/.claude/hooks/context_preloader.py and configure
your .claude/settings.json SessionStart hook to call it:

  "command": "python \"~/.claude/hooks/context_preloader.py\""
  "command": "python \"~/.claude/hooks/context_preloader.py\" --profile myproject"

This thin launcher resolves the plugin location at runtime, supporting
both marketplace installs and local development paths.
"""
import io
import os
import sys
from pathlib import Path

# Ensure UTF-8 stdout (critical for non-ASCII text)
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Resolve plugin location - checks multiple candidate paths
# Add your dev path here if developing locally
_CANDIDATE_PATHS = [
    # sys.path へ入れるので str を保つ——Path を入れると import 機構が黙って
    # 素通りし ModuleNotFoundError になる（実測）。
    str(Path("~/.claude/plugins/marketplaces/plugins-weave/ContextPreloader").expanduser()),
]

# Allow override via environment variable
_env_path = os.environ.get("CONTEXTPRELOADER_PLUGIN_DIR")
if _env_path:
    _CANDIDATE_PATHS.insert(0, _env_path)

_plugin_dir = None
for p in _CANDIDATE_PATHS:
    if (Path(p) / "scripts").is_dir():
        _plugin_dir = p
        break

if _plugin_dir is None:
    print("ContextPreloader: Plugin not found. Searched:", file=sys.stderr)
    for p in _CANDIDATE_PATHS:
        print(f"  - {p}", file=sys.stderr)
    sys.exit(1)

# Add plugin dir to path so `scripts` package is importable
sys.path.insert(0, _plugin_dir)

from scripts.infrastructure.path_resolver import get_profile_path
from scripts.interfaces.hook_runner import run_hook

# Parse --profile from sys.argv
profile_path = None
if "--profile" in sys.argv:
    idx = sys.argv.index("--profile")
    if idx + 1 < len(sys.argv):
        profile_name = sys.argv[idx + 1]
        profile_path = str(get_profile_path(profile_name))

run_hook(profile=profile_path)
