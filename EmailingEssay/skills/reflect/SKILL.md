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
- [What the Plugin Retains](#what-the-plugin-retains)
- [Essay Elements](#essay-elements)

---

## Nature of This Skill

This is an **agent-driven skill** with no standalone implementation code.
The reflection process is executed by `agents/essay-writer.md`.

For execution flow diagram, see `agents/essay-writer.md` → **Execution Flow** section.

---

## Invocation

| Source | Agent | Description |
|--------|-------|-------------|
| `/essay` | essay-writer.md | Primary invocation |
| `/essay wait` | essay-writer.md | Scheduled (one-time) |
| `/essay schedule` | essay-writer.md | Scheduled (recurring) |

For CLI options, see `commands/essay.md` → **Command Structure** section.

---

## Reflection Process

### 1. Load Context

First, ingest any replies that have arrived: `python main.py replies fetch`. This is
plumbing — it moves replies from the inbox onto disk, so what has come back is at hand.
Best-effort: an IMAP, authentication or network failure stops the fetch, not the
reflection — go on to read and write regardless. What is made of them is the writer's;
see **What the Plugin Retains**.

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

### Mode Determination

| Condition | Mode |
|-----------|------|
| `--send` flag present | **Non-interactive** (send email) |
| No `--send` flag | **Interactive** (display in chat) |

### Interactive Mode (no `--send` flag)

Output: **Chat display only** (no email)

- **Delivering**: Write essay in chat
- **Not Delivering**: Display "After reflection, I have nothing particular to share."

### Non-interactive Mode (`--send` flag present)

Output: **Email** (user is not present)

- **Delivering**: Use `skills/send-email` to deliver. Write the essay to a file and send it
  with `python main.py send --subject-file … --body-file …` — the default route, since a body
  of more than one paragraph does not fit on a shell argument line. Do not write a throwaway
  sending script
- **Answering a reply**: if the essay takes up a reply, add
  `--in-reply-to '<its Message-ID>'` (the ID is in `essay_replies.jsonl`, and
  `python main.py replies list` prints it beside the subject). The mail then belongs to that
  reply's thread instead of arriving as an unrelated letter. Whether an essay is an answer is
  the writer's judgment; without the flag it stands on its own, which is the default
- **Not Delivering**: Exit silently. Nothing records the silence — scheduled runs invoke
  `claude -p` directly and never reach the wrapper that wrote `essay_wait.log`. A `--to-self`
  note, if one is written, lands in the ledger like any other send.

---

## What the Plugin Retains

The plugin keeps these records on its own account; what becomes of them in a reflection
stays with the writer.

- `essay_ledger.jsonl` — one line per sent essay; the bodies stay in `sent/` as `YYYYMMDD_HHMM.md`
- `essay_replies.jsonl` — replies that `python main.py replies fetch` has ingested
- `python main.py send "Subject" "Body" --to-self` sends to `ESSAY_SENDER_EMAIL` and lands in the
  same ledger; the `recipient` field tells a self-addressed note from an essay

Paths: `skills/send-email/SKILL.md` → **File Locations**.

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
