#!/usr/bin/env python3
"""
Essay Mail - EmailingEssay email sending skill
===============================================

Usage:
  pip install yagmail
  python weave_mail.py test                                    # Test send
  python weave_mail.py send "Subject" "Body"                   # Custom send
  python weave_mail.py wait "22:00" -t "theme"                 # Today/tomorrow
  python weave_mail.py wait "2025-01-05 22:00" -t "theme"      # Specific date
  python weave_mail.py schedule daily 22:00 -t "theme"         # Daily schedule
  python weave_mail.py schedule weekly monday 09:00            # Weekly schedule
  python weave_mail.py schedule monthly 15 09:00 -t "theme"    # Monthly (day)
  python weave_mail.py schedule monthly 3rd-wed 09:00          # Monthly (Nth weekday)
  python weave_mail.py schedule monthly last-fri 17:00         # Monthly (last weekday)
  python weave_mail.py schedule monthly last 22:00             # Monthly (last day)
  python weave_mail.py schedule list                           # List schedules
  python weave_mail.py schedule remove "name"                  # Remove schedule

Environment variables:
  ESSAY_APP_PASSWORD    - Gmail app password (required)
  ESSAY_SENDER_EMAIL    - Sender email address (required)
  ESSAY_RECIPIENT_EMAIL - Recipient email address (required)
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime, timedelta

# Windows cp932 encoding workaround
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


# ============================================================================
# Persistent Directory (auto-update safe, outside plugin directory)
# ============================================================================

PERSISTENT_DIR_NAME = ".emailingessay"


def get_persistent_dir() -> str:
    """Get persistent directory for temporary files (creates if not exists)

    Returns:
        str: ~/.claude/plugins/.emailingessay/ path

    Note:
        This directory is outside the plugin directory, so it's not affected
        by Claude Code's auto-update mechanism.
    """
    home = os.path.expanduser("~")
    persistent_dir = os.path.join(home, ".claude", "plugins", PERSISTENT_DIR_NAME)
    os.makedirs(persistent_dir, exist_ok=True)
    return persistent_dir


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


def parse_target_time(time_str: str) -> datetime:
    """Parse time string and return target datetime

    Supported formats:
        HH:MM           - Today (or tomorrow if time has passed)
        YYYY-MM-DD HH:MM - Specific date and time
    """
    # Try YYYY-MM-DD HH:MM format first
    if " " in time_str and len(time_str) > 10:
        try:
            target = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            if target < datetime.now():
                raise ValueError(f"Target time {time_str} is in the past")
            return target
        except ValueError as e:
            if "is in the past" in str(e):
                raise
            pass  # Try HH:MM format

    # HH:MM format (today or tomorrow)
    target = datetime.strptime(time_str, "%H:%M").replace(
        year=datetime.now().year,
        month=datetime.now().month,
        day=datetime.now().day
    )
    # If target time has passed today, schedule for tomorrow
    if target < datetime.now():
        target += timedelta(days=1)
    return target


def wait_until(target: datetime):
    """Poll every minute until target time (sleep-resilient)"""
    while datetime.now() < target:
        remaining = (target - datetime.now()).total_seconds()
        # Show progress every 10 minutes
        if int(remaining) % 600 < 60:
            print(f"Waiting... {int(remaining // 60)} minutes remaining")
        time.sleep(60)  # Check every minute


def spawn_waiter(target_time: str, theme: str = "", context_file: str = "", file_list: str = ""):
    """Spawn a detached process that waits and executes essay

    Args:
        target_time: HH:MM or YYYY-MM-DD HH:MM
        theme: Essay theme (optional)
        context_file: Single context file path (optional)
        file_list: File containing list of context files (optional)
    """

    # Build the Claude command (escape quotes for embedding in script)
    claude_args = []
    if theme:
        theme_escaped = theme.replace("'", "\\'")
        claude_args.append(f"'{theme_escaped}'")
    if context_file:
        claude_args.append(f"-c '{context_file}'")
    if file_list:
        claude_args.append(f"-f '{file_list}'")
    claude_args_str = " ".join(claude_args) if claude_args else ""

    # Log file for debugging (in persistent directory)
    persistent_dir = get_persistent_dir()
    log_file = os.path.join(persistent_dir, "essay_wait.log")

    # Script to run in detached process
    script = f'''# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
import subprocess
import sys
import os

LOG_FILE = r"{log_file}"
TARGET_TIME = "{target_time}"
CLAUDE_ARGS = """{claude_args_str}"""

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write("[" + timestamp + "] " + str(msg) + "\\n")

try:
    log("Started. Target: " + TARGET_TIME)

    # Parse time - support both HH:MM and YYYY-MM-DD HH:MM
    time_str = TARGET_TIME
    if " " in time_str and len(time_str) > 10:
        target = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    else:
        target = datetime.strptime(time_str, "%H:%M").replace(
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day
        )
        if target < datetime.now():
            target += timedelta(days=1)

    log("Waiting until " + target.strftime("%Y-%m-%d %H:%M") + "...")

    # Poll every minute (sleep-resilient)
    while datetime.now() < target:
        time.sleep(60)

    log("Target time reached: " + datetime.now().strftime("%H:%M"))
    log("Launching Claude Code for essay...")

    # Execute Claude Code
    cmd = 'claude -p "/essay ' + CLAUDE_ARGS + '"'
    log("Command: " + cmd)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    log("Return code: " + str(result.returncode))
    if result.stdout:
        log("Stdout: " + result.stdout[:500])
    if result.stderr:
        log("Stderr: " + result.stderr[:500])
    log("Done.")

except Exception as e:
    log("ERROR: " + str(e))
'''

    # Write script to persistent directory and execute it
    script_file = os.path.join(persistent_dir, "essay_waiter_temp.py")

    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script)

    # Spawn detached process
    if sys.platform == "win32":
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008
        proc = subprocess.Popen(
            [sys.executable, script_file],
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    else:
        proc = subprocess.Popen(
            [sys.executable, script_file],
            start_new_session=True,
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    target = parse_target_time(target_time)
    print(f"Scheduled essay for {target.strftime('%Y-%m-%d %H:%M')}")
    print(f"Process ID: {proc.pid}")
    print("You can close this terminal. Essay will execute at the scheduled time.")
    if theme:
        print(f"Theme: {theme}")
    if context_file:
        print(f"Context: {context_file}")
    if file_list:
        print(f"File list: {file_list}")


# ============================================================================
# Schedule Functions (OS Scheduler Integration)
# ============================================================================

def get_schedules_file() -> str:
    """Get path to schedules.json in persistent directory"""
    return os.path.join(get_persistent_dir(), "schedules.json")


def get_default_context_file() -> str:
    """Get default path to daily_context.txt in persistent directory"""
    return os.path.join(get_persistent_dir(), "daily_context.txt")


def get_runners_dir() -> str:
    """Get runners directory for monthly schedule scripts"""
    runners_dir = os.path.join(get_persistent_dir(), "runners")
    os.makedirs(runners_dir, exist_ok=True)
    return runners_dir


WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
WEEKDAY_ABBRS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
WEEKDAY_NUMS = {"sunday": 1, "monday": 2, "tuesday": 3, "wednesday": 4,
                "thursday": 5, "friday": 6, "saturday": 7}
WEEK_ORDINALS = {"1st": 1, "2nd": 2, "3rd": 3, "4th": 4, "last": "LAST"}


def _get_schedules() -> dict:
    """Load schedules from JSON file"""
    schedules_file = get_schedules_file()
    if os.path.exists(schedules_file):
        with open(schedules_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"schedules": []}


def _save_schedules(data: dict):
    """Save schedules to JSON file"""
    with open(get_schedules_file(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _parse_monthly_day_spec(day_spec: str) -> tuple:
    """Parse monthly day specification

    Returns:
        (monthly_type, value1, value2) where:
        - "date": (day_num, None) - e.g., "15" -> (15, None)
        - "nth_weekday": (week_num, weekday) - e.g., "3rd-wed" -> (3, "wed")
        - "last_weekday": (None, weekday) - e.g., "last-fri" -> (None, "fri")
        - "last_day": (None, None) - e.g., "last" -> (None, None)
    """
    day_spec = day_spec.lower().strip()

    # Check for "last" (last day of month)
    if day_spec == "last":
        return ("last_day", None, None)

    # Check for numeric day (1-31)
    if day_spec.isdigit():
        day_num = int(day_spec)
        if 1 <= day_num <= 31:
            return ("date", day_num, None)
        raise ValueError(f"Day must be 1-31, got {day_num}")

    # Check for Nth-weekday pattern (e.g., "3rd-wed", "last-fri")
    if "-" in day_spec:
        parts = day_spec.split("-", 1)
        if len(parts) == 2:
            ordinal, weekday = parts

            # Validate weekday
            if weekday not in WEEKDAY_ABBRS:
                raise ValueError(f"Invalid weekday '{weekday}'. Use: {', '.join(WEEKDAY_ABBRS)}")

            # Check for "last-weekday"
            if ordinal == "last":
                return ("last_weekday", None, weekday)

            # Check for "Nth-weekday"
            if ordinal in WEEK_ORDINALS:
                week_num = WEEK_ORDINALS[ordinal]
                return ("nth_weekday", week_num, weekday)

            raise ValueError(f"Invalid ordinal '{ordinal}'. Use: 1st, 2nd, 3rd, 4th, last")

    raise ValueError(f"Invalid day_spec '{day_spec}'. Use: 1-31, Nth-day (e.g., 3rd-wed), last-day, or last")


def _build_claude_command(theme: str = "", context_file: str = "", file_list: str = "", lang: str = "") -> str:
    """Build the claude command string for scheduling"""
    args = []

    # Use escaped quotes for Windows Task Scheduler compatibility
    if sys.platform == "win32":
        q = '\\"'  # Escaped quote for Windows
    else:
        q = "'"    # Single quote for Unix

    if theme:
        args.append(f'{q}{theme}{q}')
    if context_file:
        args.append(f'-c {q}{context_file}{q}')
    if file_list:
        args.append(f'-f {q}{file_list}{q}')
    if lang:
        args.append(f'-l {lang}')
    args_str = " ".join(args)

    # Use full path for claude on Windows (Task Scheduler doesn't inherit PATH)
    # --dangerously-skip-permissions: Required for non-interactive scheduled execution
    if sys.platform == "win32":
        claude_path = os.path.expanduser("~/.local/bin/claude.exe")
        return f'"{claude_path}" --dangerously-skip-permissions -p "/essay {args_str}"'
    return f'claude --dangerously-skip-permissions -p "/essay {args_str}"'


def _generate_task_name(frequency: str, time_spec: str, theme: str) -> str:
    """Generate a unique task name"""
    base = theme if theme else f"{frequency}_{time_spec.replace(':', '')}"
    # Sanitize for task scheduler
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in base)
    return f"Essay_{safe_name}"


# Windows Task Scheduler functions
def _windows_create_task(name: str, command: str, frequency: str, time_spec: str,
                         weekday: str = "", day_spec: str = "", monthly_type: str = ""):
    """Create a Windows scheduled task using schtasks

    Args:
        name: Task name
        command: Command to execute
        frequency: daily, weekly, or monthly
        time_spec: HH:MM time
        weekday: Weekday for weekly schedules
        day_spec: Day specification for monthly (parsed)
        monthly_type: Type of monthly schedule (date, nth_weekday, last_weekday, last_day)
    """
    # Day abbreviation map for schtasks
    day_abbr_map = {"mon": "MON", "tue": "TUE", "wed": "WED",
                    "thu": "THU", "fri": "FRI", "sat": "SAT", "sun": "SUN"}
    day_map = {"monday": "MON", "tuesday": "TUE", "wednesday": "WED",
               "thursday": "THU", "friday": "FRI", "saturday": "SAT", "sunday": "SUN"}

    # Build schtasks command
    if frequency == "daily":
        schtasks_cmd = [
            "schtasks", "/create", "/tn", name,
            "/tr", command,
            "/sc", "daily",
            "/st", time_spec,
            "/f"  # Force overwrite
        ]
    elif frequency == "weekly":
        schtasks_cmd = [
            "schtasks", "/create", "/tn", name,
            "/tr", command,
            "/sc", "weekly",
            "/d", day_map.get(weekday.lower(), "MON"),
            "/st", time_spec,
            "/f"
        ]
    elif frequency == "monthly":
        if monthly_type == "date":
            # Specific day of month (e.g., 15th)
            parsed = _parse_monthly_day_spec(day_spec)
            day_num = parsed[1]
            schtasks_cmd = [
                "schtasks", "/create", "/tn", name,
                "/tr", command,
                "/sc", "monthly",
                "/d", str(day_num),
                "/st", time_spec,
                "/f"
            ]
        elif monthly_type == "nth_weekday":
            # Nth weekday of month (e.g., 3rd Wednesday)
            parsed = _parse_monthly_day_spec(day_spec)
            week_num = parsed[1]  # 1, 2, 3, 4
            weekday_abbr = day_abbr_map.get(parsed[2], "MON")
            # Windows uses FIRST, SECOND, THIRD, FOURTH for week ordinals
            week_ord_map = {1: "FIRST", 2: "SECOND", 3: "THIRD", 4: "FOURTH"}
            week_ordinal = week_ord_map.get(week_num, "FIRST")
            schtasks_cmd = [
                "schtasks", "/create", "/tn", name,
                "/tr", command,
                "/sc", "monthly",
                "/mo", week_ordinal,
                "/d", weekday_abbr,
                "/st", time_spec,
                "/f"
            ]
        elif monthly_type == "last_weekday":
            # Last weekday of month (e.g., last Friday)
            parsed = _parse_monthly_day_spec(day_spec)
            weekday_abbr = day_abbr_map.get(parsed[2], "MON")
            schtasks_cmd = [
                "schtasks", "/create", "/tn", name,
                "/tr", command,
                "/sc", "monthly",
                "/mo", "LAST",
                "/d", weekday_abbr,
                "/st", time_spec,
                "/f"
            ]
        elif monthly_type == "last_day":
            # Last day of month - use daily task with runner script
            # This will be handled by schedule_add() creating a runner
            raise ValueError("last_day requires runner script (handled by schedule_add)")
        else:
            raise ValueError(f"Unknown monthly_type: {monthly_type}")
    else:
        raise ValueError(f"Unknown frequency: {frequency}")

    result = subprocess.run(schtasks_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create task: {result.stderr}")
    return True


def _windows_delete_task(name: str):
    """Delete a Windows scheduled task"""
    result = subprocess.run(
        ["schtasks", "/delete", "/tn", name, "/f"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to delete task: {result.stderr}")
    return True


def _windows_list_tasks() -> list:
    """List Essay_ tasks from Windows Task Scheduler"""
    result = subprocess.run(
        ["schtasks", "/query", "/fo", "CSV"],
        capture_output=True, text=True
    )
    tasks = []
    for line in result.stdout.split("\n"):
        if "Essay_" in line:
            parts = line.strip().strip('"').split('","')
            if parts:
                # Remove leading backslash from task name
                task_name = parts[0].replace('"', '').lstrip('\\')
                tasks.append(task_name)
    return tasks


# Unix (Linux/Mac) cron functions
def _unix_add_cron(name: str, command: str, frequency: str, time_spec: str,
                   weekday: str = "", day_spec: str = "", monthly_type: str = ""):
    """Add a cron entry for Unix systems

    For monthly schedules, uses a runner script approach since cron
    doesn't natively support Nth weekday or last day of month.
    """
    hour, minute = time_spec.split(":")

    if frequency == "daily":
        cron_time = f"{minute} {hour} * * *"
        cron_command = command
    elif frequency == "weekly":
        day_num = WEEKDAYS.index(weekday.lower()) if weekday.lower() in WEEKDAYS else 0
        cron_time = f"{minute} {hour} * * {day_num}"
        cron_command = command
    elif frequency == "monthly":
        # All monthly schedules use runner script on Unix
        # The runner checks the condition and runs if appropriate
        runner_path = _create_monthly_runner_script(name, day_spec, monthly_type, command)
        # Daily cron entry to run the checker
        cron_time = f"{minute} {hour} * * *"
        cron_command = f"python {runner_path}"
    else:
        raise ValueError(f"Unknown frequency: {frequency}")

    cron_line = f"{cron_time} {cron_command} # {name}"

    # Get current crontab
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    current_cron = result.stdout if result.returncode == 0 else ""

    # Remove existing entry with same name if any
    lines = [l for l in current_cron.split("\n") if f"# {name}" not in l]
    lines.append(cron_line)

    # Install new crontab
    new_cron = "\n".join(lines).strip() + "\n"
    proc = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
    proc.communicate(new_cron)
    if proc.returncode != 0:
        raise RuntimeError("Failed to update crontab")
    return True


def _unix_remove_cron(name: str):
    """Remove a cron entry by name"""
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if result.returncode != 0:
        return True  # No crontab exists

    lines = [l for l in result.stdout.split("\n") if f"# {name}" not in l]
    new_cron = "\n".join(lines).strip() + "\n"

    proc = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
    proc.communicate(new_cron)
    return True


def _unix_list_cron() -> list:
    """List Essay_ entries from crontab"""
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if result.returncode != 0:
        return []

    tasks = []
    for line in result.stdout.split("\n"):
        if "# Essay_" in line:
            # Extract task name from comment
            parts = line.split("# ")
            if len(parts) > 1:
                tasks.append(parts[-1].strip())
    return tasks


# Monthly runner script functions (for last_day and Unix monthly schedules)
def _create_monthly_runner_script(name: str, day_spec: str, monthly_type: str,
                                   claude_command: str) -> str:
    """Create a runner script for monthly schedules

    This script is executed daily and checks if today matches the schedule condition.
    Used for:
    - last_day: Runs on the last day of each month
    - Unix monthly schedules (cron doesn't support Nth weekday natively)

    Returns:
        Path to the created runner script
    """
    # Ensure runners directory exists and get path
    runners_dir = get_runners_dir()
    runner_path = os.path.join(runners_dir, f"{name}_runner.py")

    # Build the condition check based on monthly_type
    if monthly_type == "last_day":
        condition_code = '''
def should_run_today():
    """Check if today is the last day of the month"""
    today = datetime.now()
    # Last day = tomorrow is day 1
    tomorrow = today + timedelta(days=1)
    return tomorrow.day == 1
'''
    elif monthly_type == "date":
        parsed = _parse_monthly_day_spec(day_spec)
        day_num = parsed[1]
        condition_code = f'''
def should_run_today():
    """Check if today is day {day_num} of the month"""
    return datetime.now().day == {day_num}
'''
    elif monthly_type == "nth_weekday":
        parsed = _parse_monthly_day_spec(day_spec)
        week_num = parsed[1]
        weekday = parsed[2]
        weekday_num = WEEKDAY_ABBRS.index(weekday)  # 0=mon, 6=sun
        condition_code = f'''
def should_run_today():
    """Check if today is the {week_num}th {weekday.upper()} of the month"""
    today = datetime.now()
    # Check if it's the right day of week (0=Monday in Python)
    if today.weekday() != {weekday_num}:
        return False
    # Count which occurrence this is
    day = today.day
    week_of_month = (day - 1) // 7 + 1
    return week_of_month == {week_num}
'''
    elif monthly_type == "last_weekday":
        parsed = _parse_monthly_day_spec(day_spec)
        weekday = parsed[2]
        weekday_num = WEEKDAY_ABBRS.index(weekday)
        condition_code = f'''
def should_run_today():
    """Check if today is the last {weekday.upper()} of the month"""
    today = datetime.now()
    # Check if it's the right day of week
    if today.weekday() != {weekday_num}:
        return False
    # Check if next week's same day is in a different month
    next_week = today + timedelta(days=7)
    return next_week.month != today.month
'''
    else:
        raise ValueError(f"Unknown monthly_type: {monthly_type}")

    # Escape the command for embedding in the script
    claude_cmd_escaped = claude_command.replace("\\", "\\\\").replace('"', '\\"')

    script_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monthly runner script for: {name}
Day spec: {day_spec}
Type: {monthly_type}

This script is executed daily and runs the essay command
only when the schedule condition is met.
"""

import subprocess
import sys
from datetime import datetime, timedelta

WEEKDAY_ABBRS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

{condition_code}

if __name__ == "__main__":
    if should_run_today():
        print(f"[{{datetime.now()}}] Running scheduled essay: {name}")
        cmd = "{claude_cmd_escaped}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {{result.stderr}}")
        else:
            print(f"Success: {{result.stdout[:200]}}")
    else:
        # Silent exit when condition not met
        pass
