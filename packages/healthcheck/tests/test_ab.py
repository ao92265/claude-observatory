from __future__ import annotations

from pathlib import Path

from healthcheck.ab import RunResult, TaskSpec, _parse_minimal_yaml, declare_winner


def test_minimal_yaml_parser() -> None:
    text = """
name: fast-fix
prompt: do the thing
max_turns: 5
max_cost_usd: 1.5
success_phrases:
  - done
  - passed
"""
    out = _parse_minimal_yaml(text)
    assert out["name"] == "fast-fix"
    assert out["max_turns"] == 5
    assert out["max_cost_usd"] == 1.5
    assert out["success_phrases"] == ["done", "passed"]


def test_taskspec_from_yaml(tmp_path: Path) -> None:
    p = tmp_path / "spec.yaml"
    p.write_text("name: t1\nprompt: hi\nmax_turns: 3\n")
    s = TaskSpec.from_yaml(p)
    assert s.name == "t1"
    assert s.max_turns == 3


def test_declare_winner_treatment_failed() -> None:
    c = RunResult("control", 1.0, 5, 10.0, True, "", 0)
    t = RunResult("treatment", 0.5, 3, 8.0, False, "", 0)
    w, _ = declare_winner(c, t)
    assert w == "control"


def test_declare_winner_treatment_cheaper() -> None:
    c = RunResult("control", 1.0, 5, 10.0, True, "", 0)
    t = RunResult("treatment", 0.5, 3, 8.0, True, "", 0)
    w, _ = declare_winner(c, t)
    assert w == "treatment"


def test_declare_winner_tie() -> None:
    c = RunResult("control", 1.0, 5, 10.0, True, "", 0)
    t = RunResult("treatment", 0.95, 5, 9.5, True, "", 0)
    w, _ = declare_winner(c, t)
    assert w == "tie"


def test_declare_winner_both_failed() -> None:
    c = RunResult("control", 0.1, 1, 1.0, False, "", 1)
    t = RunResult("treatment", 0.1, 1, 1.0, False, "", 1)
    w, _ = declare_winner(c, t)
    assert w == "neither"
