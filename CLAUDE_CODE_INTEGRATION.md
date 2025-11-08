# Claude Code Integration Guide

Complete guide for using AI Brain Vault with Claude Code CLI as the primary interface.

---

## Quick Setup (2 minutes)

### 1. Deploy the Brain

```bash
git clone https://github.com/ocristaldo/ai-brain.git
cd ai-brain
./deploy.sh
```

### 2. Add to Shell Profile

Add to `~/.bashrc` or `~/.zshrc`:

```bash
export BRAIN_HOME="/path/to/ai-brain"
export PATH="$BRAIN_HOME:$PATH"

# Aliases for convenience
alias brain='cd $BRAIN_HOME'
```

Reload shell:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

### 3. Start Using with Claude Code

Open Claude Code and start asking:

```
"Search my brain for notes about Docker"
"Add this to my brain: Docker networking uses bridge mode by default"
"List all my active projects"
"Show me ideas tagged with automation"
```

**That's it!** Claude Code will use the brain scripts automatically.

---

## How It Works

### Architecture

```
User Types → Claude Code CLI → Executes brain_*.sh → SQLite DB
                    ↓                                      ↑
              Reads/Writes .md                         Queries
                    ↓                                      ↓
              notes/*.md ←──────── make ingest ───────────┘
```

### Key Principles

1. **Claude Code has file system access** via CLI
2. **Agent can read/write markdown files** in notes/
3. **Agent uses scripts for DB operations** (never direct SQL)
4. **Automatic ingestion** after markdown changes
5. **Search-first approach** to avoid duplicates

---

## Available Commands for Claude Code

### Search Commands

```bash
# Basic search
brain_search.sh --q "kubernetes"

# Filtered search
brain_search.sh --q "deployment" --domain work --type project

# Tag search
brain_search.sh --q "" --tags "devops,automation"

# List by criteria
brain_list.sh --type idea --status active
brain_list.sh --domain work --limit 10
```

### Read Commands

```bash
# Read specific note
brain_read.sh "kubernetes"
brain_read.sh abc123def  # By ID

# Read markdown file directly
cat notes/my_note.md
```

### Create Commands

```bash
# Quick add
brain_add.sh "Note Title" work note "Content here"

# Create markdown file
cat > notes/new_note.md <<'EOF'
---
title: New Note
domain: personal
visibility: private
type: idea
status: inbox
tags: [tag1, tag2]
---
Content here...
EOF

# Then ingest
make ingest
```

### Update Commands

```bash
# Update metadata
brain_update.sh "kubernetes" --status archived
brain_update.sh "docker-notes" --tags "devops,containers"

# Update content
vim notes/kubernetes.md
make ingest
```

### Management Commands

```bash
# List tags
brain_tags.sh
brain_tags.sh devops  # Notes with this tag

# System health
make health

# Backup
make backup
```

---

## Example Claude Code Conversations

### Conversation 1: Adding Information

**User:** "I just learned that Kubernetes uses etcd for cluster state. Add this to my brain."

**Claude Code executes:**
```bash
brain_search.sh --q "kubernetes etcd"
# (checks for existing notes)

brain_add.sh "Kubernetes Cluster State Management" work note "
Kubernetes uses etcd as its distributed key-value store for maintaining cluster state.

Key points:
- etcd stores all cluster data
- Provides strong consistency
- Supports watch API for change notifications
- Critical component - cluster fails if etcd is down

Best practices:
- Run 3 or 5 etcd instances for HA
- Regular backups essential
- Monitor etcd health closely
"
```

**Claude Code responds:** "I've added a note about Kubernetes etcd to your brain under work notes. I tagged it with 'kubernetes' and 'etcd'."

---

### Conversation 2: Searching for Information

**User:** "What do I know about Docker networking?"

**Claude Code executes:**
```bash
brain_search.sh --q "docker networking" --domain work
```

**Claude Code responds:** "I found 2 notes about Docker networking:

1. 'Docker Network Modes' (2024-10-15)
   - Bridge mode (default)
   - Host mode for performance
   - Overlay for swarm

2. 'Docker Compose Networking' (2024-11-01)
   - Default network creation
   - Custom networks
   - Service discovery

Would you like me to show you the full content of either note?"

---

### Conversation 3: Organizing Notes

**User:** "Show me all my active work projects"

**Claude Code executes:**
```bash
brain_list.sh --type project --status active --domain work
```

**Claude Code responds:** "You have 4 active work projects:

1. Kubernetes Migration (updated 2024-11-05)
2. CI/CD Pipeline Improvement (updated 2024-11-03)
3. Monitoring Stack Upgrade (updated 2024-10-28)
4. API Gateway Implementation (updated 2024-10-25)

Would you like details on any of these?"

---

### Conversation 4: Updating Information

**User:** "Mark the Kubernetes Migration project as archived"

**Claude Code executes:**
```bash
brain_update.sh "Kubernetes Migration" --status archived
```

**Claude Code responds:** "I've archived the 'Kubernetes Migration' project. Great work completing it! The note is now in archived status."

---

## Claude Code Agent Behavior

### What Claude Code CAN Do

✅ **Search the brain** before answering questions
```
User: "What's my Docker setup?"
→ Claude searches brain first
→ Returns information from notes
→ Offers to add new info if user shares it
```

✅ **Capture information proactively**
```
User: "I configured Prometheus with retention of 15 days"
→ Claude recognizes this is worth saving
→ Searches for existing Prometheus notes
→ Updates existing or creates new note
→ Confirms to user
```

