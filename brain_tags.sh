#!/bin/bash
# Brain Tags - List all tags or notes with a specific tag
# Usage: ./brain_tags.sh [tag_name]

set -e

BRAIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BRAIN_DIR"

source .venv/bin/activate

python3 - "$@" <<'EOF'
import sys
import sqlite3
import os

db_path = "db/brain.sqlite"
if not os.path.exists(db_path):
    print("Error: Database not found. Run 'make init' first.", file=sys.stderr)
    sys.exit(1)

con = sqlite3.connect(db_path)
con.row_factory = sqlite3.Row

if len(sys.argv) > 1:
    # Show notes with this tag
    tag = sys.argv[1]
    cur = con.execute("""
        SELECT i.id, i.title, i.domain, i.type, i.status
        FROM item i
        JOIN item_tag it ON i.id = it.item_id
        WHERE it.tag = ?
        ORDER BY i.updated_at DESC
    """, (tag,))

    rows = cur.fetchall()

    if not rows:
        print(f"No notes found with tag: {tag}")
        sys.exit(0)

    print(f"\nNotes tagged with '{tag}' ({len(rows)}):\n")
    print(f"{'ID':<12} {'Title':<40} {'Domain':<10} {'Type':<10}")
    print("=" * 80)

    for row in rows:
        title = row['title'][:37] + '...' if len(row['title']) > 40 else row['title']
        print(f"{row['id']:<12} {title:<40} {row['domain']:<10} {row['type']:<10}")
else:
    # List all tags with counts
    cur = con.execute("""
        SELECT t.tag, COUNT(it.item_id) as count
        FROM tag t
        LEFT JOIN item_tag it ON t.tag = it.tag
        GROUP BY t.tag
        ORDER BY count DESC, t.tag
    """)

    rows = cur.fetchall()

    if not rows:
        print("No tags found in brain.")
        sys.exit(0)

    print(f"\nAll tags ({len(rows)}):\n")
    print(f"{'Tag':<30} {'Count':<10}")
    print("=" * 40)

    for row in rows:
        print(f"{row['tag']:<30} {row['count']:<10}")

    print(f"\nUse './brain_tags.sh <tag>' to see notes with a specific tag")

EOF
