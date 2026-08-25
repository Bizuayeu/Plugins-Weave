# Changelog

All notable changes to VisualExpression will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-08-25

Static checking aligned with the workspace baseline. No behavior change.

### Changed
- ruff `select` widened with `N` (naming) and `PTH` (pathlib). The existing `C4` / `RUF`
  were kept — the workspace target is the *union* of the two conventions, not a replacement.
  `E` narrowed to `E4,E7,E9`, and `E501` dropped from `ignore`: line length is the formatter's job
- Formatter aligned with the workspace default (`line-length = 100` and
  `quote-style = "preserve"` removed → 88 columns, quotes normalized). 19 files reformatted
- `[tool.mypy]` now has `mypy_path`, and the test-layer override targets `tests.*`

### Fixed
- `PTH123` ×6 — `open(x)` → `x.open()`. **Three of the six take a `str` by contract**
  (`read_template(template_path: str)`, `HtmlBuilder.template_path`,
  `build_from_json(json_path: str)`); those are wrapped as `Path(x).open()` instead, since a
  direct rewrite would break them. The other three already held `Path` objects
- The `[tool.mypy]` section was not doing its job. Without `mypy_path`, `from domain.validators
  import ...` could not resolve; `ignore_missing_imports = true` silenced that and collapsed
  everything to `Any`. The only visible symptom was three `no-any-return` diagnostics. The
  test-layer override pointed at `skills.scripts.MakeExpressionJson.tests.*`, which **matched no
  module at all**. With both corrected, the 226 previously hidden diagnostics surfaced — all of
  them in the test layer. **Production code was already at zero**; fixing the config is what
  proved it

### Notes
- CI was *not* blind: its `type-check-visualexpression` job runs from inside the package with
  CLI flags (`--explicit-package-bases --exclude tests`) and does not read `pyproject.toml`.
  What was broken is the repository-root invocation that *does* read it. The CI job is unchanged
  here, so CI and local still run mypy under different configurations
- `N999` ×5 (the package name `MakeExpressionJson`) is ignored with a documented reason: the name
  is the public one shared by `pythonpath`, the setuptools `include`, the coverage `source`, and
  the skill docs. Renaming buys nothing and leaves only reference churn

### Verification
ruff 11→0 / mypy Success (40 files) / pytest 220 passed (unchanged from baseline)

## [1.1.0] - 2026-06-01

### Changed
- Expression key table in SKILL.md is now bilingual (English/Japanese) and serves as the single source of truth
- "Project Instructions Snippet" reframed as a minimal one-line trigger — operational steps (deploy, present, sed, key table) live in SKILL.md, no longer duplicated in project instructions
- `description` (SKILL.md frontmatter + plugin.json) now states *when* to activate (session start / emotional state change), improving skill discovery
- Session-start UI placement steps (cp → present) made explicit in "Usage on claude.ai"
- Install step now zips the *contents* of `skills/` (SKILL.md at ZIP root) into `visual-expression.zip`, so Mac/Linux and Windows produce an identical archive; dropped exclusion flags (dev files are gitignored)

## [1.0.0] - 2026-01-03

### Added
- Initial release
- 20 expression variations (5 categories × 4 each)
- Nano Banana Pro integration for grid generation (MetaGenerateExpression.md)
- MakeExpressionJson Python pipeline with Clean Architecture
- Self-contained HTML output with Base64 embedded images
- sed-based one-liner expression switching
- Claude.ai custom skills support
- Claude Code plugin support
- Customizable Special expressions via `--special` option
- Custom template support via `--template` option

---

**VisualExpression** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)