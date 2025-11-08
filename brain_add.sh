#!/bin/bash
# AI Brain Add Note Wrapper

set -euo pipefail

usage() {
    cat <<'EOF'
Usage: ./brain_add.sh --title "My Note" --content "Body text" [options]

Options:
  --domain <work|personal|hobbies>   (default: personal)
  --type <idea|project|note|memory|quote|doc|task>  (default: note)
  --visibility <public|private|secret>  (default: private)
  --status <inbox|active|archived>   (default: inbox)
  --tags "tag1,tag2"                 (default: none)
  --file-name custom_file_name.md    (optional explicit filename)
EOF
    exit 1
}

TITLE=""
CONTENT=""
DOMAIN="personal"
TYPE="note"
VISIBILITY="private"
STATUS="inbox"
TAGS=""
FILENAME=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --title)
            TITLE="$2"; shift 2;;
        --content)
            CONTENT="$2"; shift 2;;
        --domain)
            DOMAIN="$2"; shift 2;;
        --type)
            TYPE="$2"; shift 2;;
        --visibility)
            VISIBILITY="$2"; shift 2;;
        --status)
            STATUS="$2"; shift 2;;
        --tags)
            TAGS="$2"; shift 2;;
        --file-name)
            FILENAME="$2"; shift 2;;
        --help|-h)
            usage;;
        *)
            echo "Unknown argument: $1" >&2
            usage;;
    esac
done

if [[ -z "$TITLE" || -z "$CONTENT" ]]; then
    echo "Both --title and --content are required." >&2
    usage
fi

BRAIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BRAIN_DIR"

if [ ! -f ".venv/bin/activate" ]; then
    echo "Virtual environment not found. Run './deploy.sh' or create .venv first." >&2
    exit 1
fi

mkdir -p notes

if [[ -z "$FILENAME" ]]; then
    slug="$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | tr -cd '[:alnum:]_-')"
    if [[ -z "$slug" ]]; then
        slug="note_$(date +%s)"
    fi
    FILENAME="notes/${slug}.md"
else
    [[ "$FILENAME" == notes/* ]] || FILENAME="notes/${FILENAME}"
fi

TAG_LIST="[]"
if [[ -n "$TAGS" ]]; then
    IFS=',' read -ra tag_array <<< "$TAGS"
    formatted=()
    for tag in "${tag_array[@]}"; do
        trimmed="$(echo "$tag" | xargs)"
        [[ -z "$trimmed" ]] && continue
        formatted+=("\"$trimmed\"")
    done
    if (( ${#formatted[@]} )); then
        TAG_LIST="[$(IFS=','; echo "${formatted[*]}")]"
    fi
fi

cat > "$FILENAME" <<NOTEEOF
---
title: ${TITLE}
domain: ${DOMAIN}
visibility: ${VISIBILITY}
type: ${TYPE}
status: ${STATUS}
tags: ${TAG_LIST}
---
${CONTENT}
NOTEEOF

echo "Created note file: $FILENAME"

source .venv/bin/activate
python3 scripts/ingest.py
echo "Note ingested!"
