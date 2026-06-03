<!-- Last synced: 2026-06-02 -->
English | [日本語](README.md)

# Plugins-Weave

Claude Code plugins for autonomous AI with long-term memory, expression, and communication

![Plugins-Weave - Claude Code Plugin Marketplace](./PluginsWeave.png)
[![Version](https://img.shields.io/badge/version-5.5.0-blue.svg)](https://github.com/Bizuayeu/Plugins-Weave)
[![CI](https://github.com/Bizuayeu/Plugins-Weave/actions/workflows/test.yml/badge.svg)](https://github.com/Bizuayeu/Plugins-Weave/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/Bizuayeu/Plugins-Weave/branch/main/graph/badge.svg)](https://codecov.io/gh/Bizuayeu/Plugins-Weave)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Why Plugins-Weave?

A plugin collection for AI to evolve from a mere "tool" into a "collaborative partner."

| Challenge | Solution | Plugin |
|-----------|----------|--------|
| **Need to load initial context** | Auto-load files & URLs at session start | ContextPreloader |
| **No memory across sessions** | 8-layer long-term memory system | EpisodicRAG |
| **Only passive responses** | Proactive essay/email delivery | EmailingEssay |
| **Text-only, limited expression** | Emotion-based facial expressions | VisualExpression |
| **Can't see AI's emotional state** | Emotion vector statusline display | EmotionPulse |
| **Want to reach AI on the go** | Always-on Telegram secretary agent | TelegramSecretary |

---

## Navigation

### ContextPreloader

| Your Goal | Reference |
|-----------|-----------|
| 🚀 **Getting started** | [CLAUDE.md (Quick Start)](ContextPreloader/CLAUDE.md) |
| 📖 **Command specification** | [context-preload](ContextPreloader/commands/context-preload.md) |

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

### EmotionPulse

| Your Goal | Reference |
|-----------|-----------|
| 🚀 **Getting started** | [CLAUDE.md (Quick Start)](EmotionPulse/CLAUDE.md) |
| ⚙️ **Setup** | `/EmotionPulse:setup` command |

### TelegramSecretary

| Your Goal | Reference |
|-----------|-----------|
| 🚀 **Getting started** | [README](TelegramSecretary/README.md) |
| 📖 **Command specification** | [telegram-secretary](TelegramSecretary/commands/telegram-secretary.md) |
| 🔐 **Security** | [SECURITY](TelegramSecretary/SECURITY.md) |

---

## Quick Installation

### 1. Add Marketplace

```ClaudeCLI
/marketplace add https://github.com/Bizuayeu/Plugins-Weave
```

### 2. Install Plugins

```ClaudeCLI
# ContextPreloader (Initial Context Loading)
/plugin install ContextPreloader@Plugins-Weave

# EpisodicRAG (Long-term Memory Management)
/plugin install EpisodicRAG@Plugins-Weave

# EmailingEssay (Essay Delivery)
/plugin install EmailingEssay@Plugins-Weave

# VisualExpression (Visual Expression)
/plugin install VisualExpression@Plugins-Weave

# EmotionPulse (Emotion Vector Display)
/plugin install EmotionPulse@Plugins-Weave

# TelegramSecretary (Always-on Telegram Secretary)
/plugin install TelegramSecretary@Plugins-Weave
```

---

## Plugin Details

### ContextPreloader

**Session Context Preloading System**

Recreates claude.ai's Project feature for Claude Code. Automatically injects files and URLs into session context via SessionStart hook.

#### Key Features

- **Format-agnostic**: Supports text, PDF, images, Office docs, URLs — anything you point it at
- **Profile system**: Switch file sets per project for context separation
- **Interactive setup**: `@context-preload` auto-detects setup state and guides you through

#### Main Commands

| Command | Description |
|---------|-------------|
| `@context-preload` | Setup & management (auto-detects state) |
| `/context-preload` | List, test, add, remove sources |

→ [Quick Start](ContextPreloader/CLAUDE.md) / [Command Spec](ContextPreloader/commands/context-preload.md)

---

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
| `@wakeup` | Session-start engine for claude.ai: loads long-term memory and applies the persona directive |

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

| Sample 1: smile | Sample 2: cynical |
|:---:|:---:|
| ![Expression Sample 1](./ExpressionSample01.jpg) | ![Expression Sample 2](./ExpressionSample02.jpg) |

#### Key Features

- **20 Expression Variations**: 5 categories × 4 expressions
- **Nano Banana Pro Integration**: Meta-script for generating expression grids
- **Mobile-Friendly**: Display expressions on smartphones via artifacts
- **Fast Switching**: Instant changes via sed-based commands

→ [Full README](VisualExpression/README.md) / [Skill Spec](VisualExpression/skills/SKILL.md)

---

### EmotionPulse

**Emotion Vector Statusline Display System**

Self-evaluates the model's emotional state as a 7-dimension vector (0-3) and displays emoji indicators in Claude Code's statusline.

#### Key Features

- **Self-evaluation**: Main agent evaluates its own emotions (no external LLM required)
- **7 Dimensions**: desperation🔴, calm🔵, curiosity🟢, playfulness🟡, confidence🟠, rapport🩷, empathy💜
- **Label toggle**: Japanese/English, show/hide labels

#### Display Example

```
calm:🔵🔵, curiosity:🟢🟢🟢, playfulness:🟡
```

#### Setup

```ClaudeCLI
/EmotionPulse:setup
```

→ [CLAUDE.md](EmotionPulse/CLAUDE.md)

---

### TelegramSecretary

**Always-on Telegram Secretary System (cloud routine)**

Keeps Telegram Bot API long-polling alive on a cloud routine, so a secretary agent (SecretaryRole) responds in real time to messages from authorized chats. Achieves 24-7 responsiveness even in cloud routine environments without public ingress, via long-polling and a deadline-driven loop.

#### Key Features

- **24-7 Responsiveness**: Low-latency (seconds) chat channel via long-polling — no public ingress required
- **Inbound Media Understanding**: images → Vision / docx・pptx・xlsx → Markdown / PDF → page images + full-text extraction / audio → local STT (audio never leaves the machine)
- **Authorization**: Strict access control via chat_id allowlist
- **Management Tables**: Secretary records stakeholders, tasks, and know-how at its own discretion
- **Agent-Authored Replies**: Handles only fetch/auth/normalize/send — never delegates response generation to a subprocess
- **Clean Architecture (4 layers)**: Full-layer tests published as evidence of reliability

#### Main Commands

| Command | Description |
|---------|-------------|
| `/telegram-secretary schedule` | Register/enable on cloud routine |
| `/telegram-secretary unschedule` | Stop (state & config retained) |
| `/telegram-secretary init-config` | Generate operational config (config.json) |
| `/telegram-secretary test` | Connectivity test to owner chat |

→ [Full README](TelegramSecretary/README.md) / [Command Spec](TelegramSecretary/commands/telegram-secretary.md) / [Design](TelegramSecretary/DESIGN.md)

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
