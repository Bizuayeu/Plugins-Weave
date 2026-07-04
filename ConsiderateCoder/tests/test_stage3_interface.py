"""Stage 3 (Interface layer) structure tests for the ConsiderateCoder plugin.

Verifies the generalized /plan-sdd command, the new /outsource command, and
the self-contained HTML report template exist and satisfy the Interface-layer
contract (frontmatter, orchestrator delegation, deletion-policy branch,
template self-containment). Stdlib only: re / pathlib. No external
dependencies, no conftest.
"""
import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
PLAN_SDD_PATH = PLUGIN_ROOT / "commands" / "plan-sdd.md"
OUTSOURCE_PATH = PLUGIN_ROOT / "commands" / "outsource.md"
DIG_PATH = PLUGIN_ROOT / "commands" / "dig.md"
TEMPLATE_PATH = PLUGIN_ROOT / "templates" / "outsource-report.template.html"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)

LITERAL_FORBIDDEN_TOKENS = [
    "初陣",
    "実証",
    r"C:\Users",
    "C:/Users",
    "Homunculus",
    "anyth",
]
DATE_PATTERN = re.compile(r"20\d\d-\d\d")

REQUIRED_PLACEHOLDERS = [
    "{{TITLE}}",
    "{{DATE}}",
    "{{SUMMARY}}",
    "{{CHANGES}}",
    "{{EVIDENCE}}",
    "{{ESCALATIONS}}",
    "{{QUIZ_ITEMS}}",
]


def _split_frontmatter(path):
    assert path.exists(), f"missing {path}"
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    assert m, f"{path.name}: frontmatter delimiters (---) not found"
    return m.group(1), m.group(2), text


def test_command_frontmatter():
    """Both commands exist and declare description/argument-hint in frontmatter."""
    for path in (PLAN_SDD_PATH, OUTSOURCE_PATH):
        frontmatter, _, _ = _split_frontmatter(path)
        for key in ("description", "argument-hint"):
            assert re.search(rf"^{key}:", frontmatter, re.MULTILINE), (
                f"{path.name} missing {key!r} in frontmatter"
            )


def test_dig_command_exists():
    """dig.md is bundled with a description in its frontmatter (it takes no
    arguments, so argument-hint is not required)."""
    frontmatter, _, _ = _split_frontmatter(DIG_PATH)
    assert re.search(r"^description:", frontmatter, re.MULTILINE), (
        "dig.md missing 'description' in frontmatter"
    )


def test_commands_show_usage_when_called_without_args():
    """plan-sdd and outsource define a no-argument help branch so a bare
    invocation explains how to use them instead of guessing at intent."""
    for path in (PLAN_SDD_PATH, OUTSOURCE_PATH):
        text = path.read_text(encoding="utf-8")
        assert "引数が空の場合" in text, (
            f"{path.name} missing the no-argument help branch"
        )


def test_outsource_references_orchestrator():
    """outsource body must synchronously launch ConsiderateCoder:orchestrator
    (bg launches would silently drop the final report per the orchestrator's
    own communication discipline)."""
    _, body, _ = _split_frontmatter(OUTSOURCE_PATH)
    assert "ConsiderateCoder:orchestrator" in body, (
        "outsource body must reference ConsiderateCoder:orchestrator"
    )
    assert "run_in_background: false" in body, (
        "outsource body must instruct a synchronous (run_in_background: false) launch"
    )


def test_report_template_self_contained():
    """template has zero external resource loads and a JS-free <details> quiz
    structure, with all 7 placeholders present for the interface to fill in."""
    assert TEMPLATE_PATH.exists(), f"missing {TEMPLATE_PATH}"
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    lower = text.lower()

    assert "<script" not in lower, "template must not include <script> tags"
    for forbidden in ('src="http', 'href="http', "@import", 'rel="stylesheet"'):
        assert forbidden not in lower, (
            f"template must not include external resource load: {forbidden!r}"
        )

    assert "<details" in lower, "template must use <details> for quiz items"
    assert "<summary" in lower, "template must use <summary> for quiz items"

    for placeholder in REQUIRED_PLACEHOLDERS:
        assert placeholder in text, f"template missing placeholder: {placeholder}"