'''

    with open(runner_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    return runner_path


def _remove_monthly_runner_script(name: str):
    """Remove a monthly runner script"""
    runner_path = os.path.join(get_runners_dir(), f"{name}_runner.py")
    if os.path.exists(runner_path):
        os.remove(runner_path)
        return True
    return False


# Cross-platform schedule functions
def schedule_add(frequency: str, time_spec: str, weekday: str = "",
                 theme: str = "", context_file: str = "", file_list: str = "",
                 lang: str = "", name: str = "", day_spec: str = ""):
    """Add a recurring essay schedule

    Args:
        frequency: daily, weekly, or monthly
        time_spec: HH:MM format
        weekday: Day of week for weekly schedules (monday, tuesday, etc.)
        theme: Essay theme
        context_file: Path to context file
        file_list: Path to file containing list of context files
        lang: Language (ja, en, auto)
        name: Custom task name (auto-generated if empty)
        day_spec: Day specification for monthly (1-31, 3rd-wed, last-fri, last)
    """
    # Validate frequency
    if frequency not in ["daily", "weekly", "monthly"]:
        print(f"Error: frequency must be 'daily', 'weekly', or 'monthly', got '{frequency}'")
        sys.exit(1)

    # Validate weekday for weekly
    if frequency == "weekly" and weekday.lower() not in WEEKDAYS:
        print(f"Error: weekday must be one of {WEEKDAYS}")
        sys.exit(1)

    # Validate and parse day_spec for monthly
    monthly_type = ""
    if frequency == "monthly":
        if not day_spec:
            print("Error: monthly schedules require day_spec (e.g., 15, 3rd-wed, last-fri, last)")
            sys.exit(1)
        try:
            parsed = _parse_monthly_day_spec(day_spec)
            monthly_type = parsed[0]
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    # Validate time format
    try:
        datetime.strptime(time_spec, "%H:%M")
    except ValueError:
        print(f"Error: time must be in HH:MM format, got '{time_spec}'")
        sys.exit(1)

    # Generate task name
    if name:
        task_name = name
    elif frequency == "monthly":
        task_name = _generate_task_name(frequency, f"{day_spec}_{time_spec}", theme)
    else:
        task_name = _generate_task_name(frequency, time_spec, theme)

    command = _build_claude_command(theme, context_file, file_list, lang)

    # Create OS schedule
    try:
        if frequency == "monthly" and monthly_type == "last_day":
            # last_day requires runner script on all platforms
            runner_path = _create_monthly_runner_script(task_name, day_spec, monthly_type, command)
            # Create daily task that runs the runner
            if sys.platform == "win32":
                runner_command = f'python "{runner_path}"'
                _windows_create_task(task_name, runner_command, "daily", time_spec)
            else:
                _unix_add_cron(task_name, command, "monthly", time_spec,
                               day_spec=day_spec, monthly_type=monthly_type)
        elif sys.platform == "win32":
            _windows_create_task(task_name, command, frequency, time_spec,
                                 weekday=weekday, day_spec=day_spec, monthly_type=monthly_type)
        else:
            _unix_add_cron(task_name, command, frequency, time_spec,
                           weekday=weekday, day_spec=day_spec, monthly_type=monthly_type)
    except Exception as e:
        print(f"Error creating schedule: {e}")
        sys.exit(1)

    # Save to JSON backup
    data = _get_schedules()
    # Remove existing with same name
    data["schedules"] = [s for s in data["schedules"] if s.get("name") != task_name]
    schedule_entry = {
        "name": task_name,
        "frequency": frequency,
        "weekday": weekday if frequency == "weekly" else "",
        "time": time_spec,
        "theme": theme,
        "context": context_file,
        "file_list": file_list,
        "lang": lang,
        "created": datetime.now().isoformat()
    }
    # Add monthly-specific fields
    if frequency == "monthly":
        schedule_entry["day_spec"] = day_spec
        schedule_entry["monthly_type"] = monthly_type
    data["schedules"].append(schedule_entry)
    _save_schedules(data)

    # Print confirmation
    print(f"Schedule created: {task_name}")
    if frequency == "monthly":
        print(f"  Frequency: {frequency} ({day_spec})")
    elif frequency == "weekly":
        print(f"  Frequency: {frequency} ({weekday})")
    else:
        print(f"  Frequency: {frequency}")
    print(f"  Time: {time_spec}")
    if theme:
        print(f"  Theme: {theme}")
    if context_file:
        print(f"  Context: {context_file}")
    if file_list:
        print(f"  File list: {file_list}")
    if lang:
        print(f"  Language: {lang}")
    print()
    print("The essay will run automatically. Survives PC restart.")


def schedule_list():
    """List all essay schedules"""
    # Get from OS scheduler
    if sys.platform == "win32":
        os_tasks = _windows_list_tasks()
    else:
        os_tasks = _unix_list_cron()

    # Get from JSON backup
    data = _get_schedules()

    if not data["schedules"] and not os_tasks:
        print("No schedules found.")
        return

    print("Registered schedules:")
    print("-" * 60)

    for sched in data["schedules"]:
        status = "active" if sched["name"] in os_tasks else "orphaned"
        freq_str = sched["frequency"]
        if sched.get("day_spec"):
            freq_str += f" ({sched['day_spec']})"
        elif sched.get("weekday"):
            freq_str += f" ({sched['weekday']})"
        print(f"  {sched['name']}")
        print(f"    Frequency: {freq_str} at {sched['time']}")
        if sched.get("theme"):
            print(f"    Theme: {sched['theme']}")
        if sched.get("context"):
            print(f"    Context: {sched['context']}")
        if sched.get("lang"):
            print(f"    Language: {sched['lang']}")
        print(f"    Status: {status}")
        print()

    # Show OS-only tasks (not in JSON)
    json_names = {s["name"] for s in data["schedules"]}
    os_only = [t for t in os_tasks if t not in json_names]
    if os_only:
        print("OS-only tasks (not in backup):")
        for t in os_only:
            print(f"  {t}")


def schedule_remove(name: str):
    """Remove a scheduled essay"""
    # Remove from OS scheduler
    try:
        if sys.platform == "win32":
            _windows_delete_task(name)
        else:
            _unix_remove_cron(name)
    except Exception as e:
        print(f"Warning: Could not remove from OS scheduler: {e}")

    # Remove runner script if exists (for monthly schedules)
    _remove_monthly_runner_script(name)

    # Remove from JSON
    data = _get_schedules()
    original_count = len(data["schedules"])
    data["schedules"] = [s for s in data["schedules"] if s.get("name") != name]

    if len(data["schedules"]) < original_count:
        _save_schedules(data)
        print(f"Removed schedule: {name}")
    else:
        print(f"Schedule not found in backup: {name}")


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
    elif cmd == "wait":
        if len(sys.argv) < 3:
            print("Usage: python weave_mail.py wait \"TIME\" [OPTIONS]")
            print()
            print("Time formats:")
            print("  HH:MM             - Today (or tomorrow if time passed)")
            print("  YYYY-MM-DD HH:MM  - Specific date and time")
            print()
            print("Options:")
            print("  -t, --theme TEXT  - Essay theme")
            print("  -c, --context FILE - Context file")
            print("  -f, --file-list FILE - File containing list of context files")
            print()
            print("Examples:")
            print("  python weave_mail.py wait \"22:00\" -t \"Weekly review\"")
            print("  python weave_mail.py wait \"22:00\" -t \"Review\" -c \"GrandDigest.txt\"")
            print("  python weave_mail.py wait \"22:00\" -t \"Review\" -f \"context_list.txt\"")
            sys.exit(1)

        target_time = sys.argv[2]
        theme = ""
        context_file = ""
        file_list = ""

        # Parse options
        i = 3
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg in ("-t", "--theme") and i + 1 < len(sys.argv):
                theme = sys.argv[i + 1]
                i += 2
            elif arg in ("-c", "--context") and i + 1 < len(sys.argv):
                context_file = sys.argv[i + 1]
                i += 2
            elif arg in ("-f", "--file-list") and i + 1 < len(sys.argv):
                file_list = sys.argv[i + 1]
                i += 2
            else:
                # Legacy positional arguments for backward compatibility
                if not theme:
                    theme = arg
                elif not context_file:
                    context_file = arg
                i += 1

        spawn_waiter(target_time, theme, context_file, file_list)
    elif cmd == "schedule":
        if len(sys.argv) < 3:
            print("Usage: python weave_mail.py schedule <subcommand> [OPTIONS]")
            print()
            print("Subcommands:")
            print("  daily HH:MM          - Schedule daily essay")
            print("  weekly DAY HH:MM     - Schedule weekly essay (DAY: monday, tuesday, ...)")
            print("  monthly DAY HH:MM    - Schedule monthly essay")
            print("  list                 - List all schedules")
            print("  remove NAME          - Remove a schedule")
            print()
            print("Monthly DAY formats:")
            print("  1-31                 - Specific day (e.g., 15)")
            print("  Nth-weekday          - Nth occurrence (e.g., 3rd-wed, 1st-mon)")
            print("  last-weekday         - Last occurrence (e.g., last-fri)")
            print("  last                 - Last day of month")
            print()
            print("Options:")
            print("  -t, --theme TEXT     - Essay theme")
            print("  -c, --context FILE   - Context file")
            print("  -f, --file-list FILE - File list")
            print("  -l, --lang LANG      - Language: ja, en, auto (default: auto)")
            print("  --name NAME          - Custom task name")
            print()
            print("Examples:")
            print('  python weave_mail.py schedule daily 22:00 -t "Daily reflection"')
            print('  python weave_mail.py schedule weekly monday 09:00 -t "Weekly review"')
            print('  python weave_mail.py schedule monthly 15 09:00 -t "Monthly review"')
            print('  python weave_mail.py schedule monthly 3rd-wed 09:00 -t "Monthly meeting"')
            print('  python weave_mail.py schedule monthly last-fri 17:00 -t "Month-end wrap"')
            print('  python weave_mail.py schedule monthly last 22:00 -t "Month-end review"')
            print("  python weave_mail.py schedule list")
            print('  python weave_mail.py schedule remove "Essay_Monthly_review"')
            sys.exit(1)

        subcmd = sys.argv[2]

        if subcmd == "list":
            schedule_list()
        elif subcmd == "remove":
            if len(sys.argv) < 4:
                print("Usage: python weave_mail.py schedule remove NAME")
                sys.exit(1)
            schedule_remove(sys.argv[3])
        elif subcmd == "daily":
            if len(sys.argv) < 4:
                print("Usage: python weave_mail.py schedule daily HH:MM [OPTIONS]")
                sys.exit(1)
            time_spec = sys.argv[3]
            theme = ""
            context_file = ""
            file_list = ""
            lang = ""
            name = ""

            i = 4
            while i < len(sys.argv):
                arg = sys.argv[i]
                if arg in ("-t", "--theme") and i + 1 < len(sys.argv):
                    theme = sys.argv[i + 1]
                    i += 2
                elif arg in ("-c", "--context") and i + 1 < len(sys.argv):
                    context_file = sys.argv[i + 1]
                    i += 2
                elif arg in ("-f", "--file-list") and i + 1 < len(sys.argv):
                    file_list = sys.argv[i + 1]
                    i += 2
                elif arg in ("-l", "--lang") and i + 1 < len(sys.argv):
                    lang = sys.argv[i + 1]
                    i += 2
                elif arg == "--name" and i + 1 < len(sys.argv):
                    name = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1

            schedule_add("daily", time_spec, "", theme, context_file, file_list, lang, name)
        elif subcmd == "weekly":
            if len(sys.argv) < 5:
                print("Usage: python weave_mail.py schedule weekly DAY HH:MM [OPTIONS]")
                print("  DAY: monday, tuesday, wednesday, thursday, friday, saturday, sunday")
                sys.exit(1)
            weekday = sys.argv[3]
            time_spec = sys.argv[4]
            theme = ""
            context_file = ""
            file_list = ""
            lang = ""
            name = ""

            i = 5
            while i < len(sys.argv):
                arg = sys.argv[i]
                if arg in ("-t", "--theme") and i + 1 < len(sys.argv):
                    theme = sys.argv[i + 1]
                    i += 2
                elif arg in ("-c", "--context") and i + 1 < len(sys.argv):
                    context_file = sys.argv[i + 1]
                    i += 2
                elif arg in ("-f", "--file-list") and i + 1 < len(sys.argv):
                    file_list = sys.argv[i + 1]
                    i += 2
                elif arg in ("-l", "--lang") and i + 1 < len(sys.argv):
                    lang = sys.argv[i + 1]
                    i += 2
                elif arg == "--name" and i + 1 < len(sys.argv):
                    name = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1

            schedule_add("weekly", time_spec, weekday, theme, context_file, file_list, lang, name)
        elif subcmd == "monthly":
            if len(sys.argv) < 5:
                print("Usage: python weave_mail.py schedule monthly DAY_SPEC HH:MM [OPTIONS]")
                print("  DAY_SPEC formats:")
                print("    1-31        - Specific day (e.g., 15)")
                print("    Nth-weekday - Nth occurrence (e.g., 3rd-wed, 1st-mon)")
                print("    last-weekday- Last occurrence (e.g., last-fri)")
                print("    last        - Last day of month")
                sys.exit(1)
            day_spec = sys.argv[3]
            time_spec = sys.argv[4]
            theme = ""
            context_file = ""
            file_list = ""
            lang = ""
            name = ""

            i = 5
            while i < len(sys.argv):
                arg = sys.argv[i]
                if arg in ("-t", "--theme") and i + 1 < len(sys.argv):
                    theme = sys.argv[i + 1]
                    i += 2
                elif arg in ("-c", "--context") and i + 1 < len(sys.argv):
                    context_file = sys.argv[i + 1]
                    i += 2
                elif arg in ("-f", "--file-list") and i + 1 < len(sys.argv):
                    file_list = sys.argv[i + 1]
                    i += 2
                elif arg in ("-l", "--lang") and i + 1 < len(sys.argv):
                    lang = sys.argv[i + 1]
                    i += 2
                elif arg == "--name" and i + 1 < len(sys.argv):
                    name = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1

            schedule_add("monthly", time_spec, "", theme, context_file, file_list, lang, name, day_spec)
        else:
            print(f"Unknown schedule subcommand: {subcmd}")
            print("Use: daily, weekly, monthly, list, remove")
            sys.exit(1)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
