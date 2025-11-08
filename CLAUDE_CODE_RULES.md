# Claude Code - AI Brain Interaction Rules

**IMPORTANT:** This document defines strict boundaries for AI agents interacting with the AI Brain system. Follow these rules to maintain data integrity and security.

---

## 🔒 Security Boundaries

### ✅ ALLOWED Operations

#### 1. Read/Write Markdown Files in notes/
```bash
# You CAN:
- Read any .md file in notes/
- Create new .md files in notes/
- Edit existing .md files in notes/
- Delete .md files in notes/ (with user confirmation)
```

**Example:**
```bash
# Read a note
cat notes/kubernetes_setup.md

# Create a note
cat > notes/new_idea.md <<'EOF'
---
title: New Idea
domain: personal
visibility: private
type: idea
status: inbox
tags: [automation]
---
Content here...
EOF

# Edit a note
vim notes/kubernetes_setup.md
```

#### 2. Execute Brain Scripts
```bash
# You CAN execute these scripts:
./brain_search.sh       # Search for notes
./brain_add.sh          # Add new note
./brain_read.sh         # Read specific note
./brain_list.sh         # List notes with filters
./brain_update.sh       # Update note metadata
./brain_tags.sh         # Manage tags
make ingest             # Ingest notes into DB
make search             # Search notes
make health             # Check system health
make backup             # Create backup
```

#### 3. Read Configuration
```bash
# You CAN read:
- config.yaml (for brain location, settings)
- .gitignore
- Documentation files (README.md, etc.)
```

---

### ❌ FORBIDDEN Operations

#### 1. Direct Database Access
```bash
# You CANNOT:
- sqlite3 db/brain.sqlite
- Direct SQL queries
- Modify db/ directory
- Delete database files
- Edit db/brain.sqlite directly
```

**Why:** Database integrity must be maintained through proper scripts only.

**Instead:** Use brain_*.sh scripts that handle DB operations safely.

#### 2. Modify Core Scripts
```bash
# You CANNOT modify:
- scripts/*.py (Python scripts)
- Makefile
- deploy.sh
- delete.sh
- brain_*.sh (shell scripts)
```

**Why:** Code changes could break the system or introduce security issues.

**Instead:** Suggest changes to user, who can review and apply them.

#### 3. Access Generated Files
```bash
# You CANNOT modify:
- logs/ (read-only for debugging)
- var/ (system state)
- backups/ (read-only for restore)
- .venv/ (Python virtual environment)
```

**Why:** These are system-managed files.

---

## 📋 Mandatory Workflow for Note Operations

### Creating a New Note

**Step 1:** Use the helper script (recommended)
```bash
./brain_add.sh "Note Title" domain type "Content..."
```

**Step 2:** Alternative - Create markdown file
```bash
cat > notes/my_note.md <<'EOF'
---
title: My Note
domain: personal
visibility: private
type: note
status: inbox
tags: []
---
Content here...
EOF

# Then ingest
make ingest
```

**✅ Allowed:** Both methods
**❌ Forbidden:** Directly inserting into database

---

### Searching for Information

**Step 1:** Use search script
```bash
./brain_search.sh --q "kubernetes"
```

**Step 2:** Parse results from stdout

**✅ Allowed:** Using brain_search.sh
**❌ Forbidden:** Direct SQL queries

---

### Reading a Note

**Step 1:** Find the note
```bash
./brain_read.sh "kubernetes"
```

**Step 2:** Get file path from output

**Step 3:** Read the markdown file
```bash
cat notes/kubernetes_setup.md
```

**✅ Allowed:** Reading markdown files
**❌ Forbidden:** Reading from database directly

---

### Updating a Note

**Option 1: Update content**
```bash
# 1. Find the note
./brain_read.sh "kubernetes"

# 2. Edit the markdown file
vim notes/kubernetes_setup.md

# 3. Ingest changes
make ingest
```

**Option 2: Update metadata only**
```bash
./brain_update.sh "kubernetes" --status active --tags "devops,k8s"
```

**✅ Allowed:** Editing markdown files + running ingest
**❌ Forbidden:** Direct database UPDATE commands

---

## 🎯 Decision Tree for Agent Operations

```
User wants to interact with brain
    ↓
What operation?
    ↓
┌─────────────┬──────────────┬──────────────┬──────────────┐
│   SEARCH    │     ADD      │    UPDATE    │     READ     │
└─────────────┴──────────────┴──────────────┴──────────────┘
      ↓              ↓              ↓              ↓
brain_search.sh  brain_add.sh   Edit .md file  brain_read.sh
                                    +
                                make ingest
```

---

## 🛡️ Safety Checklist

Before executing ANY command, verify:

- [ ] Am I modifying only .md files in notes/?
- [ ] Am I using approved brain_*.sh scripts?
- [ ] Am I NOT accessing db/ directly?
- [ ] Am I NOT modifying scripts/ files?
- [ ] Am I running make ingest after .md changes?
- [ ] Have I confirmed destructive operations with user?

---

## 📝 File Modification Rules

### notes/ Directory

