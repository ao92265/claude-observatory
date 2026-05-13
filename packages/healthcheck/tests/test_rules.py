from __future__ import annotations

from datetime import datetime, timedelta

from healthcheck.rules import Analysis, rule_low_cache_hit, rule_opus_for_simple_work, rule_unused_tools, rule_weak_claude_md, run_all


def _empty(days: int = 30) -> Analysis:
    return Analysis(window_days=days, now=datetime.now())


def test_unused_tool_flagged() -> None:
    a = _empty()
    a.tool_counts = {"RarelyUsed": 1}
    a.tool_last_seen = {"RarelyUsed": datetime.now() - timedelta(days=20)}
    sugs = list(rule_unused_tools(a))
    assert len(sugs) == 1
    assert sugs[0].kind == "tool-archive"


def test_active_tool_not_flagged() -> None:
    a = _empty()
    a.tool_counts = {"Bash": 5000}
    a.tool_last_seen = {"Bash": datetime.now()}
    assert list(rule_unused_tools(a)) == []


def test_opus_low_spend_flagged() -> None:
    a = _empty()
    a.session_cost = {"s1": 0.5}
    a.session_model = {"s1": "claude-opus-4-7"}
    sugs = list(rule_opus_for_simple_work(a))
    assert len(sugs) == 1
    assert sugs[0].estimated_savings_usd_month > 0


def test_opus_high_spend_not_flagged() -> None:
    a = _empty()
    a.session_cost = {"s1": 100.0}
    a.session_model = {"s1": "claude-opus-4-7"}
    assert list(rule_opus_for_simple_work(a)) == []


def test_low_cache_hit() -> None:
    a = _empty()
    a.session_cache = {"s1": {"read": 1000, "create": 200_000, "input": 5000, "output": 1000}}
    sugs = list(rule_low_cache_hit(a))
    assert len(sugs) == 1


def test_high_cache_hit_not_flagged() -> None:
    a = _empty()
    a.session_cache = {"s1": {"read": 200_000, "create": 5000, "input": 1000, "output": 500}}
    assert list(rule_low_cache_hit(a)) == []


def test_weak_claude_md() -> None:
    a = _empty()
    a.claude_md_text = "You should be careful. Try to follow conventions. Usually this works."
    sugs = list(rule_weak_claude_md(a))
    assert len(sugs) == 1
    assert sugs[0].evidence["hedge_count"] >= 3


def test_run_all_sorts_by_confidence_plus_savings() -> None:
    a = _empty()
    a.tool_counts = {"X": 0}
    a.tool_last_seen = {}
    a.session_cost = {"s1": 1.0}
    a.session_model = {"s1": "claude-opus-4-7"}
    result = run_all(a)
    assert len(result) >= 2
    # ranking should be monotonic in (confidence + savings/100)
    scores = [s.confidence + s.estimated_savings_usd_month / 100 for s in result]
    assert scores == sorted(scores, reverse=True)
