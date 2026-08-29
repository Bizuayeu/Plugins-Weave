# Setup Guide

Complete setup instructions for EmailingEssay plugin.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Installation](#installation)
- [Verification](#verification)
- [Scheduling Reply Ingestion](#scheduling-reply-ingestion)
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

## Scheduling Reply Ingestion

`/essay schedule` registers essay delivery only. To pull replies in without typing the
command, register `python main.py replies fetch` with the OS scheduler. `main.py` may be
invoked by absolute path from any working directory.

### Windows (Task Scheduler)

```powershell
schtasks /create /tn "EmailingEssay replies" /tr "python C:\path\to\EmailingEssay\skills\send-email\scripts\main.py replies fetch" /sc daily /st 07:00 /f
```

`/sc` and `/st` set the frequency and start time — `daily` at `07:00` here is only an
example. If the machine runs on battery, see
[Scheduled Run Not Firing on Battery](#scheduled-run-not-firing-on-battery-windows).

Scheduled tasks do not inherit a shell session's variables, but they do see the User-scope
variables set in [Installation](#installation) — no extra step is needed.

### Linux/macOS (cron)

```cron
# Ingest replies daily at 07:00 (time is an example)
0 7 * * * /usr/bin/python3 /path/to/EmailingEssay/skills/send-email/scripts/main.py replies fetch
```

cron does not read `~/.bashrc` or `~/.zshrc`, so the `export` lines from
[Installation](#installation) never reach it. Either declare the three variables at the top
of the crontab, or keep them in a `.env` file — which is read from the **current working
directory**, so the entry has to enter that directory first:

```cron
0 7 * * * cd /path/to/dir/with/.env && /usr/bin/python3 /path/to/EmailingEssay/skills/send-email/scripts/main.py replies fetch
```

A scheduled run's stdout is discarded, so the trace is
`~/.claude/plugins/.emailingessay/emailingessay.log`.

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
2. Look for the send in the ledger (`essay_ledger.jsonl` + `sent/`) — every send is recorded
   there, and each successful send also writes INFO lines to
   `~/.claude/plugins/.emailingessay/emailingessay.log`, one for the delivery and one for the
   ledger record
3. For a `wait` run, `essay_wait.log` also holds the return code; a registered `schedule` never
   writes it, so an old timestamp there is not evidence that nothing was sent
4. Wait and retry (Gmail has daily sending limits)

### IMAP Connection Fails (reply ingestion)

**Symptom**: `python main.py replies fetch` fails to connect to or log in to `imap.gmail.com`.

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

### A Reply Was Not Ingested

Connecting is one thing; being accepted is another. A candidate has to clear four gates — it
carries a `Message-ID`, its `In-Reply-To` matches an essay in the ledger, its `From` is
`ESSAY_RECIPIENT_EMAIL`, and the receiving MTA's own `Authentication-Results` shows `dkim` and
`spf` both `pass`. Missing any of them, the reply is skipped by design, not by failure.

The last gate is the one that surprises: forwarding, a mailing list, or a provider that rewrites
the message can break DKIM or SPF on a perfectly genuine reply. Each skip writes one INFO line
naming the gate that refused it to `~/.claude/plugins/.emailingessay/emailingessay.log`, so
start there rather than guessing. The line carries the Message-ID, the sender and the reason —
never the body.

### Scheduled Run Not Firing on Battery (Windows)

**Symptom**: The essay is automated via Windows Task Scheduler, but the daily run fails intermittently. Task Scheduler history shows `LastTaskResult = 0x800710E0` ("The operator or administrator has refused the request").

**Cause**: By default, Task Scheduler refuses to start a task while the machine is running on battery power.

**Solution**:
1. Open the task in Task Scheduler → **Conditions** tab
2. Uncheck **"Start the task only if the computer is on AC power"**
3. (Optional) **Settings** tab → enable **"Run task as soon as possible after a scheduled start is missed"** so a slot missed on battery still fires once back on AC

---

**EmailingEssay** | [GitHub](https://github.com/Bizuayeu/Plugins-Weave)
