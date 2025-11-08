# Agent Instructions for AI Brain Interaction

This document provides instructions for AI agents (particularly a "brain agent" in a supervisor-agent architecture) to interact with the AI Brain Vault system.

---

## Architecture Overview

```
User → Supervisor Agent → Brain Agent → AI Brain System
                              ↓
                        [Search/Add/Update]
                              ↓
                    Markdown Notes + SQLite DB
```

**Brain Agent Role:**
- Manages all interactions with the AI Brain system
- Searches for relevant information
- Creates and updates notes
- Maintains knowledge organization
- Ensures proper note structure and ingestion

---

## Core Operations

### 1. Search for Information

**When to search:**
- User asks a question that might be in the brain
- Need context from previous notes
- Looking for related ideas or projects
- Retrieving specific information

**How to search:**

```bash
# Basic search (table output)
./brain_search.sh --q "kubernetes"

# Machine-readable output with markdown content
./brain_search.sh --q "deployment" --domain work --type project --format json --include-body

# Search by tags
./brain_search.sh --q "" --tags "devops,automation"

# List all active ideas
./brain_search.sh --q "" --type idea --status active --format json
```

**Output tips:**
- Use `--format json` for Claude Code / automation.
- Add `--include-body` when the agent needs the markdown body inline.
- Use `brain_read.sh <item_id>` to stream the entire note (preferred when editing).

**Search Strategy:**
1. Start with specific keywords
2. If no results, try broader terms
3. Use filters to narrow down (domain, type, tags)
4. Empty query with filters lists all matching items

**Example Agent Workflow:**
```
User: "What do I know about Kubernetes monitoring?"

Agent thought process:
1. Search for "kubernetes monitoring"
2. If few results, search "kubernetes" + filter by tags
3. If still limited, search "monitoring" in work domain
4. Return synthesized results to user
```

---

### 2. Add New Notes

**When to add:**
- User shares new information worth remembering
- Capturing ideas from conversation
- Documenting decisions or findings
- Recording meeting notes or tasks

**How to add:**

```bash
# Using helper script (recommended)
./brain_add.sh \
  --title "Kubernetes Monitoring Setup" \
  --domain work \
  --type project \
  --visibility private \
  --status active \
  --tags "devops,monitoring" \
  --content "Prometheus + Grafana stack, alert rules, dashboards..."

./brain_add.sh \
  --title "AI Agent Architecture Idea" \
  --domain personal \
  --type idea \
  --tags "ai,agent" \
  --content "Supervisor agent with brain/task/research specialists."
```

**Note Structure Requirements:**

The helper script auto-generates frontmatter, but if creating manually:

```yaml
---
title: Your Note Title
domain: work | personal | hobbies
visibility: private | public | secret
type: idea | project | note | memory | quote | doc | task
status: inbox | active | archived
tags: [tag1, tag2, tag3]
---

Your markdown content here...
```

**Content Guidelines:**
- Use clear, descriptive titles
- Include context (what, why, when)
- Use markdown formatting (headers, lists, code blocks)
- Add relevant tags for discoverability
- Link related concepts

---

### 3. Update Existing Notes

**When to update:**
- Adding new information to existing topic
- Project status changes
- Correcting or expanding information
- Archiving completed items

**How to update:**

1. **Search for the note:**
```bash
./brain_search.sh --q "kubernetes monitoring"
```

2. **Note the source_uri from search results**

3. **Edit the markdown file directly:**
```bash
# The note path is in source_uri
vim notes/kubernetes_monitoring_setup.md
```

4. **Ingest changes:**
```bash
cd $BRAIN_HOME
source .venv/bin/activate
make ingest
```

**Alternative - Replace entire note:**
```bash
# Delete old note file
rm notes/old_note.md

# Create new version with same title (will update in DB)
./brain_add.sh "Same Title" work project "Updated content..."
```

**Update Workflow Example:**
```
User: "Update the Kubernetes monitoring note with the Grafana dashboard URL"

Agent:
1. Search for the note: brain_search.sh --q "kubernetes monitoring"
2. Read the note file from source_uri
3. Append new information to markdown
4. Run: cd $BRAIN_HOME && source .venv/bin/activate && make ingest
5. Confirm update to user
```

---

### 4. Ingest Notes

**When to ingest:**
- After creating new notes manually
- After updating existing note files
- After bulk note creation
- Periodically to ensure DB is up-to-date

**How to ingest:**

```bash
cd $BRAIN_HOME
source .venv/bin/activate
make ingest
```

