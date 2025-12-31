---
name: send_email
description: Email sending skill (Gmail SMTP + Yagmail)
---

# send_email - Email Sending Skill

Send emails via Gmail SMTP. Frugal design with yagmail as the only dependency.

## Table of Contents

- [Configuration](#configuration)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)

---

## Configuration

### Script Path

```
skills/send_email/scripts/weave_mail.py
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

**Use TodoWrite when sending from reflect skill**:

```
1. Prepare subject and body
2. Build send command
3. Execute send command
4. Verify send result
```

### Send Email

```bash
python weave_mail.py send "Subject" "Body"
python weave_mail.py test    # Send test email
```

### Wait (One-time Scheduling)

Schedule essay for a specific time. Runs in detached process.

```bash
python weave_mail.py wait "22:00" -t "theme"
python weave_mail.py wait "22:00" -t "theme" -c "context.txt"
python weave_mail.py wait "22:00" -t "theme" -f "context_list.txt" -l ja
python weave_mail.py wait "2026-01-05 22:00" -t "theme"
```

| Option | Description |
|--------|-------------|
| `-t, --theme` | Essay theme |
| `-c, --context` | Single context file |
| `-f, --file-list` | Multiple files (one path per line) |
| `-l, --lang` | Language: `ja`, `en`, or `auto` (default: auto) |

**Mechanism**:
- Spawns detached process (survives terminal close)
- Polls every 60 seconds (sleep-resilient)
- At target time, launches Claude Code with `/essay`

### Schedule (Recurring via OS Scheduler)

Register with Windows Task Scheduler or cron.

```bash
# Daily/Weekly/Monthly
python weave_mail.py schedule daily 22:00 -t "Daily reflection"
python weave_mail.py schedule weekly monday 09:00 -t "Weekly review"
python weave_mail.py schedule monthly 15 09:00 -t "Monthly review"
python weave_mail.py schedule monthly last-fri 17:00 -t "Month-end"

# Management
python weave_mail.py schedule list
python weave_mail.py schedule remove "Essay_Daily_reflection"
```

**Important**: Use absolute paths for `-c` and `-f` options (scheduled tasks run without working directory context).

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

**EmailingEssay** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
