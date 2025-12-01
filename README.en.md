<!--
  This file is for GitHub repository landing page display.
  See EpisodicRAG/ directory for detailed documentation.
  Last synced: 2025-12-01
-->
English | [日本語](README.md)

# EpisodicRAG Plugin

Hierarchical Memory & Digest Generation System (8 Layers, 100 Years, Fully Self-Contained)

![EpisodicRAG Plugin - Architecture diagram of 8-layer hierarchical memory management system](EpisodicRAG.png)
[![Version](https://img.shields.io/badge/version-4.0.0-blue.svg)](https://github.com/Bizuayeu/Plugins-Weave)
[![CI](https://github.com/Bizuayeu/Plugins-Weave/actions/workflows/test.yml/badge.svg)](https://github.com/Bizuayeu/Plugins-Weave/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/Bizuayeu/Plugins-Weave/branch/main/graph/badge.svg)](https://codecov.io/gh/Bizuayeu/Plugins-Weave)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Overview

EpisodicRAG is a system that hierarchically digests conversation logs (Loop files) and structures them as long-term memory for inheritance. It automatically manages 8 layers of memory (Weekly → Centurial, approximately 108 years).

### Key Features

- **Hierarchical Memory Management**: Automatic digest generation across 8 layers (weekly to century)
- **Fragmented Memory Prevention**: Instant detection of unprocessed Loops prevents memory gaps
- **Cross-Session Inheritance**: Carry over long-term memory to next session via GitHub
- **Fully Self-Contained**: All data stored within the plugin (can also integrate with existing projects)

---

## Documentation Navigation

| You are... | Documents to Read |
|------------|-------------------|
| 🚀 **Getting Started** | [QUICKSTART](EpisodicRAG/docs/user/QUICKSTART.en.md) → [Glossary](EpisodicRAG/README.en.md) |
| 📘 **Daily User** | [GUIDE](EpisodicRAG/docs/user/GUIDE.md) |
| 📝 **Quick Reference** | [CHEATSHEET](EpisodicRAG/docs/user/CHEATSHEET.en.md) |
| 🔧 **Customizing Settings** | [digest-config](EpisodicRAG/skills/digest-config/SKILL.md) |
| 📊 **Checking Status** | [digest-auto](EpisodicRAG/skills/digest-auto/SKILL.md) |
| ❓ **Troubleshooting** | [FAQ](EpisodicRAG/docs/user/FAQ.md) → [TROUBLESHOOTING](EpisodicRAG/docs/user/TROUBLESHOOTING.md) |
| 🛠️ **Contributing** | [CONTRIBUTING](EpisodicRAG/CONTRIBUTING.md) → [ARCHITECTURE](EpisodicRAG/docs/dev/ARCHITECTURE.md) |
| 🤖 **AI/Claude Specs** | [AI Spec Hub](EpisodicRAG/docs/README.md) |
| 📋 **Changelog** | [CHANGELOG](EpisodicRAG/CHANGELOG.md) |

---

## Quick Installation

```ClaudeCLI
# 1. Add marketplace
/marketplace add https://github.com/Bizuayeu/Plugins-Weave

# 2. Install plugin
/plugin install EpisodicRAG-Plugin@Plugins-Weave

# 3. Initial setup (interactive)
@digest-setup
```

For detailed setup instructions, see [QUICKSTART.en.md](EpisodicRAG/docs/user/QUICKSTART.en.md).

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
| `@digest-auto` | Check system status and recommended actions |
| `@digest-setup` | Initial setup |
| `@digest-config` | Change settings |

For details, see [GUIDE.md](EpisodicRAG/docs/user/GUIDE.md).

---

## 8-Layer Structure

| Layer | Time Scale |
|-------|------------|
| Weekly | ~1 week |
| Monthly | ~1 month |
| Quarterly | ~3 months |
| Annual | ~1 year |
| Triennial | ~3 years |
| Decadal | ~10 years |
| Multi-decadal | ~30 years |
| Centurial | ~100 years |

> For complete layer table, see [Glossary](EpisodicRAG/README.en.md#8-layer-hierarchy)

---

## Cross-Session Memory Inheritance

With GitHub integration, you can retain and inherit long-term memory after session ends.

→ [ADVANCED.md](EpisodicRAG/docs/user/ADVANCED.md)

---

## License

**MIT License** - See [LICENSE](LICENSE) for details

### Patent

**Japanese Patent Application 2025-198943** - Hierarchical Memory & Digest Generation System

- Personal/Non-commercial use: Freely available under MIT License
- Commercial use: Please consult regarding patent rights before use

---

## Author

**Weave** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)

---
**EpisodicRAG** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
