"""Stage 3 (Interface layer) structure tests for the ConsiderateCoder plugin.

Verifies the generalized /plan-sdd command, the /outsource and /refactor
commands, and the self-contained HTML report template exist and satisfy the
Interface-layer contract (frontmatter, orchestrator delegation,
deletion-policy branch, behavior-preserving refactor flow, template
self-containment). Stdlib only: re / pathlib. No external dependencies, no
conftest.
"""

import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
PLAN_SDD_PATH = PLUGIN_ROOT / "commands" / "plan-sdd.md"
OUTSOURCE_PATH = PLUGIN_ROOT / "commands" / "outsource.md"
DIG_PATH = PLUGIN_ROOT / "commands" / "dig.md"
REFACTOR_PATH = PLUGIN_ROOT / "commands" / "refactor.md"
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
    "{{NEXT_PLAN}}",
]


def _split_frontmatter(path: Path) -> tuple[str, str, str]:
    assert path.exists(), f"missing {path}"
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    assert m, f"{path.name}: frontmatter delimiters (---) not found"
    return m.group(1), m.group(2), text


def test_command_frontmatter() -> None:
    """The argument-taking commands exist and declare description/argument-hint
    in frontmatter."""
    for path in (PLAN_SDD_PATH, OUTSOURCE_PATH, REFACTOR_PATH):
        frontmatter, _, _ = _split_frontmatter(path)
        for key in ("description", "argument-hint"):
            assert re.search(rf"^{key}:", frontmatter, re.MULTILINE), (
                f"{path.name} missing {key!r} in frontmatter"
            )


def test_dig_command_exists() -> None:
    """dig.md is bundled with a description in its frontmatter (it takes no
    arguments, so argument-hint is not required)."""
    frontmatter, _, _ = _split_frontmatter(DIG_PATH)
    assert re.search(r"^description:", frontmatter, re.MULTILINE), (
        "dig.md missing 'description' in frontmatter"
    )


def test_commands_show_usage_when_called_without_args() -> None:
    """plan-sdd and outsource define a no-argument help branch so a bare
    invocation explains how to use them instead of guessing at intent."""
    for path in (PLAN_SDD_PATH, OUTSOURCE_PATH):
        text = path.read_text(encoding="utf-8")
        assert "引数が空の場合" in text, (
            f"{path.name} missing the no-argument help branch"
        )


def test_outsource_references_orchestrator() -> None:
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


def test_report_template_self_contained() -> None:
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


def test_deletion_policy_branch() -> None:
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


def test_plan_sdd_final_approval_phase() -> None:
    """plan-sdd closes with an AskUserQuestion approval phase whose *last*
    question always asks whether to proceed to /outsource. The '最後の設問'
    rule must sit in close (same or <=3 line) proximity to the /outsource
    mention, so the ordering reads as one rule rather than two unrelated
    facts (same proximity pattern as test_deletion_policy_branch).
    """
    text = PLAN_SDD_PATH.read_text(encoding="utf-8")
    assert re.search(r"Phase 7[:：]\s*裁可と接続", text), (
        "plan-sdd.md missing the 'Phase 7: 裁可と接続' approval phase"
    )
    assert "AskUserQuestion" in text, (
        "plan-sdd.md approval phase must use AskUserQuestion"
    )

    lines = text.splitlines()
    outsource_line_idxs = [
        i for i, line in enumerate(lines) if "outsource" in line.lower()
    ]
    last_question_line_idxs = [
        i for i, line in enumerate(lines) if "最後の設問" in line or "必ず最後" in line
    ]
    assert last_question_line_idxs, "plan-sdd.md has no '必ず最後' rule"
    assert any(
        abs(o - q) <= 3 for o in outsource_line_idxs for q in last_question_line_idxs
    ), (
        "plan-sdd.md's '最後の設問' rule must be within 3 lines of its "
        "/outsource mention"
    )


def test_plan_sdd_allows_skill_tool() -> None:
    """The approval phase hands off by launching ConsiderateCoder:outsource
    through the Skill tool, so Skill must be declared in allowed-tools."""
    frontmatter, _, _ = _split_frontmatter(PLAN_SDD_PATH)
    assert re.search(r"^\s*-\s*Skill\s*$", frontmatter, re.MULTILINE), (
        "plan-sdd.md must list 'Skill' in allowed-tools (approval hand-off)"
    )


