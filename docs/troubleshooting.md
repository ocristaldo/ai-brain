# Troubleshooting Guide

Common issues and solutions for AI Brain Vault.

---

## Installation Issues

### Error: `ModuleNotFoundError: No module named 'yaml'`

**Cause:** Dependencies not installed

**Solution:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Error: `Permission denied` when running scripts

**Cause:** Scripts not executable

**Solution:**
```bash
chmod +x scripts/*.py
```

---

## Ingestion Errors

### `FACET_VALIDATION_FAIL`

**Error Message:**
```
FACET_VALIDATION_FAIL domain='works' allowed=['hobbies', 'personal', 'work']
```

**Cause:** Invalid frontmatter value

**Solution:**
Fix the frontmatter in your markdown file. Valid values:
- **domain:** `work`, `personal`, `hobbies`
- **visibility:** `public`, `private`, `secret`
- **type:** `idea`, `project`, `note`, `memory`, `quote`, `doc`, `task`
- **status:** `inbox`, `active`, `archived`

**Example Fix:**
```yaml
---
title: My Note
domain: work  # Was: works (invalid)
visibility: private
type: note
status: inbox
tags: []
---
```

### `INGEST_PARSE_ERROR: Invalid frontmatter`

**Cause:** Malformed YAML in frontmatter

**Solution:**
1. Check YAML syntax (indentation, colons, quotes)
2. Ensure frontmatter is between `---` markers
3. Use YAML validator online if needed

**Example:**
```yaml
---
# Correct
title: My Note
tags: [ai, python]

# Wrong - missing colon
title My Note
tags [ai, python]
---
```

### Notes skipped during ingestion

**Check the logs:**
```bash
grep "ingest_skip" logs/app.*.jsonl
```

**Common causes:**
- Invalid frontmatter
- Missing required fields
- Incorrect facet values

---

## Search Issues

### No results when searching

**Troubleshooting steps:**

1. **Verify items exist:**
```bash
sqlite3 db/brain.sqlite "SELECT COUNT(*) FROM item"
```

2. **Check FTS index:**
```bash
make health
```

3. **Reindex if needed:**
```bash
python3 scripts/reindex_fts.py
```

4. **Try broader search:**
```bash
# Instead of exact phrase
make search q="kubernetes"

# Try partial matches
make search q="kube"
```

### `FTS_REINDEX_FAIL` error

**Error:** FTS5 index corrupted

**Solution:**
```bash
# Reindex FTS
python3 scripts/reindex_fts.py

# Verify health
make health
```

If still failing:
```bash
# Backup first!
make backup

# Reinitialize database
rm db/brain.sqlite
make init
make ingest
```

---

## Backup/Restore Issues

### `BACKUP_VERIFY_FAIL: Checksum mismatch`

**Cause:** Backup file corrupted

**Solution:**
1. Create new backup:
```bash
make backup
```

2. Don't use the corrupted backup file
3. Check disk space and disk health

### Restore conflicts

**Error:** Files already exist

**Solution:**
1. Backup current state first:
```bash
make backup
```

2. Review dry-run output:
```bash
make restore file=backups/brain-20251108-120000.tgz
```

3. If safe, apply restore:
```bash
CONFIRM=1 make restore file=backups/brain-20251108-120000.tgz
```

### Async backup not triggering

**Check if backup is needed:**
```bash
cat var/last_backup.json
```

**Force backup:**
```bash
make backup
```

**Check async backup logs:**
```bash
cat logs/backup_async.log
```

---

## Performance Issues

### Slow searches

**Check database size:**
```bash
ls -lh db/brain.sqlite
```

**Optimize if needed:**
```bash
sqlite3 db/brain.sqlite "VACUUM; ANALYZE;"
```

**Check FTS index:**
```bash
make health
```

### Ingestion taking too long

**Batch ingestion:**
- Better to ingest multiple files at once
- Avoid running ingest after each file

**Check logs:**
```bash
tail -f logs/app.*.jsonl
```

---

## Database Issues

### Database locked error

**Cause:** Another process accessing database

**Solution:**
1. Check for running processes:
```bash
ps aux | grep python3
```

2. Kill stale processes if needed

3. Remove lock files:
```bash
rm db/brain.sqlite-wal db/brain.sqlite-shm
```

### Duplicate items appearing

**Cause:** Notes ingested multiple times without unique IDs

**Solution:**
Add unique ID to notes:
```yaml
---
id: unique-note-id-123
title: My Note
...
---
```

Or clean duplicates:
```bash
# Check for duplicates
sqlite3 db/brain.sqlite "SELECT title, COUNT(*) FROM item GROUP BY title HAVING COUNT(*) > 1"

# Delete older duplicates (keep newest)
# Backup first!
make backup
```

---

## Configuration Issues

### Changes to config.yaml not taking effect

**Solution:**
Restart your operations - config is loaded at script startup.

### Invalid config.yaml

**Validate YAML syntax:**
```bash
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

---

## Common Questions

### Why are my backups so large?

Backups include:
- Database (SQLite)
- All notes (markdown files)
- Runtime state (var/)

**Optimize:**
- Archive old notes to separate directory
- Adjust backup retention (keep_days, min_backups)

### How do I reset everything?

```bash
# Backup first (optional)
make backup

# Remove generated files
rm -rf db/ logs/ var/ backups/

# Reinitialize
make init

# Re-ingest notes
make ingest
```

### Can I use this with multiple devices?

Current version is single-device only. Future versions will add sync via Syncthing/rclone.

For now, use manual backup/restore:
```bash
# Device 1
make backup
scp backups/brain-*.tgz device2:/path/

# Device 2
CONFIRM=1 make restore file=backups/brain-*.tgz
```

---

## Getting Help

1. **Check logs:**
```bash
tail -50 logs/app.*.jsonl
cat logs/backup_async.log
```

2. **Check health:**
```bash
make health
cat var/health.json
```

3. **Verify database:**
```bash
sqlite3 db/brain.sqlite ".schema"
sqlite3 db/brain.sqlite "SELECT COUNT(*) FROM item"
```

4. **Run tests:**
```bash
source .venv/bin/activate
pytest tests/ -v
```

5. **Create GitHub issue:**
   - Include error messages
   - Include relevant logs
   - Include steps to reproduce
   - Include system info (OS, Python version)

---

## Error Code Reference

| Code | Description | Severity | Action |
|------|-------------|----------|---------|
| `INGEST_PARSE_ERROR` | Invalid frontmatter | WARN | Fix YAML in note |
| `FACET_VALIDATION_FAIL` | Invalid facet value | ERROR | Use valid enum |
| `EMBED_PROVIDER_FAIL` | Embedding engine down | WARN | Check Ollama/retry |
| `FTS_REINDEX_FAIL` | FTS index error | ERROR | Run `make health` |
| `BACKUP_VERIFY_FAIL` | Checksum mismatch | ERROR | Retry backup |
| `RESTORE_CONFLICT` | Overwrite risk | ERROR | Review dry-run |

---

**Last Updated:** 2025-11-08
