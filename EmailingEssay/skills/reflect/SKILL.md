---
name: reflect
description: Deep reflection skill (ultrathink enabled)
---

# reflect - Reflection Skill

Read memory and context to reflect deeply.
Design principle: "Reflection first, sending second."

## Input

### Options

| Option | Description |
|--------|-------------|
| `"theme"` | Reflection theme (quoted) |
| `-c file` | Single context file |
| `-f list` | Multiple files (one path per line) |
| `-l lang` | Language: `ja`, `en`, or `auto` (default: auto) |

### Examples

```bash
/essay                           # Free reflection
/essay "Weekly review"           # With theme
/essay -c digest.txt             # Single context file
/essay -f context_list.txt       # Multiple files via list
/essay "振り返り" -l ja           # Japanese output
```

---

## Reflection Process

**Use TodoWrite to track progress**:

```
1. Load context files
2. Deep thinking (ultrathink)
3. Make send decision
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

### 2. Deep Thinking (ultrathink)

Use extended thinking to contemplate:

- Insights emerging from context
- Unresolved questions
- What to communicate to the user
- What doesn't need to be said

### 3. Send Decision

**Send**: There's something worth sharing
**Don't send**: Nothing particular to share (this is valid)

---

## Output

### Interactive Mode (`/essay`)

Output: **Chat display only** (no email)

- **Sending**: Write essay in chat
- **Not Sending**: Display "After reflection, I have nothing particular to share."

### Non-interactive Mode (`wait`/`schedule`)

Output: **Email** (user is not present)

- **Sending**: Use `skills/send_email` to deliver
- **Not Sending**: Exit silently (logged to `essay_wait.log`)

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
