"""Build an Analysis from JSONL transcripts."""
from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from observatory_core.jsonl import (
    extract_tool_uses,
    extract_usage,
    iter_events,
    session_files,
)
from observatory_core.pricing import cost_usd

from healthcheck.rules import Analysis


def _parse_ts(t: object) -> datetime | None:
    if isinstance(t, (int, float)):
        return datetime.fromtimestamp(float(t))
    if isinstance(t, str):
        try:
            return datetime.fromisoformat(t.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None
    return None


def build_analysis(window_days: int = 30, claude_md_path: Path | None = None) -> Analysis:
    now = datetime.now()
    cutoff_ts = time.time() - window_days * 86400

    a = Analysis(window_days=window_days, now=now)
    cache: dict[str, dict[str, int]] = defaultdict(
        lambda: {"read": 0, "create": 0, "input": 0, "output": 0}
    )

    for path in session_files():
        try:
            if path.stat().st_mtime < cutoff_ts:
                continue
        except OSError:
            continue
        for ev in iter_events(path):
            a.total_events += 1
            ts = _parse_ts(ev.get("timestamp"))
            sid = ev.get("sessionId") or path.stem
            u = extract_usage(ev)
            if u:
                c = cost_usd(u)
                a.session_cost[sid] = a.session_cost.get(sid, 0.0) + c
                model = u.get("model") or ""
                if model:
                    a.session_model[sid] = model
                cache[sid]["read"] += u["cache_read"]
                cache[sid]["create"] += u["cache_create"]
                cache[sid]["input"] += u["input"]
                cache[sid]["output"] += u["output"]
            for tname in extract_tool_uses(ev):
                a.tool_counts[tname] = a.tool_counts.get(tname, 0) + 1
                if ts:
                    prev = a.tool_last_seen.get(tname)
                    if not prev or ts > prev:
                        a.tool_last_seen[tname] = ts

    a.session_cache = dict(cache)
    if claude_md_path and claude_md_path.exists():
        a.claude_md_text = claude_md_path.read_text(errors="replace")
    return a
