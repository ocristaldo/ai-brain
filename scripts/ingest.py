#!/usr/bin/env python3
import os, time, json, glob, uuid, sqlite3, pathlib, argparse
import yaml
from datetime import datetime
from common import log_json, get_trace_id, CONFIG

DB_PATH   = CONFIG["paths"]["db_path"]
NOTES_DIR = CONFIG["paths"]["notes_dir"]

def source_uri_to_path(source_uri):
    if not source_uri:
        return None
    if source_uri.startswith("file://"):
        return source_uri[7:]
    return source_uri

def validate_facets(meta):
    enums = {
        "domain": {"work","personal","hobbies"},
        "visibility": {"public","private","secret"},
        "type": {"idea","project","note","memory","quote","doc","task"},
        "status": {"inbox","active","archived"}
    }
    for k, allowed in enums.items():
        if k not in meta or meta[k] not in allowed:
            raise ValueError(f"FACET_VALIDATION_FAIL {k}='{meta.get(k)}' allowed={sorted(list(allowed))}")

def upsert(con, item_id, meta, body_md, source_uri):
    now = datetime.utcnow().isoformat()+"Z"
    con.execute(
        """
        INSERT INTO item(id, title, body_md, domain, visibility, type, status, source_uri, meta_json, created_at, updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            body_md=excluded.body_md,
            domain=excluded.domain,
            visibility=excluded.visibility,
            type=excluded.type,
            status=excluded.status,
            source_uri=excluded.source_uri,
            meta_json=excluded.meta_json,
            updated_at=excluded.updated_at
        """,
        (
            item_id,
            meta["title"],
            body_md,
            meta["domain"],
            meta["visibility"],
            meta["type"],
            meta.get("status","inbox"),
            source_uri,
            json.dumps(meta, ensure_ascii=False),
            now,
            now
        )
    )

    for t in meta.get("tags", []):
        con.execute("INSERT INTO tag(tag) VALUES(?) ON CONFLICT(tag) DO NOTHING", (t,))
        con.execute("INSERT INTO item_tag(item_id, tag) VALUES(?,?) ON CONFLICT(item_id,tag) DO NOTHING", (item_id, t))

    # FTS virtual table doesn't support ON CONFLICT, use DELETE + INSERT
    con.execute("DELETE FROM item_fts WHERE id = ?", (item_id,))
    con.execute("INSERT INTO item_fts(id,title,body_md) VALUES(?,?,?)", (item_id, meta["title"], body_md))

def resolve_item_id(con, meta, source_uri):
    if meta.get("id"):
        return meta["id"]
    cur = con.execute("SELECT id FROM item WHERE source_uri = ? LIMIT 1", (source_uri,))
    row = cur.fetchone()
    if row:
        return row["id"]
    return str(uuid.uuid4())


def load_note(path):
    with open(path, "r", encoding="utf-8") as fh:
        first_line = fh.readline()
        if first_line.strip() != "---":
            body = first_line + fh.read()
            return {}, body

        frontmatter_lines = []
        for line in fh:
            if line.strip() == "---":
                break
            frontmatter_lines.append(line)
        body = fh.read()

    frontmatter_text = "".join(frontmatter_lines)
    try:
        meta = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"FRONTMATTER_PARSE_FAIL {exc}")
    return meta, body