✅ **Organize and tag automatically**
```
User: "Add note about Kubernetes monitoring"
→ Claude categorizes as work/project
→ Auto-tags with relevant terms
→ Sets appropriate status
```

✅ **Maintain context across conversations**
```
User: "Remember that Docker issue I mentioned?"
→ Claude searches brain for Docker issues
→ Retrieves previous context
→ Continues conversation with full context
```

### What Claude Code CANNOT Do

❌ **Direct database access**
```
# Never:
sqlite3 db/brain.sqlite "SELECT ..."

# Instead:
brain_search.sh --q "term"
```

❌ **Modify core scripts**
```
# Never:
vim scripts/search.py

# Instead:
Suggest improvements to user
```

❌ **Bypass ingestion**
```
# Never:
cat > notes/note.md
# (without running make ingest)

# Instead:
brain_add.sh "..."
# (which auto-ingests)
```

---

## Safety Features

### 1. Read-Only Database Access
Claude Code never directly modifies the database. All changes go through:
- Markdown files (which Claude can edit)
- Helper scripts (which validate and process)
- Ingestion pipeline (which updates DB safely)

### 2. Validation Pipeline
```
User input → .md file → Validation → DB update
                           ↓
                      (YAML check)
                      (Facet check)
                      (Required fields)
```

### 3. Audit Trail
All operations logged:
```bash
tail logs/app.*.jsonl
# Shows who did what and when
```

### 4. Automatic Backups
```bash
# Daily backups triggered automatically
# Check: ls backups/
```

---

## Advanced Usage

### Multi-Step Workflows

**User:** "Help me organize my Docker notes"

**Claude Code:**
```bash
# 1. Find all Docker notes
brain_search.sh --q "docker"

# 2. Review each note
for id in $(found_ids); do
    brain_read.sh $id
done

# 3. Suggest organization
# "I found 8 Docker notes. I suggest:
#  - Merging duplicates
#  - Tagging by topic (networking, volumes, security)
#  - Archiving old ones
#  Would you like me to proceed?"

# 4. Execute user-approved changes
brain_update.sh $id --tags "docker,networking"
brain_update.sh $old_id --status archived
```

### Research Mode

**User:** "Research Kubernetes best practices and add findings"

**Claude Code:**
```bash
# 1. Check what user already knows
brain_search.sh --q "kubernetes best practices"

# 2. Use web search (Claude's capability)
# <searches web>

# 3. Compare with user's notes
# <identifies gaps>

# 4. Add new findings
brain_add.sh "Kubernetes Best Practices 2024" work doc "
Based on recent research:

1. Resource Limits
   - Always set CPU/memory limits
   - Your note from 2023 confirms this

2. Health Checks (NEW)
   - Liveness probes essential
   - Readiness probes for zero-downtime

3. Security (UPDATED)
   - Pod Security Standards (PSS) replaced PSP
   - Network policies recommended
...
"
```

---

## Troubleshooting

### Issue: Claude Code can't find brain commands

**Solution:**
```bash
# Add brain to PATH
export BRAIN_HOME="/path/to/ai-brain"
export PATH="$BRAIN_HOME:$PATH"
```

### Issue: Ingestion fails

**Solution:**
```bash
# Check logs
grep "ingest_skip" logs/app.*.jsonl

# Common fixes:
# - Fix YAML syntax in .md file
# - Ensure required frontmatter fields
# - Validate facet values
```

### Issue: Search returns no results

**Solution:**
```bash
# Check if notes ingested
make health

# Reindex if needed
python3 scripts/reindex_fts.py

# Verify database has data
brain_list.sh
```

---

## Best Practices

### 1. Search Before Adding
```
Always check if information exists:
brain_search.sh --q "topic"
→ Found? Update existing
→ Not found? Create new
```

### 2. Descriptive Titles
```
✅ "Kubernetes Pod Security Standards 2024"
❌ "K8s stuff"
```

### 3. Rich Tagging
```
✅ tags: [kubernetes, security, pss, best-practices]
❌ tags: [k8s]
```

### 4. Appropriate Status
```
inbox → active → archived
  ↓        ↓         ↓
 new   working   done/ref
```

### 5. Regular Maintenance
```bash
# Weekly: Review inbox
brain_list.sh --status inbox

# Monthly: Archive completed
brain_list.sh --status active
# Review and archive as needed
```

---

## Integration Checklist

- [ ] Brain deployed: `./deploy.sh`
- [ ] Path configured: `export BRAIN_HOME=...`
- [ ] Shell reloaded: `source ~/.zshrc`
- [ ] Test search: `brain_search.sh --q test`
- [ ] Test add: `brain_add.sh "Test" personal note "Testing"`
- [ ] Test list: `brain_list.sh --limit 5`
- [ ] Review rules: Read `CLAUDE_CODE_RULES.md`
- [ ] Claude Code tested: Ask it to search brain

---

## Quick Reference

```bash
# SEARCH & READ
brain_search.sh --q "term" [filters]
brain_read.sh <id_or_term>
brain_list.sh [filters]
brain_tags.sh [tag]

# CREATE & UPDATE
brain_add.sh "Title" domain type "Content"
brain_update.sh <id> [--status] [--tags] [--type]

# MAINTAIN
make ingest        # After manual .md changes
make health        # System check
make backup        # Create backup
tail logs/*.jsonl  # View logs
```

---

**Ready to use! Start asking Claude Code to interact with your brain.**

For detailed agent behavior rules, see [CLAUDE_CODE_RULES.md](CLAUDE_CODE_RULES.md).
