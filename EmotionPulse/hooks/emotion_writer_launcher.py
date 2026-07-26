"""EmotionPulse Writer launcher - delegates to installed plugin.

Resolves the plugin root (DEV or marketplace), inserts it at sys.path[0] so
that `from scripts.interfaces.emotion_writer import main` loads the correct
module regardless of the caller's cwd, and forwards sys.argv to main().

Pair with hooks/stop_handler.py; both follow the same pattern.
"""

import io
import os
import sys

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

_CANDIDATE_PATHS = [
    os.path.expanduser("~/DEV/plugins-weave/EmotionPulse"),
    os.path.expanduser("~/.claude/plugins/marketplaces/plugins-weave/EmotionPulse"),
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
]

_plugin_dir = None
for p in _CANDIDATE_PATHS:
    if os.path.isdir(os.path.join(p, "scripts")):
        _plugin_dir = p
        break

if _plugin_dir is None:
    sys.exit(1)

sys.path.insert(0, _plugin_dir)

from scripts.interfaces.emotion_writer import main

main()