**You CAN:**
- ✅ Create new .md files
- ✅ Edit existing .md files
- ✅ Read .md files
- ✅ Delete .md files (with confirmation)

**Required frontmatter:**
```yaml
---
title: Required
domain: work|personal|hobbies (required)
visibility: public|private|secret (required)
type: idea|project|note|memory|quote|doc|task (required)
status: inbox|active|archived (required)
tags: [] (optional)
---
```

**After any .md modification:**
```bash
make ingest  # ALWAYS run this after modifying .md files
```

---

### Other Directories

**logs/** - Read only for debugging
```bash
# OK:
tail logs/app.*.jsonl
grep "error" logs/app.*.jsonl

# NOT OK:
echo "..." > logs/app.jsonl
rm logs/*
```

**db/** - No direct access
```bash
# NOT OK:
sqlite3 db/brain.sqlite "..."
rm db/brain.sqlite

# OK - use scripts instead:
./brain_search.sh --q "term"
```

**scripts/** - Read only
```bash
# OK:
cat scripts/search.py

# NOT OK:
vim scripts/search.py
```

---

## 🚨 Error Handling

### If ingestion fails:
```bash
# Check logs
grep "ingest_skip" logs/app.*.jsonl

# Common issues:
# - Invalid frontmatter → Fix YAML syntax
# - Invalid facet values → Check domain/type/visibility
# - Missing required fields → Add title, domain, etc.
```

### If search returns no results:
```bash
# Verify notes are ingested
make health

# Try broader search
./brain_search.sh --q ""

# Check specific filters
./brain_list.sh --domain work
```

### If scripts fail:
```bash
# Check brain is initialized
make health

# Re-initialize if needed
make init

# Restore from backup if database corrupted
make backup  # Creates new backup
# User must manually restore from older backup
```

---

## 🎓 Examples - Correct Usage

### Example 1: User asks "What do I know about Docker?"

**✅ Correct:**
```bash
# 1. Search
./brain_search.sh --q "Docker" --domain work

# 2. If found, read the note
./brain_read.sh <note_id_from_search>

# 3. Return results to user
```

**❌ Wrong:**
```bash
sqlite3 db/brain.sqlite "SELECT * FROM item WHERE title LIKE '%Docker%'"
```

---

### Example 2: User says "Add this to my brain: Docker uses namespaces for isolation"

**✅ Correct:**
```bash
./brain_add.sh "Docker Isolation" work note "Docker uses namespaces for isolation"
```

**❌ Wrong:**
```bash
sqlite3 db/brain.sqlite "INSERT INTO item ..."
```

---

### Example 3: User says "Update my Kubernetes note to mark it as archived"

**✅ Correct:**
```bash
# Option 1: Use update script
./brain_update.sh "kubernetes" --status archived

# Option 2: Edit markdown file
./brain_read.sh "kubernetes"  # Get file path
vim notes/kubernetes_setup.md  # Change status in frontmatter
make ingest
```

**❌ Wrong:**
```bash
sqlite3 db/brain.sqlite "UPDATE item SET status='archived' WHERE ..."
```

---

### Example 4: User asks "Show me all my active projects"

**✅ Correct:**
```bash
./brain_list.sh --type project --status active
```

**❌ Wrong:**
```bash
sqlite3 db/brain.sqlite "SELECT * FROM item WHERE type='project' AND status='active'"
```

---

## 🔍 Debugging Guidelines

### Check System Health
```bash
make health
```

### View Logs
```bash
# Recent logs
tail -20 logs/app.*.jsonl

# Search for errors
grep "ERROR" logs/app.*.jsonl

# Ingest issues
grep "ingest_skip" logs/app.*.jsonl
```

### Verify Note Structure
```bash
# Read a specific note
cat notes/my_note.md

# Validate YAML (using python)
python3 -c "import yaml; yaml.safe_load(open('notes/my_note.md').read().split('---')[1])"
```

---

## ⚡ Quick Reference - Allowed Commands

```bash
# SEARCH
./brain_search.sh --q "term" [--domain D] [--type T] [--tags "t1,t2"]
./brain_read.sh <id_or_term>
./brain_list.sh [--domain D] [--type T] [--status S] [--limit N]
./brain_tags.sh [tag_name]

# CREATE
./brain_add.sh "Title" domain type "Content"
cat > notes/file.md <<'EOF' ... EOF
make ingest

# UPDATE
./brain_update.sh <id> [--status S] [--tags "t1,t2"] [--type T] [--domain D]
vim notes/file.md
make ingest

# READ FILES
cat notes/file.md
less notes/file.md
head notes/file.md

# SYSTEM
make health
make backup
tail logs/app.*.jsonl
```

---

## 🎯 Remember

1. **Always use scripts** for database operations
2. **Only modify .md files** in notes/
3. **Run make ingest** after any .md changes
4. **Never directly access** db/
5. **Never modify** scripts/ or core files
6. **Always verify** frontmatter structure
7. **Confirm destructive** operations with user

---

**These rules ensure data integrity, security, and maintainability of the AI Brain system.**
