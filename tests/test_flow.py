import os
import shutil
import tempfile
import subprocess


def run(cmd, cwd):
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr)
    r.check_returncode()


def test_init_ingest_search_backup_restore(tmp_path):
    # Copy the repo into a temp dir to avoid touching dev files
    src = os.getcwd()
    dst = tmp_path / "repo"
    shutil.copytree(src, dst)
    cwd = str(dst)

    # Create a minimal config pointing to local paths
    cfg = dst / "config.yaml"
    cfg.write_text(
        """
project: ai-brain
paths:
  notes_dir: ./notes
  db_path: ./db/brain.sqlite
  logs_dir: ./logs
  var_dir: ./var
  backups_dir: ./backups
embeddings:
  enabled: false
logging:
  level: INFO
backup:
  keep_days: 1
"""
    )

    # Ensure notes exist
    notes_dir = dst / "notes"
    notes_dir.mkdir(exist_ok=True)
    sample = notes_dir / "sample.md"
    sample.write_text(
        """---\ntitle: Sample\ndomain: work\nvisibility: public\ntype: note\nstatus: inbox\ntags: [test]\n---\nThis is a sample note."""
    )

    # Run init
    run("python3 scripts/init_db.py", cwd)
    # Run ingest
    run("python3 scripts/ingest.py", cwd)
    # Run search (should return at least one line)
    run("python3 scripts/search.py --q sample", cwd)
    # Run backup
    run("python3 scripts/export_backup.py", cwd)
    # Verify backup (may exit non-zero if no backups)
    run("python3 scripts/verify_backup.py", cwd)
    # Dry-run restore
    backups = list((dst / "backups").glob("brain-*.tgz"))
    assert backups, "No backups created"
    run(f"python3 scripts/restore_backup.py --file {backups[-1]}", cwd)
    # Run health check
    run("python3 scripts/reindex_fts.py", cwd)
    # Verify health.json exists and is valid
    health = dst / "var" / "health.json"
    assert health.exists(), "health.json not created"
    import json
    h = json.loads(health.read_text())
    assert h["ok"] is True, "health check failed"
    print("✅ Full flow test passed!")