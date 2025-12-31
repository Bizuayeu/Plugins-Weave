---
name: essay
description: AI reflection and essay delivery
---

# /essay - AI Reflection and Essay Delivery

Enable your AI to reflect deeply and communicate proactively via email.
This is not just "sending mail" — it's crafting essays born from genuine reflection.

## Basic Usage

### Reflection Mode

```ClaudeCLI
/essay                                    # Free reflection
/essay "Weekly thoughts"                  # Reflection with theme
/essay -c context.txt                     # With context file
/essay "theme" -c file1.txt -c file2.txt  # Theme + context
```

### Test Email

```ClaudeCLI
/essay test
```

Sends a test email to verify system configuration.

---

## Command Options

| Option | Description |
|--------|-------------|
| `"theme"` | Specify reflection theme (quoted) |
| `-c file` | Context file (multiple allowed) |
| `-f list` | File list (one path per line) |
| `-l lang` | Language: `ja`, `en`, or `auto` (default: auto) |
| `--wait TIME` | Schedule essay (HH:MM or YYYY-MM-DD HH:MM) |
| `schedule` | Recurring schedule (daily/weekly via OS scheduler) |
| `test` | Send test email |

### Examples

```bash
# Free reflection
/essay

# Themed reflection
/essay "What I've been thinking about"

# With context files
/essay -c memories.txt
/essay -c digest.txt -c notes.txt

# Theme + context
/essay "Weekly review" -c digest.txt -c recent.txt

# From file list
/essay -f context_list.txt

# Language option
/essay -l ja                              # Japanese
/essay -l en                              # English
/essay "今週の振り返り" -c digest.txt -l ja  # Theme + context + Japanese
# Without -l option: auto (Claude chooses based on context)

# Schedule for later (detached process, sleep-resilient)
/essay "Daily thoughts" --wait 22:00
/essay "Weekly review" -c GrandDigest.txt --wait 22:00

# Schedule for specific date
/essay "New Year reflection" --wait "2026-01-01 09:00"

# Recurring schedule (OS scheduler)
/essay schedule daily 22:00 -t "Daily reflection"
/essay schedule weekly monday 09:00 -t "Weekly review"
/essay schedule list
/essay schedule remove "Essay_Daily_reflection"
```

---

## Reflection Mode Flow

### 1. Load Context

Read specified files. If none specified, look for common patterns:
- EpisodicRAG digest files
- Personal notes or journals
- Project documentation

### 2. Launch Agent

Load `agents/essay_writer.md` and start the reflection subprocess.

### 3. Deep Reflection (ultrathink)

Use extended thinking to contemplate:
- Insights emerging from context
- What needs to be communicated
- What should be expressed now

### 4. Send Decision

**CRITICAL**: This command often runs non-interactively (scheduled tasks).
**Do NOT ask for confirmation. Send automatically.**

**If sending**:
1. Write essay
2. IMMEDIATELY execute: `python weave_mail.py send "Subject" "Body"`
   - Do NOT ask "Would you like me to send?"
   - Just execute the send command directly

**If not sending**: Output "Nothing to share at this time"

---

## Test Subcommand

### Flow

1. Load `skills/send_email/SKILL.md`
2. Execute `scripts/weave_mail.py test`
3. Display send result

### Environment Setup

Set environment variables for email configuration:

| Variable | Description |
|----------|-------------|
| `ESSAY_SENDER_EMAIL` | Sender email address |
| `ESSAY_RECIPIENT_EMAIL` | Recipient email address |
| `ESSAY_APP_PASSWORD` | Gmail app password |

**Windows (PowerShell)**:
```powershell
[Environment]::SetEnvironmentVariable("ESSAY_APP_PASSWORD", "your-app-password", "User")
[Environment]::SetEnvironmentVariable("ESSAY_SENDER_EMAIL", "your-ai@gmail.com", "User")
[Environment]::SetEnvironmentVariable("ESSAY_RECIPIENT_EMAIL", "you@example.com", "User")
```

**Linux/macOS**:
```bash
export ESSAY_APP_PASSWORD="your-app-password"
export ESSAY_SENDER_EMAIL="your-ai@gmail.com"
export ESSAY_RECIPIENT_EMAIL="you@example.com"
```

---

## Wait Subcommand (--wait)

Schedule essay execution at a specified time. The process runs in the background and is sleep-resilient.

### Usage

```bash
# Time only (today or tomorrow)
/essay "theme" --wait 22:00

# Specific date
/essay "theme" --wait "2026-01-05 22:00"

# With context
/essay "theme" -c context.txt --wait 22:00
```

### Time Formats

| Format | Description |
|--------|-------------|
| `HH:MM` | Today (or tomorrow if time has passed) |
| `YYYY-MM-DD HH:MM` | Specific date and time |

### How It Works

1. Parse `--wait TIME` option
2. Spawn a detached Python process
3. Process polls every minute (sleep-resilient)
4. At target time, launches Claude Code with `/essay` command
5. Parent process exits immediately (non-blocking)

### Implementation

When `--wait` is detected, execute:

```bash
python weave_mail.py wait "HH:MM" "theme" "context_file"
```

This spawns a detached process that:
- Runs independently of the parent terminal
- Survives terminal close
- Polls every 60 seconds (handles PC sleep/wake correctly)
- Executes essay at or after the target time

### Limitations

