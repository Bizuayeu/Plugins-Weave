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

**If sending**: Write essay and send via `weave_mail.py send`
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
