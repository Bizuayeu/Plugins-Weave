---
name: send_email
description: Email sending skill (Gmail SMTP + Yagmail)
---

# send_email - Email Sending Skill

Send emails via Gmail SMTP. Frugal design with yagmail as the only dependency.

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `ESSAY_APP_PASSWORD` | Gmail app password (required) |
| `ESSAY_SENDER_EMAIL` | Sender email address (required) |
| `ESSAY_RECIPIENT_EMAIL` | Recipient email address (required) |

---

## Usage

### Test Email

```bash
cd plugins-weave/EmailingEssay/skills/send_email/scripts
python weave_mail.py test
```

### Custom Email

```bash
python weave_mail.py send "Subject" "Body"
```

---

## Implementation

### Script Path

```
skills/send_email/scripts/weave_mail.py
```

### Dependencies

```
yagmail
```

### Security

- APP_PASSWORD retrieved from environment variable (no hardcoding)
- Use app password in Gmail 2FA environments

---

## Troubleshooting

### Missing Environment Variables

```
Missing environment variables: ESSAY_APP_PASSWORD, ESSAY_SENDER_EMAIL
```

**Solution**:
```powershell
# Windows
[Environment]::SetEnvironmentVariable("ESSAY_APP_PASSWORD", "your-password", "User")
[Environment]::SetEnvironmentVariable("ESSAY_SENDER_EMAIL", "ai@gmail.com", "User")
[Environment]::SetEnvironmentVariable("ESSAY_RECIPIENT_EMAIL", "you@example.com", "User")
# Restart PowerShell to apply
```

### Authentication Error

If "Less secure app access" is disabled in Gmail settings,
enable 2FA and generate an app password.

---

**EmailingEssay** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
