# Quick Start Guide - AI Brain Vault

Get your AI-powered second brain running in under 5 minutes!

---

## 1. Install (30 seconds)

```bash
git clone https://github.com/ocristaldo/ai-brain.git
cd ai-brain
./deploy.sh
```

The deploy script will:
- ✅ Check Python version
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Initialize database
- ✅ Set up configuration
- ✅ Create integration scripts

> Skipping `./deploy.sh`? Create `.venv/` manually with:
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> pip install -r requirements.txt
> ```
>
> Running `make` with no arguments prints a help menu—always pass an explicit target such as `make search q="term"` or `make ingest`.

---

## 2. Add Your First Note (1 minute)

Create a note in the `notes/` directory:

```bash
cat > notes/my_first_note.md <<'EOF'
---
title: My First Note
domain: personal
visibility: private
type: note
status: inbox
tags: [quickstart, test]
---

# Welcome to AI Brain Vault!

This is my first note. I can add:
- Ideas and thoughts
- Project plans
- Meeting notes
- Research findings
- Anything I want to remember!

The AI can search through all my notes and help me find information.
EOF
```

**Ingest the note:**
```bash
source .venv/bin/activate
make ingest
```

You should see: `Ingested: 1, skipped: 0`

> **Tip:** The repo already includes an Obsidian-style layout:
> - `notes/ideas/` – brain dump examples (`example_idea.md`)
> - `notes/projects/` – project stubs (`example_project.md`)
> - `notes/notes/` – templates/reference. Check out `second_brain_overview.md` for a complete summary of the system and AI usage.
> - `notes/ai_memory/` – agent-specific memories. Start with `multi_agent_memory_template.md` and create one note per agent so they can pick up their own context.

---

## 3. Search Your Brain (30 seconds)

**Search for your note (table view):**
```bash
make search q="first note"
```

**Machine-readable output (for agents):**
```bash
make search q="first note" format=json body=1
```

**Other filters:**
```bash
# By domain
make search d=personal

# By type
make search t=note

# By tags
make search tags="quickstart"

# Combined + include markdown body
make search q="welcome" d=personal t=note format=full
```

---

## 4. Link to Obsidian Vault (Optional, 1 minute)

If you use Obsidian for note-taking, you can link your vault to AI Brain:

### Option A: Symlink Obsidian Vault

```bash
# Link your Obsidian vault to notes/
ln -s /path/to/your/ObsidianVault notes/obsidian

# Ingest Obsidian notes
make ingest
```

### Option B: Use Obsidian Vault Directly

**Edit `config.yaml`:**
```yaml
paths:
  notes_dir: /path/to/your/ObsidianVault
  # ... rest of config
```

Then ingest:
```bash
make ingest
```

**Note:** Make sure your Obsidian notes have the required YAML frontmatter (see Section 7).

---

## 5. Integrate as Claude Code Tool (3 minutes)

### Step-by-Step Claude Code Integration

The deployment created helper scripts for Claude Code integration. Here's how to set it up:

**1. Note the paths to the helper scripts:**
```bash
# These were created by deploy.sh
ls -l brain_search.sh brain_add.sh
# If permissions were stripped, run: chmod +x brain_*.sh
```

**2. Add to your shell profile (`~/.bashrc` or `~/.zshrc`):**

```bash
# AI Brain shortcuts
export BRAIN_HOME="/path/to/ai-brain"  # Update this to your actual path
alias brain-search='$BRAIN_HOME/brain_search.sh'
alias brain-add='$BRAIN_HOME/brain_add.sh'
alias brain-health='(cd $BRAIN_HOME && source .venv/bin/activate && make health)'
```

**3. Reload your shell:**
```bash
source ~/.bashrc  # or source ~/.zshrc
```

**4. Test the integration:**
```bash
brain-search --q "test"
brain-health
```

**5. Use with Claude Code:**

Now you can ask Claude Code:

```
"Search my brain for notes about kubernetes"
"Add a note to my brain: 'Docker tips' with content 'Use multi-stage builds'"
"What ideas do I have about AI projects?"
"Show me all work-related project notes"
```

Claude Code will execute the brain commands to:
- Search your knowledge base
- Add new notes
- Check system health
- Access your organized thoughts

**For AI Agent Integration:**
If you're building a dedicated brain agent in a supervisor-agent architecture, see **[AGENT_INSTRUCTIONS.md](AGENT_INSTRUCTIONS.md)** for comprehensive guidance on how your agent should interact with the brain system.

### Direct Command Examples

```bash
# Search from anywhere
brain-search --q "kubernetes" --domain work --format json

