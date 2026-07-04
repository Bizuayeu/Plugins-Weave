"""Stage 1 (Domain layer) structure tests for the ConsiderateCoder plugin.

Verifies the plugin skeleton exists and that the copied rules files are
generalized (no workspace-specific tokens leaked from the source copy).
Stdlib only: json / re / pathlib. No external dependencies, no conftest.
"""
import json
import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN_TOKENS = [
    r"C:\Users",
    "C:/Users",
    "Homunculus",
    "anyth",
    "初陣",
    "実証済",
]


def test_plugin_manifest():
    manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
    assert manifest_path.exists(), f"missing {manifest_path}"

    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert data["name"] == "ConsiderateCoder"
    assert re.fullmatch(r"\d+\.\d+\.\d+", data["version"]), (
        f"version must be semver (X.Y.Z), got {data['version']!r}"
    )
    assert data["license"] == "MIT"
    assert data["description"], "description must be non-empty"

    for key in ("author", "homepage", "repository", "keywords"):
        assert key in data, f"missing key: {key}"


def test_rules_exist_and_generic():
    for name in ("DEV.md", "OPS.md"):
        rule_path = PLUGIN_ROOT / "rules" / name
        assert rule_path.exists(), f"missing {rule_path}"

        text = rule_path.read_text(encoding="utf-8")
        for token in FORBIDDEN_TOKENS:
            assert token not in text, f"{name} contains forbidden token: {token!r}"


def test_dev_md_is_latest():
    dev_md_path = PLUGIN_ROOT / "rules" / "DEV.md"
    text = dev_md_path.read_text(encoding="utf-8")
    assert "CI と同じ静的チェック" in text, (
        "DEV.md missing the push-time CI static-check line "
        "(stale copy regression check)"
    )
