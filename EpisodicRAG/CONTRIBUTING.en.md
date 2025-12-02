<!-- Last synced: 2025-12-01 -->
[English](CONTRIBUTING.en.md) | [日本語](CONTRIBUTING.md)

# Contributing to EpisodicRAG Plugin

Thank you for your interest in contributing to the EpisodicRAG plugin!

> **For AI Agents**: See [.claude-plugin/CLAUDE.md](.claude-plugin/CLAUDE.md).

> **Supported Version**: EpisodicRAG Plugin (see [version.py](scripts/domain/version.py))

This document explains how to set up the development environment, test code changes, and create pull requests.

---

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Installation Methods](#installation-methods)
   - [Pattern A: Via Local Marketplace (Recommended)](#pattern-a-via-local-marketplace-recommended)
   - [Pattern B: Manual Setup (Traditional Method)](#pattern-b-manual-setup-traditional-method)
3. [Manual Script Execution](#manual-script-execution)
4. [Creating Pull Requests](#creating-pull-requests)
5. [Coding Standards](#coding-standards)
6. [Testing](#testing)
7. [Documentation](#documentation)
8. [Support](#support)

---

## Development Environment Setup

### Prerequisites

- Python 3.x
- Bash (Git Bash / WSL)
- Claude Code environment

---

## Installation Methods

There are two ways to test a plugin under development.

### Pattern A: Via Local Marketplace (Recommended)

**Overview**: Install local plugins using Claude Code's `/plugin install` command. This allows testing with the same flow as actual marketplace distribution.

#### 1. Verify Directory Structure

```text
plugins-weave/
├── .claude-plugin/                     # Marketplace configuration
│   └── marketplace.json
└── EpisodicRAG/                        # Plugin main body
    ├── .claude-plugin/
    │   ├── CLAUDE.md                   # AI agent instructions
    │   ├── plugin.json
    │   ├── config.template.json
    │   ├── last_digest_times.template.json
    │   ├── GrandDigest.template.txt
    │   └── ShadowGrandDigest.template.txt
    ├── agents/
    ├── commands/
    ├── docs/
    ├── scripts/                        # Clean Architecture (4 layers)
    │   ├── domain/                     # Core business logic
    │   │   └── config/                 # Configuration constants & validation
    │   ├── infrastructure/             # External concerns (I/O)
    │   │   └── config/                 # Configuration file I/O
    │   ├── application/                # Use cases
    │   │   └── config/                 # DigestConfig (Facade)
    │   ├── interfaces/                 # Entry points
    │   └── test/
    ├── skills/
    │   └── shared/
    ├── pyproject.toml
    ├── README.md / README.en.md
    ├── CHANGELOG.md / CHANGELOG.en.md
    └── CONTRIBUTING.md / CONTRIBUTING.en.md
```

> 📖 **Detailed Directory Structure**: [ARCHITECTURE.md](docs/dev/ARCHITECTURE.md#directory-structure)

`marketplace.json` is already in place (included in the repository).

#### 2. Register Local Marketplace

Execute the following in Claude Code:

```ClaudeCLI
# With relative path
/marketplace add ./plugins-weave

# Or with absolute path
/marketplace add C:\Users\anyth\DEV\plugins-weave
```

**Success output**:
```text
✅ Marketplace 'Plugins-Weave' added successfully
```

#### 3. Install the Plugin

```ClaudeCLI
/plugin install EpisodicRAG-Plugin@Plugins-Weave
```

**Success output**:
```text
✅ Plugin 'EpisodicRAG-Plugin' installed successfully
```

#### 4. Initial Setup

```ClaudeCLI
@digest-setup
```

Configure interactively.

#### 5. Verify Operation

```ClaudeCLI
@digest-auto
```

**Expected output**:
```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 EpisodicRAG System Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
...
```

#### 6. Development Iteration (After Code Changes)

After modifying plugin code, retest with:

```ClaudeCLI
# 1. Uninstall
/plugin uninstall EpisodicRAG-Plugin@Plugins-Weave

# 2. Reinstall
/plugin install EpisodicRAG-Plugin@Plugins-Weave

# 3. Setup (if needed)
@digest-setup

# 4. Verify operation
@digest-auto
```

**Benefits**:
- Same test environment as actual marketplace distribution flow
- Easy install/uninstall with `/plugin install` command
- Easy version management

---

### Pattern B: Manual Setup (Traditional Method)

**Overview**: Traditional method of directly manipulating the plugin directory.

#### 1. Execute Setup Script

```bash
cd plugins-weave/EpisodicRAG
bash scripts/setup.sh
```

#### 2. Verify Configuration

```bash
python scripts/config.py --show-paths
```

**Example output**:
```text
Plugin Root: [Your Project]/plugins-weave/EpisodicRAG
Config File: [Your Project]/plugins-weave/EpisodicRAG/.claude-plugin/config.json
Loops Path: [Your Project]/plugins-weave/EpisodicRAG/data/Loops
Digests Path: [Your Project]/plugins-weave/EpisodicRAG/data/Digests
Essences Path: [Your Project]/plugins-weave/EpisodicRAG/data/Essences
```

(If identity_file_path is configured, "Identity File:" line is also displayed)

**Benefits**:
- Simple (no marketplace registration required)
- Same as existing workflow

**Drawbacks**:
- May behave differently from marketplace distribution
- Manual install/uninstall

---

**Recommendation**: During development, use **Pattern A (Local Marketplace)** to develop while verifying marketplace distribution behavior.

---

## Manual Script Execution

Plugin internal scripts can also be executed directly (for debugging).

### config_cli.py - Configuration Management (v4.0.0+)

Manages all path information and ensures Plugin self-containment.

```bash
cd plugins-weave/EpisodicRAG/scripts

# Display path information
python -m interfaces.config_cli --show-paths

# Output configuration JSON
python -m interfaces.config_cli
```

### Direct CLI Execution of Skills (v4.0.0+)

Skills can be executed directly as Python scripts (for debugging):

```bash
cd plugins-weave/EpisodicRAG/scripts

# Equivalent to @digest-setup
python -m interfaces.digest_setup

# Equivalent to @digest-config
python -m interfaces.digest_config

# Equivalent to @digest-auto
python -m interfaces.digest_auto
```

> **Note**: Usage via skills (`@digest-setup`, etc.) is still available.

### generate_digest_auto.sh - Automatic Digest Generation

Automatically generates hierarchical Digests.

```bash
bash scripts/generate_digest_auto.sh
```

---

## Clean Architecture (4-Layer Structure)

Since v2.0.0, `scripts/` adopts Clean Architecture (4-layer structure).

> 📖 **Detailed Specification**: Layer structure, dependency rules, and recommended import paths at [ARCHITECTURE.md](docs/dev/ARCHITECTURE.md#clean-architecture)
>
> 📖 **Architecture Selection Rationale**: [DESIGN_DECISIONS.md](docs/dev/DESIGN_DECISIONS.md)

**v4.0.0 Changes**: Configuration management (config) is distributed across subdirectories of each layer:
- `domain/config/` - Configuration constants, validation helpers
- `infrastructure/config/` - Configuration file I/O, path resolution
- `application/config/` - DigestConfig (Facade), service classes

### Guide for Adding New Features

| Feature to Add | Location |
|----------------|----------|
| Constants, type definitions, exceptions | `domain/` |
| Configuration-related constants/validation | `domain/config/` |
| File I/O, logging | `infrastructure/` |
| Configuration file loading, path resolution | `infrastructure/config/` |
| Business logic | `application/` |
| Configuration management service (Facade) | `application/config/` |
| External entry points | `interfaces/` |

---

## Creating Pull Requests

1. Fork this repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

### Commit Messages

Use clear and concise commit messages:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation update
- `refactor:` Refactoring
- `test:` Test addition/modification

---

## Coding Standards

- Python: PEP 8 compliant
- Bash: Verified with ShellCheck
- Markdown: Clear and concise writing

---

## Testing

> 📖 **Test Details**: See [scripts/README.md](scripts/README.md#tests) for test directory structure and execution methods.

### Quick Start

```bash
cd plugins-weave/EpisodicRAG/scripts

# Run all tests
python -m pytest test/ -v

# Layer-specific tests
python -m pytest test/domain_tests/ -v
python -m pytest test/config_tests/ -v
```

### Manual Testing

After making changes, always test the following:

1. Basic commands (`/digest`, `@digest-auto`)
2. Skills (`@digest-setup`, `@digest-config`)
3. Agent (`@DigestAnalyzer`)
4. Hierarchical Digest generation flow

---

## Development Environment Notes

### Environment Mixing During Installation Testing

When development environment and installed plugin exist on the same machine, note the following:

**Problem**: Running `@digest-setup` etc. may create configuration files in the development folder

**Verification method**:
```bash
cd plugins-weave/EpisodicRAG
git status
```
```text
# Expected: "nothing to commit, working tree clean"
```

**Best Practices**:

1. **Always check git status after installation**
2. **Don't commit configuration files to the development folder**
3. **Edit configuration on the installed plugin side**
   - Installation location: `~/.claude/plugins/EpisodicRAG-Plugin@Plugins-Weave/`

For details, see [TROUBLESHOOTING.md](docs/user/TROUBLESHOOTING.md#development-and-installation-environment-mixing).

---

## Documentation

Update documentation as needed when making code changes:

- README.md - For general users
- CONTRIBUTING.md - This file
- docs/ - Detailed documentation

### Single Source of Truth (SSoT) Principle

**SSoT (Single Source of Truth)** is the principle of not writing the same information in multiple places, but defining a canonical definition location and referencing it. This reduces maintenance burden during changes and prevents inconsistencies.

#### Documentation SSoT

| Information | SSoT (Canonical Definition Location) | Reference Method |
|-------------|--------------------------------------|------------------|
| Terminology/concept definitions | [README.md](README.md) (Glossary) | `> 📖 Details: [Glossary](../../README.md#section-name)` |
| Footer | `_footer.md` | Unified at the end of each document |
| Configuration specification | [api/config.md](docs/dev/api/config.md) | Reference via link |

#### Version SSoT

Version information's single source of truth is the `version` field in `.claude-plugin/plugin.json`.

```json
// .claude-plugin/plugin.json
{
  "name": "EpisodicRAG-Plugin",
  "version": "x.y.z",  // ← This is SSoT - see plugin.json for actual value
  ...
}
```

| File | Field | Sync Method |
|------|-------|-------------|
| `.claude-plugin/plugin.json` | `version` | **SSoT** (origin) |
| `pyproject.toml` | `version` | Manual sync |
| `../.claude-plugin/marketplace.json` | `plugins[].version` | Manual sync |
| `CHANGELOG.md` | `## [x.x.x]` | Manual sync |
| `../README.md` / `../README.en.md` | Version badge | Manual sync |
| `scripts/domain/version.py` | `__version__` | **Automatic** (dynamic loading) |

> 📊 These syncs are verified by tests in `scripts/test/domain_tests/test_version.py`.

**Dynamic Loading Mechanism**:

`scripts/domain/version.py` dynamically loads the version from `plugin.json`:

```python
from domain import __version__
print(__version__)  # Displays version from plugin.json
```

### Release Procedure

When updating version, update **5 files**:

1. `.claude-plugin/plugin.json` - Update `version` field (SSoT)
2. `pyproject.toml` - Update `version` to same value
3. `../.claude-plugin/marketplace.json` - Update `plugins[0].version` to same value
4. `CHANGELOG.md` - Add new section `## [x.x.x] - YYYY-MM-DD`
5. `../README.md` and `../README.en.md` - Update version badges

```bash
# Verification (tests verify sync across all files)
cd scripts
python -m pytest test/domain_tests/test_version.py -v
```

### Document Header Version

Some documents (ARCHITECTURE.md, API_REFERENCE.md, TROUBLESHOOTING.md) have version headers:

```markdown
> **Supported Version**: EpisodicRAG Plugin ([version.py](scripts/domain/version.py) reference) / File Format 1.0
```

**Recommended**: Use dynamic reference format (`[version.py](...) reference`) to avoid manual updates.

---

## Documentation Sync Process

### Bilingual Documentation Policy

The EpisodicRAG plugin uses Japanese as the primary language and provides English versions of major documents.

1. **Primary Language**: Japanese (日本語)
2. **Secondary Language**: English

> **Translation Policy**: Only major documents (README, CHANGELOG, CONTRIBUTING, QUICKSTART, CHEATSHEET) are maintained in English. Other documents remain Japanese-only to reduce translation maintenance costs.

### Currently Synced Files

| Japanese | English | Status |
|----------|---------|--------|
| `README.md` | `README.en.md` | ✅ Synced |
| `CHANGELOG.md` | `CHANGELOG.en.md` | ✅ Synced |
| `CONTRIBUTING.md` | `CONTRIBUTING.en.md` | ✅ Synced |
| `docs/user/QUICKSTART.md` | `docs/user/QUICKSTART.en.md` | ✅ Synced |
| `docs/user/CHEATSHEET.md` | `docs/user/CHEATSHEET.en.md` | ✅ Synced |

### Sync Workflow

When updating Japanese documentation, also sync the corresponding English documentation.

1. **Edit Japanese version first** - Edit the Japanese version first
2. **Update English version** - Update English version in the same PR
3. **Add sync header** - Add header at the top of English file:
   ```markdown
   <!-- Last synced: YYYY-MM-DD -->
   ```

### Adding New Translations

When adding new English translations:

1. Copy structure from Japanese version
2. Translate content maintaining formatting
3. Add sync header with date
4. Update this table

---

## Support

If you have questions or issues, please report them via GitHub Issues.

Thank you for your contribution!

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
