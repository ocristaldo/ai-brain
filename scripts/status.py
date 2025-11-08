#!/usr/bin/env python3
"""Display AI Brain database status and useful metrics."""
import argparse
import json
import os
import sqlite3
from datetime import datetime

import yaml

CONFIG = yaml.safe_load(open("config.yaml", "r"))
DB_PATH = CONFIG["paths"]["db_path"]


def gather_stats():
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"Database not found at {DB_PATH}. Run 'make init' first.")

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    stats = {}

    stats["items"] = con.execute("SELECT COUNT(*) AS c FROM item").fetchone()["c"]
    stats["tags"] = con.execute("SELECT COUNT(*) AS c FROM tag").fetchone()["c"]
    stats["embeddings"] = con.execute("SELECT COUNT(*) AS c FROM embedding").fetchone()["c"]
    stats["change_log_entries"] = con.execute("SELECT COUNT(*) AS c FROM change_log").fetchone()["c"]

    last_item = con.execute("SELECT MAX(updated_at) AS ts FROM item").fetchone()["ts"]
    stats["last_item_update"] = last_item

    stats["domains"] = {
        row["domain"]: row["count"]
        for row in con.execute("SELECT domain, COUNT(*) AS count FROM item GROUP BY domain")
    }
    stats["types"] = {
        row["type"]: row["count"]
        for row in con.execute("SELECT type, COUNT(*) AS count FROM item GROUP BY type")
    }

    stats["visibility"] = {
        row["visibility"]: row["count"]
        for row in con.execute("SELECT visibility, COUNT(*) AS count FROM item GROUP BY visibility")
    }

    con.close()
    stats["generated_at"] = datetime.utcnow().isoformat() + "Z"
    return stats


def print_table(stats):
    def fmt_section(title):
        print(f"\n{title}")
        print("-" * len(title))

    print("AI Brain Status")
    print("================")
    print(f"Items:       {stats['items']}")
    print(f"Tags:        {stats['tags']}")
    print(f"Embeddings:  {stats['embeddings']}")
    print(f"Change Log:  {stats['change_log_entries']}")
    print(f"Last Update: {stats['last_item_update'] or 'N/A'}")

    fmt_section("Per Domain")
    for domain, count in sorted(stats["domains"].items()):
        print(f"{domain:>10}: {count}")

    fmt_section("Per Type")
    for typ, count in sorted(stats["types"].items()):
        print(f"{typ:>10}: {count}")

    fmt_section("Visibility")
    for vis, count in sorted(stats["visibility"].items()):
        print(f"{vis:>10}: {count}")

    print(f"\nGenerated at: {stats['generated_at']}")


def main():
    parser = argparse.ArgumentParser(description="Show AI Brain database status.")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of table")
    args = parser.parse_args()

    stats = gather_stats()
    if args.json:
        print(json.dumps(stats, indent=2))
    else:
        print_table(stats)


if __name__ == "__main__":
    main()
