from __future__ import annotations

from hypothesis import given, strategies as st

from observatory_core.pricing import cost_usd, model_family


def test_model_family() -> None:
    assert model_family("claude-opus-4-7") == "opus"
    assert model_family("claude-sonnet-4-6") == "sonnet"
    assert model_family("claude-haiku-4-5") == "haiku"
    assert model_family(None) == "sonnet"
    assert model_family("") == "sonnet"


def test_cost_known_values() -> None:
    # Sonnet: 1M output tokens = $15
    assert cost_usd({"model": "sonnet", "output": 1_000_000, "input": 0, "cache_read": 0, "cache_create": 0}) == 15.0


@given(
    extra=st.integers(min_value=0, max_value=1_000_000),
    field=st.sampled_from(["input", "output", "cache_read", "cache_create"]),
)
def test_cost_is_monotonic(extra: int, field: str) -> None:
    base = {"model": "sonnet", "input": 100, "output": 200, "cache_read": 300, "cache_create": 400}
    bigger = {**base, field: base[field] + extra}
    assert cost_usd(bigger) >= cost_usd(base)
