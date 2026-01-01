# Setup Guide

Complete setup instructions for EmailingEssay plugin.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Installation](#installation)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

1. **Create a dedicated Gmail account for AI**
   - Use a separate account from your personal email

2. **Enable 2-Step Verification**
   - Go to [Google Account Management](https://myaccount.google.com/) → Security → 2-Step Verification

3. **Generate a 16-digit App Password**
   - Go to [Google Account Management](https://myaccount.google.com/) → Security → App Passwords
   - Select "Mail" → Save the generated 16-digit password

---

## Environment Variables

All variables are **mandatory**.

| Variable | Description |
|----------|-------------|
| `ESSAY_APP_PASSWORD` | Gmail app password (16 digits, no spaces) |
| `ESSAY_SENDER_EMAIL` | Sender email address (AI's Gmail) |
| `ESSAY_RECIPIENT_EMAIL` | Recipient email address (your email) |

### Security Notes

- App password is retrieved from environment variable (never hardcode)
- Use app password in Gmail 2FA environments
- Keep `ESSAY_RECIPIENT_EMAIL` set to your own email address

---

## Installation

### Windows (PowerShell)

```powershell
# Set environment variables (User scope)
[Environment]::SetEnvironmentVariable("ESSAY_APP_PASSWORD", "your-16-digit-password", "User")
[Environment]::SetEnvironmentVariable("ESSAY_SENDER_EMAIL", "ai@gmail.com", "User")
[Environment]::SetEnvironmentVariable("ESSAY_RECIPIENT_EMAIL", "you@example.com", "User")

# Restart PowerShell to apply changes
```

### Linux/macOS

Add to `~/.bashrc` or `~/.zshrc`:

```bash
export ESSAY_APP_PASSWORD="your-16-digit-password"
export ESSAY_SENDER_EMAIL="ai@gmail.com"
export ESSAY_RECIPIENT_EMAIL="you@example.com"
```

Then apply:

```bash
source ~/.bashrc  # or source ~/.zshrc
```

### Dependencies

```bash
pip install yagmail
```

---

## Verification

After setting environment variables, verify your configuration:

```bash
/essay test
```

This sends a test email to `ESSAY_RECIPIENT_EMAIL`.

---

## Troubleshooting

### Missing Environment Variables

**Error**:
```
Missing environment variables: ESSAY_APP_PASSWORD, ESSAY_SENDER_EMAIL, ESSAY_RECIPIENT_EMAIL
```

**Solution**:
1. Follow the [Installation](#installation) steps above
2. Restart your terminal/PowerShell
3. Verify with `echo $ESSAY_APP_PASSWORD` (Linux/Mac) or `$env:ESSAY_APP_PASSWORD` (Windows)

### Authentication Error

**Error**:
```
SMTPAuthenticationError: Username and Password not accepted
```

**Possible causes**:
1. App password is incorrect or contains spaces
2. 2-Step Verification is not enabled
3. App password was revoked

**Solution**:
1. Ensure 2-Step Verification is enabled on Google Account
2. Generate a new App Password
3. Update `ESSAY_APP_PASSWORD` environment variable
4. Restart terminal and retry

### Email Not Received

**Possible causes**:
1. Check spam/junk folder
2. `ESSAY_RECIPIENT_EMAIL` is incorrect
3. Gmail sending limits exceeded

**Solution**:
1. Verify recipient email is correct
2. Check `~/.claude/plugins/.emailingessay/essay_wait.log` for errors
3. Wait and retry (Gmail has daily sending limits)

---

**EmailingEssay** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
