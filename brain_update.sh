#!/bin/bash
# Brain Update - Update a note's metadata (status, tags, etc.)
# Usage: ./brain_update.sh <note_id_or_search> --status STATUS --tags "tag1,tag2" --type TYPE

set -euo pipefail

BRAIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BRAIN_DIR"
export BRAIN_DIR

if [ -z "$1" ]; then
    echo "Usage: $0 <note_id_or_search> [--status STATUS] [--tags TAGS] [--type TYPE] [--domain DOMAIN]"
    echo "Example: $0 kubernetes --status active --tags 'devops,k8s'"
    echo "Example: $0 abc123 --type project"
    exit 1
fi

NOTE_ID="$1"
shift

source .venv/bin/activate

python3 - "$NOTE_ID" "$@" <<'EOF'
import argparse
import os
import sqlite3
import subprocess
import sys
import yaml


def uri_to_path(uri: str):
    if not uri:
        return None
    return uri[7:] if uri.startswith("file://") else uri


def main():
    parser = argparse.ArgumentParser(description="Update note metadata")
    parser.add_argument("note_id", help="Note ID or search term")
    parser.add_argument("--status", choices=["inbox", "active", "archived"])
    parser.add_argument("--tags", help="New tags (comma-separated, replaces existing)")
    parser.add_argument("--type", choices=["idea", "project", "note", "memory", "quote", "doc", "task"])
    parser.add_argument("--domain", choices=["work", "personal", "hobbies"])
    args = parser.parse_args()

    db_path = "db/brain.sqlite"
    if not os.path.exists(db_path):
        print("Error: Database not found. Run 'make init' first.", file=sys.stderr)
        sys.exit(1)

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    cur = con.execute("SELECT * FROM item WHERE id = ?", (args.note_id,))
    row = cur.fetchone()
    if not row:
        cur = con.execute("""
            SELECT i.* FROM item_fts
            JOIN item i ON item_fts.id = i.id
            WHERE item_fts MATCH ?
            LIMIT 1
        """, (args.note_id,))
        row = cur.fetchone()

    if not row:
        print(f"Error: No note found for: {args.note_id}", file=sys.stderr)
        sys.exit(1)

    note_id = row["id"]
    note_path = uri_to_path(row["source_uri"])
    if not note_path or not os.path.exists(note_path):
        print(f"Error: Note file not found: {row['source_uri']}", file=sys.stderr)
        sys.exit(1)

    print(f"Updating note: {row['title']}")
    with open(note_path, "r") as fh:
        content = fh.read()

    if content.startswith("---\n"):
        parts = content.split("---\n", 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2]
        else:
            print("Error: Invalid frontmatter format", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: No frontmatter found", file=sys.stderr)
        sys.exit(1)

    updated = False
    if args.status:
        frontmatter["status"] = args.status
        updated = True
        print(f"  Status: {row['status']} → {args.status}")
    if args.type:
        frontmatter["type"] = args.type
        updated = True
        print(f"  Type: {row['type']} → {args.type}")
    if args.domain:
        frontmatter["domain"] = args.domain
        updated = True
        print(f"  Domain: {row['domain']} → {args.domain}")
    if args.tags is not None:
        new_tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
        frontmatter["tags"] = new_tags
        updated = True
        old_tags = cur.execute("SELECT tag FROM item_tag WHERE item_id = ? ORDER BY tag", (note_id,)).fetchall()
        old_tags_str = ", ".join([t["tag"] for t in old_tags]) if old_tags else "none"
        new_tags_str = ", ".join(new_tags) if new_tags else "none"
        print(f"  Tags: {old_tags_str} → {new_tags_str}")

    if not updated:
        print("No changes specified. Use --status, --tags, --type, or --domain")
        sys.exit(0)

    new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n{body}"
    with open(note_path, "w") as fh:
        fh.write(new_content)

    print(f"\nUpdated: {note_path}")
    print("Running ingest to update database...")
    con.close()

    brain_dir = os.environ.get("BRAIN_DIR", ".")
    result = subprocess.run(["make", "ingest"], cwd=brain_dir, capture_output=True, text=True)
    if result.returncode == 0:
        print("✓ Changes ingested successfully")
    else:
        print(f"Error during ingest: {result.stderr}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
EOF
