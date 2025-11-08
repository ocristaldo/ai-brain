# Logging Documentation

Complete guide to AI Brain Vault logging system.

---

## Overview

AI Brain uses structured JSON logging (JSONL format) for all operations. This enables:
- Machine-readable logs
- Easy parsing and analysis
- Operation tracing with trace_id
- Performance monitoring with latency_ms

---

## Log Files

### Main Application Logs

**Location:** `logs/app.YYYY-MM-DD.jsonl`

**Format:** One JSON object per line (JSONL)

**Rotation:** Daily (one file per day)

**Example:**
```json
{
  "ts": "2025-11-08T14:12:35.123456Z",
  "level": "INFO",
  "phase": "p1",
  "component": "ingestor",
  "actor": "ingestor",
  "action": "update",
  "device_id": "default-device",
  "trace_id": "a1b2c3d4",
  "latency_ms": 7,
  "rows": 3,
  "skipped": 0,
  "msg": "ingest completed"
}
```

### Async Backup Logs

**Location:** `logs/backup_async.log`

**Format:** Plain text (for background processes)

**Content:** Backup trigger and completion messages

---

## Log Schema

### Core Fields (Always Present)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `ts` | string | ISO 8601 timestamp (UTC) | `"2025-11-08T14:12:35.123456Z"` |
| `level` | string | Log level | `"INFO"`, `"WARN"`, `"ERROR"` |
| `phase` | string | Project phase | `"p1"` |
| `component` | string | Script/component name | `"ingestor"`, `"librarian"`, `"backup"` |
| `actor` | string | Who performed action | `"ingestor"`, `"user"` |
| `action` | string | Action performed | `"update"`, `"search"`, `"backup"` |
| `device_id` | string | Device identifier | `"default-device"` |
| `msg` | string | Human-readable message | `"ingest completed"` |

### Optional Fields

| Field | Type | Description | When Present |
|-------|------|-------------|--------------|
| `trace_id` | string | 8-char hex trace ID | Operations that support tracing |
| `latency_ms` | integer | Operation duration (ms) | Timed operations |
| `rows` | integer | Records affected | Database operations |
| `skipped` | integer | Records skipped | Ingest operations |
| `query` | string | Search query | Search operations |
| `output_format` | string | CLI response format (`table/json/full`) | Search operations |
| `item_id` | string | Item identifier | Item-specific operations |
| `path` | string | File path | File operations |
| `err` | string | Error message | Error conditions |

---

## Log Levels

### INFO
Normal operations, successful completions

**Examples:**
```json
{"level": "INFO", "action": "search", "msg": "search completed", "rows": 5}
{"level": "INFO", "action": "update", "msg": "ingest completed", "rows": 10}
{"level": "INFO", "action": "backup", "msg": "backup completed"}
```

### WARN
Non-critical issues, skipped items

**Examples:**
```json
{"level": "WARN", "action": "ingest_skip", "msg": "skip ./notes/bad.md", "err": "Invalid frontmatter"}
{"level": "WARN", "action": "embed", "msg": "embedding provider unavailable"}
```

### ERROR
Critical failures, operations that couldn't complete

**Examples:**
```json
{"level": "ERROR", "action": "backup", "msg": "backup failed", "err": "Disk full"}
{"level": "ERROR", "action": "ingest", "msg": "database locked"}
```

---

## Components

### ingestor
Markdown file ingestion

**Actions:**
- `update` - Successfully ingested item
- `ingest_skip` - Skipped invalid file
- `summary` - Ingestion summary

**Example:**
```json
{
  "component": "ingestor",
  "action": "update",
  "item_id": "abc123",
  "path": "./notes/example.md",
  "msg": "upserted item"
}
```

### librarian
Search operations

**Actions:**
- `search` - Search completed

**Example:**
```json
{
  "component": "librarian",
  "action": "search",
  "query": "kubernetes",
  "rows": 5,
  "latency_ms": 8,
  "msg": "search completed"
}
```

### embedder
Embedding generation

**Actions:**
- `embed` - Embeddings created

**Example:**
```json
{
  "component": "embedder",
  "action": "embed",
  "rows": 10,
  "latency_ms": 150,
  "msg": "embedding completed (placeholder)"
}
```

### backup
Backup operations

**Actions:**
- `backup` - Backup created
- `verify` - Backup verified
- `restore_dryrun` - Dry-run restore
- `restore_apply` - Restore applied

---

## Redactions

Sensitive fields can be redacted via `config.yaml`:

```yaml
logging:
  level: INFO
  redactions: [body_md, email, password]
```

**Default Redactions:**
- `body_md` - Note content

**Redacted Output:**
```json
{
  "body_md": "[REDACTED]",
  "msg": "item ingested"
}
```

---

## Trace IDs

Each operation gets a unique 8-character hex trace ID for correlation.

**Example Flow:**
```json
// Ingest starts
{"trace_id": "a1b2c3d4", "action": "update", "msg": "starting ingest"}

// Multiple items processed
{"trace_id": "a1b2c3d4", "item_id": "item1", "msg": "ingested"}
{"trace_id": "a1b2c3d4", "item_id": "item2", "msg": "ingested"}

// Ingest completes
{"trace_id": "a1b2c3d4", "action": "summary", "msg": "ingest completed"}
```

