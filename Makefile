.DEFAULT_GOAL := help

.PHONY: help init ingest embed search backup restore health test reset

help:
	@echo "AI Brain Vault Make Targets"
	@echo "  make init                # Initialize SQLite schema (run once)"
	@echo "  make ingest [PRUNE=1]    # Ingest notes (set PRUNE=1 YES=1 to delete missing files)"
	@echo "  make sync [YES=1]        # Ingest + prune missing files (interactive unless YES=1)"
	@echo "  make search q=\"term\"      # Search notes (add format=json body=1 for JSON)"
	@echo "  make backup              # Create + verify backup"
	@echo "  make restore file=...    # Restore from backup (set CONFIRM=1 to apply)"
	@echo "  make health              # Run health check"
	@echo "  make status [JSON=1]     # Show DB metrics (add JSON=1 for machine output)"
	@echo "  make dedupe [APPLY=1]    # Detect/delete duplicate rows (set APPLY=1 YES=1 to remove)"
	@echo "  make reset               # Delete db/logs/var/backups (keeps notes/config)"
	@echo "  make test                # Run pytest suite"
	@echo ""
	@echo "Examples:"
	@echo "  make ingest PRUNE=1 YES=1"
	@echo "  make search q=\"idea\" format=json body=1"

init:
		python3 scripts/init_db.py

ingest:
	python3 scripts/ingest.py $(if $(PRUNE),--prune-missing,) $(if $(YES),--yes,)

embed:
	python3 scripts/embed.py

search:
	python3 scripts/search.py $(if $(q),--q "$(q)",) \
		$(if $(d),--domain "$(d)",) \
		$(if $(t),--type "$(t)",) \
		$(if $(vis),--visibility "$(vis)",) \
		$(if $(status),--status "$(status)",) \
		$(if $(tags),--tags "$(tags)",) \
		$(if $(k),--k $(k),) \
		$(if $(format),--format $(format),) \
		$(if $(body),--include-body,) \
		$(EXTRA)

backup:
	python3 scripts/export_backup.py && python3 scripts/verify_backup.py

restore:
	python3 scripts/restore_backup.py --file "$(file)" $(if $(CONFIRM),--confirm,)

health:
	python3 scripts/reindex_fts.py --check

test:
	python3 scripts/run_tests.py

reset:
	rm -rf db logs var backups .pytest_cache
	@echo "Environment reset. Run 'make init' then 'make ingest' to rebuild the database."

sync:
	python3 scripts/ingest.py --prune-missing $(if $(YES),--yes,)
	python3 scripts/reindex_fts.py

status:
	python3 scripts/status.py $(if $(JSON),--json,)

dedupe:
	python3 scripts/dedupe.py $(if $(APPLY),--apply,) $(if $(YES),--yes,) $(if $(JSON),--json,)
