<!-- Last synced: 2025-12-07 -->
English | [日本語](CHANGELOG.md)

# Changelog

All notable changes to EpisodicRAG Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## Table of Contents

- [v5.x](#510---2025-12-07)
- [v4.x](#410---2025-12-03)
- [v3.x](#330---2025-11-29)
- [Archive (v2.x and earlier)](#archive-v2x-and-earlier)
- [Versioning Rules](#versioning-rules)

---

## [5.1.0] - 2025-12-07

### Changed

- **digest.md refactoring**
  - Pattern 2 restructured from 7 to 9 steps
  - TOC split by pattern for easier navigation
  - Renamed "Output Examples" to "Error Output Examples" (success examples moved to each Step 9)

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

*For more details, see [ARCHITECTURE.md](docs/dev/ARCHITECTURE.md)*
