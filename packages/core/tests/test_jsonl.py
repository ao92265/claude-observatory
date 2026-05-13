"""Unit + property tests for JSONL reader."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from observatory_core.jsonl import extract_tool_uses, extract_usage, iter_events


def test_iter_events_skips_bad_lines(tmp_path: Path) -> None:
    p = tmp_path / "s.jsonl"
    p.write_text('{"a": 1}\nNOT JSON\n{"b": 2}\n\n')
    out = list(iter_events(p))
    assert out == [{"a": 1}, {"b": 2}]


def test_iter_events_missing_file(tmp_path: Path) -> None:
    assert list(iter_events(tmp_path / "missing.jsonl")) == []


def test_extract_usage_normal() -> None:
    ev = {
        "sessionId": "abc",
        "isSidechain": False,
        "timestamp": "2026-05-13T00:00:00Z",
        "message": {
            "model": "claude-sonnet-4-6",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 20,
                "cache_read_input_tokens": 100,
                "cache_creation_input_tokens": 50,
            },
        },
    }
    u = extract_usage(ev)
    assert u is not None
    assert u["input"] == 10
    assert u["output"] == 20
    assert u["cache_read"] == 100
    assert u["cache_create"] == 50
    assert u["session"] == "abc"
    assert u["is_sidechain"] is False


def test_extract_usage_returns_none_on_garbage() -> None:
    assert extract_usage({}) is None
    assert extract_usage({"message": "string"}) is None
    assert extract_usage({"message": {"usage": "not-dict"}}) is None


def test_extract_tool_uses() -> None:
    ev = {
        "message": {
            "content": [
                {"type": "text", "text": "hello"},
                {"type": "tool_use", "name": "Bash"},
                {"type": "tool_use", "name": "Read"},
            ]
        }
    }
    assert extract_tool_uses(ev) == ["Bash", "Read"]


def test_extract_tool_uses_empty() -> None:
    assert extract_tool_uses({}) == []
    assert extract_tool_uses({"message": {"content": None}}) == []


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
@given(st.text())
def test_iter_events_never_raises_on_arbitrary_text(tmp_path: Path, txt: str) -> None:
    p = tmp_path / "fuzz.jsonl"
    p.write_text(txt)
    # Must not raise
    list(iter_events(p))
