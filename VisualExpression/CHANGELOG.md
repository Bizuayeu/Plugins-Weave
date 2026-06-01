# Changelog

All notable changes to VisualExpression will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-06-01

### Changed
- Expression key table in SKILL.md is now bilingual (English/Japanese) and serves as the single source of truth
- "Project Instructions Snippet" reframed as a minimal one-line trigger — operational steps (deploy, present, sed, key table) live in SKILL.md, no longer duplicated in project instructions
- `description` (SKILL.md frontmatter + plugin.json) now states *when* to activate (session start / emotional state change), improving skill discovery
- Session-start UI placement steps (cp → present) made explicit in "Usage on claude.ai"

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