# Add a note
brain-add --title "Quick Idea" --domain personal --type idea --content "Build an AI assistant"

# Check health
brain-health

# Or use full path
./brain_search.sh --q "docker" --type project --format full
./brain_add.sh --title "Meeting Notes" --domain work --type doc --tags "meeting,decisions" --content "Discussed new features"
```

---

## 6. Deployment, Update & Delete

### Deploy (First Time)

```bash
# Clone the repository
git clone https://github.com/ocristaldo/ai-brain.git
cd ai-brain

# One-command deploy
./deploy.sh
```

The deploy script will:
1. ✅ Check Python 3.9+ is installed
2. ✅ Create virtual environment (`.venv/`)
3. ✅ Install dependencies
4. ✅ Initialize database
5. ✅ Set up configuration
6. ✅ Create integration scripts (`brain_search.sh`, `brain_add.sh`)
7. ✅ Prompt for device ID

### Update to New Version

```bash
# Backup your data first!
make backup

# Pull latest changes
git pull origin main

# Re-run deployment (preserves your data)
./deploy.sh

# Your notes/ and db/ are preserved
# Config is updated with new defaults (your values kept)
```

### Delete / Cleanup

**Option 1: Clean generated files (keeps notes and source)**

```bash
./delete.sh
```

Removes:
- `db/` - Database files
- `logs/` - Log files
- `var/` - Runtime state
- `backups/` - Backup archives
- `.venv/` - Virtual environment
- `.pytest_cache/` - Test cache

Keeps:
- `notes/` - Your markdown notes
- `scripts/` - Source code
- `config.yaml` - Your configuration

**Option 2: Complete removal**

```bash
./delete.sh --full
```

⚠️ **Warning:** This removes the entire directory including your notes!

**Before deletion, backup your data:**
```bash
make backup
cp backups/brain-*.tgz ~/safe-location/
```

---

## 7. Daily Usage

### Adding Notes

**Method 1: Create markdown files directly**
```bash
# Create in notes/ directory
vim notes/meeting_notes.md

# Then ingest
make ingest
```

**Method 2: Use the helper script**
```bash
./brain_add.sh --title "Meeting with Team" --domain work --type doc --tags "meeting,team" --content "
- Discussed new features
- Decided on timeline
- Action items: review design
"
```

### Searching

```bash
# General search
make search q="meeting"

# Filter by work domain
make search q="meeting" d=work

# Find all active projects
make search q="" t=project status=active

# Search by tag
make search q="" tags="urgent,important"
```

### Syncing after editing/deleting notes

Any time you edit or remove Markdown files directly, run the sync command to ingest changes and prune missing files:

```bash
# Interactive (lists first 10 deletions before asking)
make sync

# Non-interactive (automation / cron)
make sync YES=1
```

`make sync` uses the same ingest pipeline plus the safe prune workflow, so the SQLite DB and the `notes/` directory never drift apart.

### Cleaning up duplicates (legacy data)

Older databases might have duplicate entries that point to the same Markdown file. Use the dedupe helper to inspect and remove them:

```bash
# Show duplicates (if any)
make dedupe

# Delete duplicates automatically
make dedupe APPLY=1 YES=1
```

After running `make dedupe`, rerun `make sync` to ensure metadata is up to date.

### Backing Up

Backups happen automatically in the background when you use the brain!

**Manual backup:**
```bash
make backup
```

**Check backup status:**
```bash
ls -lh backups/
cat logs/backup_async.log
```

---

## 8. Essential Commands

```bash
# Activate environment (always do this first in new terminal)
source .venv/bin/activate

# Initialize (only needed once)
make init

# Ingest notes
make ingest

# Search
make search q="search term"

# Agent-friendly search
make search q="search term" format=json body=1

# Backup
make backup

# Health check
make health

# Status overview
make status
make status JSON=1   # JSON output

# Run tests
make test  # report written to logs/test_reports/

# Sync (ingest + prune) after editing/deleting notes
make sync
make sync YES=1   # non-interactive

# Dedupe legacy duplicates
make dedupe
make dedupe APPLY=1 YES=1   # delete automatically