def test_plan_sdd_wait_clause_replaced() -> None:
    """The old 'wait until told to start' ending is replaced by the approval
    phase: passive waiting would strand the user in free-form prose exactly
    where the structured hand-off belongs."""
    text = PLAN_SDD_PATH.read_text(encoding="utf-8")
    assert "明示的に指示するまで待機する" not in text, (
        "plan-sdd.md still carries the pre-1.3.0 passive wait clause"
    )
    assert "Phase 7" in text, (
        "plan-sdd.md must route the post-report step into Phase 7 instead"
    )


def _outsource_phase4_region() -> list[str]:
    """Lines of outsource.md between the 'Phase 4' and 'Phase 5' headings."""
    lines = OUTSOURCE_PATH.read_text(encoding="utf-8").splitlines()
    starts = [i for i, line in enumerate(lines) if re.match(r"^##\s*Phase 4\b", line)]
    ends = [i for i, line in enumerate(lines) if re.match(r"^##\s*Phase 5\b", line)]
    assert starts, "outsource.md has no 'Phase 4' heading"
    assert ends, "outsource.md has no 'Phase 5' heading"
    return lines[starts[0] : ends[0]]


def test_outsource_escalation_via_askuserquestion() -> None:
    """Phase 4 turns escalations into a structured approval step: the
    escalation term and AskUserQuestion must sit in close (same or <=3 line)
    proximity inside the Phase 4 region, so the flow reads as one rule rather
    than two unrelated facts (same proximity pattern as
    test_deletion_policy_branch)."""
    region = _outsource_phase4_region()
    escalation_idxs = [i for i, line in enumerate(region) if "上申事項" in line]
    question_idxs = [i for i, line in enumerate(region) if "AskUserQuestion" in line]
    assert escalation_idxs, "outsource.md Phase 4 never mentions 上申事項"
    assert question_idxs, "outsource.md Phase 4 must use AskUserQuestion for approval"
    assert any(abs(e - q) <= 3 for e in escalation_idxs for q in question_idxs), (
        "outsource.md Phase 4 must state the AskUserQuestion approval flow "
        "within 3 lines of its 上申事項 mention"
    )


def test_outsource_no_escalation_no_question() -> None:
    """The approval step is conditional: with zero escalations no question is
    asked (the '過剰な質問は禁止' principle stays intact, unlike plan-sdd's
    always-on hand-off question)."""
    text = OUTSOURCE_PATH.read_text(encoding="utf-8")
    assert any(
        "発火しない" in line and re.search(r"上申事項が(ゼロ|なけれ|無けれ)", line)
        for line in text.splitlines()
    ), (
        "outsource.md must state that AskUserQuestion is not fired when there "
        "are no escalations"
    )


def test_outsource_approval_recorded_in_report() -> None:
    """Approval outcomes (approved / sent back) must land in the Phase 5
    report's escalation section, so the ESCALATIONS placeholder carries the
    decision instead of the raw request."""
    text = OUTSOURCE_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert "ESCALATIONS" in text, (
        "outsource.md must name the ESCALATIONS placeholder as the record site"
    )
    assert "承認" in text and "差し戻し" in text, (
        "outsource.md must name both approval outcomes (承認 / 差し戻し)"
    )
    result_idxs = [i for i, line in enumerate(lines) if "裁可結果" in line]
    record_idxs = [i for i, line in enumerate(lines) if "ESCALATIONS" in line]
    assert result_idxs, "outsource.md never mentions 裁可結果"
    assert any(abs(r - e) <= 3 for r in result_idxs for e in record_idxs), (
        "outsource.md must record 裁可結果 into the ESCALATIONS section "
        "(within 3 lines of each other)"
    )


def _outsource_phase5_region() -> list[str]:
    """Lines of outsource.md from the 'Phase 5' heading to the next '##' heading."""
    lines = OUTSOURCE_PATH.read_text(encoding="utf-8").splitlines()
    starts = [i for i, line in enumerate(lines) if re.match(r"^##\s*Phase 5\b", line)]
    assert starts, "outsource.md has no 'Phase 5' heading"
    start = starts[0]
    ends = [i for i, line in enumerate(lines) if i > start and re.match(r"^##\s", line)]
    return lines[start : ends[0] if ends else len(lines)]


def test_outsource_next_plan_rules() -> None:
    """Phase 5 must carry the next-plan generation rules: the intent format is
    plan-sdd's (Acceptance is the stop condition that must not be dropped),
    convergence is a first-class output, and the command is never launched by
    the communicator on its own (全問正解 gates the sanctioned hand-off)."""
    text = OUTSOURCE_PATH.read_text(encoding="utf-8")
    for token in ("二次計画", "収束", "Acceptance", "自動起動しない", "全問正解"):
        assert token in text, f"outsource.md missing next-plan rule token: {token!r}"