def main():
    ap = argparse.ArgumentParser(description="Ingest markdown notes into the AI Brain database")
    ap.add_argument("--prune-missing", action="store_true", help="Remove DB entries whose source markdown file has been deleted")
    ap.add_argument("--yes", action="store_true", help="Auto-confirm prompts (use with --prune-missing)")
    args = ap.parse_args()

    start_time = time.time()
    trace_id = get_trace_id()

    # Check and trigger daily backup in background (non-blocking)
    try:
        from backup_trigger import check_and_trigger
        check_and_trigger()
    except Exception:
        pass  # Don't fail ingest if backup check fails

    pathlib.Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    ingested = 0
    skipped = 0
    # Use per-item commits to avoid partial writes when an error occurs
    for root, dirs, files in os.walk(NOTES_DIR):
        for name in files:
            if not name.lower().endswith(".md"):
                continue
            path = os.path.join(root, name)
            try:
                meta, body = load_note(path)
                if "title" not in meta:
                    meta["title"] = os.path.basename(path)
                validate_facets(meta)
                source_uri = f"file://{os.path.abspath(path)}"
                item_id = resolve_item_id(con, meta, source_uri)
                upsert(con, item_id, meta, body, source_uri)
                con.execute(
                    "INSERT INTO change_log(at, actor, action, item_id, details_json) VALUES(?,?,?,?,?)",
                    (datetime.utcnow().isoformat()+"Z", "ingestor", "update", item_id, json.dumps({"path": path}))
                )
                con.commit()
                ingested += 1
            except Exception as e:
                try:
                    con.rollback()
                except Exception:
                    pass
                skipped += 1
                try:
                    con.execute(
                        "INSERT INTO change_log(at, actor, action, details_json) VALUES(?,?,?,?)",
                        (datetime.utcnow().isoformat()+"Z", "ingestor", "ingest_skip", json.dumps({"path": path, "error": str(e)}))
                    )
                except Exception:
                    # If change_log insert fails, ensure we still log to file
                    log_json("ERROR", "ingestor", "change_log_fail", "failed to write change_log", trace_id=trace_id, err=str(e), path=path)
                log_json("WARN","ingestor","ingest_skip", f"skip {path}", trace_id=trace_id, err=str(e))
    try:
        con.commit()
    except Exception:
        # commit might be unnecessary here; already committed per-item
        pass
    log_json("INFO","ingestor","summary","ingest completed", trace_id=trace_id, start_time=start_time, rows=ingested, skipped=skipped)
    print(f"Ingested: {ingested}, skipped: {skipped}")

    if args.prune_missing:
        prune_start = time.time()
        deleted = prune_missing_items(con, auto_confirm=args.yes)
        log_json("INFO","ingestor","prune","prune completed", trace_id=trace_id, start_time=prune_start, rows=deleted)
        if deleted:
            print(f"Pruned {deleted} stale DB entr{'y' if deleted == 1 else 'ies'}.")
        else:
            print("No stale DB entries found.")

def prune_missing_items(con, auto_confirm):
    cur = con.execute("SELECT id, title, source_uri FROM item ORDER BY updated_at DESC")
    missing = []
    for row in cur.fetchall():
        source_path = source_uri_to_path(row["source_uri"])
        if not source_path:
            continue
        if not os.path.exists(source_path):
            missing.append({
                "id": row["id"],
                "title": row["title"],
                "source_uri": row["source_uri"],
                "path": source_path
            })

    if not missing:
        return 0

    total = len(missing)
    print(f"\nDetected {total} DB entr{'y' if total == 1 else 'ies'} whose source markdown file is missing.")
    print("First 10 to be deleted:")
    for row in missing[:10]:
        print(f" - [{row['id']}] {row['title']} -> {row['path']}")

    proceed = auto_confirm
    if not auto_confirm:
        resp = input("Delete these entries from the database? [y/N]: ").strip().lower()
        proceed = resp in ("y", "yes")

    if not proceed:
        print("Prune cancelled.")
        return 0

    now = datetime.utcnow().isoformat()+"Z"
    for row in missing:
        con.execute("DELETE FROM item WHERE id = ?", (row["id"],))
        con.execute("DELETE FROM item_tag WHERE item_id = ?", (row["id"],))
        con.execute("DELETE FROM embedding WHERE item_id = ?", (row["id"],))
        con.execute(
            "INSERT INTO change_log(at, actor, action, item_id, details_json) VALUES(?,?,?,?,?)",
            (now, "ingestor", "delete", row["id"], json.dumps({"reason": "missing_source", "source_uri": row["source_uri"]}))
        )
    con.commit()
    print(f"Deleted {total} entr{'y' if total == 1 else 'ies'} from DB.")
    return total

if __name__ == "__main__":
    main()
