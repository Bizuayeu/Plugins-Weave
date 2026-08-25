"""Stage 4: lint the SKILL.md procedure and engine for security & genericity.

These guard the Markdown procedure (which has no unit-testable logic):
- no persona-specific string leaks into the generic skill (those belong in examples/)
- curl examples never embed a token in the URL (Authorization header only, --fail)
- write-back never pushes directly to the default branch (claude/* + PR)
"""

import re
from pathlib import Path

HERE = Path(__file__).resolve()
SCRIPTS = HERE.parents[1]  # scripts/
SKILL_ROOT = HERE.parents[2]  # wakeup/
SKILL_MD = SKILL_ROOT / "SKILL.md"
ENGINE = SCRIPTS / "interfaces" / "wakeup_engine.py"

# Memory-repo-specific values that must only appear under examples/, never in engine/skill.
# (The plugin distribution owner "Bizuayeu" is allowed: it appears in the footer URL, like digest-*.)
PERSONA_STRINGS = ["weavingfuturity", "Homunculus", "289333046", "GrandDigest"]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


class TestSkillMdExists:
    def test_skill_md_present(self):
        assert SKILL_MD.is_file(), "SKILL.md must exist at the skill root"


class TestNoPersonaLeak:
    def test_skill_md_has_no_persona_strings(self):
        leaked = [s for s in PERSONA_STRINGS if s in _read(SKILL_MD)]
        assert not leaked, f"persona values belong in examples/, not SKILL.md: {leaked}"

    def test_engine_has_no_persona_strings(self):
        leaked = [s for s in PERSONA_STRINGS if s in _read(ENGINE)]
        assert not leaked, f"engine must stay generic: {leaked}"

    def test_skill_md_uses_generic_artifact_names(self):
        """Deployed artifacts use generic names; persona-named files live only under examples/."""
        text = _read(SKILL_MD)
        # The runtime config path must be the generic wakeup.config.json, never a persona's name.
        assert "wakeup/wakeup.config.json" in text, (
            "runtime config must be the generic wakeup.config.json"
        )
        # A persona-named config/directive must never be a deployed artifact (directly under
        # wakeup/); references under examples/ are fine.
        assert "wakeup/weave.config.json" not in text, (
            "persona config belongs under examples/, not deployed"
        )
        assert "wakeup/WeaveDirective.md" not in text, (
            "persona directive belongs under examples/, not deployed"
        )


class TestFailLoudProcedure:
    """Step 3 is a Markdown read, so the procedure itself must gate on verify."""

    def test_step_1_documents_verify(self):
        text = _read(SKILL_MD)
        assert "wakeup_engine.py verify" in text, (
            "Step 1 must run verify, not just read the config"
        )

    def test_deployment_is_materialized_not_hand_copied(self):
        assert "materialize" in _read(SKILL_MD), (
            "the ★ artifacts must be placed by materialize"
        )


class TestCurlSafety:
    def test_no_token_embedded_in_url(self):
        text = _read(SKILL_MD)
        assert "@raw.githubusercontent.com" not in text
        assert "@api.github.com" not in text
        assert not re.search(r"[?&]token=", text), (
            "token must use the Authorization header, not the URL"
        )

    def test_private_curl_uses_auth_header_and_fail(self):
        text = _read(SKILL_MD)
        assert "Authorization: Bearer $TOKEN" in text
        assert "--fail" in text


class TestWriteBackSafety:
    def test_no_direct_push_to_main(self):
        text = _read(SKILL_MD)
        assert not re.search(r"git\s+push\s+\S+\s+main\b", text), (
            "use claude/* + PR, never push to main"
        )

    def test_uses_claude_branch_prefix(self):
        assert "claude/" in _read(SKILL_MD), (
            "write-back must go through a claude/* branch"
        )
