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


RULE_SKILLS = (
    PLUGIN_ROOT / "skills" / "dev-rules" / "SKILL.md",
    PLUGIN_ROOT / "skills" / "ops-rules" / "SKILL.md",
)


def test_rule_skills_exist_and_generic():
    """Both rule skills exist with skill frontmatter (name/description) and
    carry no workspace-specific tokens."""
    for path in RULE_SKILLS:
        assert path.exists(), f"missing {path}"
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---"), f"{path} missing frontmatter"
        assert re.search(r"^name:", text, re.MULTILINE), f"{path} missing name:"
        assert re.search(r"^description:", text, re.MULTILINE), (
            f"{path} missing description:"
        )
        for token in FORBIDDEN_TOKENS:
            assert token not in text, f"{path.name} contains forbidden token: {token!r}"


def test_dev_rules_latest_and_self_contained():
    """dev-rules carries the CI static-check line (stale-copy regression
    check) and must be self-contained: subagents do not receive the full
    Claude Code system prompt, so the rules may not defer to it."""
    text = RULE_SKILLS[0].read_text(encoding="utf-8")
    assert "CI と同じ静的チェック" in text, (
        "dev-rules missing the push-time CI static-check line"
    )
    assert "System Prompt" not in text, (
        "dev-rules must not defer to the Claude Code system prompt "
        "(false premise in subagent context)"
    )
