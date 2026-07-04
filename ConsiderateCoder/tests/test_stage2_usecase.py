"""Stage 2 (UseCase layer) structure tests for the ConsiderateCoder plugin.

Verifies the generalized agent definitions (orchestrator/worker) exist,
reference the namespaced worker correctly, and carry no development-only
evidence references (dates, proof counts, local-environment paths).
Stdlib only: re / pathlib. No external dependencies, no conftest.
"""
import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
ORCHESTRATOR_PATH = PLUGIN_ROOT / "agents" / "orchestrator.md"
WORKER_PATH = PLUGIN_ROOT / "agents" / "worker.md"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)

LITERAL_FORBIDDEN_TOKENS = [
    "初陣",
    "実証",
    "fable",
    r"C:\Users",
    "C:/Users",
    "Homunculus",
    "anyth",
]
DATE_PATTERN = re.compile(r"20\d\d-\d\d")


def _split_frontmatter(path):
    assert path.exists(), f"missing {path}"
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    assert m, f"{path.name}: frontmatter delimiters (---) not found"
    return m.group(1), m.group(2), text


def test_agent_frontmatter():
    """Both agents declare name/description/model; orchestrator's tools
    line excludes Edit/Write (structural guarantee: the commander cannot
    touch files directly). Word-boundary matching avoids false positives
    on legitimate tools like TodoWrite (contains "Write").
    """
    for path in (ORCHESTRATOR_PATH, WORKER_PATH):
        frontmatter, _, _ = _split_frontmatter(path)
        for key in ("name", "description", "model"):
            assert re.search(rf"^{key}:", frontmatter, re.MULTILINE), (
                f"{path.name} missing {key!r} in frontmatter"
            )

    orchestrator_fm, _, _ = _split_frontmatter(ORCHESTRATOR_PATH)
    tools_match = re.search(r"^tools:\s*(.+)$", orchestrator_fm, re.MULTILINE)
    assert tools_match, "orchestrator frontmatter missing tools line"
    tools_line = tools_match.group(1)
    assert not re.search(r"\bEdit\b", tools_line), (
        f"orchestrator tools line must not include Edit: {tools_line!r}"
    )
    assert not re.search(r"\bWrite\b", tools_line), (
        f"orchestrator tools line must not include Write: {tools_line!r}"
    )


def test_orchestrator_references_namespaced_worker():
    """orchestrator body must delegate via the namespaced worker
    (ConsiderateCoder:worker); a bare `subagent_type: worker` would not
    resolve once the agent is installed as a plugin.
    """
    _, body, _ = _split_frontmatter(ORCHESTRATOR_PATH)
    assert "ConsiderateCoder:worker" in body, (
        "orchestrator body must reference ConsiderateCoder:worker"
    )
    bare_refs = re.findall(r"subagent_type:\s*worker\b", body)
    assert not bare_refs, (
        f"bare (non-namespaced) subagent_type: worker reference(s) found: {bare_refs}"
    )


def test_structural_tool_guarantees():
    """Structural guarantees on both sides of the delegation: the
    orchestrator cannot send async messages (no SendMessage — its own
    discipline bans round-trips), and the worker cannot re-delegate
    (Agent is disallowed). Discipline is culture; the tool list is law."""
    orchestrator_fm, _, _ = _split_frontmatter(ORCHESTRATOR_PATH)
    tools_line = re.search(
        r"^tools:\s*(.+)$", orchestrator_fm, re.MULTILINE
    ).group(1)
    assert not re.search(r"\bSendMessage\b", tools_line), (
        f"orchestrator tools must not include SendMessage: {tools_line!r}"
    )

    worker_fm, _, _ = _split_frontmatter(WORKER_PATH)
    disallowed_match = re.search(
        r"^disallowedTools:\s*(.+)$", worker_fm, re.MULTILINE
    )
    assert disallowed_match, "worker frontmatter missing disallowedTools line"
    assert re.search(r"\bAgent\b", disallowed_match.group(1)), (
        f"worker disallowedTools must include Agent (no re-delegation): "
        f"{disallowed_match.group(1)!r}"
    )


def test_agents_wired_to_rules():
    """Both agent bodies must explicitly Read the bundled DEV.md via
    ${CLAUDE_PLUGIN_ROOT} — the plugin loader does not auto-discover
    rules/, so an unreferenced rules file is a dead file."""
    for path in (ORCHESTRATOR_PATH, WORKER_PATH):
        _, body, _ = _split_frontmatter(path)
        assert "${CLAUDE_PLUGIN_ROOT}/rules/DEV.md" in body, (
            f"{path.name} body must reference "
            "${CLAUDE_PLUGIN_ROOT}/rules/DEV.md"
        )


def test_no_dev_evidence_refs():
    """Neither agent may carry development-session evidence: dates,
    proof-count callouts, local model assumptions, or local paths.
    """
    for path in (ORCHESTRATOR_PATH, WORKER_PATH):
        assert path.exists(), f"missing {path}"
        text = path.read_text(encoding="utf-8")
        for token in LITERAL_FORBIDDEN_TOKENS:
            assert token not in text, f"{path.name} contains forbidden token: {token!r}"
        assert not DATE_PATTERN.search(text), (
            f"{path.name} contains a date-like pattern (YYYY-MM)"
        )
