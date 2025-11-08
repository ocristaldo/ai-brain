#!/bin/bash
# Brain List - List notes with filters
# Usage: ./brain_list.sh [--domain DOMAIN] [--type TYPE] [--status STATUS] [--tags TAGS] [--limit N]

set -e

BRAIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BRAIN_DIR"

source .venv/bin/activate

python3 - "$@" <<'EOF'
import sys
import sqlite3
import argparse
import os

parser = argparse.ArgumentParser(description='List notes from brain')
parser.add_argument('--domain', choices=['work', 'personal', 'hobbies'], help='Filter by domain')
parser.add_argument('--type', choices=['idea', 'project', 'note', 'memory', 'quote', 'doc', 'task'], help='Filter by type')
parser.add_argument('--status', choices=['inbox', 'active', 'archived'], help='Filter by status')
parser.add_argument('--tags', help='Filter by tags (comma-separated)')
parser.add_argument('--limit', type=int, default=50, help='Limit number of results')

args = parser.parse_args()

db_path = "db/brain.sqlite"
if not os.path.exists(db_path):
    print("Error: Database not found. Run 'make init' first.", file=sys.stderr)
    sys.exit(1)

con = sqlite3.connect(db_path)
con.row_factory = sqlite3.Row

# Build query
sql = "SELECT id, title, domain, type, status, created_at, updated_at FROM item WHERE 1=1"
params = []

if args.domain:
    sql += " AND domain = ?"
    params.append(args.domain)

if args.type:
    sql += " AND type = ?"
    params.append(args.type)

if args.status:
    sql += " AND status = ?"
    params.append(args.status)

if args.tags:
    tags = [t.strip() for t in args.tags.split(',')]
    sql += " AND id IN (SELECT item_id FROM item_tag WHERE tag IN (" + ','.join(['?']*len(tags)) + "))"
    params.extend(tags)

sql += " ORDER BY updated_at DESC LIMIT ?"
params.append(args.limit)

cur = con.execute(sql, params)
rows = cur.fetchall()

if not rows:
    print("No notes found matching criteria.")
    sys.exit(0)

print(f"\nFound {len(rows)} note(s):\n")
print(f"{'ID':<12} {'Title':<40} {'Domain':<10} {'Type':<10} {'Status':<10}")
print("=" * 90)

for row in rows:
    title = row['title'][:37] + '...' if len(row['title']) > 40 else row['title']
    print(f"{row['id']:<12} {title:<40} {row['domain']:<10} {row['type']:<10} {row['status']:<10}")

print("\nUse './brain_read.sh <id>' to read a specific note")

EOF
