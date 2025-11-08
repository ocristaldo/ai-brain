#!/bin/bash
#
# AI Brain Vault - One-Command Deploy
# Usage: ./deploy.sh
#

set -e  # Exit on error

echo "============================================"
echo "   AI Brain Vault - Deployment Script"
echo "============================================"
echo

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get brain directory (where this script lives)
BRAIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BRAIN_DIR"

echo -e "${BLUE}📍 Brain directory: $BRAIN_DIR${NC}"
echo

# Step 1: Check Python version
echo -e "${BLUE}🔍 Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 not found${NC}"
    echo "Please install Python 3.9+ and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
echo

# Step 2: Create virtual environment
echo -e "${BLUE}🐍 Setting up virtual environment...${NC}"
if [ -d ".venv" ]; then
    echo "Virtual environment already exists, using existing one"
else
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi
echo

# Step 3: Activate and install dependencies
echo -e "${BLUE}📦 Installing dependencies...${NC}"
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo

# Step 4: Initialize database
echo -e "${BLUE}🗄️  Initializing database...${NC}"
if [ -f "db/brain.sqlite" ]; then
    echo "Database already exists, skipping initialization"
else
    python3 scripts/init_db.py
    echo -e "${GREEN}✓ Database initialized${NC}"
fi
echo

# Step 5: Set up configuration
echo -e "${BLUE}⚙️  Checking configuration...${NC}"
if [ ! -f "config.yaml" ]; then
    echo -e "${RED}❌ Error: config.yaml not found${NC}"
    exit 1
fi

# Prompt for device ID if it's still default
if grep -q "device_id: default-device" config.yaml; then
    echo
    echo "Current device_id is 'default-device'"
    echo -n "Enter your device ID (or press Enter to keep default): "
    read device_id
    if [ ! -z "$device_id" ]; then
        # Update device_id in config.yaml
        sed -i.bak "s/device_id: default-device/device_id: $device_id/" config.yaml
        rm config.yaml.bak
        echo -e "${GREEN}✓ Device ID updated to: $device_id${NC}"
    fi
fi
echo -e "${GREEN}✓ Configuration OK${NC}"
echo

# Step 6: Create example notes if notes/ is empty
echo -e "${BLUE}📝 Checking for notes...${NC}"
if [ -z "$(ls -A notes/*.md 2>/dev/null)" ]; then
    echo "No notes found. Example notes are available."
    echo "Notes directory is ready for your markdown files."
else
    NOTE_COUNT=$(ls -1 notes/*.md 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${GREEN}✓ Found $NOTE_COUNT note(s)${NC}"
fi
echo

# Step 7: Ingest existing notes
if [ ! -z "$(ls -A notes/*.md 2>/dev/null)" ]; then
    echo -e "${BLUE}📥 Ingesting notes...${NC}"
    python3 scripts/ingest.py
    echo -e "${GREEN}✓ Notes ingested${NC}"
    echo
fi

# Step 8: Run health check
echo -e "${BLUE}🏥 Running health check...${NC}"
python3 scripts/reindex_fts.py --check
echo

# Step 9: Create shell integration scripts
echo -e "${BLUE}🔧 Creating integration scripts...${NC}"

# Create brain_search.sh
cat > brain_search.sh <<'EOF'
#!/bin/bash
# AI Brain Search Wrapper
BRAIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BRAIN_DIR"
source .venv/bin/activate
python3 scripts/search.py "$@"
EOF
chmod +x brain_search.sh

# Create brain_add.sh
cat > brain_add.sh <<'EOF'
#!/bin/bash
# AI Brain Add Note Wrapper
BRAIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BRAIN_DIR"

if [ $# -lt 1 ]; then
    echo "Usage: ./brain_add.sh 'Note Title' [domain] [type] 'Note content'"
    echo "Example: ./brain_add.sh 'My Idea' personal idea 'This is my idea'"
    exit 1
fi

TITLE="$1"
DOMAIN="${2:-personal}"
TYPE="${3:-note}"
shift 3 || shift $#
CONTENT="$*"

# Create filename from title
FILENAME="notes/$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | tr -cd '[:alnum:]_').md"

cat > "$FILENAME" <<NOTEEOF
---
title: $TITLE
domain: $DOMAIN
visibility: private
type: $TYPE
status: inbox
tags: []
---
$CONTENT
NOTEEOF

echo "Created: $FILENAME"

source .venv/bin/activate
python3 scripts/ingest.py
echo "Note ingested!"
EOF
chmod +x brain_add.sh

echo -e "${GREEN}✓ Integration scripts created:${NC}"
echo "  - brain_search.sh (search notes)"
echo "  - brain_add.sh (add notes)"
echo "  - brain_read.sh (read specific note)"
echo "  - brain_list.sh (list notes with filters)"
echo "  - brain_update.sh (update note metadata)"
echo "  - brain_tags.sh (manage tags)"

# Make all brain scripts executable
chmod +x brain_*.sh 2>/dev/null || true
echo

# Step 10: Print success message and next steps
echo
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   ✓ AI Brain Vault Deployed Successfully!${NC}"
echo -e "${GREEN}============================================${NC}"
echo
echo -e "${BLUE}📚 Quick Start:${NC}"
echo
echo "1. Search your brain:"
echo "   ./brain_search.sh --q 'search term'"
echo
echo "2. Add a note:"
echo "   ./brain_add.sh 'My Note' personal idea 'Note content here'"
echo
echo "3. Or use Make commands:"
echo "   make search q='kubernetes'"
echo "   make backup"
echo "   make health"
echo
echo -e "${BLUE}🔌 Claude Code Integration (Recommended):${NC}"
echo
echo "Add this to your shell profile (~/.bashrc or ~/.zshrc):"
echo
echo "  export BRAIN_HOME=\"$BRAIN_DIR\""
echo "  export PATH=\"\$BRAIN_HOME:\$PATH\""
echo
echo "Then reload your shell and use with Claude Code:"
echo "  source ~/.zshrc  # or ~/.bashrc"
echo
echo "Ask Claude Code:"
echo '  "Search my brain for kubernetes notes"'
echo '  "Add this to my brain: Docker networking basics"'
echo '  "List all my active projects"'
echo
echo "See CLAUDE_CODE_INTEGRATION.md for complete guide"
echo
echo -e "${BLUE}📖 Documentation:${NC}"
echo "  - QUICKSTART.md - Get started in 5 minutes"
echo "  - CLAUDE_CODE_INTEGRATION.md - Claude Code setup"
echo "  - CLAUDE_CODE_RULES.md - Agent interaction rules"
echo "  - README.md - Full documentation and FAQ"
echo "  - docs/ - Technical documentation"
echo
echo -e "${GREEN}Happy brain building! 🧠${NC}"
echo