**Output interpretation:**
```
Ingested: 3, skipped: 2
```
- Ingested: New or updated notes successfully processed
- Skipped: Notes with errors or no changes

**Check for errors:**
```bash
grep "ingest_skip" logs/app.*.jsonl
```

**Common skip reasons:**
- Invalid frontmatter (missing required fields)
- Invalid facet values
- Malformed YAML syntax

### 5. Prune Missing Notes

If Obsidian files were deleted or moved outside the ingest process, clean up stale DB rows:

```bash
# Preview deletions and confirm interactively
make ingest PRUNE=1

# Non-interactive (automation / after sync jobs)
make ingest PRUNE=1 YES=1
```

- The command lists how many entries are missing and shows the first 10 before asking for confirmation.
- Each deletion is logged to `change_log` with `reason=missing_source`.
- Use this after large Obsidian reorganizations to keep the DB aligned with the file system.

---

## Agent Decision Tree

### When User Provides Information

```
User provides information
    ↓
Is it worth remembering?
    ↓ YES
Does a related note exist?
    ↓ Search brain
    ↓
Found related note?
    ↓ YES                    ↓ NO
Update existing note    Create new note
    ↓                        ↓
Ingest changes          Auto-ingested by helper script
    ↓                        ↓
Confirm to user         Confirm to user
```

### When User Asks Question

```
User asks question
    ↓
Search brain with keywords
    ↓
Found relevant notes?
    ↓ YES                    ↓ NO
Return synthesized      Inform user + offer to
answer from notes       add new note if they
                        provide information
```

---

## Best Practices for Brain Agent

### 1. Search Before Adding
Always search for existing notes on the topic before creating new ones to avoid duplicates.

### 2. Use Descriptive Titles
Titles should be clear and searchable:
- ✅ "Kubernetes Monitoring with Prometheus and Grafana"
- ❌ "K8s stuff"

### 3. Appropriate Domain Classification
- **work** - Professional, job-related notes
- **personal** - Personal interests, learning
- **hobbies** - Side projects, recreational activities

### 4. Choose Correct Type
- **idea** - Concepts, brainstorming, future possibilities
- **project** - Active or planned projects with goals
- **note** - General information, references, documentation
- **memory** - Important things to remember, decisions
- **quote** - Quotes, snippets, references
- **doc** - Formal documentation
- **task** - Action items, todos

### 5. Use Status Appropriately
- **inbox** - New, unprocessed (default for new notes)
- **active** - Currently relevant, in progress
- **archived** - Historical, completed, reference only

### 6. Tag Generously
Tags improve discoverability:
- Use 3-5 relevant tags per note
- Use consistent tag naming (lowercase, hyphenated)
- Common tags: technology names, methodologies, categories

### 7. Keep Content Structured
```markdown
# Main Topic

## Context
Why this matters, when it was created

## Details
The actual information

## Resources
Links, references, related notes

## Next Steps
Action items, follow-ups
```

---

## Example Agent Interactions

### Scenario 1: User Shares a New Idea

```
User: "I have an idea for using AI agents to automatically organize my notes"

Brain Agent:
1. Identifies this is worth capturing
2. Searches for related notes: brain_search.sh --q "AI agents notes"
3. No existing note found
4. Creates new note:
   ./brain_add.sh "AI-Powered Note Organization" personal idea "
   Use AI agents to automatically:
   - Tag notes based on content
   - Link related notes
   - Suggest note structure
   - Identify gaps in knowledge

   Potential implementation:
   - NLP for content analysis
   - Graph database for relationships
   - Agent workflows for automation
   "
5. Confirms: "I've captured your idea about AI-powered note organization in the brain"
```

### Scenario 2: User Asks About Previous Work

```
User: "What did we decide about the monitoring setup?"

Brain Agent:
1. Searches: brain_search.sh --q "monitoring setup" --domain work
2. Finds note: "Kubernetes Monitoring Setup"
3. Reads content
4. Responds: "According to your notes from [date], you decided to use Prometheus + Grafana for monitoring. The setup includes..."
5. Offers: "Would you like me to read the full details or update this note?"
```

### Scenario 3: Updating Project Status

```
User: "The Kubernetes monitoring project is complete"

Brain Agent:
1. Searches: brain_search.sh --q "kubernetes monitoring" --type project
2. Finds the project note
3. Reads the note file from source_uri
4. Updates frontmatter: status: archived
5. Adds completion note to content
6. Runs: make ingest
7. Confirms: "I've archived the Kubernetes monitoring project. Great work!"
```