# Reset generated artifacts (keeps notes/config)
make reset && make init && make ingest
```

---

## 9. Understanding Note Structure

Every note needs YAML frontmatter:

```yaml
---
title: Your Note Title          # Required
domain: work                    # Required: work, personal, hobbies
visibility: private             # Required: public, private, secret
type: note                      # Required: idea, project, note, memory, quote, doc, task
status: inbox                   # Required: inbox, active, archived
tags: [tag1, tag2]             # Optional but recommended
---
Your markdown content here...
```

### Field Options

**domain:**
- `work` - Work-related notes
- `personal` - Personal notes
- `hobbies` - Hobby-related notes

**visibility:**
- `public` - Can be shared
- `private` - Private to you
- `secret` - Will not be embedded (extra privacy)

**type:**
- `idea` - Ideas and concepts
- `project` - Project documentation
- `note` - General notes
- `memory` - Things to remember
- `quote` - Quotes and references
- `doc` - Documentation
- `task` - Tasks and todos

**status:**
- `inbox` - New, not yet processed
- `active` - Currently relevant
- `archived` - Historical reference

---

## 10. Troubleshooting

### "Command not found: make"

**macOS:**
```bash
xcode-select --install
```

**Linux:**
```bash
sudo apt-get install build-essential  # Ubuntu/Debian
sudo yum install make                  # CentOS/RHEL
```

### "ModuleNotFoundError: No module named 'yaml'"

Activate virtual environment first:
```bash
source .venv/bin/activate
```

### Note was skipped during ingestion

Check the error in logs:
```bash
grep "ingest_skip" logs/app.*.jsonl
```

Common issues:
- Missing required fields in frontmatter
- Invalid YAML syntax
- Invalid facet values

**Fix:** Edit the note's frontmatter and run `make ingest` again.

### No search results

```bash
# Check if notes were ingested
make health

# Reindex if needed
python3 scripts/reindex_fts.py
```

---

## 11. Next Steps

### Learn More

- **Full FAQ:** See README.md for 10+ common questions
- **Troubleshooting:** Check `docs/troubleshooting.md`
- **Logging:** Learn about logs in `docs/logging.md`
- **Contributing:** See `CONTRIBUTING.md`

### Customize

**Edit configuration:**
```bash
vim config.yaml
```

Change:
- `device_id` - Identify your device
- `keep_days` - Backup retention
- `redactions` - What to redact from logs

### Integrate with Your Workflow

**Daily backup (cron):**
```bash
# Add to crontab
0 2 * * * cd /path/to/ai-brain && source .venv/bin/activate && make backup
```

**Pre-commit hook (Git repo):**
```bash
# Automatically ingest on git commit
echo 'cd /path/to/ai-brain && source .venv/bin/activate && make ingest' > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

---

## 12. Common Workflows

### Capture Ideas Quickly

```bash
brain-add "$(date +%Y-%m-%d) Daily Notes" personal note "
Today's thoughts:
- $(read -p 'Thought: ' thought && echo $thought)
"
```

### Weekly Review

```bash
# Find notes from this week
make search q="" status=active

# Archive old notes
# (manually edit status to 'archived' in frontmatter)
```

### Research Project

```bash
# Create project note
brain-add "Research: AI Agents" work project "
Goals:
- Understand current state
- Identify use cases
- Build prototype

Resources:
- Papers to read
- Tools to try
"

# Add findings as you research
brain-add "AI Agents - Finding 1" work note "Content..."

# Search all project notes
make search q="research" t=project
```

---

## 🎉 You're Ready!

Your AI Brain Vault is set up and ready to capture your knowledge.

**Remember:**
1. Add notes to `notes/` directory
2. Run `make ingest` to index them
3. Search with `make search q="..."`
4. Backups happen automatically!

**Happy brain building! 🧠**

---

## Quick Reference Card

```bash
# Setup (once)
git clone https://github.com/ocristaldo/ai-brain.git
cd ai-brain
./deploy.sh

# Daily usage
source .venv/bin/activate  # Activate environment
make ingest                # Index new notes
make search q="term"       # Search
make backup                # Manual backup
make health                # Check status

# Helper scripts
./brain_search.sh --q "term"
./brain_add.sh "Title" domain type "Content"

# Cleanup
./delete.sh                # Remove generated files
./delete.sh --full         # Complete removal
```

---

**Need help?** Check README.md or docs/troubleshooting.md
