#!/usr/bin/env python3
"""Remove duplicate rows (same source_uri) from the brain database."""
import argparse
import json
import os
import sqlite3
from datetime import datetime

import yaml

CONFIG = yaml.safe_load(open("config.yaml", "r"))
DB_PATH = CONFIG["paths"]["db_path"]


def find_duplicates(con):
    cur = con.execute(
        """
        SELECT source_uri, COUNT(*) AS cnt
        FROM item
        WHERE source_uri IS NOT NULL
        GROUP BY source_uri
        HAVING cnt > 1
        ORDER BY cnt DESC
        """
    )
    duplicates = []
    for row in cur.fetchall():
        source_uri = row["source_uri"]
        items = con.execute(
            "SELECT id, updated_at FROM item WHERE source_uri = ? ORDER BY datetime(updated_at) DESC",
            (source_uri,),
        ).fetchall()
        duplicates.append({
            "source_uri": source_uri,
            "rows": [dict(r) for r in items],
        })
    return duplicates


def delete_duplicates(con, dup_list):
    now = datetime.utcnow().isoformat() + "Z"
    deleted = 0
    for entry in dup_list:
        keep = entry["rows"][0]["id"]
        to_delete = [row["id"] for row in entry["rows"][1:]]
        if not to_delete:
            continue
        for item_id in to_delete:
            con.execute("DELETE FROM item WHERE id = ?", (item_id,))
            con.execute("DELETE FROM item_tag WHERE item_id = ?", (item_id,))
            con.execute("DELETE FROM embedding WHERE item_id = ?", (item_id,))
            con.execute(
                "INSERT INTO change_log(at, actor, action, item_id, details_json) VALUES(?,?,?,?,?)",
                (now, "dedupe", "delete", item_id, json.dumps({"reason": "duplicate_source_uri", "kept": keep})),
            )
            deleted += 1
    con.commit()
    return deleted


def main():
    parser = argparse.ArgumentParser(description="Detect or remove duplicate notes (same source_uri).")
    parser.add_argument("--apply", action="store_true", help="Delete duplicates instead of only reporting")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation when applying")
    parser.add_argument("--json", action="store_true", help="Output JSON (useful for scripting)")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        raise SystemExit(f"Database not found at {DB_PATH}. Run 'make init' first.")

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    duplicates = find_duplicates(con)
    summary = {
        "duplicate_groups": len(duplicates),
        "rows_to_delete": sum(max(0, len(entry["rows"]) - 1) for entry in duplicates),
        "details": duplicates,
    }

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        if not duplicates:
            print("No duplicates found.")
        else:
            print(f"Found {summary['duplicate_groups']} duplicate source_uri groups")
            for entry in duplicates:
                print(f"\nSource: {entry['source_uri']}")
                for row in entry["rows"]:
                    print(f" - {row['id']} (updated_at={row['updated_at']})")
            print(f"\nRows slated for deletion: {summary['rows_to_delete']}")

    if args.apply and duplicates:
        proceed = args.yes
        if not proceed:
            resp = input("Delete duplicates as described above? [y/N]: ").strip().lower()
            proceed = resp in ("y", "yes")
        if not proceed:
            print("Deduplication cancelled.")
            con.close()
            return
        deleted = delete_duplicates(con, duplicates)
        print(f"Deleted {deleted} duplicate entr{'y' if deleted == 1 else 'ies'}.")
    con.close()


if __name__ == "__main__":
    main()