def test_deletion_policy_branch():
    """Both commands document the IMPLEMENTATION_PLAN.md deletion-policy
    branch: plan-sdd alone deletes it after all Stages complete (unchanged),
    but /outsource does not auto-delete it (kept as the report/quiz source
    and acceptance-check reference). plan-sdd.md must state this in close
    (same or <=3 line) proximity to its /outsource mention, so the branch
    reads as one policy rather than two unrelated facts.
    """
    for path in (PLAN_SDD_PATH, OUTSOURCE_PATH):
        text = path.read_text(encoding="utf-8")
        assert "自動削除しない" in text, (
            f"{path.name} missing the '自動削除しない' deletion-policy phrase"
        )

    plan_sdd_text = PLAN_SDD_PATH.read_text(encoding="utf-8")
    lines = plan_sdd_text.splitlines()
    outsource_line_idxs = [
        i for i, line in enumerate(lines) if "outsource" in line.lower()
    ]
    deletion_line_idxs = [i for i, line in enumerate(lines) if "自動削除しない" in line]
    assert outsource_line_idxs, "plan-sdd.md has no /outsource mention"
    assert deletion_line_idxs, "plan-sdd.md has no '自動削除しない' line"

    assert any(
        abs(o - d) <= 3 for o in outsource_line_idxs for d in deletion_line_idxs
    ), (
        "plan-sdd.md's '自動削除しない' phrase must be within 3 lines of its "
        "/outsource mention"
    )


def test_plugin_internal_refs_use_plugin_root():
    """Command bodies must reference plugin-internal files via
    ${CLAUDE_PLUGIN_ROOT}, never via cwd-relative ../ links — the runtime
    cwd is the user's project, so ../ links break after installation."""
    for path in (PLAN_SDD_PATH, OUTSOURCE_PATH, DIG_PATH):
        text = path.read_text(encoding="utf-8")
        assert "](../" not in text, (
            f"{path.name} contains cwd-relative plugin-internal link(s)"
        )
    for path in (PLAN_SDD_PATH, OUTSOURCE_PATH):
        text = path.read_text(encoding="utf-8")
        assert "${CLAUDE_PLUGIN_ROOT}/" in text, (
            f"{path.name} must reference bundled files via "
            "${CLAUDE_PLUGIN_ROOT}"
        )


def test_interactive_commands_not_forked():
    """Commands whose flow depends on AskUserQuestion must run in the main
    conversation: AskUserQuestion depends on the main conversation's UI and
    is silently unavailable in subagents (context: fork included, even when
    listed in tools), so a forked interviewer degrades into guessing
    instead of asking."""
    for path in (PLAN_SDD_PATH, OUTSOURCE_PATH, DIG_PATH):
        frontmatter, _, _ = _split_frontmatter(path)
        assert not re.search(r"^context:\s*fork\b", frontmatter, re.MULTILINE), (
            f"{path.name} must not use context: fork "
            "(its AskUserQuestion flow would silently fail)"
        )


def test_no_forbidden_tokens():
    """None of the three Interface-layer artifacts may carry development-only
    evidence (local paths, dates, proof-count callouts). {{DATE}} is a literal
    placeholder token, not a YYYY-MM date, so it does not trip DATE_PATTERN.
    """
    for path in (PLAN_SDD_PATH, OUTSOURCE_PATH, DIG_PATH, TEMPLATE_PATH):
        text = path.read_text(encoding="utf-8")
        for token in LITERAL_FORBIDDEN_TOKENS:
            assert token not in text, f"{path.name} contains forbidden token: {token!r}"
        assert not DATE_PATTERN.search(text), (
            f"{path.name} contains a date-like pattern (YYYY-MM)"
        )
