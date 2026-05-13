from __future__ import annotations

from pathlib import Path

from observatory_core.store import Store


def test_store_roundtrip(tmp_path: Path) -> None:
    s = Store(tmp_path / "t.db")
    eid = s.insert_event(
        ts=1.0, kind="hook", payload={"x": 1}, hook="PreToolUse", duration_ms=42, exit_code=0
    )
    assert eid > 0
    rows = s.recent_events(10)
    assert len(rows) == 1
    assert rows[0]["kind"] == "hook"
    assert rows[0]["payload"] == {"x": 1}
    s.close()


def test_store_upsert_session(tmp_path: Path) -> None:
    s = Store(tmp_path / "t.db")
    s.upsert_session("sess1", model="claude-sonnet-4-6", last_seen_at=10.0)
    s.upsert_session("sess1", last_seen_at=20.0)
    cur = s.conn.execute("SELECT last_seen_at, model FROM sessions WHERE id=?", ("sess1",))
    row = cur.fetchone()
    assert row[0] == 20.0
    assert row[1] == "claude-sonnet-4-6"
    s.close()
