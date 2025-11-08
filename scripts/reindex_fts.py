#!/usr/bin/env python3
import os, json, sqlite3, yaml, pathlib, argparse, sys
from datetime import datetime

CONFIG = yaml.safe_load(open("config.yaml","r"))
DB_PATH   = CONFIG["paths"]["db_path"]
VAR_DIR   = CONFIG["paths"]["var_dir"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="Check health without reindexing")
    args = ap.parse_args()

    con = sqlite3.connect(DB_PATH)

    # Check FTS integrity
    fts_ok = True
    try:
        cur = con.execute("SELECT count(*) FROM item_fts")
        fts_count = cur.fetchone()[0]
        cur = con.execute("SELECT count(*) FROM item")
        item_count = cur.fetchone()[0]
        if fts_count != item_count:
            fts_ok = False
            if not args.check:
                print(f"FTS count mismatch ({fts_count} vs {item_count}). Reindexing...")
    except Exception as e:
        fts_ok = False
        if not args.check:
            print(f"FTS check failed: {e}. Reindexing...")

    # Reindex if needed and not in check-only mode
    if not fts_ok and not args.check:
        con.execute("DELETE FROM item_fts")
        con.execute("INSERT INTO item_fts(id,title,body_md) SELECT id,title,body_md FROM item")
        con.commit()
        fts_ok = True
        print("FTS reindexed successfully")

    # Gather stats
    cur = con.execute("SELECT count(*) FROM item"); items = cur.fetchone()[0]
    cur = con.execute("SELECT count(*) FROM tag"); tags = cur.fetchone()[0]

    health = {
        "ok": fts_ok,
        "items": items,
        "tags": tags,
        "fts_ok": fts_ok,
        "last_ingest": None,
        "updated_at": datetime.utcnow().isoformat()+"Z"
    }

    pathlib.Path(VAR_DIR).mkdir(parents=True, exist_ok=True)
    with open(os.path.join(VAR_DIR,"health.json"),"w",encoding="utf-8") as f:
        f.write(json.dumps(health, indent=2))

    if args.check:
        print(f"Health check: {'✅ OK' if health['ok'] else '❌ FAIL'}")
        print(f"  Items: {items}, Tags: {tags}, FTS: {'OK' if fts_ok else 'FAIL'}")
    else:
        print("Health updated:", health)

    sys.exit(0 if health['ok'] else 1)

if __name__ == "__main__":
    main()
