"""SQLite event store with WAL mode."""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    session TEXT,
    kind TEXT NOT NULL,            -- 'usage' | 'tool_use' | 'hook' | 'message'
    tool TEXT,
    hook TEXT,
    duration_ms INTEGER,
    exit_code INTEGER,
    cost_usd REAL,
    payload TEXT NOT NULL          -- raw JSON
);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
CREATE INDEX IF NOT EXISTS idx_events_kind ON events(kind);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    started_at REAL,
    last_seen_at REAL,
    model TEXT,
    total_cost_usd REAL DEFAULT 0,
    project TEXT
);

CREATE TABLE IF NOT EXISTS suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at REAL NOT NULL,
    kind TEXT NOT NULL,            -- 'skill-archive' | 'claude-md-rule' | 'mcp-disable' | ...
    target TEXT,
    diff TEXT,
    rationale TEXT,
    evidence TEXT,                 -- JSON
    confidence REAL,
    status TEXT DEFAULT 'pending'  -- pending | applied | rejected | tested
);
"""


class Store:
    def __init__(self, db_path: Path):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self.conn.executescript(SCHEMA)

    def insert_event(
        self,
        *,
        ts: float,
        kind: str,
        payload: dict,
        session: str | None = None,
        tool: str | None = None,
        hook: str | None = None,
        duration_ms: int | None = None,
        exit_code: int | None = None,
        cost_usd: float | None = None,
    ) -> int:
        cur = self.conn.execute(
            "INSERT INTO events (ts, session, kind, tool, hook, duration_ms, exit_code, cost_usd, payload) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ts, session, kind, tool, hook, duration_ms, exit_code, cost_usd, json.dumps(payload)),
        )
        return cur.lastrowid or 0

    def insert_events(self, rows: Iterable[dict]) -> int:
        n = 0
        for r in rows:
            self.insert_event(**r)
            n += 1
        return n

    def upsert_session(self, session: str, **fields) -> None:
        cols = ["id"] + list(fields.keys())
        vals = [session] + list(fields.values())
        placeholders = ", ".join("?" * len(cols))
        updates = ", ".join(f"{k}=excluded.{k}" for k in fields)
        self.conn.execute(
            f"INSERT INTO sessions ({', '.join(cols)}) VALUES ({placeholders}) "
            f"ON CONFLICT(id) DO UPDATE SET {updates}",
            vals,
        )

    def recent_events(self, limit: int = 100) -> list[dict]:
        cur = self.conn.execute(
            "SELECT id, ts, session, kind, tool, hook, duration_ms, exit_code, cost_usd, payload "
            "FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        cols = [c[0] for c in cur.description]
        out = []
        for row in cur.fetchall():
            d = dict(zip(cols, row, strict=False))
            try:
                d["payload"] = json.loads(d["payload"])
            except (json.JSONDecodeError, TypeError):
                pass
            out.append(d)
        return out

    def close(self) -> None:
        self.conn.close()
