import os
import json
import shutil
import sqlite3
import subprocess


def run(cmd, cwd):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    return result.stdout


def bootstrap_repo(tmp_path):
    src = os.getcwd()
    dst = tmp_path / "repo"
    ignore = shutil.ignore_patterns("db", "logs", "var", "backups", ".venv", "__pycache__", "*.pyc")
    shutil.copytree(src, dst, ignore=ignore)

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
    notes_dir = dst / "notes"
    notes_dir.mkdir(exist_ok=True)
    return dst


def test_search_json_output(tmp_path):
    repo = bootstrap_repo(tmp_path)
    sample = repo / "notes" / "sample.md"
    sample.write_text(
        """---
title: Sample
domain: work
visibility: public
type: note
status: inbox
tags: [alpha, beta]
---
Sample body
"""
    )

    run("python3 scripts/init_db.py", str(repo))
    run("python3 scripts/ingest.py", str(repo))
    output = run("python3 scripts/search.py --q sample --format json --include-body", str(repo))
    data = json.loads(output)
    assert len(data) == 1
    item = data[0]
    assert item["title"] == "Sample"
    assert item["domain"] == "work"
    assert "body_md" in item and "Sample body" in item["body_md"]


def test_ingest_prune_missing(tmp_path):
    repo = bootstrap_repo(tmp_path)
    sample = repo / "notes" / "to_delete.md"
    sample.write_text(
        """---
title: To Delete
domain: personal
visibility: private
type: note
status: inbox
tags: []
---
Body
"""
    )

    run("python3 scripts/init_db.py", str(repo))
    run("python3 scripts/ingest.py", str(repo))
    os.remove(sample)
    run("python3 scripts/ingest.py --prune-missing --yes", str(repo))

    con = sqlite3.connect(os.path.join(repo, "db", "brain.sqlite"))
    cur = con.execute("SELECT COUNT(*) FROM item WHERE title = 'To Delete'")
    assert cur.fetchone()[0] == 0
    con.close()


def test_status_command(tmp_path):
    repo = bootstrap_repo(tmp_path)
    sample = repo / "notes" / "status.md"
    sample.write_text(
        """---
title: Status Note
domain: personal
visibility: private
type: note
status: inbox
tags: [status]
---
Body
"""
    )

    run("python3 scripts/init_db.py", str(repo))
    run("python3 scripts/ingest.py", str(repo))
    output = run("python3 scripts/status.py --json", str(repo))
    stats = json.loads(output)
    assert stats["items"] >= 1
    assert stats["tags"] >= 1
    assert stats["domains"].get("personal", 0) >= 1


def test_dedupe_command(tmp_path):
    repo = bootstrap_repo(tmp_path)
    sample = repo / "notes" / "dup.md"
    sample.write_text(
        """---
title: Duplicate Note
domain: work
visibility: private
type: note
status: inbox
tags: []
---
content
"""
    )

    run("python3 scripts/init_db.py", str(repo))
    run("python3 scripts/ingest.py", str(repo))

    db_path = repo / "db" / "brain.sqlite"
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute("DROP INDEX IF EXISTS idx_item_source_uri")
    row = con.execute("SELECT * FROM item WHERE title = 'Duplicate Note' LIMIT 1").fetchone()
    con.execute(
        "INSERT INTO item(id, title, body_md, domain, visibility, type, status, source_uri, meta_json, created_at, updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            "dup-test",
            row["title"],
            row["body_md"],
            row["domain"],
            row["visibility"],
            row["type"],
            row["status"],
            row["source_uri"],
            row["meta_json"],
            row["created_at"],
            row["updated_at"],
        ),
    )
    con.commit()
    con.close()

    run("python3 scripts/dedupe.py --apply --yes", str(repo))
    con = sqlite3.connect(db_path)
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_item_source_uri ON item(source_uri)")
    con.commit()
    cur = con.execute("SELECT COUNT(*) FROM item WHERE title = 'Duplicate Note'")
    assert cur.fetchone()[0] == 1
    con.close()


def test_reindex_restores_fts(tmp_path):
    repo = bootstrap_repo(tmp_path)
    note = repo / "notes" / "fts.md"
    note.write_text(
        """---
title: FTS Sample
domain: work
visibility: public
type: note
status: inbox
---
body
"""
    )
    run("python3 scripts/init_db.py", str(repo))
    run("python3 scripts/ingest.py", str(repo))

    db_path = repo / "db" / "brain.sqlite"
    con = sqlite3.connect(db_path)
    con.execute("DELETE FROM item_fts")
    con.commit()
    con.close()

    run("python3 scripts/reindex_fts.py", str(repo))
    con = sqlite3.connect(db_path)
    cur = con.execute("SELECT COUNT(*) FROM item")
    items = cur.fetchone()[0]
    cur = con.execute("SELECT COUNT(*) FROM item_fts")
    fts = cur.fetchone()[0]
    con.close()
    assert fts == items
