# Schema Migrations

Guide for managing database schema changes across versions.

---

## Current Schema Version

**Version:** 1.0
**Last Updated:** 2025-11-08

---

## Schema Overview

### Tables

#### `item`
Core content table with metadata.

```sql
CREATE TABLE item (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  body_md TEXT NOT NULL,
  domain TEXT NOT NULL,       -- work, personal, hobbies
  visibility TEXT NOT NULL,   -- public, private, secret
  type TEXT NOT NULL,         -- idea, project, note, etc.
  status TEXT NOT NULL DEFAULT 'inbox',  -- inbox, active, archived
  source_uri TEXT,
  meta_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

#### `tag`
Unique tags across all items.

```sql
CREATE TABLE tag (
  tag TEXT PRIMARY KEY
);
```

#### `item_tag`
Many-to-many relationship between items and tags.

```sql
CREATE TABLE item_tag (
  item_id TEXT NOT NULL,
  tag TEXT NOT NULL,
  PRIMARY KEY(item_id, tag),
  FOREIGN KEY(item_id) REFERENCES item(id) ON DELETE CASCADE,
  FOREIGN KEY(tag) REFERENCES tag(tag) ON DELETE CASCADE
);
```

#### `embedding`
Vector embeddings for semantic search.

```sql
CREATE TABLE embedding (
  item_id TEXT PRIMARY KEY,
  model TEXT NOT NULL,
  vec_blob BLOB NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(item_id) REFERENCES item(id) ON DELETE CASCADE
);
```

#### `edge`
Graph relationships between items.

```sql
CREATE TABLE edge (
  src_id TEXT NOT NULL,
  dst_id TEXT NOT NULL,
  rel TEXT NOT NULL,
  PRIMARY KEY(src_id, dst_id, rel),
  FOREIGN KEY(src_id) REFERENCES item(id) ON DELETE CASCADE,
  FOREIGN KEY(dst_id) REFERENCES item(id) ON DELETE CASCADE
);
```

#### `change_log`
Audit trail of all operations.

```sql
CREATE TABLE change_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT NOT NULL,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  item_id TEXT,
  details_json TEXT
);
```

#### `item_fts`
FTS5 full-text search index.

```sql
CREATE VIRTUAL TABLE item_fts USING fts5(
  id UNINDEXED,
  title,
  body_md
);
```

---

## Schema Stability

### Guaranteed Stable

These fields will **never** change across all versions:
- `item.id`
- `item.title`
- `item.body_md`
- `item.created_at`
- `item.updated_at`
- `tag.tag`
- `change_log` structure

### May Evolve

These may have additions (but not breaking changes):
- Facet enums (new domain/type/visibility values)
- `edge.rel` types
- `change_log.action` types

### Future Additions

Planned for future versions:
- `attachment` table (file attachments)
- `sync_state` table (multi-device sync)
- `user_preference` table (UI settings)

---

## Migration Strategy

### Version Tracking

Add schema version to database:

```sql
CREATE TABLE IF NOT EXISTS schema_version (
  version TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL,
  description TEXT
);

INSERT INTO schema_version VALUES ('1.0', '2025-11-08T00:00:00Z', 'Initial schema');
```

### Migration Script Template

Create `migrations/001_add_field.sql`:

```sql
-- Migration: Add new field to item table
-- Version: 1.1
-- Date: 2025-XX-XX

BEGIN TRANSACTION;

-- Check current version
SELECT version FROM schema_version ORDER BY version DESC LIMIT 1;

-- Add new column (example)
ALTER TABLE item ADD COLUMN priority TEXT DEFAULT 'medium';

-- Update version
INSERT INTO schema_version VALUES ('1.1', datetime('now'), 'Add priority field');

COMMIT;
```

**Apply migration:**
```bash
sqlite3 db/brain.sqlite < migrations/001_add_field.sql
```

---

## Backward Compatibility

### Reading Old Schemas

Newer code should handle older schemas gracefully:

```python
# Example: Handle optional fields
def read_item(row):
    return {
        'id': row['id'],
        'title': row['title'],
        'priority': row.get('priority', 'medium'),  # Default if missing
    }
```

### Forward Compatibility

Older code ignores new fields automatically (SQLite allows extra columns).

---

## Migration Scenarios

### Adding a New Facet Value

**Example:** Add `education` to `domain` enum

**Migration:**
```sql
-- No schema change needed!
-- Just update validation in code
```

**Code Update:**
```python
# scripts/ingest.py
enums = {
    "domain": {"work", "personal", "hobbies", "education"},  # Added education
    ...
}
```

**Backward Compatible:** Yes (existing data unchanged)

### Adding a New Table

**Example:** Add `attachment` table in future version

**Migration:**
```sql
BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS attachment (
  id TEXT PRIMARY KEY,
  item_id TEXT NOT NULL,
  filename TEXT NOT NULL,
  filepath TEXT NOT NULL,
  size_bytes INTEGER,
  mime_type TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(item_id) REFERENCES item(id) ON DELETE CASCADE
);

INSERT INTO schema_version VALUES
  ('2.0', datetime('now'), 'Add attachment support');

