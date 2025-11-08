"""
Test search functionality including FTS and tag filtering
"""
import os
import pytest
import tempfile
import shutil
import subprocess
import sqlite3


def run(cmd, cwd):
    """Helper to run commands"""
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return r


def setup_test_data(dst):
    """Create test notes with various content"""
    notes_dir = dst / "notes"
    notes_dir.mkdir(exist_ok=True)

    # Note 1: Kubernetes monitoring
    (notes_dir / "k8s_monitoring.md").write_text("""---
title: Kubernetes Monitoring Setup
domain: work
visibility: private
type: project
status: active
tags: [kubernetes, monitoring, prometheus]
---
Setup Prometheus for Kubernetes cluster monitoring.
""")

    # Note 2: Docker optimization
    (notes_dir / "docker_opt.md").write_text("""---
title: Docker Optimization Tips
domain: work
visibility: public
type: note
status: inbox
tags: [docker, performance]
---
Tips for optimizing Docker containers.
""")

    # Note 3: Personal learning
    (notes_dir / "learning.md").write_text("""---
title: Learning Plan
domain: personal
visibility: private
type: idea
status: active
tags: [learning, ai, python]
---
Plan to learn more about AI and Python.
""")

    # Initialize and ingest
    run("python3 scripts/init_db.py", str(dst))
    run("python3 scripts/ingest.py", str(dst))


def test_fts_search_accuracy(tmp_path):
    """Test that FTS search returns accurate results"""
    dst = tmp_path / "repo"
    shutil.copytree(os.getcwd(), dst)
    setup_test_data(dst)

    # Search for "kubernetes"
    r = run("python3 scripts/search.py --q 'kubernetes'", str(dst))
    assert "Kubernetes Monitoring Setup" in r.stdout
    assert "Docker" not in r.stdout

    # Search for "docker"
    r = run("python3 scripts/search.py --q 'docker'", str(dst))
    assert "Docker Optimization" in r.stdout
    assert "Kubernetes" not in r.stdout

    # Search for "ai"
    r = run("python3 scripts/search.py --q 'ai'", str(dst))
    assert "Learning Plan" in r.stdout


def test_domain_filtering(tmp_path):
    """Test filtering by domain"""
    dst = tmp_path / "repo"
    shutil.copytree(os.getcwd(), dst)
    setup_test_data(dst)

    # Filter by work domain
    r = run("python3 scripts/search.py --q '' --domain work", str(dst))
    assert "Kubernetes" in r.stdout
    assert "Docker" in r.stdout
    assert "Learning Plan" not in r.stdout

    # Filter by personal domain
    r = run("python3 scripts/search.py --q '' --domain personal", str(dst))
    assert "Learning Plan" in r.stdout
    assert "Kubernetes" not in r.stdout


def test_type_filtering(tmp_path):
    """Test filtering by type"""
    dst = tmp_path / "repo"
    shutil.copytree(os.getcwd(), dst)
    setup_test_data(dst)

    # Filter by project type
    r = run("python3 scripts/search.py --q '' --type project", str(dst))
    assert "Kubernetes Monitoring" in r.stdout
    assert "Docker Optimization" not in r.stdout

    # Filter by note type
    r = run("python3 scripts/search.py --q '' --type note", str(dst))
    assert "Docker Optimization" in r.stdout
    assert "Kubernetes Monitoring" not in r.stdout


def test_visibility_filtering(tmp_path):
    """Test filtering by visibility"""
    dst = tmp_path / "repo"
    shutil.copytree(os.getcwd(), dst)
    setup_test_data(dst)

    # Filter by public visibility
    r = run("python3 scripts/search.py --q '' --visibility public", str(dst))
    assert "Docker Optimization" in r.stdout
    assert "Kubernetes" not in r.stdout

    # Filter by private visibility
    r = run("python3 scripts/search.py --q '' --visibility private", str(dst))
    assert "Kubernetes" in r.stdout or "Learning" in r.stdout
    assert "Docker Optimization" not in r.stdout


def test_tag_filtering(tmp_path):
    """Test filtering by tags"""
    dst = tmp_path / "repo"
    shutil.copytree(os.getcwd(), dst)
    setup_test_data(dst)

    # Filter by single tag
    r = run("python3 scripts/search.py --q '' --tags 'kubernetes'", str(dst))
    assert "Kubernetes Monitoring" in r.stdout
    assert "Docker" not in r.stdout

    # Filter by multiple tags (any match)
    r = run("python3 scripts/search.py --q '' --tags 'kubernetes,docker'", str(dst))
    assert "Kubernetes" in r.stdout or "Docker" in r.stdout


def test_combined_filters(tmp_path):
    """Test combining multiple filters"""
    dst = tmp_path / "repo"
    shutil.copytree(os.getcwd(), dst)
    setup_test_data(dst)

    # Search with query + domain filter
    r = run("python3 scripts/search.py --q 'monitoring' --domain work", str(dst))
    assert "Kubernetes Monitoring" in r.stdout

    # Search with query + type + tag
    r = run("python3 scripts/search.py --q 'kubernetes' --type project --tags 'monitoring'", str(dst))
    assert "Kubernetes Monitoring" in r.stdout


def test_empty_query_returns_all(tmp_path):
    """Test that empty query returns all items"""
    dst = tmp_path / "repo"
    shutil.copytree(os.getcwd(), dst)
    setup_test_data(dst)

    # Empty query should return all
    r = run("python3 scripts/search.py --q ''", str(dst))
    assert "Kubernetes" in r.stdout
    assert "Docker" in r.stdout
    assert "Learning" in r.stdout


def test_no_results(tmp_path):
    """Test handling of queries with no results"""
    dst = tmp_path / "repo"
    shutil.copytree(os.getcwd(), dst)
    setup_test_data(dst)

    # Query that should return nothing
    r = run("python3 scripts/search.py --q 'nonexistent_term_xyz123'", str(dst))
    # Should not crash, just return empty
    assert r.returncode == 0


def test_case_insensitive_search(tmp_path):
    """Test that search is case-insensitive"""
    dst = tmp_path / "repo"
    shutil.copytree(os.getcwd(), dst)
    setup_test_data(dst)

    # Try different cases
    r1 = run("python3 scripts/search.py --q 'kubernetes'", str(dst))
    r2 = run("python3 scripts/search.py --q 'Kubernetes'", str(dst))
    r3 = run("python3 scripts/search.py --q 'KUBERNETES'", str(dst))

    # All should return the same result
    assert "Kubernetes Monitoring" in r1.stdout
    assert "Kubernetes Monitoring" in r2.stdout
    assert "Kubernetes Monitoring" in r3.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
