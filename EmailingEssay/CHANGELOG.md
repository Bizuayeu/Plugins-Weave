# Changelog

All notable changes to EmailingEssay will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-08-29

Reply ingestion joins the reflection flow as plumbing, and the file log finally reaches the
send path that production actually uses.

### Changed
- **`python main.py replies fetch` is now a step of the reflection flow**
  (`skills/reflect/SKILL.md` → **Reflection Process** → *Load Context*, and
  `agents/essay-writer.md` → *Load Context*). It is plumbing — replies move from the inbox
  onto disk so what has come back is at hand. Best-effort: an IMAP, authentication or network
  failure stops the fetch, not the reflection. Whether to read them, and whether anything of
  them reaches the essay, stays with the writer; nothing instructs it

### Fixed
- **File logging did not reach the send path in actual use.** v1.2.4 wired the file handler in
  `frameworks/logging_config.py`, but only `main.py` called the setup — the route production
  takes, importing `usecases.factories` directly and never passing through `main.py`, wrote
  nothing to `emailingessay.log`. `get_logger()` now establishes the configuration when none
  is set, and the adapters that reached for `logging.getLogger("emailingessay.xxx")` on their
  own go through `get_logger()` instead, so a logger exists on every entry path. What is
  logged, its format, logging being on by default, `ESSAY_LOG_FILE` overriding the path, and
  a log file that cannot be opened not stopping the run are all unchanged from v1.2.4

### Verification
ruff 0 / ruff format clean (75 files) / mypy Success (75 files) / pytest 540 passed

## [1.2.4] - 2026-08-29

The reply gate stops trusting `From` alone, and a dropped reply now says why it was dropped.
No behavior change to essay delivery.

### Added
- **`Authentication-Results` as the fourth gate on reply ingestion.** `From` is forgeable, so
  a candidate that clears Message-ID, `In-Reply-To` and sender is now also checked against the
  receiving MTA's own verdict: `_is_verified_by_receiving_mta` (`usecases/ingest_replies.py`)
  ingests only when the `authserv-id` is the receiving MTA's and `dkim` and `spf` are both
  `pass`. A header the sender wrote themselves carries another `authserv-id` and counts for
  nothing. Fail-closed — missing, unparseable or short of a `pass`, the reply is dropped.
  `parse_auth_results` is a pure function beside it, so the parsing rules (comments are not
  separators, a repeated method with conflicting results never resolves to `pass`) are tested
  without an inbox. `ReplyRecord.auth_results` (`domain/models.py`) carries the header and
  defaults to `""` — "no grounds" — so JSONL lines written before this version still read back
- `adapters/mail/imap_inbox.py` takes the **topmost** `Authentication-Results` only
  (`_topmost_header`). Lower ones were added before the message reached the receiving MTA and
  are as forgeable as the body
- **A dropped reply leaves a reason.** Each of the four gates in `_is_accepted` writes one INFO
  line naming the Message-ID, the sender and which gate refused it. The body is never in it —
  the record class says untrusted external data, and the log is not a way around that
- **File logging.** `frameworks/logging_config.py` now writes to `emailingessay.log` under the
  persistent directory as well as stdout, on by default, `ESSAY_LOG_FILE` overriding the path.
  A scheduled run's stdout is discarded, so without this a failed ingestion left no trace. A
  log file that cannot be opened is reported in one line and the run continues on stdout
- `SETUP.md` → **Scheduling Reply Ingestion**: `/essay schedule` registers delivery only, so
  pulling replies in needs an OS scheduler entry (`schtasks` / cron) for
  `python main.py replies fetch`. Written down with what neither scheduler inherits — cron
  reads no `~/.bashrc`, and `.env` is read from the working directory

### Fixed
- `SETUP.md`, IMAP troubleshooting: "this path has not yet been exercised against a live Gmail
  account" was written while that was true and outlived it. `replies fetch` ran against real
  Gmail on 2026-08-28 and ingested a reply; the note is gone
- `SETUP.md` → **A Reply Was Not Ingested**: the section described two gates when there are
  four, so the one most likely to skip a genuine reply — forwarding or a mailing list breaking
  DKIM or SPF — was undocumented. The four gates are now named, and the reader is sent to
  `emailingessay.log`, where the refusing gate is on the record

### Verification
ruff 0 / ruff format clean (75 files) / mypy Success (75 files) / pytest 539 passed

## [1.2.3] - 2026-08-28

A note one can leave for oneself, and the reflection skill told what the plugin keeps.
No behavior change to essay delivery.

### Added
- **`send --to-self`**. `python main.py send "Subject" "Body" --to-self` sends to
  `ESSAY_SENDER_EMAIL`, the AI's own address — a place to leave a note on a silent day.
  `LedgerRecordingMail` records it like any other send, so nothing new stores anything; the
  ledger's `recipient` field is what tells a self-addressed note from an essay. There is no
  general `--to <address>`: the plugin writes to the two addresses it already knows
- `skills/reflect/SKILL.md` → **What the Plugin Retains**: what the plugin holds on its own
  account (`essay_ledger.jsonl`, the bodies under `sent/`, `essay_replies.jsonl`, and a
  `--to-self` note) is now stated where the reflecting side reads. It states the fact; it does
  not ask that the records be read

