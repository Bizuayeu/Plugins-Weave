# EmailingEssay

AI-driven essay delivery — proactive communication born from genuine reflection.

## Table of Contents

- [Quick Start](#quick-start)
- [Documentation Map](#documentation-map)
- [Glossary](#glossary)
- [Quick Reference](#quick-reference)
- [See Also](#see-also)

---

## Quick Start

1. Set environment variables (see [SETUP.md](SETUP.md))
2. Run `/essay test` to verify configuration
3. Run `/essay` for immediate reflection
4. Run `/essay wait 22:00 -t "theme"` for scheduled delivery

---

## Documentation Map

| File | For | Content |
|------|-----|---------|
| [README.md](README.md) | Everyone | Quick start & glossary (this file) |
| [SETUP.md](SETUP.md) | First-time users | Environment setup |
| [CONCEPT.md](CONCEPT.md) | Curious minds | Philosophy & design rationale |
| [CLAUDE.md](CLAUDE.md) | AI/Architects | Architecture overview |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contributors | Development workflow |
| [commands/essay.md](commands/essay.md) | Users | Command reference |
| [agents/essay-writer.md](agents/essay-writer.md) | AI | Agent specification |
| [skills/reflect/SKILL.md](skills/reflect/SKILL.md) | AI | Reflection skill |
| [skills/send-email/SKILL.md](skills/send-email/SKILL.md) | AI | Email sending skill |

---

## Glossary

Key terms used throughout this plugin:

| Term | Definition |
|------|------------|
| **theme** | Essay topic or subject provided via `-t` or `--theme` option |
| **context_files** | Reference files for reflection, provided via `-f` or `--file` option |
| **mode** | Execution mode: `wait` (one-time), `schedule` (recurring), or `test` |
| **frequency** | Schedule interval: `daily`, `weekly`, `monthly`, `quarterly`, `half_yearly`, `yearly`, or `custom` |
| **reflection** | Deep thinking process before essay composition (uses UltraThink) |
| **delivery decision** | Conscious choice to send or not send (silence is meaningful) |
| **ledger** | Append-only record of every sent essay, keyed by `message_id` |
| **reply ingestion** | Pulling back the replies to sent essays, matched by `In-Reply-To` |

---

## Quick Reference

### Commands

| Command | Description |
|---------|-------------|
| `/essay` | Immediate reflection (output to chat) |
| `/essay wait <time>` | One-time scheduled delivery |
| `/essay schedule <frequency>` | Recurring scheduled delivery |
| `/essay schedule list` | List all registered schedules |
| `/essay schedule remove <name>` | Remove a registered schedule |
| `/essay test` | Test email configuration |

### Common Options

| Option | Description | Example |
|--------|-------------|---------|
| `-t`, `--theme` | Essay theme | `-t "Weekly reflection"` |
| `-f`, `--file` | Context file | `-f ./notes.md` |
| `-r`, `--recipient` | Email recipient | `-r user@example.com` |
| `--time` | Delivery time | `--time 09:00` |

### Ledger and Replies

Sends are recorded on their own. Replies are pulled back through the script CLI:

```bash
python main.py replies fetch    # Ingest replies to sent essays
python main.py replies list     # List ingested replies
```

A body of more than one paragraph is sent from a file, not from the command line:

```bash
python main.py send --subject-file s.txt --body-file b.txt
```

See [skills/send-email/SKILL.md](skills/send-email/SKILL.md) for the round trip
(**Correspondence Paths**) and file locations.

---

## See Also

- [CONCEPT.md](CONCEPT.md) — Why EmailingEssay? Design philosophy explained
- [commands/essay.md](commands/essay.md) — Full command reference with examples
- [SETUP.md](SETUP.md) — Installation and troubleshooting
- [CONTRIBUTING.md](CONTRIBUTING.md) — Development setup and guidelines
- [GitHub](https://github.com/Bizuayeu/Plugins-Weave) — Source repository

---

**EmailingEssay** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
