---
title: Multi-Agent Memory Template
domain: personal
visibility: private
type: doc
status: active
tags: [ai-memory, template]
---

# Multi-Agent Memory Template

Use this file as a blueprint for storing AI memories that agents can reference while working in the vault. Each agent should get its own section so their behavior, preferences, and long-term reminders are easy to fetch programmatically.

## Agent Catalog
- `claude_code` – default CLI assistant
d- `task_runner` – automation/scripting agent
- `researcher` – external knowledge gatherer

Add/remove agents as needed.

## Memory Schema
For consistency, keep every memory in the following YAML-like block:
```
- id: <unique-id>
  topic: <short label>
  importance: high | medium | low
  last_updated: YYYY-MM-DD
  details: |
    Paragraph describing the behavior, preference, or fact to remember.
  expires_on: <optional date>
```

## Example Entries
### Claude Code
```
- id: cc-comms-tone
  topic: Communication style
  importance: high
  last_updated: 2025-02-14
  details: |
    Always explain command plans before executing them. Ask for confirmation
    if a destructive action is detected. Summaries should be concise with
    actionable next steps.
```

### Task Runner
```
- id: tr-backup-schedule
  topic: Backups
  importance: medium
  last_updated: 2025-02-14
  details: |
    After any bulk ingest, run `make backup` followed by `make status JSON=1`
    and attach the output to the runbook entry.
```

## Retrieval Guidance
- Store this folder under `notes/ai_memory/` so agents can list available memories via `make search q="" --domain meta --type doc` or direct filesystem reads.
- Prefix filenames with the agent name when committing real memories, e.g., `ai_memory/claude_code-memory.md` or `ai_memory/task_runner-memory.md`.
- Agents should only read notes tagged with their name (or `shared`) to avoid leaking behavior instructions intended for other roles.

## Maintenance Checklist
- [ ] Review each agent’s memory weekly; remove outdated entries.
- [ ] Ensure long-lived facts are mirrored in config or docs if needed.
- [ ] Keep `tags` up to date so search queries can filter by agent (`tags: [ai-memory, claude_code]`).
- [ ] Document new conventions in `docs/STRUCTURE.md`.
