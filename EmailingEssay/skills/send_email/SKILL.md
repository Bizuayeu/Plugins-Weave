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
| test | `python main.py test` | Send test email to verify configuration |
| send | `python main.py send "Subject" "Body"` | Send email with custom subject and body |
| wait | `python main.py wait TIME [OPTIONS]` | Schedule one-time essay (detached process) |
| wait list | `python main.py wait list` | View all active waiting processes |
| schedule | `python main.py schedule FREQ TIME [OPTIONS]` | Register recurring schedule (OS scheduler) |
| list | `python main.py schedule list` | View all registered schedules |
| remove | `python main.py schedule remove "name"` | Remove a registered schedule |

**Options** (for wait/schedule):
- `-t, --theme TEXT` - Essay theme
- `-c, --context FILE` - Single context file
- `-f, --file-list FILE` - Multiple files (one path per line)
- `-l, --lang LANG` - Language: `ja`, `en`, `auto` (default: auto)
- `--name NAME` - Custom task name (schedule only)

**Examples**:

```bash
# Test
python main.py test

# Send
python main.py send "Subject" "Body"

# Wait (one-time)
python main.py wait "22:00" -t "theme"
python main.py wait "22:00" -t "theme" -c context.txt -l ja
python main.py wait "2025-01-05 22:00" -t "theme"
python main.py wait list                     # List active waiting processes

# Schedule (recurring)
python main.py schedule daily 22:00 -t "theme"
python main.py schedule weekly monday 09:00 -t "theme"
python main.py schedule monthly 15 09:00 -t "theme"
python main.py schedule monthly 2nd_mon 09:00
python main.py schedule monthly last_fri 17:00
python main.py schedule monthly last_day 22:00

# Management
python main.py schedule list
python main.py schedule remove "name"
```

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
