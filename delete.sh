#!/bin/bash
#
# AI Brain Vault - One-Command Delete/Cleanup
# Usage: ./delete.sh [--full]
#
# Options:
#   --full    Delete everything including the repository itself
#   (default) Clean generated files only (keeps source code and notes)
#

set -e

echo "============================================"
echo "   AI Brain Vault - Cleanup Script"
echo "============================================"
echo

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get brain directory
BRAIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BRAIN_DIR"

FULL_DELETE=false
if [ "$1" == "--full" ]; then
    FULL_DELETE=true
fi

if $FULL_DELETE; then
    echo -e "${RED}⚠️  FULL DELETE MODE${NC}"
    echo
    echo "This will permanently delete:"
    echo "  - The entire AI Brain directory"
    echo "  - All notes, database, and backups"
    echo "  - All configuration"
    echo
    echo -e "${YELLOW}This directory: $BRAIN_DIR${NC}"
    echo
    echo -n -e "${RED}Are you ABSOLUTELY sure? (type 'yes' to confirm): ${NC}"
    read confirm

    if [ "$confirm" != "yes" ]; then
        echo "Cancelled."
        exit 0
    fi

    echo
    echo -e "${RED}🗑️  Deleting everything...${NC}"
    cd ..
    rm -rf "$BRAIN_DIR"
    echo -e "${GREEN}✓ AI Brain deleted completely${NC}"
    echo "Directory removed: $BRAIN_DIR"
    exit 0
fi

# Normal cleanup mode (keep source, delete generated files)
echo -e "${BLUE}Cleanup mode: Generated files only${NC}"
echo
echo "This will delete:"
echo "  - Database (db/)"
echo "  - Logs (logs/)"
echo "  - Runtime state (var/)"
echo "  - Backups (backups/)"
echo "  - Virtual environment (.venv/)"
echo "  - Integration scripts (brain_*.sh)"
echo
echo "This will keep:"
echo "  - Source code (scripts/)"
echo "  - Notes (notes/)"
echo "  - Configuration (config.yaml)"
echo "  - Documentation"
echo
echo -n -e "${YELLOW}Continue? (y/N): ${NC}"
read confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Cancelled."
    exit 0
fi

echo
echo -e "${BLUE}🧹 Cleaning up generated files...${NC}"

# Delete generated directories
for dir in db logs var backups .venv .pytest_cache; do
    if [ -d "$dir" ]; then
        echo "  Removing $dir/"
        rm -rf "$dir"
    fi
done

# Delete integration scripts
for script in brain_search.sh brain_add.sh; do
    if [ -f "$script" ]; then
        echo "  Removing $script"
        rm -f "$script"
    fi
done

# Delete Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo
echo -e "${GREEN}✓ Cleanup complete!${NC}"
echo
echo -e "${BLUE}📋 Summary:${NC}"
echo "  - Generated files removed"
echo "  - Source code preserved"
echo "  - Notes preserved in notes/"
echo "  - Configuration preserved"
echo
echo -e "${GREEN}Ready for re-deployment!${NC}"
echo "Run ./deploy.sh to set up again"
echo
