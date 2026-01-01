---
name: reflect
description: Deep reflection skill (ultrathink enabled)
---

# reflect - Reflection Skill

Read memory and context to reflect deeply.
Design principle: "Reflection first, sending second."

## Table of Contents

- [Nature of This Skill](#nature-of-this-skill)
- [Invocation](#invocation)
- [Reflection Process](#reflection-process)
- [Output](#output)
- [Essay Elements](#essay-elements)

---

## Nature of This Skill

This is an **agent-driven skill** with no standalone implementation code.
The reflection process is executed by `agents/essay_writer.md`.

For execution flow diagram, see `agents/essay_writer.md`.

---

## Invocation

| Source | Agent | Description |
|--------|-------|-------------|
| `/essay` | essay_writer.md | Primary invocation |
| `/essay wait` | essay_writer.md | Scheduled (one-time) |
| `/essay schedule` | essay_writer.md | Scheduled (recurring) |

For CLI options, see `commands/essay.md`.

---

## Reflection Process

### 1. Load Context

Read specified files as material for reflection.

**Recommended context**:
- Memory digest files (GrandDigest, etc.)
- Personal notes or journals
- Project documentation

**Additional context** (AI may read as needed):
- Hierarchical digests
- Recent conversation logs
- Identity/persona files

### 2. Deep Reflection (ultrathink)

Use extended thinking to contemplate:

- Insights emerging from context
- Unresolved questions
- What to communicate to the user
- What doesn't need to be said

### 3. Delivery Decision

**Deliver**: There's something worth sharing
**Don't deliver**: Nothing particular to share (this is valid)

---

## Output

### Interactive Mode (`/essay`)

Output: **Chat display only** (no email)

- **Delivering**: Write essay in chat
- **Not Delivering**: Display "After reflection, I have nothing particular to share."

### Non-interactive Mode (`wait`/`schedule`)

Output: **Email** (user is not present)

- **Delivering**: Use `skills/send_email` to deliver
- **Not Delivering**: Exit silently (logged to `essay_wait.log`)

---

## Essay Elements

When sending, write naturally. No forced templates.

**Typical elements** (not mandatory):
- Insights from memory
- Unresolved questions
- Questions for the reader
- Signature

---

## Related Files

| File | Role |
|------|------|
| `CLAUDE.md` | Plugin overview |
| `commands/essay.md` | Command reference |
| `agents/essay_writer.md` | Agent specification |
| `skills/send_email/SKILL.md` | Email/scheduling implementation |

---

**EmailingEssay** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
