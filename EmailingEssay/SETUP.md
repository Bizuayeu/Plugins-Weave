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

Reply ingestion (`python main.py replies fetch`) reads the same Gmail account over IMAP
(`imap.gmail.com`) with these same three variables. **No additional variable is required**,
and `imaplib` ships with Python, so no additional dependency is installed either.

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

### Development

```bash
pip install pytest  # For running tests
```

For full development setup, see `CONTRIBUTING.md` → **Development Setup** section.

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
```text
Missing environment variables: ESSAY_APP_PASSWORD, ESSAY_SENDER_EMAIL, ESSAY_RECIPIENT_EMAIL
```

**Solution**:
1. Follow the [Installation](#installation) steps above
2. Restart your terminal/PowerShell
3. Verify with `echo $ESSAY_APP_PASSWORD` (Linux/Mac) or `$env:ESSAY_APP_PASSWORD` (Windows)

### Authentication Error

**Error**:
```text
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
2. Look for the send in the ledger (`essay_ledger.jsonl` + `sent/`) — every send is recorded there
3. For a `wait` run, `essay_wait.log` also holds the return code; a registered `schedule` never
   writes it, so an old timestamp there is not evidence that nothing was sent
4. Wait and retry (Gmail has daily sending limits)

### IMAP Connection Fails (reply ingestion)

**Symptom**: `python main.py replies fetch` fails to connect to or log in to `imap.gmail.com`.

**Note**: this path has not yet been exercised against a live Gmail account. If it fails,
work through the causes below before suspecting the code.

**Possible causes**:
1. IMAP is disabled on the account (Gmail → Settings → Forwarding and POP/IMAP)
2. The app password was generated before IMAP was enabled, or has been revoked
3. `ESSAY_SENDER_EMAIL` names an account other than the one the essays were sent from

**Solution**:
1. Enable IMAP in Gmail settings, then retry
2. If sending (`/essay test`) works and only fetching fails, the credentials are good and
   the account setting is the suspect — regenerate the app password and update
   `ESSAY_APP_PASSWORD`
3. If neither works, both directions share the same credentials, so treat it as the
   [Authentication Error](#authentication-error) case above

Replies are matched by `In-Reply-To` against the ledger and by `From` against
`ESSAY_RECIPIENT_EMAIL`, so a reply sent from a different address is skipped by design,
not by failure.

### Scheduled Run Not Firing on Battery (Windows)

**Symptom**: The essay is automated via Windows Task Scheduler, but the daily run fails intermittently. Task Scheduler history shows `LastTaskResult = 0x800710E0` ("The operator or administrator has refused the request").

**Cause**: By default, Task Scheduler refuses to start a task while the machine is running on battery power.

**Solution**:
1. Open the task in Task Scheduler → **Conditions** tab
2. Uncheck **"Start the task only if the computer is on AC power"**
3. (Optional) **Settings** tab → enable **"Run task as soon as possible after a scheduled start is missed"** so a slot missed on battery still fires once back on AC

---

**EmailingEssay** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
