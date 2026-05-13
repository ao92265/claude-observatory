"""JSONL session-transcript reader (Claude Code format).

Robust against malformed/truncated lines. Total function (never raises on bad input).
"""
from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

DEFAULT_ROOT = Path.home() / ".claude" / "projects"


def session_files(root: Path | None = None) -> Iterator[Path]:
    base = root or DEFAULT_ROOT
    if not base.exists():
        return
    yield from base.rglob("*.jsonl")


def iter_events(path: Path) -> Iterator[dict]:
    """Yield parsed events; skip malformed lines silently."""
    try:
        fh = path.open()
    except OSError:
        return
    with fh as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def extract_usage(event: dict) -> dict | None:
    """Normalize token-usage fields from an assistant message event."""
    if not isinstance(event, dict):
        return None
    msg = event.get("message")
    if not isinstance(msg, dict):
        return None
    usage = msg.get("usage")
    if not isinstance(usage, dict):
        return None
    return {
        "model": msg.get("model"),
        "input": int(usage.get("input_tokens", 0) or 0),
        "output": int(usage.get("output_tokens", 0) or 0),
        "cache_read": int(usage.get("cache_read_input_tokens", 0) or 0),
        "cache_create": int(usage.get("cache_creation_input_tokens", 0) or 0),
        "timestamp": event.get("timestamp"),
        "session": event.get("sessionId"),
        "is_sidechain": bool(event.get("isSidechain", False)),
    }


def extract_tool_uses(event: dict) -> list[str]:
    """Return list of tool names invoked in an assistant message."""
    if not isinstance(event, dict):
        return []
    msg = event.get("message")
    if not isinstance(msg, dict):
        return []
    content = msg.get("content")
    if not isinstance(content, list):
        return []
    names: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            name = block.get("name")
            if isinstance(name, str):
                names.append(name)
    return names