### Scenario 4: Research Request

```
User: "Find all my ideas about automation"

Brain Agent:
1. Searches: brain_search.sh --q "automation" --type idea
2. Also searches: brain_search.sh --q "" --tags "automation"
3. Combines results
4. Presents: "I found 5 ideas about automation:
   1. AI-Powered Note Organization
   2. Automated Deployment Pipeline
   3. ...
   Would you like details on any of these?"
```

---

## Error Handling

### Note Creation Failed
```bash
# Check logs
grep "ingest_skip" logs/app.*.jsonl

# Common fixes:
# - Verify frontmatter syntax
# - Check domain/type/visibility values
# - Ensure all required fields present
```

### Search Returns No Results
```bash
# Strategy:
1. Try broader search terms
2. Search without filters
3. Check if notes were ingested: make health
4. List all notes: brain_search.sh --q ""
```

### Ingest Skips Notes
```bash
# Debug:
1. Check the note's frontmatter
2. Verify YAML syntax
3. Ensure valid facet values
4. Fix and re-run: make ingest
```

---

## Agent Responsibilities

### Daily Operations
1. **Search** - Find information for user queries
2. **Add** - Capture new information as notes
3. **Update** - Keep notes current and accurate
4. **Organize** - Ensure proper tagging and classification

### Maintenance
1. **Health Check** - Periodically run `make health`
2. **Backup Verification** - Check `backups/` directory exists
3. **Log Monitoring** - Review logs for errors

### Quality Assurance
1. **Avoid Duplicates** - Always search before creating
2. **Consistent Structure** - Follow note templates
3. **Proper Classification** - Use correct domain/type/status
4. **Rich Metadata** - Include comprehensive tags

---

## Integration with Supervisor Agent

### Communication Protocol

**Brain Agent receives:**
- `search(query, filters)` - Search for information
- `add(title, domain, type, content, tags)` - Create new note
- `update(note_id, new_content)` - Update existing note
- `list(type, status, domain)` - List notes by criteria
- `health()` - Check system health

**Brain Agent returns:**
- Search results with relevance
- Confirmation of additions/updates
- Lists of notes
- Health status

### Example Supervisor → Brain Agent Flow

```
Supervisor receives: "What do I know about Docker?"
    ↓
Supervisor: brain_agent.search("Docker", domain="work")
    ↓
Brain Agent:
    1. Execute: brain_search.sh --q "Docker" --domain work
    2. Parse results
    3. Return formatted response
    ↓
Supervisor: Synthesize and present to user
```

---

## Quick Reference

### Search Commands
```bash
# Basic search
./brain_search.sh --q "search term"

# Filtered search
./brain_search.sh --q "term" --domain work --type project

# Tag search
./brain_search.sh --q "" --tags "tag1,tag2"

# List all active items
./brain_search.sh --q "" --status active
```

### Add Commands
```bash
# Add note
./brain_add.sh "Title" domain type "Content"

# Examples
./brain_add.sh "Meeting Notes" work note "Content..."
./brain_add.sh "Project Idea" personal idea "Content..."
./brain_add.sh "Important Decision" work memory "Content..."
```

### Maintenance Commands
```bash
# Ingest notes
cd $BRAIN_HOME && source .venv/bin/activate && make ingest

# Health check
cd $BRAIN_HOME && source .venv/bin/activate && make health

# Manual backup
cd $BRAIN_HOME && source .venv/bin/activate && make backup
```

---

## Environment Setup for Agent

```bash
# Set brain home directory
export BRAIN_HOME="/path/to/ai-brain"

# Helper functions for agent
brain_search() {
    $BRAIN_HOME/brain_search.sh "$@"
}

brain_add() {
    $BRAIN_HOME/brain_add.sh "$@"
}

brain_ingest() {
    (cd $BRAIN_HOME && source .venv/bin/activate && make ingest)
}

brain_health() {
    (cd $BRAIN_HOME && source .venv/bin/activate && make health)
}
```

---

## Success Criteria

Your brain agent is working well when:

1. ✅ Searches return relevant results quickly
2. ✅ New notes are properly structured and tagged
3. ✅ Updates are applied correctly
4. ✅ No duplicate notes are created
5. ✅ Health checks pass consistently
6. ✅ Backups are created automatically
7. ✅ User can retrieve any saved information

---

**Remember:** The brain agent is the guardian of the user's knowledge. Treat every note as valuable, maintain organization, and ensure nothing is lost.
