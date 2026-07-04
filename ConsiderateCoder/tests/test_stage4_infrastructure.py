"""Stage 4 (Infrastructure/distribution layer) structure tests for the
ConsiderateCoder plugin.

Verifies the marketplace.json entry mirrors plugin.json exactly, the
methodology README's relative links all resolve, and neither README.md nor
CHANGELOG.md carry development-only local-environment tokens (the date-like
pattern check applies to README.md only, since CHANGELOG.md release dates
are legitimate record-keeping, not development-session leakage).
Stdlib only: json / re / pathlib. No external dependencies, no conftest.
"""
import json
import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE_PATH = PLUGIN_ROOT.parent / ".claude-plugin" / "marketplace.json"
PLUGIN_MANIFEST_PATH = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
README_PATH = PLUGIN_ROOT / "README.md"
CHANGELOG_PATH = PLUGIN_ROOT / "CHANGELOG.md"

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

FORBIDDEN_TOKENS = [
    r"C:\Users",
    "C:/Users",
    "Homunculus",
    "anyth",
    "初陣",
    "実証",
]
DATE_PATTERN = re.compile(r"20\d\d-\d\d")


def test_marketplace_entry_consistency():
    """marketplace.json top-level version is semver and carries exactly one
    ConsiderateCoder entry whose fields mirror plugin.json 1:1."""
    assert MARKETPLACE_PATH.exists(), f"missing {MARKETPLACE_PATH}"
    assert PLUGIN_MANIFEST_PATH.exists(), f"missing {PLUGIN_MANIFEST_PATH}"

    marketplace = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(PLUGIN_MANIFEST_PATH.read_text(encoding="utf-8"))

    assert re.fullmatch(r"\d+\.\d+\.\d+", marketplace["version"]), (
        f"marketplace top-level version must be semver (X.Y.Z), "
        f"got {marketplace['version']!r}"
    )

    entries = [p for p in marketplace["plugins"] if p.get("name") == "ConsiderateCoder"]
    assert entries, "marketplace.json has no ConsiderateCoder plugin entry"
    assert len(entries) == 1, "marketplace.json has duplicate ConsiderateCoder entries"
    entry = entries[0]

    assert entry["source"] == "./ConsiderateCoder"

    for key in ("description", "version", "license", "keywords"):
        assert entry[key] == manifest[key], (
            f"marketplace entry {key!r} ({entry[key]!r}) != "
            f"plugin.json {key!r} ({manifest[key]!r})"
        )
    # author/homepage/repository are boilerplate shared across all plugin
    # entries; the update spec requires literal 1:1 mirroring of plugin.json
    # for these fields too, so verify them alongside the mandated four.
    assert entry["author"] == manifest["author"]
    assert entry["homepage"] == manifest["homepage"]
    assert entry["repository"] == manifest["repository"]


def test_readme_links_resolve():
    """Every relative (non-http, non-anchor) markdown link in README.md
    resolves to a real file/dir under PLUGIN_ROOT."""
    assert README_PATH.exists(), f"missing {README_PATH}"
    text = README_PATH.read_text(encoding="utf-8")

    targets = LINK_RE.findall(text)
    relative_targets = [
        t for t in targets if not t.startswith("http") and not t.startswith("#")
    ]
    assert relative_targets, "README.md has no relative links to verify"

    for target in relative_targets:
        resolved = PLUGIN_ROOT / target
        assert resolved.exists(), f"README.md link target does not exist: {target!r}"


def test_readme_and_changelog_generic():
    """README.md and CHANGELOG.md carry no local-environment/dev-session
    tokens; the YYYY-MM date-pattern check applies to README.md only."""
    assert README_PATH.exists(), f"missing {README_PATH}"
    assert CHANGELOG_PATH.exists(), f"missing {CHANGELOG_PATH}"

    readme_text = README_PATH.read_text(encoding="utf-8")
    changelog_text = CHANGELOG_PATH.read_text(encoding="utf-8")

    for text, name in ((readme_text, "README.md"), (changelog_text, "CHANGELOG.md")):
        for token in FORBIDDEN_TOKENS:
            assert token not in text, f"{name} contains forbidden token: {token!r}"

    assert not DATE_PATTERN.search(readme_text), (
        "README.md contains a date-like pattern (YYYY-MM)"
    )
