# Changelog

All notable changes to EmailingEssay will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-08-25

Static checking aligned with the workspace baseline. No behavior change.

### Changed
- ruff `select` widened with `N` (naming) and `PTH` (pathlib); the existing `C4` / `RUF` were
  kept — the workspace target is the *union* of the two conventions, not a replacement.
  `E` narrowed to `E4,E7,E9` and `E501` dropped: line length is the formatter's job
- Formatter aligned with the workspace default (88 columns, quotes normalized).
  36 files reformatted

### Fixed
- `PTH123` ×10 in production code — `open(x)` → `x.open()`. Nine already held `Path` objects
  (`filepath.with_suffix()`, `_get_*_file() -> Path`, `runners_dir / ...`). The tenth,
  `wait_essay.py`'s `script_file = str(persistent_dir / ...)`, is a `str` by contract (it is
  handed to a subprocess as a string), so it is wrapped as `Path(script_file).open()` instead

### Notes
- **`PTH` is ignored under `tests/`** with a documented reason. Nineteen test files start with
  `sys.path.insert(0, os.path.dirname(...os.path.abspath(__file__)))` to make `scripts/`
  importable. **Entries in `sys.path` must be `str`**; inserting a `Path` makes the import fail
  silently (verified: `ModuleNotFoundError`). The rule's advice cannot apply to that line
- **`N806` ×3 is ignored** with a documented reason. `CREATE_NEW_PROCESS_GROUP`,
  `DETACHED_PROCESS`, and `SYNCHRONIZE` carry the Win32 SDK (`winbase.h`) spelling; lowercasing
  them would break the correspondence with the platform's own names

### Verification
ruff 102→0 / mypy Success (63 files) / pytest 343 passed (unchanged from baseline)

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
