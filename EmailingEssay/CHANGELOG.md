# Changelog

All notable changes to EmailingEssay will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-08-28

Sent essays are now recorded in an append-only ledger, and replies to them are ingested
back. No new dependency, no new environment variable.

### Added
- **Sent ledger**. `get_mail_adapter()` now returns the mail adapter wrapped in a
  `LedgerRecordingMail` decorator, so every send is recorded without a single change at
  the call sites. `test()` (the configuration test mail) is not recorded, and a send that
  ends in an exception is not recorded either
- **Persistence under `~/.claude/plugins/.emailingessay/`**: `essay_ledger.jsonl`
  (one line per send, `message_id` as the primary key), `sent/YYYYMMDD_HHMM.md` (body with
  YAML frontmatter), `essay_replies.jsonl` (one line per reply, linked by `in_reply_to`)
- **Reply ingestion** over `imaplib` (standard library) from `imap.gmail.com`. Only mail
  whose `In-Reply-To` matches a `message_id` in the ledger **and** whose `From` matches
  `ESSAY_RECIPIENT_EMAIL` is taken; the inbox is never searched across. The plugin picks up
  only the return of a ball it threw itself, which is what keeps the attack surface small.
  Ingested bodies are stored as data carrying a `content_class: untrusted_external_data`
  declaration — they are external input, not instructions
- **CLI**: `python main.py replies fetch` / `replies list` /
  `python main.py ledger import-legacy [--dry-run]`
- New modules: `domain/message_id.py`, `adapters/storage/ledger_storage.py`,
  `adapters/mail/ledger_recording_mail.py`, `adapters/mail/imap_inbox.py`,
  `usecases/ingest_replies.py`, `usecases/import_legacy.py` (each with its test file)

### Changed
- Retroactive migration was run once: 17 past essays (2026-07-02 – 08-16) were imported,
  45 body files excluded. Only essays whose **actually sent subject** could be recovered
  were taken in — no subject was inferred, because a ledger mixing recovered and guessed
  subjects cannot be told apart by whoever reads it later. Source files were not deleted.
  Migrated rows carry `<legacy.{body file stem}@emailingessay.invalid>` as `message_id`;
  being synthetic, these rows can never be matched by a reply — an intended limit

### Notes
- **Why the ledger did not exist before**: there was no record of sends anywhere as a
  structure. The `SENT` lines in `essay_wait.log` were not a plugin feature — they were
  5 lines hand-copied into a throwaway runner, and they were lost when the runner was
  rewritten in 2026-08. The log stops at 2026-07-30 while the body files continue to
  08-27. The missing record was the necessary consequence of depending on a habit, so it
  is now held by structure (the confluence point of the send path) rather than by convention
- **IMAP connection is not yet verified**. The adapter and its tests are complete, but the
  code path that talks to `imap.gmail.com` has never been executed — a live connection needs
  the user's explicit permission, and that is still pending

### Verification
ruff 0 / ruff format clean / mypy Success (75 files) / pytest 482 passed

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
