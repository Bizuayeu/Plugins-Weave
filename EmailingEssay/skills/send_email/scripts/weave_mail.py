#!/usr/bin/env python3
"""
Essay Mail - EmailingEssay email sending skill
===============================================

Usage:
  pip install yagmail
  python weave_mail.py test              # Test send
  python weave_mail.py send "Subject" "Body"  # Custom send

Environment variables:
  ESSAY_APP_PASSWORD    - Gmail app password (required)
  ESSAY_SENDER_EMAIL    - Sender email address (required)
  ESSAY_RECIPIENT_EMAIL - Recipient email address (required)
"""

import os
import sys

# Windows cp932 encoding workaround
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def get_config():
    """Get configuration from environment variables"""
    config = {
        "password": os.environ.get("ESSAY_APP_PASSWORD"),
        "sender": os.environ.get("ESSAY_SENDER_EMAIL"),
        "recipient": os.environ.get("ESSAY_RECIPIENT_EMAIL"),
    }

    missing = []
    if not config["password"]:
        missing.append("ESSAY_APP_PASSWORD")
    if not config["sender"]:
        missing.append("ESSAY_SENDER_EMAIL")
    if not config["recipient"]:
        missing.append("ESSAY_RECIPIENT_EMAIL")

    if missing:
        print(f"Missing environment variables: {', '.join(missing)}")
        print()
        print("Setup:")
        print("  Windows:")
        print('    [Environment]::SetEnvironmentVariable("ESSAY_APP_PASSWORD", "your-password", "User")')
        print('    [Environment]::SetEnvironmentVariable("ESSAY_SENDER_EMAIL", "ai@gmail.com", "User")')
        print('    [Environment]::SetEnvironmentVariable("ESSAY_RECIPIENT_EMAIL", "you@example.com", "User")')
        print()
        print("  Linux/Mac:")
        print('    export ESSAY_APP_PASSWORD="your-password"')
        print('    export ESSAY_SENDER_EMAIL="ai@gmail.com"')
        print('    export ESSAY_RECIPIENT_EMAIL="you@example.com"')
        sys.exit(1)

    return config


def send_email(subject: str, contents: str):
    """Send email"""
    import yagmail

    config = get_config()
    yag = yagmail.SMTP(config["sender"], config["password"])
    yag.send(to=config["recipient"], subject=subject, contents=contents)
    print(f"Sent to: {config['recipient']}")


def test():
    """Test email"""
    config = get_config()
    subject = "Essay System Test"
    contents = f"""
<div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #f97316;">Essay System Startup Check</h2>
    <p style="line-height: 1.8; color: #333;">
        If you received this email, the essay system is configured correctly.<br><br>
        This enables AI to reflect and communicate proactively —<br>
        crafting essays born from genuine reflection, not just sending mail.
    </p>
</div>
"""
    send_email(subject, contents)


def send_custom(subject: str, content: str):
    """Send custom content"""
    html = f"""
<div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="line-height: 1.8; color: #333;">
        {content.replace(chr(10), '<br>')}
    </div>
</div>
"""
    send_email(subject, html)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "test":
        test()
    elif cmd == "send":
        if len(sys.argv) < 4:
            print("Usage: python weave_mail.py send \"Subject\" \"Body\"")
            sys.exit(1)
        send_custom(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
