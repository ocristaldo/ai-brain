#!/usr/bin/env python3
import os, tarfile, argparse, yaml, sqlite3, json
from datetime import datetime

CONFIG = yaml.safe_load(open("config.yaml","r"))
BACKUPS_DIR = CONFIG["paths"]["backups_dir"]
DB_PATH = CONFIG["paths"]["db_path"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="path to backup .tgz")
    ap.add_argument("--confirm", action="store_true", help="apply changes")
    args = ap.parse_args()

    path = args.file
    if not os.path.exists(path):
        raise SystemExit(f"Backup not found: {path}")
    print(f"[DRY-RUN={not args.confirm}] Restore from: {path}")
    # Extract to temp dir first
    import tempfile, shutil, time

    tmpdir = tempfile.mkdtemp(prefix="brain_restore_")
    try:
        with tarfile.open(path, "r:gz") as tar:
            members = tar.getmembers()
            for member in members:
                print(" -", member.name)
            tar.extractall(path=tmpdir)

        if not args.confirm:
            print(f"Dry-run extraction completed to temporary directory: {tmpdir}")
            print("Run again with --confirm to apply the restore")
            # Log dry-run to change_log (use DB from tmpdir if extracted)
            db_in_tmp = os.path.join(tmpdir, "db", "brain.sqlite")
            if os.path.exists(db_in_tmp):
                try:
                    con = sqlite3.connect(db_in_tmp)
                    con.execute(
                        "INSERT INTO change_log(at, actor, action, details_json) VALUES(?,?,?,?)",
                        (datetime.utcnow().isoformat()+"Z", "restore", "restore_dryrun", json.dumps({"file": path}))
                    )
                    con.commit()
                    con.close()
                except Exception:
                    pass  # Dry-run, don't fail on log error
            return

        # On confirm: perform safe swap for targets (db, notes, var)
        ts = time.strftime("%Y%m%d-%H%M%S")
        bakdir = f"backups/restore_backup_bak_{ts}"
        os.makedirs(bakdir, exist_ok=True)

        # For each top-level item in tmpdir, move existing to bakdir and move new into place
        for name in os.listdir(tmpdir):
            src = os.path.join(tmpdir, name)
            dst = os.path.join(".", name)
            if os.path.exists(dst):
                print(f"Backing up existing {dst} -> {bakdir}")
                shutil.move(dst, os.path.join(bakdir, name))
            print(f"Applying restore: {src} -> {dst}")
            shutil.move(src, dst)

        # Log to change_log in the restored database
        try:
            con = sqlite3.connect(DB_PATH)
            con.execute(
                "INSERT INTO change_log(at, actor, action, details_json) VALUES(?,?,?,?)",
                (datetime.utcnow().isoformat()+"Z", "restore", "restore_apply", json.dumps({"file": path, "backup_dir": bakdir}))
            )
            con.commit()
            con.close()
        except Exception as e:
            print(f"Warning: Failed to log to change_log: {e}")

        print("Restore applied. Previous files moved to:", bakdir)
    finally:
        # tmpdir will be empty if moved; remove if it still exists
        try:
            if os.path.exists(tmpdir):
                shutil.rmtree(tmpdir)
        except Exception:
            pass

if __name__ == "__main__":
    main()
