"""
Test facet validation and error handling
"""
import os
import pytest
import tempfile
import shutil
from pathlib import Path
import subprocess
import sqlite3


def run(cmd, cwd):
    """Helper to run commands"""
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return r


def test_facet_validation_invalid_domain(tmp_path):
    """Test that invalid domain values are rejected"""
    dst = tmp_path / "repo"
    shutil.copytree(os.getcwd(), dst)

    # Create note with invalid domain
    note = dst / "notes" / "invalid_domain.md"
    note.write_text("""---
title: Invalid Domain Test
domain: invalid_domain
visibility: private
type: note
status: inbox
tags: [test]
---
This should be rejected.
""")

    # Run ingest
    r = run("python3 scripts/ingest.py", str(dst))

    # Should skip the invalid note
    assert "skipped: 1" in r.stdout or "FACET_VALIDATION_FAIL" in r.stderr


def test_facet_validation_invalid_visibility(tmp_path):
    """Test that invalid visibility values are rejected"""
    dst = tmp_path / "repo"
    shutil.copytree(os.getcwd(), dst)

    note = dst / "notes" / "invalid_vis.md"
    note.write_text("""---
title: Invalid Visibility
domain: personal
visibility: confidential
type: note
status: inbox
---
Invalid visibility.
""")

    r = run("python3 scripts/ingest.py", str(dst))
    assert "skipped: 1" in r.stdout or "FACET_VALIDATION_FAIL" in r.stderr


def test_facet_validation_invalid_type(tmp_path):
    """Test that invalid type values are rejected"""
    dst = tmp_path / "repo"
    shutil.copytree(os.getcwd(), dst)

    note = dst / "notes" / "invalid_type.md"
    note.write_text("""---
title: Invalid Type
domain: work
visibility: private
type: unknown_type
status: inbox
---
Invalid type.
""")

    r = run("python3 scripts/ingest.py", str(dst))
    assert "skipped: 1" in r.stdout


def test_facet_validation_missing_required_field(tmp_path):
    """Test that missing required fields are rejected"""
    dst = tmp_path / "repo"
    shutil.copytree(os.getcwd(), dst)

    note = dst / "notes" / "missing_field.md"
    note.write_text("""---
title: Missing Field
domain: work
# Missing visibility!
type: note
status: inbox
---
Missing required field.
""")

    r = run("python3 scripts/ingest.py", str(dst))
    assert "skipped: 1" in r.stdout


def test_invalid_frontmatter_syntax(tmp_path):
    """Test that malformed YAML is handled"""
    dst = tmp_path / "repo"
    shutil.copytree(os.getcwd(), dst)

    note = dst / "notes" / "bad_yaml.md"
    note.write_text("""---
title: Bad YAML
domain work  # Missing colon!
visibility: private
type: note
---
Malformed frontmatter.
""")

    r = run("python3 scripts/ingest.py", str(dst))
    assert "skipped: 1" in r.stdout


def test_secret_items_not_embedded(tmp_path):
    """Test that visibility=secret items are not embedded"""
    dst = tmp_path / "repo"
    shutil.copytree(os.getcwd(), dst)

    # Create secret note
    note = dst / "notes" / "secret.md"
    note.write_text("""---
title: Secret Note
domain: personal
visibility: secret
type: note
status: inbox
---
This is secret content.
""")

    # Ingest
    run("python3 scripts/init_db.py", str(dst))
    run("python3 scripts/ingest.py", str(dst))

    # Run embeddings
    run("python3 scripts/embed.py", str(dst))

    # Check that secret item is not in embeddings table
    db_path = dst / "db" / "brain.sqlite"
    con = sqlite3.connect(db_path)
    cur = con.execute("SELECT id FROM item WHERE visibility = 'secret'")
    secret_id = cur.fetchone()[0]

    cur = con.execute("SELECT COUNT(*) FROM embedding WHERE item_id = ?", (secret_id,))
    count = cur.fetchone()[0]

    assert count == 0, "Secret items should not be embedded"


def test_update_vs_create_detection(tmp_path):
    """Test that updates are detected vs creates"""
    dst = tmp_path / "repo"
    shutil.copytree(os.getcwd(), dst)

    # Create note
    note = dst / "notes" / "update_test.md"
    note.write_text("""---
id: test-update-123
title: Original Title
domain: personal
visibility: private
type: note
status: inbox
---
Original content.
""")

    # First ingest (create)
    run("python3 scripts/init_db.py", str(dst))
    r1 = run("python3 scripts/ingest.py", str(dst))
    # Should have ingested the note (plus any example notes)
    assert "Ingested:" in r1.stdout and "skipped: 0" in r1.stdout

    # Update note
    note.write_text("""---
id: test-update-123
title: Updated Title
domain: personal
visibility: private
type: note
status: active
---
Updated content.
""")

    # Second ingest (update)
    r2 = run("python3 scripts/ingest.py", str(dst))
    assert "Ingested:" in r2.stdout

    # Check that there's still only one item
    db_path = dst / "db" / "brain.sqlite"
    con = sqlite3.connect(db_path)
    cur = con.execute("SELECT COUNT(*) FROM item WHERE id = 'test-update-123'")
    count = cur.fetchone()[0]

    assert count == 1, "Should have exactly one item (updated, not duplicated)"

    # Check that title was updated
    cur = con.execute("SELECT title FROM item WHERE id = 'test-update-123'")
    title = cur.fetchone()[0]
    assert title == "Updated Title"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