def test_outsource_default_to_convergence() -> None:
    """The default-to-convergence tilt ('収束に倒す') depends on generation
    behaviour rather than machinery, so its rule text must at least exist —
    and sit in close (same or <=3 line) proximity to the NEXT_PLAN mention
    inside Phase 5 (same proximity pattern as test_deletion_policy_branch)."""
    region = _outsource_phase5_region()
    tilt_idxs = [i for i, line in enumerate(region) if "収束に倒す" in line]
    plan_idxs = [i for i, line in enumerate(region) if "NEXT_PLAN" in line]
    assert tilt_idxs, "outsource.md Phase 5 missing the '収束に倒す' tilt rule"
    assert plan_idxs, "outsource.md Phase 5 never names the NEXT_PLAN placeholder"
    assert any(abs(t - p) <= 3 for t in tilt_idxs for p in plan_idxs), (
        "outsource.md's '収束に倒す' rule must sit within 3 lines of a "
        "NEXT_PLAN mention in Phase 5"
    )


def test_outsource_allows_skill_tool() -> None:
    """The sanctioned hand-off launches ConsiderateCoder:plan-sdd through the
    Skill tool, so Skill must be declared in allowed-tools."""
    frontmatter, _, _ = _split_frontmatter(OUTSOURCE_PATH)
    assert re.search(r"^\s*-\s*Skill\s*$", frontmatter, re.MULTILINE), (
        "outsource.md must list 'Skill' in allowed-tools (next-plan hand-off)"
    )


def test_outsource_gate_conditions() -> None:
    """Both gate branches are conditional and must be stated as conditions:
    convergence skips the comprehension gate entirely (same conditional
    asymmetry as the zero-escalation branch), and a less-than-perfect score
    stops short of the hand-off question and proposes a re-read instead."""
    lines = OUTSOURCE_PATH.read_text(encoding="utf-8").splitlines()
    assert any(
        "発火しない" in line and re.search(r"収束(の場合|時|であれば|なら)", line)
        for line in lines
    ), (
        "outsource.md must state that the comprehension gate does not fire "
        "when the next plan converges"
    )
    assert any(
        "全問正解" in line and re.search(r"(でなけれ|不正解)", line) and "再読" in line
        for line in lines
    ), (
        "outsource.md must state that a less-than-perfect score stops before "
        "the hand-off question and proposes re-reading the report"
    )


def _refactor_region(heading: str) -> list[str]:
    """Lines of refactor.md from the '## <heading>' line to the next '##' heading."""
    lines = REFACTOR_PATH.read_text(encoding="utf-8").splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith(f"## {heading}")]
    assert starts, f"refactor.md has no '## {heading}' heading"
    start = starts[0]
    ends = [i for i, line in enumerate(lines) if i > start and re.match(r"^##\s", line)]
    return lines[start : ends[0] if ends else len(lines)]


def test_refactor_reads_dev_rules() -> None:
    """/refactor applies the bundled norms (surgical changes, Deletion Test,
    cc-defer, Completion Checklist) instead of restating them, so it must
    point at dev-rules through ${CLAUDE_PLUGIN_ROOT}."""
    text = REFACTOR_PATH.read_text(encoding="utf-8")
    assert "${CLAUDE_PLUGIN_ROOT}/skills/dev-rules/SKILL.md" in text, (
        "refactor.md must Read dev-rules via ${CLAUDE_PLUGIN_ROOT}"
    )


def test_refactor_empty_args_target_project_root() -> None:
    """Unlike plan-sdd / outsource, a bare /refactor is the common call (the
    whole project is the usual target), so the empty-argument branch selects
    the current project's root instead of printing usage, and asks only when
    the root is ambiguous."""
    region = _refactor_region("引数が空の場合")
    assert any("ルート" in line for line in region), (
        "refactor.md's empty-argument branch must target the project root"
    )
    assert any("AskUserQuestion" in line for line in region), (
        "refactor.md's empty-argument branch must ask when the root is ambiguous"
    )


def test_refactor_defines_behavior_preservation() -> None:
    """Refactoring changes structure without changing observable behavior;
    behavior changes (bug fixes / features / performance) stay out of the
    change set and go to the report instead of being fixed in passing."""
    text = REFACTOR_PATH.read_text(encoding="utf-8")
    for token in ("観測可能な振る舞い", "混ぜない"):
        assert token in text, (
            f"refactor.md missing behavior-preservation token: {token!r}"
        )


