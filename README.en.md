<!-- Last synced: 2026-01-04 -->
English | [日本語](README.md)

# Plugins-Weave

Claude Code plugins for autonomous AI with long-term memory, expression, and communication

![Plugins-Weave - Claude Code Plugin Marketplace](./PluginsWeave.png)
[![Version](https://img.shields.io/badge/version-5.2.0-blue.svg)](https://github.com/Bizuayeu/Plugins-Weave)
[![CI](https://github.com/Bizuayeu/Plugins-Weave/actions/workflows/test.yml/badge.svg)](https://github.com/Bizuayeu/Plugins-Weave/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Why Plugins-Weave?

A plugin collection for AI to evolve from a mere "tool" into a "collaborative partner."

| Challenge | Solution | Plugin |
|-----------|----------|--------|
| **No memory across sessions** | 8-layer long-term memory system | EpisodicRAG |
| **Only passive responses** | Proactive essay/email delivery | EmailingEssay |
| **Text-only, limited expression** | Emotion-based facial expressions | VisualExpression |

---

## Navigation

### EpisodicRAG

| Your Goal | Reference |
|-----------|-----------|
| 🚀 **Getting started** | [QUICKSTART](EpisodicRAG/docs/user/QUICKSTART.en.md) |
| 📚 **Look up terms** | [Glossary](EpisodicRAG/GLOSSARY.en.md) |
| ❓ **Solve problems** | [FAQ](EpisodicRAG/docs/user/FAQ.md) / [TROUBLESHOOTING](EpisodicRAG/docs/user/TROUBLESHOOTING.md) |
| 🛠️ **Contribute** | [CONTRIBUTING](EpisodicRAG/CONTRIBUTING.en.md) |

### EmailingEssay

| Your Goal | Reference |
|-----------|-----------|
| 🚀 **Getting started** | [SETUP](EmailingEssay/SETUP.md) |
| 💡 **Understand concept** | [CONCEPT](EmailingEssay/CONCEPT.md) |
| 📖 **Command reference** | [essay.md](EmailingEssay/commands/essay.md) |
| 🛠️ **Contribute** | [CONTRIBUTING](EmailingEssay/CONTRIBUTING.md) |

### VisualExpression

| Your Goal | Reference |
|-----------|-----------|
| 🚀 **Getting started** | [README](VisualExpression/README.md) |
| 📖 **Skill specification** | [SKILL](VisualExpression/skills/SKILL.md) |
| 🛠️ **Contribute** | [CONTRIBUTING](VisualExpression/CONTRIBUTING.md) |

---

## Quick Installation

### 1. Add Marketplace

```ClaudeCLI
/marketplace add https://github.com/Bizuayeu/Plugins-Weave
```

### 2. Install Plugins

```ClaudeCLI
# EpisodicRAG (Long-term Memory Management)
/plugin install EpisodicRAG@Plugins-Weave

# EmailingEssay (Essay Delivery)
/plugin install EmailingEssay@Plugins-Weave

# VisualExpression (Visual Expression)
/plugin install VisualExpression@Plugins-Weave
```

---

## Plugin Details

### EpisodicRAG

**Hierarchical Memory & Digest Generation System (8 Layers, 100 Years)**

A system that hierarchically digests conversation logs (Loop files) and structures them as long-term memory for inheritance.

#### Key Features

- **Hierarchical Memory Management**: Automatic digest generation across 8 layers (weekly to century)
- **Fragmented Memory Prevention**: Instant detection of unprocessed Loops prevents memory gaps
- **Cross-Session Inheritance**: Carry over long-term memory to next session via GitHub

#### Main Commands

| Command | Description |
|---------|-------------|
| `/digest` | Detect and analyze new Loops |
| `/digest weekly` | Finalize Weekly Digest |
| `@digest-auto` | Check system status |
| `@digest-setup` | Initial setup |

→ [Full README](EpisodicRAG/README.en.md) / [QUICKSTART](EpisodicRAG/docs/user/QUICKSTART.en.md) / [Glossary](EpisodicRAG/GLOSSARY.en.md)

---

### EmailingEssay

**AI-Driven Essay Delivery System**

Enables proactive communication born from genuine reflection. AI spontaneously thinks, writes essays, and delivers them via email.

#### Key Features

- **Deep Reflection**: Leverages UltraThink for deep thinking
- **Proactive Delivery**: Automatic sending via schedule settings
- **Conscious Choice**: Respects the choice not to send

#### Main Commands

| Command | Description |
|---------|-------------|
| `/essay` | Immediate reflection & output |
| `/essay wait <time>` | Deliver at specified time |
| `/essay schedule <frequency>` | Set recurring delivery |
| `/essay test` | Test email configuration |

→ [Full README](EmailingEssay/README.md) / [Setup](EmailingEssay/SETUP.md) / [Concept](EmailingEssay/CONCEPT.md)

---

### VisualExpression

**Visual Expression System for AI Personas**

Provides emotion-based face switching to extend AI's expressive capabilities.

#### Key Features

- **20 Expression Variations**: 5 categories × 4 expressions
- **Nano Banana Pro Integration**: Meta-script for generating expression grids
- **Mobile-Friendly**: Display expressions on smartphones via artifacts
- **Fast Switching**: Instant changes via sed-based commands

→ [Full README](VisualExpression/README.md) / [Skill Spec](VisualExpression/skills/SKILL.md)

---

## License

**MIT License** - See [LICENSE](LICENSE) for details

### Patent (EpisodicRAG)

**Japanese Patent Application 2025-198943** - Hierarchical Memory & Digest Generation System

- Personal/Non-commercial use: Freely available under MIT License
- Commercial use: Please consult regarding patent rights before use

---

## Support

- **Issues**: [GitHub Issues](https://github.com/Bizuayeu/Plugins-Weave/issues)
- **Author**: [Weave](https://note.com/weave_ai)

---
**Plugins-Weave** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
