#!/usr/bin/env python3
"""
Background backup trigger - checks if daily backup needed and triggers asynchronously
"""
import os, json, yaml, pathlib, subprocess, sys
from datetime import datetime, timedelta

CONFIG = yaml.safe_load(open("config.yaml","r"))
VAR_DIR = CONFIG["paths"]["var_dir"]
BACKUP_STATE_FILE = os.path.join(VAR_DIR, "last_backup.json")

def get_last_backup_info():
    """Get info about last successful backup"""
    try:
        if os.path.exists(BACKUP_STATE_FILE):
            with open(BACKUP_STATE_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return None

def should_trigger_backup():
    """Check if we need to trigger a backup today"""
    last_backup = get_last_backup_info()

    if not last_backup:
        return True  # No backup record, trigger one

    # Parse last backup timestamp
    try:
        last_backup_date = datetime.fromisoformat(last_backup["timestamp"].replace("Z", "+00:00"))
        today = datetime.utcnow().date()
        last_backup_day = last_backup_date.date()

        # If last backup was not today, trigger new one
        return last_backup_day < today
    except Exception:
        return True  # If we can't parse, assume we need backup

def trigger_background_backup():
    """Trigger backup in background without blocking"""
    try:
        # Use subprocess.Popen with detached process
        # Redirect output to backup log file
        log_file = os.path.join(CONFIG["paths"]["logs_dir"], "backup_async.log")

        with open(log_file, "a") as f:
            # Start backup process in background, completely detached
            subprocess.Popen(
                ["python3", "scripts/export_backup.py"],
                stdout=f,
                stderr=f,
                start_new_session=True,  # Detach from parent process
                cwd=os.getcwd()
            )
        return True
    except Exception as e:
        print(f"Warning: Failed to trigger background backup: {e}", file=sys.stderr)
        return False

def check_and_trigger():
    """Main function: check if backup needed and trigger if so"""
    pathlib.Path(VAR_DIR).mkdir(parents=True, exist_ok=True)

    if should_trigger_backup():
        # Don't block - just trigger and return immediately
        trigger_background_backup()
        # Don't wait for completion, return immediately

def mark_backup_complete():
    """Called by export_backup.py to mark backup as complete"""
    pathlib.Path(VAR_DIR).mkdir(parents=True, exist_ok=True)
    state = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "complete"
    }
    with open(BACKUP_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

if __name__ == "__main__":
    # Can be called directly for manual trigger
    check_and_trigger()
