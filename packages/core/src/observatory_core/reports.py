"""Report commands: cost ledger, cache radar."""
from __future__ import annotations

import argparse
import time
from collections import defaultdict
from pathlib import Path

from observatory_core.jsonl import (
    extract_tool_uses,
    extract_usage,
    iter_events,
    session_files,
)
from observatory_core.pricing import cost_usd


def cost_main() -> int:
    p = argparse.ArgumentParser(prog="observatory cost")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--project", help="substring filter on project path")
    args = p.parse_args()

    cutoff = time.time() - args.days * 86400
    by_session: dict[str, dict] = defaultdict(
        lambda: {"cost": 0.0, "main": 0.0, "side": 0.0, "tools": defaultdict(int), "model": ""}
    )
    by_tool: dict[str, float] = defaultdict(float)

    for path in session_files():
        if args.project and args.project not in str(path):
            continue
        try:
            if path.stat().st_mtime < cutoff:
                continue
        except OSError:
            continue
        for ev in iter_events(path):
            u = extract_usage(ev)
            if u:
                c = cost_usd(u)
                sid = u["session"] or path.stem
                by_session[sid]["cost"] += c
                if u["is_sidechain"]:
                    by_session[sid]["side"] += c
                else:
                    by_session[sid]["main"] += c
                by_session[sid]["model"] = u.get("model") or by_session[sid]["model"]
            for tname in extract_tool_uses(ev):
                sid = ev.get("sessionId") or path.stem
                by_session[sid]["tools"][tname] += 1
                by_tool[tname] += 1

    rows = sorted(by_session.items(), key=lambda kv: -kv[1]["cost"])[: args.top]
    total = sum(v["cost"] for v in by_session.values())
    print(f"\n=== cost (last {args.days}d, {len(by_session)} sessions, ${total:.2f}) ===\n")
    print(f"{'session':<40} {'model':<20} {'main$':>8} {'side$':>8} {'total$':>8}")
    print("-" * 88)
    for sid, v in rows:
        print(
            f"{sid[:40]:<40} {(v['model'] or '?')[:20]:<20} "
            f"{v['main']:>8.3f} {v['side']:>8.3f} {v['cost']:>8.3f}"
        )

    tools = sorted(by_tool.items(), key=lambda kv: -kv[1])[: args.top]
    print(f"\n=== tool frequency (top {args.top}) ===\n")
    for name, n in tools:
        print(f"  {int(n):>6}  {name}")
    return 0


def cache_main() -> int:
    p = argparse.ArgumentParser(prog="observatory cache")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--top", type=int, default=20)
    args = p.parse_args()

    cutoff = time.time() - args.days * 86400
    by_session: dict[str, dict] = defaultdict(
        lambda: {"read": 0, "create": 0, "input": 0, "output": 0}
    )

    for path in session_files():
        try:
            if path.stat().st_mtime < cutoff:
                continue
        except OSError:
            continue
        for ev in iter_events(path):
            u = extract_usage(ev)
            if not u:
                continue
            s = by_session[u["session"] or path.stem]
            s["read"] += u["cache_read"]
            s["create"] += u["cache_create"]
            s["input"] += u["input"]
            s["output"] += u["output"]

    total_read = sum(s["read"] for s in by_session.values())
    total_create = sum(s["create"] for s in by_session.values())
    total_input = sum(s["input"] for s in by_session.values())
    bill = total_read + total_create + total_input
    hit = total_read / bill if bill else 0.0
    saved = total_read * (3.0 - 0.30) / 1_000_000

    print(f"\n=== cache (last {args.days}d) ===\n")
    print(f"Reads:    {total_read:>14,}")
    print(f"Creates:  {total_create:>14,}")
    print(f"Input:    {total_input:>14,}")
    print(f"Hit rate: {hit:>14.1%}")
    print(f"Saved:    ${saved:>13.2f}  (sonnet-equivalent baseline)")

    rows = []
    for sid, s in by_session.items():
        b = s["read"] + s["create"] + s["input"]
        if b < 1000:
            continue
        rows.append((sid, s, s["read"] / b if b else 0.0))
    rows.sort(key=lambda r: (r[2], -r[1]["create"]))
    print(f"\n=== worst offenders (top {args.top}) ===\n")
    print(f"{'session':<40} {'reads':>10} {'creates':>10} {'hit%':>8}")
    print("-" * 70)
    for sid, s, rate in rows[: args.top]:
        print(f"{sid[:40]:<40} {s['read']:>10,} {s['create']:>10,} {rate:>7.1%}")
    return 0
