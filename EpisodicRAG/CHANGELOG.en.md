<!-- Last synced: 2026-07-02 -->
English | [日本語](CHANGELOG.md)

# Changelog

All notable changes to EpisodicRAG Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## Table of Contents

- [v5.x](#582---2026-07-29)
- [v4.x](#410---2025-12-03)
- [v3.x](#330---2025-11-29)
- [Archive (v2.x and earlier)](#archive-v2x-and-earlier)
- [Versioning Rules](#versioning-rules)

---

## [5.8.2] - 2026-07-29

### Changed

- **Version badges are now dynamic badges (sync work removed by construction)** — the version badges in README (ja/en) and `docs/README.md` are now shields.io dynamic JSON badges that read the SSoT (`.claude-plugin/plugin.json`; the root badge reads `marketplace.json`) at display time. With no literal number left in the badge, the manual sync step at bump time no longer exists (a permanent fix for the CI failure caused by a missed badge sync during the v5.9.8 bump)
- **Consistency tests changed from "number match" to "target check"** — the badge tests in `test_version.py` now assert that a dynamic badge's `url=` points at the correct SSoT and its `query=` is `$.version`. They also assert the absence of static badges (`badge/version-x.y.z-`) as a permanent gate, and cover the EpisodicRAG README (ja/en), which had no pytest coverage before
- **CONTRIBUTING (ja/en) release procedure updated** — badge rows dropped from the version sync table; the release procedure goes from 5 files to 4 (badges follow automatically)

---

## [5.8.1] - 2026-07-25

### Changed

- **DigestAnalyzer now declares `effort: high`** — analysis depth directly determines digest quality, so the thinking budget is pinned in the frontmatter instead of inheriting the caller's setting (`model: opus` unchanged)

---

## [5.8.0] - 2026-07-25

### Added

- **wakeup: `materialize` / `verify` subcommands (kill deployment drift, close the fail-open)**
  - **Background**: the ★ artifacts (config / directive / token) were hand-copied per zip. Because config and directive travel separately, a real deployment ended up with a **fresh directive and a months-old config** (`commit_identity.coauthor` still naming a previous model generation). Worse, Step 3 is a Markdown read, so a directive that was never placed passed silently
  - `materialize --config <path> --out <dir> [--token <path>]`: the persona's config is the **single source of truth** and the directive is resolved **beside it** via `directive_path`. The config lands as `wakeup.config.json` (fixed generic name); the token keeps its own basename (no silent renaming, so case mismatches cannot hide). **Everything is validated before the first copy** — never a half-materialized skill root. Path-driven, so no persona name enters the engine (`examples/` stays a sample and other personas' values never enter this repo)
  - `verify [--root <dir>]`: checks that config / directive / token exist and are readable, exiting non-zero otherwise. The `config` line fingerprints the load repo (**one deployment = one persona**, so booting with another persona's stale config is detectable). The token is only probed for readability — its contents are never printed
  - Clean Architecture: the verification policy is a UseCase (`usecases/verify_deployment.py` + `DeploymentProbePort`), file placement is Interface (engine). TDD (wakeup: 61 → 132 tests)
- **wakeup skill added to CI** — ruff check / ruff format --check, bandit, mypy strict and pytest steps added to the existing EpisodicRAG jobs (previously local-only, so the tests could rot). Workflow changes now trigger CI as well

### Changed

- **`directive_path` structural validation moved into the domain** — relative, POSIX separators, no parent escape, no empty segment, enforced in `WakeupConfig.__post_init__`. Personas keep naming their own directive at any depth, but nothing can resolve outside the skill root
- **SKILL.md**: new "deployment (just before zipping)" section; Step 1 changed from "read config" to **deployment verification (verify)**; documents "one deployment = one persona" and "`commit_identity.coauthor` is the key to update when the model generation changes"
- **pyproject**: added `skills/wakeup/scripts/**/*.py` to ruff `include` and `usecases` to isort `known-first-party` (the skill tree was outside lint scope); applied `ruff format` to that tree for the first time

### Fixed

- **Hole in config validation** — `load_config` constructed `WakeupConfig` *outside* the try block, so the domain's `ValueError` escaped instead of surfacing as `ConfigError` (breaking the uniform error surface)
- **Non-regular tar member** — `extractfile()` could return `None` and was dereferenced with `.read()` (caught by mypy strict; now an explicit error)

---

## [5.7.0] - 2026-07-02

### Added

- **update_shadow_overall CLI (interface for SGD overall_digest updates)** — new `interfaces/update_shadow_overall.py` that updates the 5 overall_digest fields (digest_type / keywords / abstract / impression / timestamp) of ShadowGrandDigest from JSON input
  - **Background**: overall_digest abstracts contain ~2400-char Japanese strings; manual updates via Edit-tool exact-match replacement are error-prone. A JSON round-trip through ShadowIO updates them safely
  - Never touches `source_files` (invariant). `timestamp` / `metadata.last_updated` are auto-updated
  - Input validation: 4 required keys with type checks. SGD is left unchanged on error
  - Usage: `python -m interfaces.update_shadow_overall <level> <json_file>` (supports `--stdin`)

### Changed

- **`/digest` SGD integration steps now use the CLI** — Pattern 1 Step 7 / Pattern 2 Step 6 & Step 8.5 changed from "update each field with the Edit tool" to a temp-file + `update_shadow_overall` procedure (`commands/digest.md`). The source_files formatting rule (one entry per line) moved to Pattern 1 Step 3

### Fixed

- **Log crash on Windows cp932 consoles** — when `logging.StreamHandler` writes to a cp932 stream (the default under redirect/pipe), the em-dash "——" (U+2014) frequently used in digest_type raised `UnicodeEncodeError` (`--- Logging error ---`). `setup_logging()` now re-wraps handler streams in a UTF-8 `TextIOWrapper` (`_utf8_safe_stream()`, a handler-local swap that leaves `sys.stdout` itself untouched)
  - Side benefit: Japanese log lines that used to appear garbled under pipes are now readable
  - Tests: `test_logging_config.py::TestHandlerEncodingSafety` (verifies content delivery through a simulated cp932 console)

---

## [5.6.0] - 2026-06-14

### Added

- **dream-defrag command (subtractive dream = auto-memory GC)** — a reductive housekeeping pass over Claude Code auto-memory (`MEMORY.md` + `memory/*.md`), forming a pair with the `/digest` Step 11 Auto-dream (additive dream = enrichment)
  - Handles **③Dedup & Resolve (cross-entry merge) and ④Prune & Index (graduate completed, lean index)** of the memory-dream 4 phases (①Mine and ②Consolidate remain Step 11's responsibility)
  - Subcommands: `scan` (count diagnosis / `DEFRAG_THRESHOLD=50` over-threshold check) / `snapshot` (pre-prune backup) / `rebuild-index` (sync `MEMORY.md` to on-disk files, `--preview` supported)
  - **Separation of judgment and determinism**: the scripts do only deterministic work (count, snapshot, index sync). What counts as a duplicate / graduate / upper-layer-DRY violation is judged by Claude in the `commands/dream-defrag.md` flow
  - **Safety**: auto-memory is not git-tracked (not revertable), so a pre-prune snapshot is mandatory. Non-destructive flow (snapshot → propose → user approval → apply). Snapshots are created outside the scanned dir (under the persistent dir's `snapshots/`)
  - **Graduation boundary**: completed projects are only demoted from the `MEMORY.md` live index; nothing is written to EpisodicRAG (Loops/Digests) (the memory layer is immutable). If not yet recorded, flag rather than delete
  - Clean Architecture (Domain / UseCase / Interface / Infrastructure) + TDD (24 tests: defrag types, DefragScanner count check, snapshot, index round-trip, CLI subcommands)

### Architecture

- Co-located within the existing `auto_dream` package (no new package): `domain/auto_dream/defrag_types.py`, `application/auto_dream/defrag_scanner.py`, `infrastructure/auto_dream/{snapshot_writer,index_writer}.py`, `interfaces/dream_defrag.py`

---

## [5.5.0] - 2026-05-31

### Added

- **wakeup skill (claude.ai session-start engine)** — a general-purpose engine that loads long-term memory and applies the persona directive at session start in claude.ai
  - Separates the "general-purpose engine (scripts/)" from "persona-specific values (examples/)". Repo names, files, commit identity, and persona policy are all injected via config (no hardcoding; enforced by lint)
  - Deployed artifacts are fixed to generic names that do not contain a persona name (runtime config = `wakeup.config.json`; only the directive name is variable via the config's `directive_path`). Persona-specific samples are isolated under `examples/` (e.g. `weave.config.json`), and any leakage of persona-specific names into runtime paths is detected by lint
  - Clean Architecture (Domain / UseCase / Interface) + TDD (59 tests: value objects, BootSequence, config loader, engine, SKILL.md lint [including verification of generic names for deployed artifacts and persona-name leakage])
  - Memory loading uses a Read token for SHA-pinned fetch (on claude.ai's shared IPs the unauthenticated API is exhausted, and raw's main branch is CDN-cached so the latest cannot be retrieved)
  - Supports Private reference / write-back (`claude/*` → PR). The token is bundled with the skill as a tar.gz (claude.ai does not allow nested zip), and the URL is not exposed since only the Authorization header is used
  - Does not handle facial UI (no cross-reference with the VisualExpression skill). Both skills are self-contained and designed to be enabled independently via claude.ai project instructions
  - Note (to be addressed separately): claude.ai live verification (Stage 0); reorganizing `HowToUseEpisodicRAG.md` to present wakeup and VisualExpression as independent triggers (project instructions); documentation propagation for wakeup (`docs/user/ADVANCED.md`, `homunculus/Weave/STRUCTURE.md`, `WeaveSupplement.md`, `plugins-weave/README.md`, `skills/shared/_implementation-notes.md`, `EpisodicRAG/GLOSSARY.md`)

---

## [5.4.0] - 2026-05-01

### Changed

- **Refocused auto_dream_scan output to "memory location notification" (case B operation)**
  - Removed `content` / `content_length` from `MemoryFile`
  - Removed `raw_content` from `MemoryIndex`
  - Output size reduced from 68KB to 12.3KB (5.4x reduction); Claude Code preview truncation issue resolved
  - Claude now judges relevance from `MEMORY.md` and each `frontmatter.description`, then individually reads only relevant memories via `path` to reconcile with digest content
  - Updated Step 11 in `commands/digest.md` to reflect case B operation guidance

### Fixed

- **hypothesis FailedHealthCheck in test_template_properties.py**
  - The `valid_levels` strategy's `whitelist_categories=("L", "N")` included `Lo` (CJK, etc.), generating hundreds of thousands of candidate characters, slowing input generation enough to trigger FailedHealthCheck
  - Narrowed to `("Ll", "Lu", "Nd")` + `whitelist_characters="_"`, restricting to ASCII alphanumerics and underscore
  - Runtime reduced from 242s to 5.80s (13/13 pass)

### Internal

- Added 9 tests for TypedDict structure / return value / scanner result verification
- Updated docstrings in domain/auto_dream/types.py, infrastructure/auto_dream/memory_reader.py, and interfaces/auto_dream_scan.py to reflect the new responsibility

---

## [5.3.0] - 2026-03-26

### Added

- **Auto-dream: Memory Consolidation**
  - Added automatic scanning and consolidation of Claude Code auto-memory files as Step 11 of the digest process
  - New CLI: `python -m interfaces.auto_dream_scan`
  - Discovers and parses memory files under `~/.claude/projects/*/memory/`
  - Lightweight frontmatter parser (no PyYAML dependency, zero-dependency policy maintained)
  - Works with both Pattern 1 (new Loop detection) and Pattern 2 (level finalization)
  - Graceful degradation: auto-skips in environments without auto-memory

### Architecture

- **New packages**: `domain/auto_dream/`, `infrastructure/auto_dream/`, `application/auto_dream/`
- Clean Architecture 4-layer compliance (Domain → Infrastructure → Application → Interfaces)
- 59 new tests added (domain: 12, infrastructure: 34, application: 8, interfaces: 5)

---

## [5.2.0] - 2025-12-14

### Changed

- **Persistent Path**
  - Moved config.json and last_digest_times.json to `~/.claude/plugins/.episodicrag/`
  - Configuration is no longer lost during Claude Code plugin auto-updates (delete → re-clone)
  - Environment variable `EPISODICRAG_CONFIG_DIR` allows custom path specification (for testing)

### Added

- **Internal Refactoring (TDD Improvements)**
  - Split `digest_auto.py` into `digest_auto/` package (548 lines → 5 modules: models, analyzer, path_resolver, file_scanner, report)
  - Added `CascadeComponents` parameter object (Parameter Object Pattern)
  - Documented reset methods in singleton module docstrings (`level_registry`, `error_formatter`, `file_naming`)

### Documentation

- **INDEX.md / INDEX.en.md added**
  - Navigation to all documents
  - Reader-based guide (beginners/daily use/troubleshooting/developers/AI)
  - Also serves as a checklist for documentation updates

- **CLAUDE.md improvements**
  - Added "Available Features" section (commands/skills/agents/basic workflow)
  - AI can now use the plugin from first encounter

- **Documentation structure cleanup**
  - Simplified `_footer.md` to footer SSoT only
  - Added INDEX.md links from all READMEs

> 📖 See [DESIGN_DECISIONS.md](docs/dev/DESIGN_DECISIONS.md) for details

---

## [5.1.0] - 2025-12-07

### Changed

- **digest.md refactoring**
  - Pattern 2 restructured from 7 to 9 steps
  - TOC split by pattern for easier navigation
  - Renamed "Output Examples" to "Error Output Examples" (success examples moved to each Step 9)

- **Skill documentation improvements**
  - Added TodoWrite usage guide to each SKILL.md
  - Standardized skill document structure
  - Updated usage examples and output examples

---

## [5.0.0] - 2025-12-05

> **⚠️ Migration Note**: Migration from v4.x or earlier is deprecated. Plugin reinstallation is recommended.
> Existing conversation records (GrandDigest, ShadowGrandDigest, Loop files, etc.) can be used as-is.

### Breaking Changes

- **Plugin root auto-detection**
  - Prevents `config.json` detection errors during `/digest`
  - Enables `/digest` execution from any directory

- **Loop level added**
  - Added Loop layer to `last_digest_times.json`
  - All levels (including Loop) can now track latest `/digest` targets

- **Shell scripts deprecated**
  - Consolidated interactive processes into md files
  - Purpose: Improved readability, prevention of skipped steps

### Added

- **Bandit security scan integration**
  - Scan for security vulnerabilities with `make security`
  - Added security job to CI/CD (GitHub Actions)
  - Added Bandit to pre-commit hooks
  - Added integration test `test_bandit_integration.py`

- **cascade_orchestrator readability improvement**
  - Added 4-step control flow comments
  - Added `CascadeStepResult.details` structure documentation

---

## [4.1.0] - 2025-12-03

### Added

- **CONCEPT.md / CONCEPT.en.md**: New concept documentation (Japanese/English synced, 210 lines each)

- **Internal Refactoring**: TypedDict split, Literal types, CLI common helpers, validation consolidation, 4 new design patterns

- **Development Tools**: Footer checker, link checker (`scripts/tools/`)

> 📖 See [DESIGN_DECISIONS.md](docs/dev/DESIGN_DECISIONS.md) for details

---

## [4.0.0] - 2025-12-01

> **⚠️ Migration Note**: Migration from v3.x or earlier is deprecated. Plugin reinstallation is recommended.
> Existing conversation records (GrandDigest, ShadowGrandDigest, Loop files, etc.) can be used as-is.

### Breaking Changes

- **Clean Architecture decomposition of config layer**: Reorganized single config module into 3 layers
  - `domain/config/` - Constants and type validation
  - `infrastructure/config/` - File I/O and path resolution
  - `application/config/` - Validation and services
  - **Migration**: Update import paths to match the layer structure

- **Python script implementation for skills**: From pseudo-code to executable CLI
  - `@digest-setup` → `python -m interfaces.digest_setup`
  - `@digest-config` → `python -m interfaces.digest_config`
  - `@digest-auto` → `python -m interfaces.digest_auto`
  - Usage via skills still supported

- **Introduction of trusted_external_paths**: Enhanced security for external path access
  - Added `trusted_external_paths: []` field to config.json
  - Explicit whitelist registration required for external path usage

---

## [3.3.0] - 2025-11-29

### Added

- **LEARNING_PATH.md**: Added Python learning documentation
  - Step-by-step path for learning Clean Architecture
  - Python learning guide using EpisodicRAG codebase as teaching material

### Changed

- **Version SSoT enhancement**: Placeholder version examples in CONTRIBUTING.md
  - Changed hardcoded version numbers to `x.y.z`
  - Explicit reference to plugin.json

- **English documentation sync**: Added sync headers
  - README.en.md, EpisodicRAG/README.en.md
  - QUICKSTART.en.md, CHEATSHEET.en.md
  - `<!-- Last synced: YYYY-MM-DD -->` format per CONTRIBUTING.md guidelines

---

## [3.2.0] - 2025-11-29

### Added

- **FAQ.md**: Added cross-search guide using GitHub search
  - Repository search (GitHub Web) guide
  - Local search (VS Code) guide
  - Reference to terminology index

- **TESTING.md**: Enhanced test documentation
  - Added GitHub Actions CI/CD badge
  - Added Codecov coverage report link
  - Added layer-based test file list
  - Added coverage target table
  - Added local coverage execution commands

- **api/domain.md**: Added complete schema for major TypedDicts
  - ConfigData (full config.json structure)
  - ShadowDigestData (full ShadowGrandDigest.txt structure)
  - GrandDigestData (full GrandDigest.txt structure)
  - RegularDigestData (finalized Digest file)
  - IndividualDigestData (individual digest element)
  - Schema expressed in TypeScript format

---

## [3.1.0] - 2025-11-29

### Added

- **DESIGN_DECISIONS.md**: Created new design decisions document
  - Reasons for adopting Clean Architecture
  - Rationale for design pattern selection (Facade, Repository, Strategy, Builder, Singleton, Template Method, Factory)
  - Aimed at enhancing value as Python programming teaching material

- **CHEATSHEET.md / CHEATSHEET.en.md**: Created new quick reference
  - Command and skill quick reference table
  - File naming conventions
  - Default thresholds
  - Daily workflow
  - Japanese/English fully synced (91 lines each)

### Changed

- **Document SSoT enhancement**: Comprehensive SSoT reference refactoring
  - ADVANCED.md: Added 3 SSoT references (memory structure, 8-layer hierarchy)
  - QUICKSTART.md/en.md: Added SSoT references, Japanese/English fully synced (179 lines each)
  - API_REFERENCE.md: Added "How to Use" section, DESIGN_DECISIONS reference
  - ARCHITECTURE.md: Added DESIGN_DECISIONS reference
  - CONTRIBUTING.md: Added DESIGN_DECISIONS reference
  - README.en.md: Added Path Format Differences section (Japanese/English sync 380 lines each)
  - FAQ.md: Fixed reference paths, added CHEATSHEET reference
  - GUIDE.md: Added CHEATSHEET reference

- **Design pattern clarification**: Added pattern list to API_REFERENCE.md
  - Facade, Repository, Singleton, Strategy, Template Method, Builder, Factory

---

## [3.0.0] - 2025-11-28

### Breaking Changes

- **Loop ID digit change**: 4 digits → 5 digits
  - Old format: `Loop0001`
  - New format: `L00001`
  - **Migration method**: Renaming existing Loop files required
    ```bash
    # Example: L0001_xxx.txt → L00001_xxx.txt
    cd your_loops_directory
    for f in L[0-9][0-9][0-9][0-9]_*.txt; do
      mv "$f" "L0${f:1}"
    done
    ```
  - **Affected areas**:
    - Loop file names
    - `source_files` references in ShadowGrandDigest.txt
    - References in last_digest_times.json

- **Full SSoT for documentation**: Terminology definitions centralized in README.md
  - No impact on users (documentation structure improvement only)

- **Test suite introduction**: Property-based testing with pytest + hypothesis
  - Developer-facing change, no impact on end users

### Changed

- Synchronized version management across all files

---

<details id="archive-v2x-and-earlier">
<summary>Archive (v2.x and earlier)</summary>

## [2.3.0] - 2025-11-28

### Breaking Changes

- **config/__init__.py: Completely removed backward compatibility re-exports**
  - `extract_file_number`, `extract_number_only`, `format_digest_number` → Import directly from `domain.file_naming`
  - `ConfigData`, `LevelConfigData` → Import directly from `domain.types`

  ```python
  # Old (no longer works)
  from config import extract_file_number, ConfigData

  # New (recommended)
  from domain.file_naming import extract_file_number
  from domain.types import ConfigData
  ```

---

## [2.2.0] - 2025-11-28

### Changed

- **Type safety improvement**: Migration from `Dict[str, Any]` to `ConfigData` (TypedDict)
  - `config/path_resolver.py`: Changed parameter type to `ConfigData`
  - `config/threshold_provider.py`: Changed parameter type to `ConfigData`
- **config/__init__.py refactoring**:
  - Removed domain constant re-exports (use `from domain.constants import ...` directly)
  - Unified initialization pattern to eager initialization (removed lazy initialization)
  - Moved local imports to module level
- **infrastructure/json_repository.py**: Consolidated error handling to `_safe_read_json()` helper function
- **Dynamic repetitive properties**:
  - `ThresholdProvider`: Dynamic property access using `__getattr__`
  - `DigestConfig`: Dynamic threshold delegation

### Added

- **GrandDigestManager unit tests added** (11 tests):
  - `get_template()` structure, version, and level validation
  - `load_or_create()` new creation, existing load, and corrupted file handling
  - `update_digest()` normal update, level retention, and timestamp update
- **`__all__` exports added**:
  - `config/path_resolver.py`
  - `config/threshold_provider.py`
  - `infrastructure/json_repository.py`
  - `infrastructure/logging_config.py`
  - `application/shadow/cascade_processor.py`
- Added footer to `agents/README.md`

### Fixed

- `config/__init__.py`: Moved local imports (in `show_paths` method) to module top level
- Import path unification: `from config import LEVEL_CONFIG` → `from domain.constants import LEVEL_CONFIG`

---

## [2.1.0] - 2025-11-27

### Changed

- **Complete removal of DEPRECATED methods**:
  - Removed `load_or_create`, `save`, `find_new_files`

### Added

- **Type safety improvement**:
  - Added `ProvisionalDigestFile` type
  - Type replacement in `provisional_loader.py`, `save_provisional_digest.py`
  - Limited `Dict[str, Any]` usage to generic functions only

---

## [2.0.1] - 2025-11-27

### Changed

- **Log unification**: Replaced all `print` with `logger`
- **Facade simplification**: Organized public API (DEPRECATED 3 methods)

### Added

- **Test coverage expansion**
- **Type definition unification**: Added `DigestMetadataComplete`

### Fixed

- `cascade_processor.py`: Fixed missing type check

---

## [2.0.0] - 2025-11-27

### Breaking Changes

**Clean Architecture refactoring complete** - Full migration of internal structure to 4-layer architecture

- **Backward compatibility layer removed**: Old import paths (`from validators import ...`, `from finalize_from_shadow import ...`, etc.) no longer work
- **Recommended import path changes**:
  ```python
  # Old (no longer works)
  from validators import validate_dict
  from finalize_from_shadow import DigestFinalizerFromShadow

  # New (recommended)
  from application.validators import validate_dict
  from interfaces import DigestFinalizerFromShadow
  ```

### Added

- **Clean Architecture 4-layer structure**:
  - `domain/` - Core business logic (constants, types, exceptions, file naming)
  - `infrastructure/` - External concerns (JSON operations, file scanning, logging)
  - `application/` - Use cases (Shadow management, GrandDigest management, Finalize processing)
  - `interfaces/` - Entry points (DigestFinalizerFromShadow, ProvisionalDigestSaver)

- **Major test expansion**:
  - New test files added
  - All tests adapted to new architecture

- **Documentation updates**:
  - ARCHITECTURE.md - Added detailed 4-layer structure explanation
  - API_REFERENCE.md - Restructured by layer
  - scripts/README.md - Fully updated to 4-layer structure
  - CONTRIBUTING.md - Added new feature addition guide

### Changed

- **Dependency clarification**: Resolved circular references and established layered dependencies
  - `domain/` ← Depends on nothing
  - `infrastructure/` ← domain/ only
  - `application/` ← domain/ + infrastructure/
  - `interfaces/` ← application/

### Removed

- **Backward compatibility layer removed**:
  - `scripts/finalize/`
  - `scripts/shadow/`
  - Root level files: `validators.py`, `digest_times.py`, `grand_digest.py`, `shadow_grand_digest.py`, `finalize_from_shadow.py`, `save_provisional_digest.py`, `__version__.py`, `digest_types.py`, `exceptions.py`, `utils.py`

### Migration Guide

Developer migration guide:

1. **Update import paths**:
   ```python
   # Domain layer
   from domain import LEVEL_CONFIG, __version__, ValidationError
   from domain.file_naming import extract_file_number

   # Application layer
   from application.shadow import ShadowUpdater
   from application.grand import ShadowGrandDigestManager

   # Interfaces layer
   from interfaces import DigestFinalizerFromShadow
   from interfaces.interface_helpers import sanitize_filename
   ```

2. **Details**: See ARCHITECTURE.md and scripts/README.md

---

## [1.1.8] - 2025-11-27

### Added
- **CLAUDE.md**: Project-specific AI agent guidelines
  - SSoT locations and reference patterns
  - Development workflow and coding conventions
  - Terminology unification rules (Loop, Digest, GrandDigest)
- **Backup & Recovery**: Added section to ADVANCED.md
  - 4-layer structure of long-term memory (Loop/Provisional/Hierarchical Digest/Essence)
  - Backup priority based on reconstructability (only Loop is required)
  - 3 methods: Git integration/manual/cloud sync
  - Recovery procedures (per layer) and recommended frequency

### Changed
- **SSoT reference enforcement**:
  - `digest-auto/SKILL.md`: Simplified "Mottled Memory" explanation to README.md SSoT reference
  - `FAQ.md`: Simplified "Mottled Memory" answer to SSoT reference
- **Version information unification**:
  - Added version headers to `ARCHITECTURE.md`, `TROUBLESHOOTING.md`, `API_REFERENCE.md`
- **Documentation improvements**:
  - Improvements based on document health diagnostics
  - Reduced duplicate content
  - Updated ADVANCED.md table of contents

---

## [1.1.7] - 2025-11-27

### Changed
- **Documentation refactoring**: Major documentation reorganization
  - README.md: Traffic director approach (major simplification)
  - docs/README.md: Specialized as AI Specification Hub
  - Removed version footer - consolidated to SSoT
  - Added breadcrumbs (under docs/)
  - scripts/README.md: Added shadow/, finalize/, __version__.py

### Fixed
- **Path reference fixes**: `homunculus/Toybox` → Changed to placeholder
  - `skills/digest-config/SKILL.md` (line 26, 97)
  - `skills/digest-setup/SKILL.md` (line 27)
- **Documentation improvements**:
  - ARCHITECTURE.md: Added SSoT reference for cascade flow
  - Added breadcrumb navigation to all docs files
  - Introduced persona-based navigation table

---

## [1.1.6] - 2025-11-27

### Added
- **shadow/ package**: Split `shadow_grand_digest.py` into 4 modules
  - `shadow/template.py`: Template generation (ShadowTemplate class)
  - `shadow/file_detector.py`: File detection (FileDetector class)
  - `shadow/shadow_io.py`: Shadow I/O (ShadowIO class)
  - `shadow/shadow_updater.py`: Shadow update (ShadowUpdater class)

### Changed
- **Refactoring**: Facade split of shadow_grand_digest.py
  - Original file maintained as Facade for backward compatibility

---

## [1.1.5] - 2025-11-27

### Added
- **finalize/ package**: Split `finalize_from_shadow.py` into 4 modules
  - `finalize/shadow_validator.py`: Shadow validation (ShadowValidator class)
  - `finalize/provisional_loader.py`: Provisional loading (ProvisionalLoader class)
  - `finalize/digest_builder.py`: Digest building (RegularDigestBuilder class)
  - `finalize/persistence.py`: Persistence handling (DigestPersistence class)

### Changed
- **Refactoring**: Facade split of finalize_from_shadow.py
  - Original file maintained as Facade for backward compatibility

---

## [1.1.4] - 2025-11-27

### Changed
- **Refactoring**: Complete migration to exception handling
  - Started using exception classes from `exceptions.py` (`ValidationError`, `DigestError`, `FileIOError`)
  - Replaced `log_error()` with appropriate exceptions
  - Changed method return values from `bool`/`Optional` to exception-based
  - Updated related tests from `assertFalse()` to `assertRaises()`

---

## [1.1.3] - 2025-11-27

### Added
- **__version__.py**: Created new Single Source of Truth for version constant (`DIGEST_FORMAT_VERSION`)

### Changed
- **Refactoring**: Version string consolidation
  - Replaced hardcoded `"1.0"` with `DIGEST_FORMAT_VERSION` constant
- **Refactoring**: Gradual adoption of validators.py
  - Replaced `isinstance()` with `is_valid_dict()`/`is_valid_list()`

---

## [1.1.2] - 2025-11-27

### Fixed
- **plugin.json**: Updated version number to 1.1.2 (ensuring consistency with CHANGELOG)
- **digest-auto/SKILL.md**: Fixed path reference (Toybox → Weave)
- **save_provisional_digest.py**: Unified Provisional Digest field name to `source_file` (consistency with digest_types.py)
- **ARCHITECTURE.md**: Unified Provisional Digest field name to `source_file`

### Changed
- **SKILL.md**: Changed implementation guidelines to reference common file (_implementation-notes.md) (reduced duplication)

---

## [1.1.1] - 2025-11-27

### Changed
- **ARCHITECTURE.md**: Fixed GrandDigest/ShadowGrandDigest/Provisional file format to match source code
- **API_REFERENCE.md**: Added format_digest_number(), PLACEHOLDER_* constants, utils.py functions
- **TROUBLESHOOTING.md**: Fixed Provisional path, fixed last_digest_times.json path
- **GUIDE.md**: Simplified Mottled Memory explanation via SSoT reference, changed troubleshooting to TROUBLESHOOTING.md reference
- **GLOSSARY.md**: SSoT reference
- **FAQ.md**: SSoT reference
- **docs/README.md**: Added SSoT cross-reference table
- **skills/digest-setup/SKILL.md**: Fixed Provisional directory path

### Fixed
- Unified all document dates to 2025-11-27
- Reduced duplicate content across documents (established Single Source of Truth)

---

## [1.1.0] - 2025-11-26

### Added
- **GLOSSARY.md**: Created new glossary
- **QUICKSTART.md**: Created new 5-minute quickstart guide
- **docs/README.md**: Created new documentation hub
- **skills/shared/**: Created new shared components directory
  - `_common-concepts.md`: Common definitions for Mottled Memory, memory consolidation cycle
  - `_implementation-notes.md`: Common implementation guidelines
- **CHANGELOG.md**: Created new changelog file

### Changed
- **ARCHITECTURE.md**: Fixed version notation from 1.3.0 to 1.1.0 (consistency)
- **README.md**: Unified plugin path to `@Plugins-Weave`
- **TROUBLESHOOTING.md**: Fixed file naming convention explanation
- **digest-setup/SKILL.md**: Changed sample paths to variable format
- **digest-config/SKILL.md**: Changed sample paths to variable format
- **digest-auto/SKILL.md**: Changed sample paths to variable format

### Fixed
- Resolved version inconsistencies across documents
- Unified plugin name (@Toybox → @Plugins-Weave)
- Fixed file naming convention explanation to accurate format

---

## [1.0.0] - 2025-11-24

### Added
- Initial release
- 8-layer memory structure (Weekly to Centurial)
- `/digest` command
- `@digest-setup` skill
- `@digest-config` skill
- `@digest-auto` skill
- DigestAnalyzer agent
- GrandDigest/ShadowGrandDigest management
- Provisional/Regular Digest generation
- Mottled Memory detection feature

</details>

---

## Versioning Rules

- **MAJOR**: Incompatible changes
- **MINOR**: Backward-compatible feature additions
- **PATCH**: Backward-compatible bug fixes

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
