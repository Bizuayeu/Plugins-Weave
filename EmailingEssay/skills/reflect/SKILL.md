---
name: reflect
description: Deep reflection skill (ultrathink enabled)
---

# reflect - Reflection Skill

Read memory and context to reflect deeply.
Design principle: "Reflection first, sending second."

## Input

### Context Files (-c option)

Load user-specified files. Multiple files allowed.

```bash
-c digest.txt                    # Single file
-c digest.txt -c notes.txt       # Multiple files
-f context_list.txt              # Load from file list
```

### Theme (optional)

```bash
/essay "Weekly review"           # With theme
/essay                           # Free reflection
```

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

### When Sending

Write naturally as an essay. No forced templates.

**Typical elements** (not mandatory):
- Insights from memory
- Unresolved questions
- Questions for the reader
- Signature

### When Not Sending

```
After reflection, I have nothing particular to share at this time.
Until next time.
```

---

## Usage Example

```markdown
# Called from essay_writer.md

Load context files and reflect deeply using ultrathink.

Theme: {{theme}}
Context: {{context_files}}

If you have something to share after reflection, write an essay.
If nothing to share, return that message.
```

---

**EmailingEssay** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
