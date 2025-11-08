# AI Brain Vault

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](https://github.com/ocristaldo/ai-brain/releases)

**Your AI-powered second brain, designed for Claude Code.**

Local-first knowledge management system with hybrid search. Store notes in Markdown, let Claude Code access and organize your knowledge through natural conversation.

> **Primary Interface: Claude Code CLI** - Talk to your brain naturally. Claude Code handles all the searching, organizing, and retrieval for you.

## ⚡ Quick Start with Claude Code

```bash
# 1. Deploy
git clone https://github.com/ocristaldo/ai-brain.git
cd ai-brain
./deploy.sh

# 2. Add to shell (follow deploy.sh output)
export BRAIN_HOME="/path/to/ai-brain"
export PATH="$BRAIN_HOME:$PATH"

# 3. Start using with Claude Code
# Just ask: "Search my brain for Docker notes"
```

That's it! Claude Code can now access your brain.

> **Heads up:** All helper scripts assume `.venv/` exists. If you skip `./deploy.sh`, create it manually:
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> pip install -r requirements.txt
> ```
> 
> Running `make` with no arguments now prints a help menu instead of reinitializing anything—use explicit targets (e.g., `make search q="..."`).

**See [CLAUDE_CODE_INTEGRATION.md](CLAUDE_CODE_INTEGRATION.md) for complete setup.**

## 🧹 One-Command Delete

```bash
# Clean generated files (keeps notes and source)
./delete.sh

# Full delete (removes everything)
./delete.sh --full
```

## Primary Use: Claude Code

This brain is designed to work seamlessly with **Claude Code CLI**. You can:
- Search your knowledge by asking Claude
- Add information through natural conversation
- Let Claude organize and tag your notes
- Retrieve context from past notes automatically

**Setup:** [CLAUDE_CODE_INTEGRATION.md](CLAUDE_CODE_INTEGRATION.md)
**Agent Rules:** [CLAUDE_CODE_RULES.md](CLAUDE_CODE_RULES.md)
**For Developers:** [AGENT_INSTRUCTIONS.md](AGENT_INSTRUCTIONS.md)

## Alternative: Manual CLI Use

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make init
# add your .md files to notes/
make ingest
make search q="search term"
make backup
```

## Features

- **Smart Backups**: Only creates backups when changes detected, keeps 15 days or 15 backups minimum
- **Hybrid Search**: Full-text search (FTS5) + faceted filtering
- **Agent Output Modes**: `--format json` or `--format full` for machine-readable or narrative results
- **Safe Pruning**: `--prune-missing` cleans DB entries when the source Markdown is deleted (with confirmation)
- **Structured Logging**: JSONL format with trace_id and latency tracking
- **Audit Trail**: All operations logged to change_log table
- **Health Checks**: Data integrity validation with `make health`
- **Status Snapshot**: `make status [JSON=1]` prints item/tag/domain counts and last update
- **Docs for Everything**: See `docs/` (especially `docs/STRUCTURE.md` for layout)

## Sample Obsidian Layout

The repository ships with an opinionated structure under `notes/` so you can drop it straight into an Obsidian vault:

```
notes/
├─ ideas/              # Brainstorms (e.g., example_idea.md)
├─ projects/           # Active initiatives (e.g., example_project.md)
├─ notes/              # Templates & references (e.g., second_brain_overview.md)
└─ ai_memory/          # Agent-specific memories (e.g., multi_agent_memory_template.md)
```

- `notes/notes/second_brain_overview.md` → high-level system template.
- `notes/ai_memory/multi_agent_memory_template.md` → blueprint for storing per-agent memories so Claude/other agents can reference or sync their own behavior settings.

## Available Scripts (for Claude Code)

**Search & Read:**
- `brain_search.sh --q "term" --format json` - Search notes (JSON/table/full)
- `brain_read.sh <id>` - Read specific note
- `brain_list.sh [filters]` - List notes
- `brain_tags.sh [tag]` - View/filter by tags

**Create & Update:**
- `brain_add.sh --title "Title" --domain work --type project --content "Body"` - Add note (supports visibility/status/tags)
- `brain_update.sh <id> [--status] [--tags]` - Update metadata

**System:**
- `make ingest` - Ingest notes after manual edits
- `make sync` - Ingest + prune missing files and rebuild FTS index (interactive; add `YES=1` to auto-confirm)
- `make status` - Show counts/metrics (add `JSON=1` for machine-readable output)
- `make dedupe` - Detect (and optionally delete) duplicate DB rows (set `APPLY=1 YES=1` to remove)
- `make health` - System health check
- `make backup` - Create backup
- `make reset` - Remove DB/logs/backups (keeps notes; run `make init` + `make ingest` afterwards)
- `make test` - Run test suite + coverage (report saved to `logs/test_reports/latest-test-report.md`)

**Claude Code uses these automatically when you talk to it.**

> Scripts are committed with executable bits. If your tooling strips permissions, run `chmod +x brain_*.sh` once after cloning.

## Testing

```bash
source .venv/bin/activate
make test
```

This command runs `pytest` with coverage via `scripts/run_tests.py` and stores the latest report under `logs/test_reports/` (both timestamped and `latest-test-report.md`). Share those logs when reporting issues.

---

## FAQ

### How do I access the brain to see what information is stored?

Use the search command:

```bash
# Search for specific terms
make search q="kubernetes"

# Search with filters
make search q="eks" d=work t=project

# Search by tags
make search q="" tags="kubernetes,monitoring"

# List all items (no query) with JSON output
make search format=json
```

`scripts/search.py` supports multiple output modes:

| Mode | When to use | Example |
|------|-------------|---------|
| `table` (default) | Quick human scans | `make search q="eks"` |
| `json` | Claude/agent tooling | `make search format=json body=1 q="kubernetes"` |
| `full` | Need markdown content inline | `make search q="idea" format=full` |

Set `body=1` to include markdown content in JSON responses.

### How do I access the logs?

Logs are stored in JSONL format (one JSON object per line):

```bash
# View recent logs
tail -20 logs/app.2025-11-08.jsonl

# View logs in readable format
cat logs/app.2025-11-08.jsonl | python3 -m json.tool

# Search logs for specific component
grep '"component": "ingestor"' logs/*.jsonl

# View async backup logs
cat logs/backup_async.log
```

Each log entry includes:
- `ts` - Timestamp
- `level` - Log level (INFO, WARN, ERROR)
- `component` - Which script generated the log
- `action` - What action was performed
- `trace_id` - Unique ID for operation tracking
- `latency_ms` - How long the operation took
- `device_id` - Which device performed the operation

### How does the background backup system work?

**Performance First**: Backups never block normal operations!

- Every time you access the brain (search, ingest), it checks if a daily backup exists
- If no backup today, it triggers one **in the background** (non-blocking)
- Your search/ingest continues immediately without waiting
- Backup runs asynchronously and completes separately
- Only creates backup if changes detected since last one
- Keeps 15 days OR minimum 15 backups (whichever is more)

**Manual backup:**
```bash
make backup  # Force backup now (still respects change detection)
```

**Scheduled backup (recommended):**
```bash
# Add to crontab for daily backup at 2 AM
0 2 * * * cd /path/to/brain && source .venv/bin/activate && make backup
```

### How do I integrate with Claude Code as an AI assistant?

Helper scripts are already committed (`brain_search.sh`, `brain_add.sh`, `brain_read.sh`, `brain_list.sh`, `brain_tags.sh`, `brain_update.sh`). Point Claude Code at the project directory and call them directly. Examples:

```bash
# JSON search with markdown bodies
brain_search.sh --q "kubernetes" --format json --include-body

# Add a note with extra metadata and tags
brain_add.sh --title "Vector DB Plan" \
             --domain work \
             --type project \
             --visibility private \
             --tags "ai,milestone" \
             --content "Outline milestones for vector DB adoption."
```

### How do I remove DB entries for notes deleted in Obsidian?

Use the new prune mode to keep the SQLite DB in sync with your vault:

```bash
# Interactively ingest + prune missing files
make sync

# Non-interactive (e.g., CI/cron)
make sync YES=1
```

The script lists how many DB rows will be removed, writes a summary to stdout, and records each deletion in `change_log`.

### How do I check the database status?

```bash
# Human-friendly table
make status

# JSON output for agents/dashboards
make status JSON=1
```

The status command reports total items, tags, embeddings, change-log entries, and breakdowns by domain/type/visibility along with the last updated timestamp.

### How is the repo organized?

See `docs/STRUCTURE.md` for a high-level map. In short:
- `phase1/ai-brain-phase1/` – Source code + CLI (the part you publish)
- `phase1/ai-brain-planning/` – Private planning vault that mirrors the same structure (`notes/`, `roadmap/`, `releases/`); remove it before pushing to GitHub if you don’t want planning docs public.

### How do I clean up duplicates?

```bash
# Inspect duplicates (dry-run)
make dedupe

# Delete duplicates (non-interactive)
make dedupe APPLY=1 YES=1
```

Run this once if you have legacy data created before source-uri uniqueness existed. Afterwards, `make init` can create the unique index and `make sync` will keep things tidy.

Claude Code can then execute:
```bash
./brain_search.sh --q "kubernetes" --domain work
```

**Option 2: MCP Server (Model Context Protocol) - Recommended**

For seamless integration with Claude Desktop/Code:

**1. Create `mcp_server.py`:**
```python
#!/usr/bin/env python3
"""
MCP Server for AI Brain integration with Claude
Provides search, add, and query capabilities
"""
import json
import sys
from scripts.search import main as search_main
from scripts.ingest import main as ingest_main

# See docs/mcp_integration.md for full implementation
```

**2. Configure Claude Code:**

Add to your Claude configuration (`~/.claude/config.json`):
```json
{
  "mcpServers": {
    "brain": {
      "command": "python3",
      "args": ["/path/to/ai-brain/mcp_server.py"],
      "env": {
        "BRAIN_DIR": "/path/to/ai-brain"
      }
    }
  }
}
```

**3. Use natural language with Claude:**
```
"Search my brain for all project ideas about automation"
"Add a note to my brain: title 'Docker optimization' type 'idea'"
"What notes do I have about kubernetes monitoring?"
```

Claude will automatically use your brain as a knowledge source!

**Option 3: Simple Alias Integration**

Add to your shell profile (`~/.bashrc` or `~/.zshrc`):

```bash
# AI Brain shortcuts
export BRAIN_HOME="/path/to/ai-brain"

brain-search() {
    (cd "$BRAIN_HOME" && source .venv/bin/activate && python3 scripts/search.py --q "$*")
}

brain-add() {
    # Quick note creation
    local title="$1"
    shift
    local content="$*"
    (cd "$BRAIN_HOME" && source .venv/bin/activate && \
     echo "Creating note: $title" && \
     cat > "notes/${title//[^a-zA-Z0-9]/_}.md" <<EOF
---
title: $title
domain: personal
visibility: private
type: note
status: inbox
tags: []
---
$content
EOF
     python3 scripts/ingest.py)
}

brain-health() {
    (cd "$BRAIN_HOME" && source .venv/bin/activate && make health)
}
```

Then use from anywhere:
```bash
brain-search "kubernetes monitoring"
brain-add "Quick idea" "Use AI to analyze logs automatically"
brain-health
```

See GitHub milestones for advanced integration features (coming in future versions).

### How do I view what's in the database directly?

```bash
# Activate virtual environment
source .venv/bin/activate

# Count items
sqlite3 db/brain.sqlite "SELECT COUNT(*) FROM item"

# List all items
sqlite3 db/brain.sqlite "SELECT title, domain, type FROM item" -header

# View recent changes
sqlite3 db/brain.sqlite "SELECT at, action, item_id FROM change_log ORDER BY id DESC LIMIT 10" -header

# View all tags
sqlite3 db/brain.sqlite "SELECT tag FROM tag ORDER BY tag"

# View health status
cat var/health.json
```

### How do I add notes to the brain?

Notes are markdown files with YAML frontmatter:

```bash
# Create a note in notes/ directory
cat > notes/my_idea.md <<'EOF'
---
title: My Great Idea
domain: personal
visibility: private
type: idea
status: inbox
tags: [innovation, productivity]
---
This is my great idea about...
EOF

# Ingest it
make ingest

# Search for it
make search q="great idea"
```

**Required frontmatter fields:**
- `title` - Note title
- `domain` - `work`, `personal`, or `hobbies`
- `visibility` - `public`, `private`, or `secret`
- `type` - `idea`, `project`, `note`, `memory`, `quote`, `doc`, or `task`
- `status` - `inbox`, `active`, or `archived`
- `tags` - Array of strings (optional but recommended)

### How do I backup and restore?

```bash
# Backup (only if changes detected)
make backup

# List backups
ls -lh backups/

# Restore (dry-run first)
make restore file=backups/brain-20251108-141235.tgz

# Apply restore (after reviewing dry-run)
CONFIRM=1 make restore file=backups/brain-20251108-141235.tgz
```

### How do I check system health?

```bash
# Check health (read-only)
make health

# View health status
cat var/health.json

# Reindex FTS if needed (auto-fixes issues)
python3 scripts/reindex_fts.py
```

### Performance tips?

- **Searches are fast**: Sub-10ms for typical queries
- **Backups are async**: Never block normal operations
- **Batch your ingests**: Better to ingest multiple notes at once
- **Use filters**: More specific searches are faster
- **Check health regularly**: `make health` to catch issues early

### What files should I backup externally?

The backup system handles everything, but for external backup:
- `db/brain.sqlite` - Your data
- `notes/` - Your markdown files
- `config.yaml` - Your configuration
- `backups/` - Your backup archives (optional)

**Don't backup:**
- `logs/` - Regenerated
- `var/` - Runtime state
- `.venv/` - Virtual environment (reinstall with `pip install -r requirements.txt`)

### How do I migrate to a new machine?

```bash
# On old machine
make backup

# Copy to new machine
scp backups/brain-20251108-141235.tgz newmachine:/path/

# On new machine
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make init
CONFIRM=1 make restore file=backups/brain-20251108-141235.tgz
```
