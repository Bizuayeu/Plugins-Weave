---
name: send_email
description: Email sending skill (Gmail SMTP + Yagmail)
---

# send_email - Email Sending Skill

Send emails via Gmail SMTP. Frugal design with yagmail as the only dependency.

## Table of Contents

- [Invocation](#invocation)
- [Options](#options-for-waitschedule)
- [Configuration](#configuration)
- [Usage](#usage)
- [File Locations](#file-locations)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

---

## Invocation

| Source | Operation | Input |
|--------|-----------|-------|
| `/send_email` | send | Subject, Body |
| `essay_writer.md` | send | Subject, Body |
| `/essay test` | test | (none) |
| `/essay wait` | wait | theme, context, lang |
| `/essay schedule` | schedule | theme, context, lang |

---

## Options (for wait/schedule)

See `commands/essay.md` → **Command Structure** section.

---

## Configuration

### Prerequisites

1. **AI専用Gmailアカウントを作成**
   - 個人アカウントとは別に、AI専用のGmailアドレスを取得

2. **二段階認証を有効化**
   - [Googleアカウント管理](https://myaccount.google.com/) → セキュリティ → 2段階認証プロセス

3. **16桁のアプリパスワードを取得**
   - [Googleアカウント管理](https://myaccount.google.com/) → セキュリティ → アプリパスワード
   - 「メール」を選択 → 生成された16桁のパスワードを保存

### Script Path

```
skills/send_email/scripts/main.py
```

### Dependencies

```
yagmail
```

### Environment Variables (all mandatory)

| Variable | Description |
|----------|-------------|
| `ESSAY_APP_PASSWORD` | Gmail app password |
| `ESSAY_SENDER_EMAIL` | Sender email address |
| `ESSAY_RECIPIENT_EMAIL` | Recipient email address |

### Security

- APP_PASSWORD retrieved from environment variable (no hardcoding)
- Use app password in Gmail 2FA environments

---

## Usage

### Send

Send email immediately with specified subject and body.

```bash
python main.py send "Subject" "Body"
```

### Test

Verify email configuration by sending a test email.

```bash
python main.py test
```

### Wait (One-time Scheduling)

Schedule essay for a specific time. Runs in detached process.

```bash
python main.py wait "22:00" -t "theme"
python main.py wait "22:00" -t "theme" -c "context.txt"
python main.py wait "22:00" -t "theme" -f "context_list.txt" -l ja
python main.py wait "2026-01-05 22:00" -t "theme"
```

**Mechanism**:
- Spawns detached process (survives terminal close)
- Polls every 60 seconds (sleep-resilient)
- At target time, launches Claude Code with `/essay`

### Schedule (Recurring via OS Scheduler)

Register with Windows Task Scheduler or cron.

```bash
# Examples (see commands/essay.md for full format reference)
python main.py schedule daily 22:00 -t "Daily reflection"
python main.py schedule weekly monday 09:00 -t "Weekly review"
python main.py schedule monthly 15 09:00 -t "Monthly review"

# Management
python main.py schedule list
python main.py schedule remove "Essay_Daily_reflection"
```

**How It Works**:
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

**Important**: Use absolute paths for `-c` and `-f` options (scheduled tasks run without working directory context).

---

## File Locations

| File | Location | Description |
|------|----------|-------------|
| `essay_wait.log` | `~/.claude/plugins/.emailingessay/` | Logs for wait/schedule operations |
| `schedules.json` | `~/.claude/plugins/.emailingessay/` | Backup of registered schedules |
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

## Troubleshooting

### Missing Environment Variables

```
Missing environment variables: ESSAY_APP_PASSWORD, ESSAY_SENDER_EMAIL, ESSAY_RECIPIENT_EMAIL
```

**Solution**:
```powershell
# Windows
[Environment]::SetEnvironmentVariable("ESSAY_APP_PASSWORD", "your-password", "User")
[Environment]::SetEnvironmentVariable("ESSAY_SENDER_EMAIL", "ai@gmail.com", "User")
[Environment]::SetEnvironmentVariable("ESSAY_RECIPIENT_EMAIL", "you@example.com", "User")
# Restart PowerShell to apply
```

```bash
# Linux/macOS (.bashrc or .zshrc)
export ESSAY_APP_PASSWORD="your-app-password"
export ESSAY_SENDER_EMAIL="ai@gmail.com"
export ESSAY_RECIPIENT_EMAIL="you@example.com"
# Run: source ~/.bashrc (or restart terminal)
```

### Authentication Error

If "Less secure app access" is disabled in Gmail settings,
enable 2FA and generate an app password.

---

## Related Files

| File | Role |
|------|------|
| `CLAUDE.md` | Plugin overview |
| `commands/essay.md` | Command reference |
| `agents/essay_writer.md` | Agent specification |
| `skills/reflect/SKILL.md` | Reflection process |

---

**EmailingEssay** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
