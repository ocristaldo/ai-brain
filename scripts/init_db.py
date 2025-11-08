#!/usr/bin/env python3
import sqlite3, os, json, time, pathlib, yaml

CONFIG = yaml.safe_load(open("config.yaml","r"))
DB_PATH = CONFIG["paths"]["db_path"]
LOGS_DIR = CONFIG["paths"]["logs_dir"]
VAR_DIR = CONFIG["paths"]["var_dir"]

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

schema = """
CREATE TABLE IF NOT EXISTS item (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  body_md TEXT NOT NULL,
  domain TEXT NOT NULL,
  visibility TEXT NOT NULL,
  type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'inbox',
  source_uri TEXT,
  meta_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tag (
  tag TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS item_tag (
  item_id TEXT NOT NULL,
  tag TEXT NOT NULL,
  PRIMARY KEY(item_id, tag),
  FOREIGN KEY(item_id) REFERENCES item(id) ON DELETE CASCADE,
  FOREIGN KEY(tag) REFERENCES tag(tag) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS embedding (
  item_id TEXT PRIMARY KEY,
  model TEXT NOT NULL,
  vec_blob BLOB NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(item_id) REFERENCES item(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS edge (
  src_id TEXT NOT NULL,
  dst_id TEXT NOT NULL,
  rel TEXT NOT NULL,
  PRIMARY KEY(src_id, dst_id, rel),
  FOREIGN KEY(src_id) REFERENCES item(id) ON DELETE CASCADE,
  FOREIGN KEY(dst_id) REFERENCES item(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS change_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT NOT NULL,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  item_id TEXT,
  details_json TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS item_fts USING fts5(
  id UNINDEXED,
  title,
  body_md
);
"""


def ensure_unique_index(con):
    try:
        con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_item_source_uri ON item(source_uri)")
    except sqlite3.IntegrityError:
        print("Warning: Duplicate source_uri rows detected. Run 'make dedupe APPLY=1' to clean duplicates before re-running init.")


def main():
    con = sqlite3.connect(DB_PATH)
    con.executescript(schema)
    ensure_unique_index(con)
    con.commit()
    pathlib.Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)
    pathlib.Path(VAR_DIR).mkdir(parents=True, exist_ok=True)
    pathlib.Path(CONFIG["paths"]["backups_dir"]).mkdir(parents=True, exist_ok=True)
    health_path = os.path.join(VAR_DIR, "health.json")
    with open(health_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"ok": True, "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")}, indent=2))
    print(f"Initialized database at {DB_PATH}")
    print(f"Created directories: {LOGS_DIR}, {VAR_DIR}, {CONFIG['paths']['backups_dir']}")
    print(f"Health check initialized at {health_path}")

if __name__ == "__main__":
    main()
