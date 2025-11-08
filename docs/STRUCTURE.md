# Repository Structure

```
ai-brain/
├─ phase1/
│  ├─ ai-brain-phase1/        # Production-ready CLI + scripts
│  │  ├─ scripts/             # Python utilities (ingest, search, status, dedupe, ...)
│  │  ├─ docs/                # Architecture, logging, troubleshooting, structure docs
│  │  ├─ notes/
│  │  │  ├─ ideas/
│  │  │  ├─ projects/
│  │  │  ├─ notes/
│  │  │  └─ ai_memory/        # Agent-specific memories
│  │  ├─ tests/               # Pytest suite
│  │  ├─ var/, logs/, db/, backups/ (generated)
│  └─ ai-brain-planning/      # Internal planning (roadmaps, releases, research)
│     ├─ roadmap/             # todo.md, bugfix.md, roadmap tracking
│     ├─ releases/            # release-v*.md, phase1-completion.md
│     └─ notes/               # Supporting research/plan docs
└─ description/               # Phase descriptions (legacy)
```

- Only `phase1/ai-brain-phase1` should be published to GitHub. Keep `phase1/ai-brain-planning` private or remove it before pushing.
- `scripts/status.py` and `scripts/dedupe.py` are new helper tools described in the README.
- Every script assumes it is run from within `ai-brain-phase1/` (use `make` targets when possible).
