"""Anthropic pricing tables + cost calculation."""
from __future__ import annotations

# USD per 1M tokens (approximate, May 2026)
PRICING: dict[str, dict[str, float]] = {
    "opus": {"input": 15.0, "output": 75.0, "cache_read": 1.50, "cache_create": 18.75},
    "sonnet": {"input": 3.0, "output": 15.0, "cache_read": 0.30, "cache_create": 3.75},
    "haiku": {"input": 1.0, "output": 5.0, "cache_read": 0.10, "cache_create": 1.25},
}


def model_family(model: str | None) -> str:
    if not model:
        return "sonnet"
    m = model.lower()
    if "opus" in m:
        return "opus"
    if "haiku" in m:
        return "haiku"
    return "sonnet"


def cost_usd(usage: dict) -> float:
    """Compute USD cost. Monotonic in token counts."""
    p = PRICING[model_family(usage.get("model"))]
    return (
        usage.get("input", 0) * p["input"]
        + usage.get("output", 0) * p["output"]
        + usage.get("cache_read", 0) * p["cache_read"]
        + usage.get("cache_create", 0) * p["cache_create"]
    ) / 1_000_000
