---
name: reflect
description: Deep reflection skill (ultrathink enabled)
---

# reflect - Reflection Skill

Read memory and context to reflect deeply.
Design principle: "Reflection first, sending second."

## Table of Contents

- [Invocation](#invocation)
- [Options](#options)
- [Reflection Process](#reflection-process)
- [Output](#output)
- [Essay Elements](#essay-elements)

---

## Invocation

| Source | Description |
|--------|-------------|
| `/reflect` | Direct skill call |
| `/essay` | Via command (→ reflect → send_email) |
| `essay_writer.md` | Via agent |

---
## Options

See `commands/essay.md` for full option details.

---

## Reflection Process

**Use TodoWrite to track progress**:

```
1. Load context files
2. Deep reflection (ultrathink)
3. Delivery decision
4. Write essay (if sending)
5. Deliver via send_email (if sending)
```

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

**EmailingEssay** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
