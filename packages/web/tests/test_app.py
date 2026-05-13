"""Smoke tests for FastAPI app."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from observatory_core.store import Store
from observatory_web.app import create_app


def _seed(tmp_path: Path) -> Path:
    db = tmp_path / "t.db"
    s = Store(db)
    s.insert_event(ts=1.0, kind="hook", hook="PreToolUse", duration_ms=10, exit_code=0, payload={"a": 1})
    s.insert_event(ts=2.0, kind="tool_use", tool="Bash", payload={"name": "Bash"})
    s.close()
    return db


def test_index(tmp_path: Path) -> None:
    db = _seed(tmp_path)
    client = TestClient(create_app(db))
    r = client.get("/")
    assert r.status_code == 200
    assert "claude-observatory" in r.text


def test_events_filter(tmp_path: Path) -> None:
    db = _seed(tmp_path)
    client = TestClient(create_app(db))
    r = client.get("/events?kind=hook")
    assert r.status_code == 200
    assert "PreToolUse" in r.text
    assert "Bash" not in r.text


def test_event_detail(tmp_path: Path) -> None:
    db = _seed(tmp_path)
    client = TestClient(create_app(db))
    r = client.get("/event/1")
    assert r.status_code == 200
    assert "PreToolUse" in r.text


def test_health(tmp_path: Path) -> None:
    db = _seed(tmp_path)
    client = TestClient(create_app(db))
    r = client.get("/api/health")
    assert r.json()["ok"] is True
