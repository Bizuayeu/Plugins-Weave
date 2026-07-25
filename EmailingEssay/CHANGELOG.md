# Changelog

All notable changes to EmailingEssay will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2026-07-26

### Fixed
- Mail HTML: collapse whitespace inside `<style>` before handing the body to yagmail. yagmail converts newlines to `<br>`, which injected `<br>` into the CSS and made premailer's inlining fail wholesale — mail arrived unstyled while the process still exited 0, so nothing surfaced the breakage. `collapse_style_whitespace()` now folds only the `<style>` blocks (body newlines are left alone), keeping the template readable

## [1.0.1] - 2026-07-25

### Changed
- `essay-writer` agent: declare `effort: high` alongside `model: opus`. Reflection quality depends on thinking depth, so the effort level is now pinned in the frontmatter instead of inheriting whatever the caller happens to run with

## [1.0.0] - 2025-12-31

### Added
- Initial release of EmailingEssay plugin
- `/essay` command with subcommands: wait, schedule, test
- `reflect` skill - Deep reflection with ultrathink
- `send-email` skill - Gmail SMTP via yagmail
- `essay-writer` agent - Autonomous essay generation
- Clean Architecture implementation (domain/usecases/adapters/frameworks)
- Cross-platform scheduler support (cron/Task Scheduler)
- Comprehensive documentation (README, CONCEPT, SETUP, CLAUDE)

### Technical Details
- Loop: L00298
- Dependencies: yagmail
- Storage: ~/.claude/plugins/.emailingessay/