def test_refactor_description_covers_documents() -> None:
    """Documents are a first-class target, so the description (what the model
    matches a request against) must name them next to code."""
    frontmatter, _, _ = _split_frontmatter(REFACTOR_PATH)
    match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
    assert match, "refactor.md frontmatter has no description line"
    assert "文書" in match.group(1), "refactor.md description must name documents"


def test_refactor_defines_document_behavior() -> None:
    """For a document, the behavior to keep is the facts and procedures it
    states. Aligning a document with the real thing (code / config / current
    state) is in scope; changing the policy it states is a behavior change.
    Both halves sit in one line so the boundary reads as one rule."""
    lines = REFACTOR_PATH.read_text(encoding="utf-8").splitlines()
    assert any(
        "文書では" in line
        and "合わせて直す" in line
        and "方針" in line
        and "振る舞いの変更" in line
        for line in lines
    ), "refactor.md must define what behavior means for documents"


def test_refactor_doc_only_baseline_and_safety_net() -> None:
    """A document set with no checkers and no place for tests still gets a
    baseline (links / anchors / diagrams checked by hand) and a safety net
    (structure tests where they fit, otherwise a before/after diff review) —
    "write the tests first" must not stall on a folder of notes."""
    phase2 = _refactor_region("Phase 2")
    assert any("文書" in line and "ベースライン" in line for line in phase2), (
        "refactor.md Phase 2 must give document-only targets a baseline"
    )
    phase5 = _refactor_region("Phase 5")
    assert any("構造テスト" in line and "差分" in line for line in phase5), (
        "refactor.md Phase 5 must give document-only targets a safety net"
    )


def test_refactor_doc_specific_rot() -> None:
    """Two kinds of rot are specific to documents: diagrams / directory trees
    drifting from the real tree in either direction, and code / command
    examples that no longer run."""
    text = REFACTOR_PATH.read_text(encoding="utf-8")
    for token in ("構成図", "双方向", "コマンド例"):
        assert token in text, f"refactor.md missing document-rot token: {token!r}"


def test_refactor_stops_on_red_baseline() -> None:
    """A red baseline means behavior is not pinned, so the premise of a
    refactor fails before it starts: one line must carry both the baseline
    and the do-not-start rule."""
    lines = REFACTOR_PATH.read_text(encoding="utf-8").splitlines()
    assert any("ベースライン" in line and "着手しない" in line for line in lines), (
        "refactor.md must state that a red baseline stops the refactor"
    )


REFACTOR_VIEWPOINTS = (
    # the eight the hand-typed refactor prompt always carried
    "SSoT",
    "腐敗",
    "矛盾",
    "参照",
    "構造化",
    "責務",
    "粒度",
    "テスト",
    # the three it was missing
    "外部契約",
    "モデルに届く文",
    "公開境界",
)


def test_refactor_viewpoint_headings() -> None:
    """Every viewpoint is a checklist heading, not a passing mention: a
    viewpoint named only in prose is skipped as soon as the list gets long."""
    headings = [
        line
        for line in REFACTOR_PATH.read_text(encoding="utf-8").splitlines()
        if line.startswith("### ")
    ]
    for viewpoint in REFACTOR_VIEWPOINTS:
        assert any(viewpoint in heading for heading in headings), (
            f"refactor.md has no ### heading for viewpoint {viewpoint!r}"
        )


def test_refactor_safety_net_first() -> None:
    """Missing tests are written before the change (characterization tests
    that pin the current behavior), and each added test is made to fail once
    — a test that has never failed has not shown that it guards anything."""
    text = REFACTOR_PATH.read_text(encoding="utf-8")
    for token in ("characterization test", "失敗させ"):
        assert token in text, f"refactor.md missing safety-net token: {token!r}"


def test_refactor_keeps_the_floor() -> None:
    """Simplification must not cut validation, error handling or security
    (dev-rules' Deletion Test floor) — a refactor is where that floor is most
    tempting to cut, so the command names it."""
    text = REFACTOR_PATH.read_text(encoding="utf-8")
    for token in ("入力検証", "エラー処理", "セキュリティ"):
        assert token in text, f"refactor.md missing floor token: {token!r}"


