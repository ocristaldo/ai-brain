---
title: Second Brain Overview Template
domain: personal
visibility: public
type: doc
status: active
tags: [template, secondbrain, ai]
---

# AI Brain Vault Overview

Use this note as a starting point for every new vault. It summarizes what the AI Brain does, where to find things, and how agents should interact with it.

## What This Vault Does
- Local-first, Markdown + SQLite knowledge base
- CLI-driven workflow (`make init|ingest|search|backup|status`)
- Agent-friendly outputs (JSON search results, structured logs, dedupe/sync helpers)
- Async backups plus audit trail for every action

## Where Things Live
| Folder | Purpose |
|--------|---------|
| `notes/ideas/` | Brainstorms, half-baked thoughts |
| `notes/projects/` | Active initiatives with outcomes, timelines |
| `notes/notes/` | Docs, references, templates (this file) |
| `scripts/` | CLI tools (`ingest.py`, `search.py`, `status.py`, `dedupe.py`, etc.) |
| `docs/` | Architecture, troubleshooting, structure map |

> Planning artifacts live in `phase1/ai-brain-planning/` (keep private). Production code and notes live in `phase1/ai-brain-phase1/`.

## Basic Usage Cheat Sheet
```bash
# Activate environment
source .venv/bin/activate

# Sync filesystem → DB (ingest + prune)
make sync

# Search (JSON output for agents)
make search q="topic" format=json body=1

# Snapshot status (counts, last update)
make status JSON=1

# Clean legacy duplicates
make dedupe          # dry-run
make dedupe APPLY=1 YES=1

# Backup (also runs verify)
make backup
```

## AI Assistant Playbook
1. **Search first**: `make search q="keyword" format=json body=1`
2. **Read full note**: `brain_read.sh <id>` or open the markdown path from `source_uri`
3. **Update**: edit markdown → `make sync`
4. **Add**: `brain_add.sh --title "..." --domain work --type project --content "..."`
5. **Summarize**: log results back into `notes/notes/` as decision records or templates

## Template Checklist for New Notes
- [ ] Accurate frontmatter (`title`, `domain`, `visibility`, `type`, `status`, `tags`)
- [ ] Links to related items (`source_uri` references)
- [ ] `Last updated` section with timestamp and author/agent
- [ ] Next steps / open questions block

```
Checklist Example:
- Context: <why this matters>
- Facts learned: <bullets>
- Decisions: <bullets>
- Next actions: <bullets>
```

Keep this template updated whenever the README changes so future imports stay in sync.
