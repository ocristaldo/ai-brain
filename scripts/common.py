#!/usr/bin/env python3
"""Common utilities for AI Brain scripts"""
import os, json, pathlib, uuid, time
from datetime import datetime
import yaml

# Load config once
CONFIG = yaml.safe_load(open("config.yaml","r"))

def get_trace_id():
    """Generate a unique trace ID for operation tracking"""
    return uuid.uuid4().hex[:8]

def log_json(level, component, action, msg, trace_id=None, start_time=None, **kw):
    """
    Log structured JSONL entry with trace_id and latency_ms

    Args:
        level: Log level (INFO, WARN, ERROR)
        component: Component name (ingestor, librarian, backup, etc.)
        action: Action being performed (update, search, backup, etc.)
        msg: Human-readable message
        trace_id: Optional trace ID for correlating operations
        start_time: Optional start time (from time.time()) to calculate latency_ms
        **kw: Additional fields to include in log
    """
    logs_dir = CONFIG["paths"]["logs_dir"]
    device_id = CONFIG.get("device_id", "unknown")
    redactions = set(CONFIG.get("logging", {}).get("redactions", []))

    pathlib.Path(logs_dir).mkdir(parents=True, exist_ok=True)
    fname = os.path.join(logs_dir, f"app.{datetime.utcnow().strftime('%Y-%m-%d')}.jsonl")

    rec = {
        "ts": datetime.utcnow().isoformat()+"Z",
        "level": level,
        "phase": "p1",
        "component": component,
        "actor": component,
        "action": action,
        "device_id": device_id,
        **kw,
        "msg": msg
    }

    # Add trace_id if provided
    if trace_id:
        rec["trace_id"] = trace_id

    # Add latency_ms if start_time provided
    if start_time is not None:
        rec["latency_ms"] = int((time.time() - start_time) * 1000)

    # Apply redactions
    for k in list(rec.keys()):
        if k in redactions:
            rec[k] = "[REDACTED]"

    with open(fname, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
