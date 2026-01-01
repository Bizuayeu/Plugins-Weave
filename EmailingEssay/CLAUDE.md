# EmailingEssay Plugin

AI が主体的な思索を行った結果を、メールで届けられるようになるプラグイン。

## Table of Contents

- [What is EmailingEssay?](#what-is-emailingessay)
- [Benefits](#benefits)
- [File Structure](#file-structure)
- [Architecture](#architecture)
- [Component Roles](#component-roles)
- [Execution Modes](#execution-modes)
- [Quick Start](#quick-start)
- [Configuration](#configuration)

---

## What is EmailingEssay?

AIが定期的に「振り返り」を行い、洞察があればメールで届ける仕組み。
単なるメール送信ではなく、**深い思考から生まれたエッセイ**を配信する。

---

## Benefits

- **Proactive communication**: AI が自発的に考え、伝える
- **Scheduled reflection**: 定期的なリフレクションをスケジュール可能
- **Thoughtful output**: 送らない判断も尊重（沈黙は有効な選択）

---

## File Structure

```
EmailingEssay/
├── CLAUDE.md                 # This file (plugin overview)
├── commands/
│   └── essay.md              # /essay command definition
├── agents/
│   └── essay_writer.md       # Reflection & writing agent
└── skills/
    ├── reflect/
    │   └── SKILL.md          # Reflection skill
    └── send_email/
        ├── SKILL.md          # Email sending skill
        └── scripts/          # Clean Architecture implementation
            ├── main.py       # Entry point
            ├── domain/       # Core entities (models.py)
            ├── usecases/     # Business logic (ports.py, schedule_essay.py, wait_essay.py)
            ├── adapters/     # Interface implementations
            │   ├── cli/      # CLI handlers & parser
            │   ├── mail/     # yagmail adapter
            │   ├── scheduler/ # cron/Task Scheduler adapters
            │   └── storage/  # JSON persistence
            ├── frameworks/   # External frameworks (templates)
            └── tests/        # Comprehensive test suite
```

The `scripts/` directory follows Clean Architecture (Domain → Use Cases → Adapters → Frameworks).

---

## Architecture

```
User → /essay command → essay_writer.md agent
                              ↓
                    reflect skill (ultrathink)
                              ↓
                    Delivery Decision
                              ↓
            ┌─────────────────┴─────────────────┐
            ↓                                   ↓
    Interactive Mode                   Non-interactive Mode
    (Chat output)                      (send_email skill)
```

See `skills/reflect/SKILL.md` for reflection process details.

---

## Component Roles

| Component | Role |
|-----------|------|
| `commands/essay.md` | User-facing command interface |
| `agents/essay_writer.md` | Orchestrates reflection → delivery flow |
| `skills/reflect/SKILL.md` | Deep reflection process definition |
| `skills/send_email/SKILL.md` | Email delivery and scheduling |

---

## Execution Modes

| Mode | Trigger | Output |
|------|---------|--------|
| Reflection | `/essay` | Chat display |
| Wait | `/essay wait` | Email (one-time) |
| Schedule | `/essay schedule` | Email (recurring) |
| Test | `/essay test` | Test email |

---

## Quick Start

```bash
# Immediate reflection (interactive)
/essay

# Themed reflection
/essay "Weekly review"

# One-time scheduled
/essay wait 22:00 -t "Daily thoughts"

# Recurring schedule
/essay schedule daily 22:00 -t "Daily reflection"

# Test email configuration
/essay test
```

---

## Configuration

Environment variables required for email delivery:

```
ESSAY_APP_PASSWORD      # Gmail app password
ESSAY_SENDER_EMAIL      # Sender email address
ESSAY_RECIPIENT_EMAIL   # Recipient email address
```

See `skills/send_email/SKILL.md` for setup details.

---

**EmailingEssay** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
