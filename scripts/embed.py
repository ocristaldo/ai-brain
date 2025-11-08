#!/usr/bin/env python3
# Placeholder embeddings for Phase 1; safe to disable by setting embeddings.enabled=false in config.yaml
import os, sqlite3, yaml, time
from datetime import datetime
from common import log_json, get_trace_id, CONFIG

DB_PATH = CONFIG["paths"]["db_path"]

def main():
    start_time = time.time()
    trace_id = get_trace_id()

    con = sqlite3.connect(DB_PATH)
    cur = con.execute("SELECT id FROM item WHERE visibility <> 'secret'")
    count = 0
    for (item_id,) in cur.fetchall():
        con.execute(
            """
            INSERT INTO embedding(item_id, model, vec_blob, updated_at)
            VALUES(?,?,?,?)
            ON CONFLICT(item_id) DO UPDATE SET model=excluded.model, vec_blob=excluded.vec_blob, updated_at=excluded.updated_at
            """,
            (item_id, "placeholder", b"", datetime.utcnow().isoformat()+"Z")
        )
        count += 1
    con.commit()
    log_json("INFO", "embedder", "embed", "embedding completed (placeholder)", trace_id=trace_id, start_time=start_time, rows=count)
    print(f"Embedded (placeholder) {count} items.")

if __name__ == "__main__":
    main()
