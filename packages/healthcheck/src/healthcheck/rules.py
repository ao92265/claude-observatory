"""Recommendation rules.

Each rule receives an Analysis dataclass and yields Suggestions.
Rules are pure functions over aggregated data — no I/O.
"""
from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from healthcheck.types import Suggestion


@dataclass
class Analysis:
    """Aggregated telemetry over a time window."""

    window_days: int
    now: datetime
    # tool name -> invocation count
    tool_counts: dict[str, int] = field(default_factory=dict)
    # tool name -> last seen datetime
    tool_last_seen: dict[str, datetime] = field(default_factory=dict)
    # session id -> spend $
    session_cost: dict[str, float] = field(default_factory=dict)
    # session id -> model
    session_model: dict[str, str] = field(default_factory=dict)
    # session id -> cache stats
    session_cache: dict[str, dict[str, int]] = field(default_factory=dict)
    # raw event count
    total_events: int = 0
    # CLAUDE.md text (joined)
    claude_md_text: str = ""

    def total_cost(self) -> float:
        return sum(self.session_cost.values())


def rule_unused_tools(a: Analysis) -> Iterator[Suggestion]:
    """Flag tools with zero invocations in window."""
    if not a.tool_counts:
        return
    cutoff = a.now - timedelta(days=max(7, a.window_days // 2))
    for tool, n in a.tool_counts.items():
        last = a.tool_last_seen.get(tool)
        if last and last >= cutoff:
            continue
        if n >= 5:
            continue
        yield Suggestion(
            id=f"unused-tool:{tool}",
            kind="tool-archive",
            target=tool,
            rationale=(
                f"Tool '{tool}' invoked only {n}x in last {a.window_days}d "
                f"(last seen {last.isoformat() if last else 'never'}). "
                f"Consider disabling its MCP server / skill to reduce schema overhead."
            ),
            confidence=0.7 if n == 0 else 0.55,
            evidence={"invocations": n, "last_seen": last.isoformat() if last else None},
        )


def rule_opus_for_simple_work(a: Analysis) -> Iterator[Suggestion]:
    """Opus sessions with low cost — likely overkill."""
    for sid, cost in a.session_cost.items():
        model = a.session_model.get(sid, "")
        if "opus" not in model.lower():
            continue
        if cost > 2.0:
            continue
        yield Suggestion(
            id=f"opus-downgrade:{sid}",
            kind="model-downgrade",
            target=sid,
            rationale=(
                f"Session {sid[:12]} used {model} for ${cost:.3f}. "
                f"Low spend = simple work; sonnet would suffice at ~5× cheaper."
            ),
            confidence=0.6,
            estimated_savings_usd_month=cost * 30 * 0.8,
            evidence={"model": model, "cost": cost},
        )


def rule_low_cache_hit(a: Analysis) -> Iterator[Suggestion]:
    """Sessions burning cache_creation without cache_read."""
    for sid, s in a.session_cache.items():
        bill = s["read"] + s["create"] + s["input"]
        if bill < 50_000:
            continue
        rate = s["read"] / bill if bill else 0.0
        if rate >= 0.5:
            continue
        yield Suggestion(
            id=f"low-cache:{sid}",
            kind="cache-restructure",
            target=sid,
            rationale=(
                f"Session {sid[:12]} cache hit {rate:.0%} on {bill:,} billable tokens. "
                f"Stabilize CLAUDE.md / tool ordering or extend cache TTL."
            ),
            confidence=0.65,
            evidence={"hit_rate": rate, "billable_tokens": bill},
        )


_HEDGE = re.compile(r"\b(you should|try to|usually|generally|typically|if possible)\b", re.I)


def rule_weak_claude_md(a: Analysis) -> Iterator[Suggestion]:
    """Hedging language in CLAUDE.md."""
    if not a.claude_md_text:
        return
    matches = _HEDGE.findall(a.claude_md_text)
    if len(matches) < 3:
        return
    yield Suggestion(
        id="claude-md:hedging",
        kind="claude-md-rule",
        target="CLAUDE.md",
        rationale=(
            f"CLAUDE.md contains {len(matches)} hedging phrases. "
            f"Stronger imperatives (MUST/WILL/NEVER) get followed more reliably."
        ),
        diff="(suggest s/you should/MUST/ and similar replacements)",
        confidence=0.55,
        evidence={"hedge_count": len(matches), "examples": matches[:5]},
    )


def rule_high_tool_concentration(a: Analysis) -> Iterator[Suggestion]:
    """One tool dominates — consider skill consolidation."""
    if not a.tool_counts:
        return
    total = sum(a.tool_counts.values())
    if total < 100:
        return
    top_tool, top_n = max(a.tool_counts.items(), key=lambda kv: kv[1])
    share = top_n / total
    if share < 0.6:
        return
    yield Suggestion(
        id=f"tool-concentration:{top_tool}",
        kind="workflow-pattern",
        target=top_tool,
        rationale=(
            f"'{top_tool}' = {share:.0%} of all tool calls. "
            f"Repetitive use of one tool suggests a skill could automate the pattern."
        ),
        confidence=0.5,
        evidence={"share": share, "count": top_n, "total": total},
    )


ALL_RULES = [
    rule_unused_tools,
    rule_opus_for_simple_work,
    rule_low_cache_hit,
    rule_weak_claude_md,
    rule_high_tool_concentration,
]


def run_all(a: Analysis) -> list[Suggestion]:
    out: list[Suggestion] = []
    for rule in ALL_RULES:
        out.extend(rule(a))
    out.sort(key=lambda s: -(s.confidence + s.estimated_savings_usd_month / 100))
    return out
