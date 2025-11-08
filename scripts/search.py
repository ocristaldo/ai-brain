#!/usr/bin/env python3
import os, sqlite3, argparse, yaml, json, pathlib, sys, time
from datetime import datetime
from common import log_json, get_trace_id, CONFIG

DB_PATH = CONFIG["paths"]["db_path"]

def main():
    start_time = time.time()
    trace_id = get_trace_id()

    # Check and trigger daily backup in background (non-blocking)
    try:
        from backup_trigger import check_and_trigger
        check_and_trigger()
    except Exception:
        pass  # Don't fail search if backup check fails

    ap = argparse.ArgumentParser(description="Search AI Brain notes")
    ap.add_argument("--q", default="", help="Full-text search query (leave blank to list)")
    ap.add_argument("--domain", default=None)
    ap.add_argument("--type", default=None)
    ap.add_argument("--visibility", default=None)
    ap.add_argument("--status", default=None)
    ap.add_argument("--tags", default="", help="Comma separated tags")
    ap.add_argument("--k", type=int, default=20, help="Maximum results")
    ap.add_argument("--format", choices=["table", "json", "full"], default="table", help="Output format")
    ap.add_argument("--include-body", action="store_true", help="Include note body in JSON output")
    args = ap.parse_args()

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    q = args.q.strip()

    select_fields = "i.id, i.title, i.source_uri, i.domain, i.visibility, i.type, i.status"
    need_body = args.format in ("json", "full") or args.include_body
    if need_body:
        select_fields += ", i.body_md"

    # Build query based on whether we have a search term
    if q:
        # FTS search: start from the FTS table
        sql = """
          SELECT {fields}
          FROM item_fts
          JOIN item i ON item_fts.id = i.id
          WHERE item_fts MATCH ?
        """.format(fields=select_fields)
        params = [q]
    else:
        # No search term: query all items
        sql = """
          SELECT {fields}
          FROM item i
          WHERE 1=1
        """.format(fields=select_fields)
        params = []

    # Add filters
    for field, val in (("domain", args.domain), ("type", args.type), ("visibility", args.visibility), ("status", args.status)):
        if val:
            sql += f" AND i.{field} = ?"
            params.append(val)

    # Add tag filters
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    if tags:
        sql += f" AND EXISTS (SELECT 1 FROM item_tag it WHERE it.item_id = i.id AND it.tag IN ({','.join('?'*len(tags))}))"
        params.extend(tags)

    sql += " LIMIT ?"
    params.append(args.k)
    cur = con.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]

    if args.format == "json":
        payload = []
        for r in rows:
            entry = {
                "id": r["id"],
                "title": r["title"],
                "domain": r["domain"],
                "visibility": r["visibility"],
                "type": r["type"],
                "status": r["status"],
                "source_uri": r["source_uri"]
            }
            if args.include_body and need_body:
                entry["body_md"] = r["body_md"]
            payload.append(entry)
        print(json.dumps(payload, indent=2))
    elif args.format == "full":
        if not rows:
            print("No results.")
        for r in rows:
            print("="*80)
            print(f"{r['title']} [{r['id']}]")
            print(f"Domain: {r['domain']}  Type: {r['type']}  Status: {r['status']}  Visibility: {r['visibility']}")
            print(f"Source: {r['source_uri']}\n")
            body = r.get("body_md", "")
            if body:
                print(body.strip())
            print()
    else:
        if not rows:
            print("No results.")
        for r in rows:
            print(f"- [{r['id']}] {r['title']}  ({r['domain']}/{r['type']}, {r['visibility']})")
            print(f"  {r['source_uri']}")

    log_json(
        "INFO",
        "librarian",
        "search",
        "search completed",
        trace_id=trace_id,
        start_time=start_time,
        rows=len(rows),
        query=q,
        output_format=args.format
    )

if __name__ == "__main__":
    main()