- If PC is sleeping at target time, essay executes when PC wakes up
- Cannot wake PC from sleep (OS-independent limitation)

---

## Schedule Subcommand (Recurring)

Register recurring essay schedules using OS scheduler (Windows Task Scheduler / cron).

### Usage

```bash
# Daily schedule
/essay schedule daily HH:MM [OPTIONS]

# Weekly schedule
/essay schedule weekly DAY HH:MM [OPTIONS]

# Monthly schedule
/essay schedule monthly DAY_SPEC HH:MM [OPTIONS]

# Management
/essay schedule list
/essay schedule remove NAME
```

### Options

| Option | Description |
|--------|-------------|
| `-t, --theme TEXT` | Essay theme |
| `-c, --context FILE` | Context file |
| `-f, --file-list FILE` | File containing list of context files |
| `-l, --lang LANG` | Language: `ja`, `en`, `auto` (default: auto) |
| `--name NAME` | Custom task name (auto-generated if omitted) |

### Frequency

| Type | Format | Example |
|------|--------|---------|
| Daily | `daily HH:MM` | `daily 22:00` |
| Weekly | `weekly DAY HH:MM` | `weekly monday 09:00` |
| Monthly (date) | `monthly DAY HH:MM` | `monthly 15 09:00` |
| Monthly (Nth weekday) | `monthly Nth-DAY HH:MM` | `monthly 3rd-wed 09:00` |
| Monthly (last weekday) | `monthly last-DAY HH:MM` | `monthly last-fri 17:00` |
| Monthly (last day) | `monthly last HH:MM` | `monthly last 22:00` |

**Weekdays**: monday, tuesday, wednesday, thursday, friday, saturday, sunday

**Monthly DAY_SPEC formats**:
- `1-31` - Specific day of month (e.g., `15`)
- `Nth-weekday` - Nth occurrence of weekday (e.g., `3rd-wed`, `1st-mon`)
- `last-weekday` - Last occurrence of weekday (e.g., `last-fri`)
- `last` - Last day of month

**Week ordinals**: 1st, 2nd, 3rd, 4th, last
**Weekday abbreviations**: mon, tue, wed, thu, fri, sat, sun

### Examples

```bash
# Daily reflection at 10pm
/essay schedule daily 22:00 -t "Daily reflection"

# Daily reflection in Japanese
/essay schedule daily 22:00 -t "日次振り返り" -l ja

# Weekly review every Monday at 9am
/essay schedule weekly monday 09:00 -t "Weekly review" -c GrandDigest.txt

# Monthly review on the 15th at 9am
/essay schedule monthly 15 09:00 -t "Monthly review"

# Monthly meeting on the 3rd Wednesday at 9am
/essay schedule monthly 3rd-wed 09:00 -t "Monthly meeting"

# Month-end wrap on the last Friday at 5pm
/essay schedule monthly last-fri 17:00 -t "Month-end wrap"

# Month-end review on the last day at 10pm
/essay schedule monthly last 22:00 -t "Month-end review"

# List all schedules
/essay schedule list

# Remove a schedule
/essay schedule remove "Essay_Daily_reflection"
```

### How It Works

1. Parse schedule command and options
2. Register with OS scheduler:
   - **Windows**: `schtasks /create /tn "Essay_..." /sc daily|weekly|monthly ...`
   - **Linux/Mac**: crontab entry with `# Essay_...` comment
3. Save backup to `schedules.json`
4. At scheduled time, OS launches `claude -p "/essay ..."`

**Monthly schedule notes**:
- On Windows, most monthly patterns use native Task Scheduler features
- For `last` (last day of month), a runner script is used that checks daily
- On Linux/Mac, all monthly schedules use a runner script approach
- If the specified day doesn't exist (e.g., 31st in February), that month is skipped

### Important: Use Absolute Paths

**OS schedulers run without a working directory context.** All file paths must be absolute:

```bash
# WRONG - relative paths won't work
/essay schedule daily 22:00 -f "context_list.txt"
/essay schedule daily 22:00 -c "GrandDigest.txt"

# CORRECT - use absolute paths
/essay schedule daily 22:00 -f "C:/Users/you/path/to/context_list.txt"
/essay schedule daily 22:00 -c "C:/Users/you/path/to/GrandDigest.txt"
```

File list contents must also use absolute paths:
```
# context_list.txt - use absolute paths
C:/Users/you/path/to/file1.txt
C:/Users/you/path/to/file2.txt
```

### Advantages over --wait

| Feature | --wait | schedule |
|---------|--------|----------|
| One-time | Yes | No |
| Recurring | No | Yes |
| Survives reboot | No* | Yes |
| OS managed | No | Yes |

*`--wait` survives terminal close but not PC restart.

### Management Commands

```bash
# View all registered schedules
/essay schedule list

# Remove by task name
/essay schedule remove "Essay_Weekly_review"
```

---

## Design Principles

- **Reflection first, sending second**: Email is the result, not the goal
- **Not sending is valid**: "Nothing to share" is a legitimate conclusion
- **Deep thinking**: Use ultrathink for genuine contemplation

---

## Related Files

| File | Role |
|------|------|
| `agents/essay_writer.md` | Reflection and writing agent |
| `skills/reflect/SKILL.md` | Reflection skill definition |
| `skills/send_email/SKILL.md` | Email sending skill |
| `skills/send_email/scripts/weave_mail.py` | SMTP operations |

---

**EmailingEssay** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