def test_refactor_model_facing_text_approved_with_diff() -> None:
    """Rewording text that a model reads as instructions can change its
    behavior, so such edits are approved one at a time with the before/after
    text: inside Phase 4 the before/after rule must sit within 3 lines of an
    AskUserQuestion mention (same proximity pattern as
    test_deletion_policy_branch)."""
    region = _refactor_region("Phase 4")
    diff_idxs = [i for i, line in enumerate(region) if "変更前後" in line]
    question_idxs = [i for i, line in enumerate(region) if "AskUserQuestion" in line]
    assert diff_idxs, "refactor.md Phase 4 never asks for the before/after text"
    assert question_idxs, "refactor.md Phase 4 must use AskUserQuestion for approval"
    assert any(abs(d - q) <= 3 for d in diff_idxs for q in question_idxs), (
        "refactor.md Phase 4 must state the before/after approval within 3 lines "
        "of its AskUserQuestion mention"
    )


def test_refactor_renames_leave_no_trace() -> None:
    """Moves and renames go through git mv (history survives) and are done
    only when the old names grep to zero — leftover references are where rot
    starts."""
    text = REFACTOR_PATH.read_text(encoding="utf-8")
    for token in ("git mv", "残存ゼロ"):
        assert token in text, f"refactor.md missing rename token: {token!r}"


def test_refactor_does_not_preapprove_bash() -> None:
    """allowed-tools pre-approves the listed tools; it does not restrict the
    rest. Bash stays callable under the user's own permission settings, so
    listing it would only grant unrestricted shell without a prompt — the
    test runner and git calls the flow needs do not justify that."""
    frontmatter, _, _ = _split_frontmatter(REFACTOR_PATH)
    assert not re.search(r"^\s*-\s*Bash\b", frontmatter, re.MULTILINE), (
        "refactor.md must not pre-approve Bash in allowed-tools"
    )


def test_plugin_internal_refs_use_plugin_root() -> None:
    """Command bodies must reference plugin-internal files via
    ${CLAUDE_PLUGIN_ROOT}, never via cwd-relative ../ links — the runtime
    cwd is the user's project, so ../ links break after installation."""
    for path in (PLAN_SDD_PATH, OUTSOURCE_PATH, DIG_PATH, REFACTOR_PATH):
        text = path.read_text(encoding="utf-8")
        assert "](../" not in text, (
            f"{path.name} contains cwd-relative plugin-internal link(s)"
        )
    for path in (PLAN_SDD_PATH, OUTSOURCE_PATH, REFACTOR_PATH):
        text = path.read_text(encoding="utf-8")
        assert "${CLAUDE_PLUGIN_ROOT}/" in text, (
            f"{path.name} must reference bundled files via ${{CLAUDE_PLUGIN_ROOT}}"
        )


def test_no_stale_rules_filenames() -> None:
    """v1.1.0 moved rules/DEV.md and rules/OPS.md into skills/ as
    dev-rules / ops-rules; command bodies (including plan-sdd's output
    template, which propagates into every generated IMPLEMENTATION_PLAN.md)
    must not reference the pre-move filenames."""
    for path in (PLAN_SDD_PATH, OUTSOURCE_PATH, DIG_PATH, REFACTOR_PATH):
        text = path.read_text(encoding="utf-8")
        for stale in ("DEV.md", "OPS.md"):
            assert stale not in text, (
                f"{path.name} references stale pre-1.1.0 rules filename: {stale!r}"
            )


def test_interactive_commands_not_forked() -> None:
    """Commands whose flow depends on AskUserQuestion must run in the main
    conversation: AskUserQuestion depends on the main conversation's UI and
    is silently unavailable in subagents (context: fork included, even when
    listed in tools), so a forked interviewer degrades into guessing
    instead of asking."""
    for path in (PLAN_SDD_PATH, OUTSOURCE_PATH, DIG_PATH, REFACTOR_PATH):
        frontmatter, _, _ = _split_frontmatter(path)
        assert not re.search(r"^context:\s*fork\b", frontmatter, re.MULTILINE), (
            f"{path.name} must not use context: fork "
            "(its AskUserQuestion flow would silently fail)"
        )


def test_no_forbidden_tokens() -> None:
    """None of the Interface-layer artifacts may carry development-only
    evidence (local paths, dates, proof-count callouts). {{DATE}} is a literal
    placeholder token, not a YYYY-MM date, so it does not trip DATE_PATTERN.
    """
    for path in (PLAN_SDD_PATH, OUTSOURCE_PATH, DIG_PATH, REFACTOR_PATH, TEMPLATE_PATH):
        text = path.read_text(encoding="utf-8")
        for token in LITERAL_FORBIDDEN_TOKENS:
            assert token not in text, f"{path.name} contains forbidden token: {token!r}"
        assert not DATE_PATTERN.search(text), (
            f"{path.name} contains a date-like pattern (YYYY-MM)"
        )
