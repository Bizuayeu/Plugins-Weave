<!--
  This file is the EpisodicRAG plugin landing page.
  Last synced: 2026-05-31
-->
English | [日本語](README.md)

# EpisodicRAG Plugin

Hierarchical Memory & Digest Generation System (8 Layers, 100 Years)

![EpisodicRAG Plugin - Architecture diagram of 8-layer hierarchical memory management system](./EpisodicRAG.png)
[![Version](https://img.shields.io/badge/version-5.8.1-blue.svg)](https://github.com/Bizuayeu/Plugins-Weave)
[![CI](https://github.com/Bizuayeu/Plugins-Weave/actions/workflows/test.yml/badge.svg)](https://github.com/Bizuayeu/Plugins-Weave/actions/workflows/test.yml)
[![Tests](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FBizuayeu%2F96d92fd7b8d51f31734ca068dfb1e850%2Fraw%2Ftest_badge.json)](https://github.com/Bizuayeu/Plugins-Weave/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/Bizuayeu/Plugins-Weave/branch/main/graph/badge.svg)](https://codecov.io/gh/Bizuayeu/Plugins-Weave)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](../LICENSE)

---

## Overview

EpisodicRAG is a system that hierarchically digests conversation logs (Loop files) and structures them as long-term memory for inheritance. It automatically manages 8 layers of memory (Weekly → Centurial, approximately 108 years).

### Key Features

- **Hierarchical Memory Management**: Automatic digest generation across 8 layers (weekly to century)
- **Fragmented Memory Prevention**: Instant detection of unprocessed Loops prevents memory gaps
- **Cross-Session Inheritance**: Carry over long-term memory to next session via GitHub

---

## Documentation Navigation

| Your Goal | Documents to Read |
|-----------|-------------------|
| 📚 **Browse all documents** | [INDEX.en.md](./INDEX.en.md) |
| 🚀 **Get started** | [QUICKSTART](./docs/user/QUICKSTART.en.md) → [Glossary](./GLOSSARY.en.md) |
| 📘 **Use daily** | [GUIDE](./docs/user/GUIDE.md) *(Japanese)* |
| 📝 **Quick reference** | [CHEATSHEET](./docs/user/CHEATSHEET.en.md) |
| 🔧 **Customize settings** | [digest-config](./skills/digest-config/SKILL.md) *(Japanese)* |
| 📊 **Check status** | [digest-auto](./skills/digest-auto/SKILL.md) *(Japanese)* |
| ❓ **Solve problems** | [FAQ](./docs/user/FAQ.md) → [TROUBLESHOOTING](./docs/user/TROUBLESHOOTING.md) *(Japanese)* |
| 🛠️ **Contribute** | [CONTRIBUTING](./CONTRIBUTING.md) → [ARCHITECTURE](./docs/dev/ARCHITECTURE.md) *(Japanese)* |
| 💡 **Understand design philosophy** | [CONCEPT](./CONCEPT.en.md) |
| 🤖 **View AI/Claude specs** | [AI Spec Hub](./docs/README.md) *(Japanese)* |
| 📋 **Check changelog** | [CHANGELOG](./CHANGELOG.md) *(Japanese)* |

> **Note**: Documents marked *(Japanese)* are available in Japanese only.
> Per our [AI-First Documentation Policy](./GLOSSARY.en.md#language-policy), AI agents can understand and translate Japanese content on-the-fly.

---

## Quick Installation

```ClaudeCLI
# 1. Add marketplace
/plugin marketplace add https://github.com/Bizuayeu/Plugins-Weave

# 2. Install plugin
/plugin install EpisodicRAG@plugins-weave

# 3. Initial setup (interactive)
@digest-setup
```

For detailed setup instructions, see [QUICKSTART.en.md](./docs/user/QUICKSTART.en.md).

---

## Basic Usage

### Memory Retention Cycle

```
Add Loop → /digest → Add Loop → /digest → ...
```

By following this principle, AI can remember all Loops.

### Main Commands

| Command | Description |
|---------|-------------|
| `/digest` | Detect and analyze new Loops |
| `/digest weekly` | Finalize Weekly Digest |
| `/dream-defrag` | Prune auto-memory (subtractive dream = GC; recommended when >50) |
| `@digest-auto` | Check system status and recommended actions |
| `@digest-setup` | Initial setup |
| `@digest-config` | Change settings |
| `@wakeup` | Session-start engine for claude.ai: loads long-term memory and applies the persona directive (requires config & Read token) |

For details, see [GUIDE.md](./docs/user/GUIDE.md) *(Japanese)*.

---

## 8-Layer Structure

| Layer | Time Scale |
|-------|------------|
| Weekly | ~1 week |
| Monthly | ~1 month |
| Quarterly | ~3 months |
| Annual | ~1 year |
| Triennial | ~3 years |
| Decadal | ~9 years |
| Multi-decadal | ~27 years |
| Centurial | ~108 years |

> For complete layer table, see [Glossary](./GLOSSARY.en.md#8-layer-hierarchy)

---

## Cross-Session Memory Inheritance

With GitHub integration, you can retain and inherit long-term memory after session ends.

In claude.ai environments, the `@wakeup` skill automates session-start memory loading (SHA-pinned fetch via Read token; supports Private repo reference and PR write-back; all repo-specific values injected via config).

→ [ADVANCED.md](./docs/user/ADVANCED.md) *(Japanese)*

---

## License

**MIT License** - See [LICENSE](../LICENSE) for details

### Patent

**Japanese Patent Application 2025-198943** - Hierarchical Memory & Digest Generation System

- Personal/Non-commercial use: Freely available under MIT License
- Commercial use: Please consult regarding patent rights before use

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
