#!/bin/bash
# AI Brain Search Wrapper

set -euo pipefail

BRAIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BRAIN_DIR"

if [ ! -f ".venv/bin/activate" ]; then
    echo "Virtual environment not found. Run './deploy.sh' or create .venv first." >&2
    exit 1
fi

source .venv/bin/activate
python3 scripts/search.py "$@"
