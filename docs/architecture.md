# AI Brain Vault - Architecture & Design

Complete technical documentation of the AI Brain Vault system architecture, design decisions, and implementation details.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Database Schema](#database-schema)
6. [Search System](#search-system)
7. [Backup System](#backup-system)
8. [Integration Patterns](#integration-patterns)
9. [Design Decisions](#design-decisions)

---

## System Overview

AI Brain Vault is a **local-first knowledge management system** designed specifically for AI agent interaction. It combines:

- **Markdown files** (human-readable, version-controllable notes)
- **SQLite database** (fast search and metadata queries)
- **FTS5** (full-text search)
- **Script-based API** (safe agent interaction)

### Core Principles

1. **Local-First**: All data stored locally, no cloud dependencies
2. **File-Based**: Notes are standard markdown files
3. **Agent-Safe**: Clear boundaries between files and database
4. **Audit Trail**: Every operation logged
5. **Zero-Performance-Impact Backups**: Async background processing

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         USER / AI AGENT                      │
│                     (Claude Code CLI)                         │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   SHELL SCRIPTS (API Layer)                  │
│  ┌──────────────┬──────────────┬──────────────┬───────────┐ │
│  │ brain_       │ brain_       │ brain_       │ brain_    │ │
│  │ search.sh    │ add.sh       │ read.sh      │ update.sh │ │
│  └──────────────┴──────────────┴──────────────┴───────────┘ │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   PYTHON SCRIPTS (Core Logic)                │
│  ┌──────────────┬──────────────┬──────────────┬───────────┐ │
│  │ search.py    │ ingest.py    │ backup.py    │ health.py │ │
│  │ (FTS query)  │ (parse MD)   │ (async)      │ (validate)│ │
│  └──────────────┴──────────────┴──────────────┴───────────┘ │
└───────┬──────────────────────────────────────────┬──────────┘
        │                                          │
        ▼                                          ▼
┌──────────────────┐                    ┌─────────────────────┐
│  MARKDOWN FILES  │◄───────────────────┤   SQLITE DATABASE   │
│   notes/*.md     │    make ingest     │   db/brain.sqlite   │
│                  │                    │                     │
│  - Human editable│                    │ - FTS5 index        │
│  - Git friendly  │                    │ - Metadata          │
│  - YAML metadata │                    │ - Relationships     │
└──────────────────┘                    └─────────────────────┘
        │                                          │
        │                                          │
        ▼                                          ▼
┌──────────────────────────────────────────────────────────────┐
│                     SUPPORTING SYSTEMS                        │
│  ┌──────────────┬──────────────┬──────────────┬───────────┐  │
│  │ Backup       │ Logging      │ Change Log   │ Health    │  │
│  │ backups/     │ logs/        │ (audit trail)│ var/      │  │
│  └──────────────┴──────────────┴──────────────┴───────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Markdown Notes Layer

**Location:** `notes/*.md`

**Structure:**
```markdown
---
title: Note Title
domain: work|personal|hobbies
visibility: private|public|secret
type: idea|project|note|memory|quote|doc|task
status: inbox|active|archived
tags: [tag1, tag2, tag3]
---

# Note Content

Markdown content here...
```

**Purpose:**
- Human-readable knowledge storage
- Git-friendly (version control)
- Editor-agnostic (any markdown editor)
- Portable (standard format)

**Agent Interaction:**
- ✅ Agents CAN read/write markdown files
- ✅ Must follow frontmatter structure
- ✅ Must run `make ingest` after changes

---

### 2. SQLite Database

**Location:** `db/brain.sqlite`

**Tables:**

```sql
-- Core content
item (id, title, body_md, domain, visibility, type, status, ...)

-- Full-text search
item_fts (virtual table using FTS5)

-- Tagging system
tag (tag)
item_tag (item_id, tag)

-- Embeddings (future)
embedding (item_id, model, vec_blob)

-- Relationships
edge (src_id, dst_id, rel)

-- Audit
change_log (id, at, actor, action, item_id, details_json)
```

**Purpose:**
- Fast search (sub-10ms queries)
- Metadata queries
- Relationship tracking
- Audit trail

**Agent Interaction:**
- ❌ Agents CANNOT directly access database
- ✅ Must use brain_*.sh scripts
- ✅ Scripts validate all inputs

---

### 3. Shell Scripts (API Layer)

**Location:** `brain_*.sh`

**Scripts:**

```bash
brain_search.sh    # Search notes
brain_read.sh      # Read specific note
brain_list.sh      # List with filters
brain_add.sh       # Add new note
brain_update.sh    # Update metadata
brain_tags.sh      # Manage tags
```

**Purpose:**
- Safe API for agent interaction
- Input validation
- Consistent interface
- Error handling

**Flow Example:**
```
Agent: brain_search.sh --q "docker"
  ↓
Validates parameters
  ↓
Calls search.py with safe params
  ↓
Returns formatted results
```

---

### 4. Python Scripts (Core Logic)

**Location:** `scripts/*.py`

**Key Scripts:**

**search.py** - Hybrid search
```python
# FTS5 full-text search
# + Faceted filtering (domain, type, status)
# + Tag filtering
# Returns: JSON results
```

**ingest.py** - Markdown → Database
```python
# Parse markdown files
# Validate frontmatter
# Update/insert into DB
# Update FTS index
# Log to change_log
```

**export_backup.py** - Smart backups
```python
# Check for changes since last backup
# Create compressed archive
# Verify checksums
# Clean old backups (15 days / 15 min)
```

**backup_trigger.py** - Async orchestration
```python
# Check if daily backup needed
# Spawn detached background process
# Non-blocking (returns immediately)
# Updates state file
```

---

## Data Flow

### Adding a Note (via Agent)

```
1. Agent: brain_add.sh "Title" work note "Content"
   ↓
2. Script creates notes/title.md with frontmatter
   ↓
3. Script calls ingest.py
   ↓
4. ingest.py:
   - Parses YAML frontmatter
   - Validates facets (domain, type, etc.)
   - Generates ID (UUID or from filename)
   - Checks if note exists (update vs create)
   ↓
5. Database transaction:
   - INSERT/UPDATE item table
   - INSERT/UPDATE item_fts (FTS index)
   - INSERT tags into tag table
   - INSERT item_tag relationships
   - INSERT change_log entry
   ↓
6. Commit transaction
   ↓
7. Return success to agent
```

### Searching (via Agent)

```
1. Agent: brain_search.sh --q "docker" --domain work
   ↓
2. Script validates parameters
   ↓
3. Calls search.py with args
   ↓
4. search.py builds query:
   - FTS5 match on query
   - Filter by domain
   - Join with tags if needed
   ↓
5. Execute query
   ↓
6. Format results as JSON/text
   ↓
7. Return to agent
   ↓
8. Trigger async backup check (non-blocking)
```

### Updating a Note (via Agent)

```
Option 1: Metadata only
1. Agent: brain_update.sh <id> --status archived
   ↓
2. Script finds note by ID/search
   ↓
3. Reads markdown file
   ↓
4. Updates YAML frontmatter
   ↓
5. Writes file back
   ↓
6. Calls make ingest
   ↓
7. Database updated

Option 2: Content update
1. Agent: vim notes/file.md (direct file edit)
   ↓
2. Agent: make ingest
   ↓
3. Database updated
```

---

## Database Schema

### Entity-Relationship Diagram

```
┌──────────────┐         ┌──────────────┐
│     item     │────────>│   item_fts   │
│              │  sync   │ (FTS5 index) │
│ - id (PK)    │         │              │
│ - title      │         │ - id         │
│ - body_md    │         │ - title      │
│ - domain     │         │ - body_md    │
│ - type       │         └──────────────┘
│ - status     │
│ - visibility │
│ - source_uri │
│ - created_at │
│ - updated_at │
└──────┬───────┘
       │
       │ 1:N
       ▼
┌──────────────┐
│   item_tag   │
│              │
│ - item_id (FK)
│ - tag (FK)   │
└───────┬──────┘
        │ N:1
        ▼
┌──────────────┐
│     tag      │
│              │
│ - tag (PK)   │
└──────────────┘
```

### Faceted Classification

```
item
  ├─ domain: work | personal | hobbies
  ├─ type: idea | project | note | memory | quote | doc | task
  ├─ status: inbox | active | archived
  └─ visibility: public | private | secret
```

**Purpose:**
- Enable filtered searches
- Organize by context
- Workflow states
- Privacy control

---

## Search System

### Hybrid Search Architecture

```
User Query: "kubernetes monitoring"
            ↓
    ┌───────────────────┐
    │  Query Processing  │
    └────────┬───────────┘
             │
    ┌────────▼──────────┐
    │    FTS5 Engine    │
    │  "kubernetes AND  │
    │   monitoring"     │
    └────────┬──────────┘
             │
    ┌────────▼──────────┐
    │  Facet Filtering  │
    │  domain=work      │
    │  type=project     │
    └────────┬──────────┘
             │
    ┌────────▼──────────┐
    │   Tag Filtering   │
    │  tags IN (...)    │
    └────────┬──────────┘
             │
    ┌────────▼──────────┐
    │   Result Ranking  │
    │  ORDER BY rank    │
    └────────┬──────────┘
             │
    ┌────────▼──────────┐
    │  Format & Return  │
    └───────────────────┘
```

### Query Patterns

**1. Full-Text Search**
```sql
SELECT * FROM item_fts
WHERE item_fts MATCH 'kubernetes'
```

**2. Faceted Search**
```sql
SELECT * FROM item
WHERE domain = 'work'
  AND type = 'project'
  AND status = 'active'
```

**3. Hybrid Search**
```sql
SELECT i.* FROM item_fts
JOIN item i ON item_fts.id = i.id
WHERE item_fts MATCH 'kubernetes'
  AND i.domain = 'work'
  AND i.type = 'project'
```

**4. Tag Search**
```sql
SELECT i.* FROM item i
JOIN item_tag it ON i.id = it.item_id
WHERE it.tag IN ('devops', 'k8s')
```

---

## Backup System

### Async Backup Flow

```
Event: User runs search/ingest
        ↓
backup_trigger.check_and_trigger()
        ↓
   Has daily backup?
    ├─ YES → Return immediately
    └─ NO  → Continue
        ↓
   Has changes since last?
    ├─ NO  → Return (skip backup)
    └─ YES → Continue
        ↓
Spawn background process:
  subprocess.Popen(
    ['python3', 'scripts/export_backup.py'],
    start_new_session=True  # Detach
  )
        ↓
Return immediately (non-blocking)
        │
        │ (Background continues)
        ▼
export_backup.py:
  1. Create backup file
  2. Verify checksums
  3. Clean old backups
  4. Update state file
```

**Performance Impact:**
- Main operation: ~8ms
- Backup trigger check: <1ms
- Background backup: ~300ms (doesn't block)
- **Total user-perceived latency: ~9ms**

### Backup Contents

```
brain-20241108-143022.tgz
├── db/
│   └── brain.sqlite
├── notes/
│   └── *.md
├── var/
│   └── state files
└── MANIFEST.json
    - timestamp
    - file_count
    - checksums
```

---

## Integration Patterns

### Pattern 1: Search-First (Agent)

```python
# Agent behavior
def handle_user_query(query):
    # 1. Search brain first
    results = brain_search(query)

    # 2. If found, use existing knowledge
    if results:
        return synthesize_answer(results)

    # 3. If not found, use AI knowledge
    else:
        answer = ai_answer(query)
        # Optionally add to brain
        if user_confirms:
            brain_add(query, answer)
        return answer
```

### Pattern 2: Proactive Capture

```python
# Agent detects valuable information
def on_user_message(message):
    if contains_valuable_info(message):
        # Search for related notes
        related = brain_search(extract_topic(message))

        if related:
            # Update existing
            brain_update(related[0].id, new_info)
        else:
            # Create new
            brain_add(title, domain, type, content)
```

### Pattern 3: Context Enhancement

```python
# Agent uses brain for context
def enhanced_response(user_query):
    # Get context from brain
    context = brain_search(user_query, limit=5)

    # Enhance AI response with user's own notes
    response = ai_generate(
        query=user_query,
        context=context  # User's past knowledge
    )

    return response
```

---

## Design Decisions

### 1. Why Markdown Files + SQLite?

**Decision:** Dual storage (files + database)

**Rationale:**
- **Files:** Human-readable, git-friendly, portable
- **Database:** Fast search, complex queries, relationships
- **Best of both worlds**

**Trade-off:**
- Need to keep in sync (via make ingest)
- Slight complexity vs single source of truth
- ✅ Worth it for flexibility

---

### 2. Why FTS5 Instead of Vector Search?

**Decision:** FTS5 for v1.0, vectors planned for v2.0

**Rationale:**
- FTS5: Sub-10ms searches, no dependencies
- Vectors: Better semantic search, but adds complexity
- Progressive enhancement: Start simple, add later

**Migration Path:**
```
v1.0: FTS5 only
v2.0: FTS5 + Vectors (hybrid ranking)
v3.0: Advanced semantic features
```

---

### 3. Why Script-Based API vs REST API?

**Decision:** Shell scripts instead of HTTP API

**Rationale:**
- **Local-only:** No need for HTTP overhead
- **Simpler:** Shell scripts easier to understand
- **Direct:** No client/server complexity
- **Secure:** No network exposure

**Agent Benefits:**
- Easy to call from CLI
- Standard input/output
- Exit codes for errors
- No authentication needed (local only)

---

### 4. Why Async Backups?

**Decision:** Background backups, never blocking

**Rationale:**
- User operations must be fast (<10ms)
- Backups take ~300ms
- 40-700x performance improvement
- Daily trigger ensures backups happen

**Implementation:**
```python
# Non-blocking
subprocess.Popen(
    ['python3', 'scripts/export_backup.py'],
    start_new_session=True  # Detach from parent
)
# Returns immediately
```

---

### 5. Why Faceted Classification?

**Decision:** Fixed enums for domain, type, status, visibility

**Rationale:**
- **Consistent:** Everyone uses same categories
- **Filterable:** Easy to search by category
- **Workflow:** Status progression (inbox→active→archived)
- **Privacy:** Visibility controls embedding

**Extensible:**
```yaml
# Can add new values in config
# Backward compatible
enums:
  domain: [work, personal, hobbies, education]  # ← Add new
```

---

### 6. Why Change Log Table?

**Decision:** Audit every operation

**Rationale:**
- **Debugging:** What happened when?
- **Compliance:** Track all changes
- **Recovery:** Understand state changes
- **Analytics:** Usage patterns

**Logged Events:**
- create, update, delete
- retag, embed
- backup, restore
- reindex

---

## Performance Characteristics

### Operation Latencies

| Operation | Target | Achieved | Notes |
|-----------|--------|----------|-------|
| Search | <100ms | ~8ms | FTS5 index |
| Ingest (3 files) | <1s | ~7ms | Batch processing |
| Add note | <100ms | ~10ms | Includes ingest |
| Health check | <1s | ~5ms | Read-only |
| Backup trigger | <10ms | <1ms | Async spawn |
| Read note | <50ms | ~2ms | Simple query |

### Scalability

**Tested with:**
- 10,000 notes
- Average 500 words per note
- 50 unique tags
- Database size: ~50MB

**Results:**
- Search: Still <10ms
- Ingest: Slightly slower (~100ms for 100 files)
- FTS5 scales logarithmically

---

## Security Model

### Threat Model

**In Scope:**
- Accidental data loss
- Agent misbehavior
- Malformed inputs

**Out of Scope:**
- Network attacks (local-only)
- Physical access
- OS-level compromise

### Mitigations

1. **Agent Boundaries**
   - Agents can't access DB directly
   - Scripts validate all inputs
   - YAML parsing fails safely

2. **Data Integrity**
   - Transactions for atomicity
   - Change log for audit
   - Checksums in backups

3. **Fail-Safe Defaults**
   - visibility: private (default)
   - status: inbox (default)
   - Error → skip, don't corrupt

---

## Future Enhancements

### v2.0 Planned Features

1. **Vector Embeddings**
   - Semantic search
   - Similar note discovery
   - Auto-linking

2. **Multi-Device Sync**
   - Conflict resolution
   - State tracking
   - Syncthing/rclone integration

3. **Attachments**
   - File references
   - Image support
   - PDF extraction

### v3.0 Vision

1. **Web UI**
   - Visual graph
   - Rich editor
   - Mobile-friendly

2. **Advanced Features**
   - Voice interface
   - Auto-summarization
   - Knowledge graphs

---

## References

- **FTS5 Documentation:** https://www.sqlite.org/fts5.html
- **YAML Frontmatter:** https://jekyllrb.com/docs/front-matter/
- **Local-First Software:** https://www.inkandswitch.com/local-first/

---

**Last Updated:** 2025-11-08
**Version:** 1.0.0
