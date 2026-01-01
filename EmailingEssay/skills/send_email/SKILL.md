---
name: send_email
description: Email sending skill (Gmail SMTP + Yagmail)
---

# send_email - Email Sending Skill

Send emails via Gmail SMTP. Frugal design with yagmail as the only dependency.

## Table of Contents

- [Invocation](#invocation)
- [Implementation](#implementation)
- [File Locations](#file-locations)
- [Security Considerations](#security-considerations)

---

## Invocation

| Source | Operation |
|--------|-----------|
| `/send_email` | send |
| `essay_writer.md` | send |
| `/essay test` | test |
| `/essay wait` | wait |
| `/essay schedule` | schedule |

---

## Implementation

### Script Path

```
skills/send_email/scripts/main.py
```

### Dependencies

```
yagmail
```

### CLI Usage

| Operation | CLI | Description |
|-----------|-----|-------------|
| test | `python main.py test` | Send test email |
| send | `python main.py send "Subject" "Body"` | Send custom email |
| wait | `python main.py wait TIME [OPTIONS]` | One-time schedule |
| schedule | `python main.py schedule FREQ TIME [OPTIONS]` | Recurring schedule |

**Quick test**:

```bash
python main.py test
python main.py send "Test Subject" "Test Body"
```

For full options and examples, see `commands/essay.md` → **Command Structure** section.

---

## File Locations

| File | Location | Description |
|------|----------|-------------|
| `essay_wait.log` | `~/.claude/plugins/.emailingessay/` | Logs for wait/schedule operations |
| `schedules.json` | `~/.claude/plugins/.emailingessay/` | Backup of registered schedules |
| `active_waiters.json` | `~/.claude/plugins/.emailingessay/` | Active waiting process tracking |
| `runners/` | `~/.claude/plugins/.emailingessay/runners/` | Monthly schedule runner scripts |

Note: Persistent data directory is created automatically if not exists.

---

## Security Considerations

### Non-interactive Execution Flag

The `wait` and `schedule` features use `--dangerously-skip-permissions` when launching Claude Code.

**Why it's needed**:
- Scheduled/background tasks run without a terminal
- Claude cannot prompt for permission confirmations in headless mode

**What it does**:
- Bypasses interactive permission prompts for automated execution
- Only used for invoking `/essay` command (read + email operation)

**Safeguards**:
- No file modifications or system changes are made by the essay command
- Essay content is sent only to the configured `ESSAY_RECIPIENT_EMAIL`
- All operations are logged to `~/.claude/plugins/.emailingessay/essay_wait.log`

**Best practices**:
- Keep `ESSAY_RECIPIENT_EMAIL` set to your own email address
- Review logs periodically with `cat ~/.claude/plugins/.emailingessay/essay_wait.log`
- Audit registered tasks with `python main.py schedule list`

---

**EmailingEssay** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
