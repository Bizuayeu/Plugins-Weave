<!-- Last synced: 2025-12-16 -->
English | [日本語](INDEX.md)

# Document Index

Navigation to all EpisodicRAG plugin documentation.

## Reader's Guide

| Reader | Start With | Next |
|--------|-----------|------|
| New Users | [QUICKSTART](docs/user/QUICKSTART.en.md) | [GUIDE](docs/user/GUIDE.md) |
| Daily Use | [CHEATSHEET](docs/user/CHEATSHEET.en.md) | [FAQ](docs/user/FAQ.md) |
| Troubleshooting | [TROUBLESHOOTING](docs/user/TROUBLESHOOTING.md) | [FAQ](docs/user/FAQ.md) |
| Developers | [ARCHITECTURE](docs/dev/ARCHITECTURE.md) | [API_REFERENCE](docs/dev/API_REFERENCE.md) |
| AI (Claude) | [CLAUDE.md](.claude/CLAUDE.md) | [AI Spec Hub](docs/README.md) |

---

## User Documentation (`docs/user/`)

| File | Description | Japanese |
|------|-------------|----------|
| [QUICKSTART.en.md](docs/user/QUICKSTART.en.md) | 5-minute Quickstart | [JP](docs/user/QUICKSTART.md) |
| [GUIDE.md](docs/user/GUIDE.md) | Basic Operations Guide | - |
| [ADVANCED.md](docs/user/ADVANCED.md) | Advanced Usage | - |
| [CHEATSHEET.en.md](docs/user/CHEATSHEET.en.md) | Command Quick Reference | [JP](docs/user/CHEATSHEET.md) |
| [FAQ.md](docs/user/FAQ.md) | Frequently Asked Questions | - |
| [TROUBLESHOOTING.md](docs/user/TROUBLESHOOTING.md) | Troubleshooting | - |

---

## Developer Documentation (`docs/dev/`)

| File | Description |
|------|-------------|
| [ARCHITECTURE.md](docs/dev/ARCHITECTURE.md) | System Design & Directory Structure |
| [API_REFERENCE.md](docs/dev/API_REFERENCE.md) | DigestConfig API |
| [DESIGN_DECISIONS.md](docs/dev/DESIGN_DECISIONS.md) | Design Decision Rationale |
| [LEARNING_PATH.md](docs/dev/LEARNING_PATH.md) | Learning Path |
| [ERROR_RECOVERY_PATTERNS.md](docs/dev/ERROR_RECOVERY_PATTERNS.md) | Error Handling Patterns |

### Layer-specific API (`docs/dev/api/`)

| File | Layer |
|------|-------|
| [domain.md](docs/dev/api/domain.md) | Constants, Types, Exceptions |
| [infrastructure.md](docs/dev/api/infrastructure.md) | JSON Operations, File I/O |
| [application.md](docs/dev/api/application.md) | Facade, Use Cases |
| [interfaces.md](docs/dev/api/interfaces.md) | CLI, Entry Points |
| [config.md](docs/dev/api/config.md) | Configuration API |

---

## Specifications

### Commands (`commands/`)

| Command | File |
|---------|------|
| `/digest` | [digest.md](commands/digest.md) |

### Skills (`skills/`)

| Skill | File |
|-------|------|
| `@digest-setup` | [SKILL.md](skills/digest-setup/SKILL.md) |
| `@digest-config` | [SKILL.md](skills/digest-config/SKILL.md) |
| `@digest-auto` | [SKILL.md](skills/digest-auto/SKILL.md) |

### Agents (`agents/`)

| Agent | File |
|-------|------|
| DigestAnalyzer | [digest-analyzer.md](agents/digest-analyzer.md) |

---

## Project Information

| File | Description | Japanese |
|------|-------------|----------|
| [README.en.md](README.en.md) | Glossary & Reference | [JP](README.md) |
| [CONCEPT.en.md](CONCEPT.en.md) | Design Philosophy | [JP](CONCEPT.md) |
| [CHANGELOG.en.md](CHANGELOG.en.md) | Change History | [JP](CHANGELOG.md) |
| [CONTRIBUTING.en.md](CONTRIBUTING.en.md) | Contribution Guide | [JP](CONTRIBUTING.md) |

---

## Others

| File | Description |
|------|-------------|
| [scripts/README.md](scripts/README.md) | Python Scripts Overview |
| [scripts/test/TESTING.md](scripts/test/TESTING.md) | Test Execution Guide |
| [skills/shared/_implementation-notes.md](skills/shared/_implementation-notes.md) | Implementation Guidelines (SSoT) |

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
