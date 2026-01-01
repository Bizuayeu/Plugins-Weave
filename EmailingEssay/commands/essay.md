---
name: essay
description: AI reflection and essay delivery
---

# /essay - AI Reflection and Essay Delivery

Enable your AI to reflect deeply and communicate proactively via email.
This is not just "sending mail" — it's crafting essays born from genuine reflection.

## Table of Contents

- [Architecture](#architecture)
- [Command Structure](#command-structure)
- [Wait Subcommand (One-time)](#wait-subcommand-one-time)
- [Schedule Subcommand (Recurring)](#schedule-subcommand-recurring)
- [Related Files](#related-files)

---

## Architecture

Execution flow for each mode:

| Mode | Execution Flow |
|------|----------------|
| Reflection | `/essay` → essay_writer.md → (reflect → send) |
| Wait | `/essay wait` → detached process → `/essay` → essay_writer.md |
| Schedule | `/essay schedule` → OS scheduler → `/essay` → essay_writer.md |
| Test | `/essay test` → skills/send_email (verify configuration) |

**Parameters passed to agent**:

| Parameter | Source |
|-----------|--------|
| `theme` | From `"theme"` argument or `-t` option |
| `context_files` | From `-c` or `-f` option |
| `language` | From `-l` option (default: auto) |

See `agents/essay_writer.md` for the reflection and writing process.
See `skills/send_email/SKILL.md` for email configuration and troubleshooting.

---

## Command Structure

```
/essay [SUBCOMMAND] [OPTIONS]
```

### Subcommands (must come first)

| Subcommand | Description |
|------------|-------------|
| *(none)* | Run reflection mode immediately |
| `wait` | Schedule one-time essay |
| `schedule` | Manage recurring schedules (daily/weekly/monthly) |
| `test` | Send test email to verify configuration |

### Options (for reflection mode)

| Option | Description |
|--------|-------------|
| `"theme"` | Specify reflection theme (quoted) |
| `-c file` | Single context file |
| `-f list` | Multiple files (one path per line) |
| `-l lang` | Language: `ja`, `en`, or `auto` (default: auto) |

### Options (for wait subcommand)

| Option | Description |
|--------|-------------|
| `TIME` | Target time: HH:MM or YYYY-MM-DD HH:MM (required, first argument) |
| `-t, --theme TEXT` | Essay theme |
| `-c, --context FILE` | Single context file |
| `-f, --file-list FILE` | Multiple files (one path per line) |
| `-l, --lang LANG` | Language: `ja`, `en`, `auto` (default: auto) |

### Options (for schedule subcommand)

| Option | Description |
|--------|-------------|
| `-t, --theme TEXT` | Essay theme |
| `-c, --context FILE` | Single context file |
| `-f, --file-list FILE` | Multiple files (one path per line) |
| `-l, --lang LANG` | Language: `ja`, `en`, `auto` (default: auto) |
| `--name NAME` | Custom task name (auto-generated if omitted) |

### Usage

```bash
# Free reflection
/essay

# Themed reflection
/essay "What I've been thinking about"

# With single context file
/essay -c memories.txt

# With multiple context files (use -f)
/essay -f context_list.txt

# Theme + context
/essay "Weekly review" -c digest.txt
/essay "Weekly review" -f context_list.txt

# Language option
/essay -l ja                              # Japanese
/essay -l en                              # English
/essay "今週の振り返り" -f context_list.txt -l ja  # Theme + files + Japanese
# Without -l option: auto (Claude chooses based on context)

# One-time schedule (detached process, sleep-resilient)
/essay wait 22:00 -t "Daily thoughts"
/essay wait 22:00 -t "Weekly review" -c GrandDigest.txt

# One-time schedule for specific date
/essay wait "2026-01-01 09:00" -t "New Year reflection"

# Recurring schedule (OS scheduler)
/essay schedule daily 22:00 -t "Daily reflection"
/essay schedule weekly monday 09:00 -t "Weekly review"
/essay schedule list
/essay schedule remove "Essay_Daily_reflection"

# Test configuration
/essay test
```

---

## Wait Subcommand (One-time)

Schedule essay execution at a specified time. The process runs in the background and is sleep-resilient.

See `skills/send_email/SKILL.md` → **Usage** section.

### Time Formats

| Format | Description |
|--------|-------------|
| `HH:MM` | Today (or tomorrow if time has passed) |
| `YYYY-MM-DD HH:MM` | Specific date and time |

### Examples

```bash
# Time only (today or tomorrow)
/essay wait 22:00 -t "theme"

# Specific date
/essay wait "2026-01-05 22:00" -t "theme"

# With context
/essay wait 22:00 -t "theme" -c context.txt
```

### Limitations

- If PC is sleeping at target time, essay executes when PC wakes up
- Cannot wake PC from sleep (OS-independent limitation)

---

## Schedule Subcommand (Recurring)

Register recurring essay schedules using OS scheduler (Windows Task Scheduler / cron).

See `skills/send_email/SKILL.md` → **Usage** section.

### Frequency

| Type | Format | Example |
|------|--------|---------|
| Daily | `daily HH:MM` | `daily 22:00` |
| Weekly | `weekly DAY HH:MM` | `weekly monday 09:00` |
| Monthly (date) | `monthly DAY HH:MM` | `monthly 15 09:00` |
| Monthly (Nth weekday) | `monthly Nth_DAY HH:MM` | `monthly 3rd_wed 09:00` |
| Monthly (last weekday) | `monthly last_DAY HH:MM` | `monthly last_fri 17:00` |
| Monthly (last day) | `monthly last_day HH:MM` | `monthly last_day 22:00` |

**Weekdays**: monday, tuesday, wednesday, thursday, friday, saturday, sunday

**Monthly DAY_SPEC formats**:
- `1-31` - Specific day of month (e.g., `15`)
- `Nth_weekday` - Nth occurrence of weekday (e.g., `3rd_wed`, `1st_mon`)
- `last_weekday` - Last occurrence of weekday (e.g., `last_fri`)
- `last_day` - Last day of month

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
/essay schedule monthly 3rd_wed 09:00 -t "Monthly meeting"

# Month-end wrap on the last Friday at 5pm
/essay schedule monthly last_fri 17:00 -t "Month-end wrap"

# Month-end review on the last day at 10pm
/essay schedule monthly last_day 22:00 -t "Month-end review"

# List all schedules
/essay schedule list

# Remove a schedule
/essay schedule remove "Essay_Daily_reflection"
```

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

### Advantages over Wait Subcommand

| Feature | wait | schedule |
|---------|------|----------|
| One-time | Yes | No |
| Recurring | No | Yes |
| Survives reboot | No* | Yes |
| OS managed | No | Yes |

*`wait` survives terminal close but not PC restart.

### Schedule Management Commands

```bash
# View all registered schedules
/essay schedule list

# Remove by task name
/essay schedule remove "Essay_Weekly_review"
```

---

## Related Files

| File | Role |
|------|------|
| `CLAUDE.md` | Plugin overview |
| `agents/essay_writer.md` | Agent specification |
| `skills/reflect/SKILL.md` | Reflection process |
| `skills/send_email/SKILL.md` | Email/scheduling implementation |

---

**EmailingEssay** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