COMMIT;
```

**Backward Compatible:** Yes (existing operations unaffected)

### Adding a Column

**Example:** Add `priority` to items

**Migration:**
```sql
BEGIN TRANSACTION;

ALTER TABLE item ADD COLUMN priority TEXT DEFAULT 'medium';

INSERT INTO schema_version VALUES
  ('1.1', datetime('now'), 'Add priority field');

COMMIT;
```

**Code Update:**
```python
# scripts/ingest.py - frontmatter
priority = meta.get("priority", "medium")

# Insert statement
INSERT INTO item(..., priority) VALUES (..., ?)
```

**Backward Compatible:** Yes (DEFAULT value provided)

### Changing a Column Type

**⚠️ Not Backward Compatible!**

**Example:** Change `item.id` from UUID to INTEGER

**Don't Do This!** Breaking change.

**Alternative:** Create new column and migrate:

```sql
BEGIN TRANSACTION;

ALTER TABLE item ADD COLUMN id_v2 INTEGER;
-- Populate id_v2 with migration logic
-- Update foreign keys
-- Drop old id column (careful!)

COMMIT;
```

Better: Keep original schema if possible.

---

## Safe Migration Process

### 1. Backup First
```bash
make backup
```

### 2. Test on Copy
```bash
cp db/brain.sqlite db/brain.sqlite.test
sqlite3 db/brain.sqlite.test < migrations/001_new_field.sql
```

### 3. Validate
```bash
sqlite3 db/brain.sqlite.test ".schema"
sqlite3 db/brain.sqlite.test "SELECT COUNT(*) FROM item"
```

### 4. Apply to Production
```bash
sqlite3 db/brain.sqlite < migrations/001_new_field.sql
```

### 5. Verify
```bash
make health
make test
```

---

## Rollback Strategy

### Before Migration
```bash
# Always backup before migration
make backup
cp db/brain.sqlite db/brain.sqlite.pre-migration
```

### Rollback
```bash
# If migration fails, restore backup
cp db/brain.sqlite.pre-migration db/brain.sqlite

# Or use backup
CONFIRM=1 make restore file=backups/brain-YYYYMMDD-HHMMSS.tgz
```

---

## Future Planned Changes

### Multi-Device Sync

**New Table:**
```sql
CREATE TABLE sync_state (
  table_name TEXT,
  item_id TEXT,
  device_id TEXT,
  last_sync TEXT,
  sync_hash TEXT,
  PRIMARY KEY(table_name, item_id, device_id)
);
```

**Backward Compatible:** Yes

### Attachment Support

**New Table:**
```sql
CREATE TABLE attachment (
  id TEXT PRIMARY KEY,
  item_id TEXT NOT NULL,
  filename TEXT NOT NULL,
  filepath TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(item_id) REFERENCES item(id) ON DELETE CASCADE
);
```

**Backward Compatible:** Yes

### Enhanced Embeddings

**Column Addition:**
```sql
ALTER TABLE embedding ADD COLUMN confidence REAL DEFAULT 0.0;
ALTER TABLE embedding ADD COLUMN metadata TEXT;
```

**Backward Compatible:** Yes

---

## Migration Checklist

Before applying any migration:

- [ ] Backup database (`make backup`)
- [ ] Document migration in `migrations/` directory
- [ ] Test on copy of database
- [ ] Update schema version
- [ ] Update code to handle new schema
- [ ] Test backward compatibility
- [ ] Run health check (`make health`)
- [ ] Run test suite (`make test`)
- [ ] Update documentation

---

## Schema Export

### Export Current Schema
```bash
sqlite3 db/brain.sqlite ".schema" > schema/v1.0.sql
```

### Compare Schemas
```bash
diff schema/v1.0.sql schema/v1.1.sql
```

---

## Best Practices

1. **Never delete columns** - mark as deprecated instead
2. **Always provide DEFAULT values** for new columns
3. **Test migrations on copies first**
4. **Version all migrations** in `migrations/` directory
5. **Document breaking changes** clearly
6. **Keep old data** during migrations
7. **Use transactions** for atomic migrations
8. **Validate after migration** with health checks

---

## Migration Tools

### Auto-Migration Script

Create `scripts/migrate.py`:
```python
#!/usr/bin/env python3
"""
Apply schema migrations in order
"""
import sqlite3
import os
import glob

DB_PATH = "db/brain.sqlite"
MIGRATIONS_DIR = "migrations"

def get_current_version():
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        return cur.fetchone()[0]
    except:
        return "0.0"

def apply_migration(filepath):
    print(f"Applying {filepath}...")
    con = sqlite3.connect(DB_PATH)
    with open(filepath) as f:
        con.executescript(f.read())
    con.commit()
    print(f"✓ Applied {filepath}")

def main():
    current = get_current_version()
    print(f"Current schema version: {current}")

    migrations = sorted(glob.glob(f"{MIGRATIONS_DIR}/*.sql"))
    for migration in migrations:
        # Apply migrations newer than current version
        # (Implement version comparison logic)
        apply_migration(migration)

if __name__ == "__main__":
    main()
```

---

**Last Updated:** 2025-11-08
