"""EmotionPulse Stop hook launcher - delegates to installed plugin."""
import io
import os
import sys

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

_CANDIDATE_PATHS = [
    os.path.expanduser("~/DEV/plugins-weave/EmotionPulse"),
    os.path.expanduser("~/.claude/plugins/marketplaces/plugins-weave/EmotionPulse"),
]

_plugin_dir = None
for p in _CANDIDATE_PATHS:
    if os.path.isdir(os.path.join(p, "scripts")):
        _plugin_dir = p
        break

if _plugin_dir is None:
    # Non-fatal: approve to avoid blocking Claude Code
    import json
    print(json.dumps({"decision": "approve"}))
    sys.exit(0)

sys.path.insert(0, _plugin_dir)

from scripts.interfaces.stop_hook_handler import handle_stop

handle_stop()
