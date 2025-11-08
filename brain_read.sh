#!/bin/bash
# Brain Read - Read a specific note by ID or search term
# Usage: ./brain_read.sh <note_id_or_search_term>

set -e

BRAIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BRAIN_DIR"

if [ -z "$1" ]; then
    echo "Usage: $0 <note_id_or_search_term>"
    echo "Example: $0 kubernetes"
    echo "Example: $0 abc123def"
    exit 1
fi

source .venv/bin/activate

# Try to find note by search first
python3 - "$1" <<'EOF'
import sys
import sqlite3
import json
import os

search_term = sys.argv[1]
db_path = "db/brain.sqlite"

if not os.path.exists(db_path):
    print("Error: Database not found. Run 'make init' first.", file=sys.stderr)
    sys.exit(1)

con = sqlite3.connect(db_path)
con.row_factory = sqlite3.Row

# Try exact ID match first
cur = con.execute("SELECT * FROM item WHERE id = ?", (search_term,))
row = cur.fetchone()

if not row:
    # Try FTS search
    cur = con.execute("""
        SELECT i.* FROM item_fts
        JOIN item i ON item_fts.id = i.id
        WHERE item_fts MATCH ?
        LIMIT 1
    """, (search_term,))
    row = cur.fetchone()

if not row:
    print(f"No note found for: {search_term}", file=sys.stderr)
    sys.exit(1)

# Output note details
def uri_to_path(uri):
    if not uri:
        return None
    return uri[7:] if uri.startswith("file://") else uri

file_path = uri_to_path(row['source_uri'])

print("=" * 80)
print(f"ID: {row['id']}")
print(f"Title: {row['title']}")
print(f"Domain: {row['domain']}")
print(f"Type: {row['type']}")
print(f"Status: {row['status']}")
print(f"Visibility: {row['visibility']}")
print(f"Source URI: {row['source_uri']}")
print(f"File Path: {file_path or 'unknown'}")
print(f"Created: {row['created_at']}")
print(f"Updated: {row['updated_at']}")

# Get tags
cur = con.execute("""
    SELECT tag FROM item_tag WHERE item_id = ? ORDER BY tag
""", (row['id'],))
tags = [r['tag'] for r in cur.fetchall()]
print(f"Tags: {', '.join(tags) if tags else 'none'}")

print("=" * 80)
print("\nContent:\n")
print(row['body_md'])
print("\n" + "=" * 80)

# Print file path for editing
if row['source_uri']:
    print(f"\nFile: {row['source_uri']}")
    print(f"Edit: vim {row['source_uri']}")
    print("After editing, run: make ingest")

EOF
