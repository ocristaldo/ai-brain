#!/usr/bin/env python3
import os, tarfile, hashlib, time, yaml, pathlib, sqlite3, json
from datetime import datetime

CONFIG = yaml.safe_load(open("config.yaml","r"))
BACKUPS_DIR = CONFIG["paths"]["backups_dir"]
DB_PATH = CONFIG["paths"]["db_path"]

def sha256sum(path):
    h = hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def has_changes_since_last_backup():
    """Check if there have been any changes since the last backup"""
    try:
        con = sqlite3.connect(DB_PATH)
        # Get timestamp of last backup from change_log
        cur = con.execute(
            "SELECT at FROM change_log WHERE action = 'backup' ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()
        if not row:
            # No previous backup, assume changes exist
            return True

        last_backup_time = row[0]

        # Check if there are any updates/creates after the last backup
        cur = con.execute(
            "SELECT COUNT(*) FROM change_log WHERE action IN ('update', 'create', 'retag', 'delete') AND at > ?",
            (last_backup_time,)
        )
        count = cur.fetchone()[0]
        con.close()
        return count > 0
    except Exception as e:
        print(f"Warning: Could not check for changes: {e}")
        return True  # Assume changes if we can't check

def main():
    # Check if there are changes before creating backup
    if not has_changes_since_last_backup():
        print("No changes detected since last backup. Skipping backup.")
        return

    pathlib.Path(BACKUPS_DIR).mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    out = os.path.join(BACKUPS_DIR, f"brain-{ts}.tgz")

    with tarfile.open(out, "w:gz") as tar:
        for p in ["db/brain.sqlite", "notes", "var"]:
            if os.path.exists(p):
                tar.add(p, arcname=p)

    digest = sha256sum(out)
    with open(out+".sha256","w") as f:
        f.write(f"{digest}  {os.path.basename(out)}\n")

    # Log to change_log
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "INSERT INTO change_log(at, actor, action, details_json) VALUES(?,?,?,?)",
            (
                datetime.utcnow().isoformat()+"Z",
                "backup",
                "backup",
                json.dumps({"file": out, "sha256": digest, "size_bytes": os.path.getsize(out)})
            )
        )
        con.commit()
        con.close()
    except Exception as e:
        print(f"Warning: Failed to log to change_log: {e}")

    # Cleanup old backups based on keep_days AND minimum backup count
    keep_days = CONFIG.get("backup", {}).get("keep_days", 15)
    min_backups = CONFIG.get("backup", {}).get("min_backups", 15)

    import glob
    all_backups = sorted(
        glob.glob(os.path.join(BACKUPS_DIR, "brain-*.tgz")),
        key=os.path.getmtime,
        reverse=True  # Newest first
    )

    if len(all_backups) > min_backups:
        cutoff_time = time.time() - (keep_days * 24 * 60 * 60)
        cleaned = 0

        # Keep at least min_backups, but can delete older ones beyond that
        for i, backup_file in enumerate(all_backups):
            # Skip the first min_backups (newest ones)
            if i < min_backups:
                continue

            # For backups beyond min_backups, delete if older than keep_days
            if os.path.getmtime(backup_file) < cutoff_time:
                try:
                    os.remove(backup_file)
                    # Also remove corresponding sha256 file
                    sha_file = backup_file + ".sha256"
                    if os.path.exists(sha_file):
                        os.remove(sha_file)
                    cleaned += 1
                    print(f"Cleaned old backup: {os.path.basename(backup_file)}")
                except Exception as e:
                    print(f"Warning: Failed to remove old backup {backup_file}: {e}")

        if cleaned > 0:
            print(f"Removed {cleaned} old backup(s) (older than {keep_days} days, keeping minimum {min_backups} backups)")

    print("Backup:", out)
    print("SHA256:", digest)

    # Mark backup as complete for daily tracking
    try:
        from backup_trigger import mark_backup_complete
        mark_backup_complete()
    except Exception:
        pass  # Don't fail backup if state update fails

if __name__ == "__main__":
    main()
