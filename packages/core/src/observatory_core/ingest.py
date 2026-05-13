"""One-shot ingest: scan JSONL transcripts → SQLite store."""
from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path

from observatory_core.jsonl import (
    extract_tool_uses,
    extract_usage,
    iter_events,
    session_files,
)
from observatory_core.pricing import cost_usd
from observatory_core.store import Store


def _ts(event: dict) -> float:
    t = event.get("timestamp")
    if isinstance(t, (int, float)):
        return float(t)
    if isinstance(t, str):
        try:
            return datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return time.time()
    return time.time()


def ingest_one(path: Path, store: Store) -> int:
    n = 0
    for ev in iter_events(path):
        ts = _ts(ev)
        sid = ev.get("sessionId")
        u = extract_usage(ev)
        if u:
            c = cost_usd(u)
            store.insert_event(
                ts=ts, kind="usage", session=sid, cost_usd=c, payload=u
            )
            store.upsert_session(sid or path.stem, last_seen_at=ts, model=u.get("model") or "")
            n += 1
        for tname in extract_tool_uses(ev):
            store.insert_event(
                ts=ts, kind="tool_use", session=sid, tool=tname, payload={"name": tname}
            )
            n += 1
    return n


def main() -> int:
    p = argparse.ArgumentParser(prog="observatory ingest")
    p.add_argument("--db", default=str(Path.home() / ".claude-observatory" / "observatory.db"))
    p.add_argument("--root", default=None, help="JSONL project root (default ~/.claude/projects)")
    p.add_argument("--limit", type=int, default=0, help="cap on files processed (0 = all)")
    args = p.parse_args()

    store = Store(Path(args.db))
    root = Path(args.root) if args.root else None
    total = 0
    files = 0
    for path in session_files(root):
        if args.limit and files >= args.limit:
            break
        total += ingest_one(path, store)
        files += 1
    print(f"ingested {total} events from {files} files into {args.db}")
    store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