**Use trace_id to:**
- Correlate related operations
- Debug complex flows
- Track operation chains

---

## Performance Monitoring

`latency_ms` tracks operation duration:

```json
{
  "action": "search",
  "latency_ms": 8,
  "msg": "search completed"
}
```

**Analyze Performance:**
```bash
# Extract latencies for search operations
grep '"action": "search"' logs/*.jsonl | grep -o '"latency_ms": [0-9]*'

# Average search latency
grep '"action": "search"' logs/*.jsonl | grep -o '"latency_ms": [0-9]*' | \
  awk -F: '{sum+=$2; count++} END {print sum/count}'
```

---

## Querying Logs

### View Recent Logs
```bash
tail -20 logs/app.$(date +%Y-%m-%d).jsonl
```

### Pretty Print Logs
```bash
# Install jq first: brew install jq
cat logs/app.*.jsonl | jq '.'

# Or use Python
cat logs/app.*.jsonl | while read line; do echo $line | python3 -m json.tool; done
```

### Filter by Component
```bash
grep '"component": "ingestor"' logs/*.jsonl
```

### Filter by Level
```bash
grep '"level": "ERROR"' logs/*.jsonl
```

### Filter by Trace ID
```bash
grep '"trace_id": "a1b2c3d4"' logs/*.jsonl
```

### Search for Errors
```bash
grep '"level": "ERROR"' logs/*.jsonl | tail -10
```

### Count Operations
```bash
# Count searches today
grep '"action": "search"' logs/app.$(date +%Y-%m-%d).jsonl | wc -l

# Count errors
grep '"level": "ERROR"' logs/*.jsonl | wc -l
```

---

## Log Analysis Scripts

### Simple Stats Script

Create `scripts/log_stats.py`:
```python
#!/usr/bin/env python3
import json
import sys
from collections import Counter

def analyze_logs(filename):
    levels = Counter()
    components = Counter()
    actions = Counter()
    latencies = []

    with open(filename) as f:
        for line in f:
            try:
                log = json.loads(line)
                levels[log.get('level')] += 1
                components[log.get('component')] += 1
                actions[log.get('action')] += 1
                if 'latency_ms' in log:
                    latencies.append(log['latency_ms'])
            except:
                pass

    print("=== Log Statistics ===")
    print(f"\nLevels: {dict(levels)}")
    print(f"Components: {dict(components)}")
    print(f"Actions: {dict(actions)}")
    if latencies:
        print(f"\nLatency (ms):")
        print(f"  Avg: {sum(latencies)/len(latencies):.1f}")
        print(f"  Min: {min(latencies)}")
        print(f"  Max: {max(latencies)}")

if __name__ == "__main__":
    analyze_logs(sys.argv[1])
```

**Usage:**
```bash
python3 scripts/log_stats.py logs/app.2025-11-08.jsonl
```

---

## Log Retention

**Default:** Logs kept indefinitely

**Manual Cleanup:**
```bash
# Remove logs older than 30 days
find logs/ -name "app.*.jsonl" -mtime +30 -delete

# Archive old logs
tar -czf logs-archive-$(date +%Y%m).tar.gz logs/app.2025-*.jsonl
rm logs/app.2025-*.jsonl
```

**Automated Cleanup:**
Add to crontab:
```bash
# Monthly log cleanup
0 0 1 * * find /path/to/brain/logs -name "app.*.jsonl" -mtime +90 -delete
```

---

## Integration with Monitoring Tools

### Splunk
```bash
# Forward logs to Splunk
tail -f logs/app.*.jsonl | splunk-forwarder
```

### Elasticsearch
```python
# Ingest logs to Elasticsearch
from elasticsearch import Elasticsearch
import json

es = Elasticsearch(['localhost:9200'])

with open('logs/app.2025-11-08.jsonl') as f:
    for line in f:
        log = json.loads(line)
        es.index(index='brain-logs', document=log)
```

### Grafana Loki
```yaml
# promtail config
clients:
  - url: http://localhost:3100/loki/api/v1/push

scrape_configs:
  - job_name: brain
    static_configs:
      - targets:
          - localhost
        labels:
          job: brain
          __path__: /path/to/brain/logs/app.*.jsonl
```

---

## Best Practices

1. **Keep logs for at least 30 days** for debugging
2. **Monitor ERROR level logs** regularly
3. **Use trace_id** to correlate operations
4. **Archive old logs** to save space
5. **Redact sensitive data** via config
6. **Monitor latency_ms** for performance issues
7. **Set up alerts** for critical errors

---

## Example Queries

### Find slow operations (>1000ms)
```bash
grep '"latency_ms"' logs/*.jsonl | awk -F'"latency_ms": ' '{print $2}' | \
  awk -F',' '{if($1 > 1000) print $1}'
```

### Count operations by hour
```bash
cat logs/app.*.jsonl | jq -r '.ts[11:13]' | sort | uniq -c
```

### Find failed ingestions
```bash
grep '"action": "ingest_skip"' logs/*.jsonl | jq '{ts, path, err}'
```

### Track backup operations
```bash
grep '"action": "backup"' logs/*.jsonl | jq '{ts, msg}'
```

---

**Last Updated:** 2025-11-08