### Fixed
- `skills/reflect/SKILL.md`, Non-interactive Mode: "Exit silently (logged to `essay_wait.log`)"
  was not true. Scheduled runs invoke `claude -p` directly and never reach the wrapper that
  wrote that log, whose last line is 2026-07-30. The text now says what holds — the silence is
  recorded nowhere
- `skills/send-email/SKILL.md`, File Locations and Security Considerations: "Logs for
  wait/schedule operations" and "All operations are logged to `essay_wait.log`" claimed a reach
  the log never had. Only the waiter generated by `wait` writes it — launch, target reached,
  return code; a registered `schedule` invokes `claude -p` directly and never reaches that
  wrapper. The text now scopes the log to `wait` and points at the ledger
  (`essay_ledger.jsonl` + `sent/`), where every send is recorded
- `SETUP.md`, "Email Not Received": the third instance of the same claim, and the one that
  misleads during an incident — it sent the reader to a log a registered `schedule` never
  writes, whose stale timestamp reads as "nothing was sent". Diagnosis now starts at the
  ledger, and the log's `wait`-only scope is stated where it could otherwise be misread

### Verification
ruff 0 / ruff format clean / mypy Success (75 files) / pytest 511 passed

## [1.2.2] - 2026-08-28

Closes the duplicate hole in the retroactive import. No behavior change to sending.

### Fixed
- **`ledger import-legacy` no longer re-imports essays the sending path already recorded.**
  A real send is recorded by the `LedgerRecordingMail` decorator under the Message-ID
  `make_msgid()` issued; the migration synthesizes `<legacy.{stem}@emailingessay.invalid>`
  from the body file name. The two never join on `message_id`, so every bare re-run added a
  duplicate row for each essay sent since [1.2.0]. `plan()` now applies two gates **in this
  order**: a candidate whose synthetic id is already in the ledger stays an item (it is the
  migrated row, reported as "already in the ledger"); any remaining candidate whose body
  text matches a recorded body under `sent/` is excluded, with its own reason
  (`台帳に同一本文あり`). Reversed, the gates would drop all 38 migrated bodies, since
  those are in `sent/` too
- Timestamps cannot serve as the key: measured, `essay_body_20260828_2107.txt` was sent at
  `21:15:34` — eight minutes after the name was minted, because the body is named when the
  writing starts and sent when it ends. Hence no cutoff date and no tolerance window; the
  key is the body text itself
- The comparison reads the source with `utf-8-sig`. A BOM survives `str.strip()` (U+FEFF is
  not whitespace) and would make the comparison miss in silence. Nothing else is
  normalized — the match was measured exact (2279 characters), and further normalization
  would only widen the room for false matches
- A resend of the same text is treated as a duplicate on purpose: if the same essay went
  out twice, one ledger row is enough

### Added
- `LedgerPort.load_sent_bodies()` — the recorded bodies with their YAML frontmatter
  stripped. The stripping sits next to `_write_body`, which puts the frontmatter on

### Changed
- Dry-run against the live data: candidates 40 → 38, **new 2 → 0**, already in the ledger
  38 (unchanged), excluded 24 → 26 (the two 2026-08-28 sends). The ledger stays at 40 rows

## [1.2.1] - 2026-08-28

A third recovery path for the retroactive import, and the IMAP connectivity check that
[1.2.0] left pending. No behavior change to sending.

### Added
- **Third subject recovery path: the literal subjects in the old runners.** Throwaway
  runners such as `_send_20260611.py` name their body file and pass the subject as a string
  literal; `import-legacy` now reads that literal (`ast.Constant`, str assignments only —
  the runner is parsed, never executed) and joins it to the body file the runner names.
  Priority stays ① subject-file → ② `essay_wait.log` → ③ runner, and ③ never overrides ①②
- Guards on the new path: the runner is decoded utf-8-sig strict then cp932 strict, a
  subject with U+FFFD is skipped, a runner referencing zero or several body files is
  skipped, and undated generic runners are not candidates at all

### Changed
- Retroactive migration re-run with the third path: the ledger went **17 → 38 rows**
  (`sent/` likewise 38 files), covering 2026-06-11 – 08-27. By source: ① subject-file 7 /
  ② wait-log 10 / ③ runner 21. The 21 include seven essays from 2026-06-11 – 06-19
  that no `essay_wait.log` covered (the log begins 2026-07-02). A second run adds 0 rows, and the
  source files were again neither deleted nor altered
- `import-legacy --dry-run` now separates candidates into **new / already in the ledger**,
  so re-running it on a migrated ledger reads as "nothing to do" rather than as a re-import

### Notes
- **IMAP connectivity is verified; the fetch path is not.** With the user's permission a
  single live check against `imap.gmail.com` succeeded — `login`, `NOOP`, and
  `SELECT INBOX` (readonly, 29 messages) all OK, so IMAP is enabled on the account and the
  same app password used for SMTP works for it. `ImapInboxAdapter`'s own retrieval logic
  (`_collect` / the fetch path) has still never run against the real server. Both halves
  hold: the door opens, the walk through it is untested
- Reply bodies are untrusted external input; `skills/send-email/SKILL.md` now says so where
  the other security notes live

### Verification
ruff 0 / ruff format clean / mypy Success (75 files) / pytest 497 passed

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
