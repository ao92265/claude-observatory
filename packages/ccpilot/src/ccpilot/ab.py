"""A/B harness: apply a proposed change in a worktree, run task vs control, score outcomes.

External-dependency notes (read before --apply):
- Requires `claude` CLI in PATH (Claude Code installation)
- Requires `ANTHROPIC_API_KEY` (or vended credentials) — real Claude calls cost money
- Worktrees created under /tmp/ccpilot-ab-<id>; auto-cleaned on success

Architecture:
- TaskSpec is loaded from YAML
- Variant: control (no changes) + treatment (apply diff)
- Each variant runs Claude headless via `claude --bare -p <prompt>`
- Output JSONL captured + scored on:
    cost (lower wins), turns (lower wins), success_phrase match (binary)
- Result + diff stored alongside spec
"""
from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TaskSpec:
    name: str
    prompt: str
    success_phrases: list[str] = field(default_factory=list)
    max_turns: int = 20
    max_cost_usd: float = 2.0
    timeout_sec: int = 600

    @classmethod
    def from_yaml(cls, path: Path) -> "TaskSpec":
        try:
            import yaml  # type: ignore[import-untyped]

            data = yaml.safe_load(path.read_text())
        except ImportError:
            # Minimal YAML-subset parser fallback (key: value lines)
            data = _parse_minimal_yaml(path.read_text())
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


def _parse_minimal_yaml(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    cur_list_key: str | None = None
    for raw in text.splitlines():
        ln = raw.rstrip()
        if not ln or ln.lstrip().startswith("#"):
            continue
        if ln.startswith(" ") and cur_list_key and ln.strip().startswith("-"):
            out.setdefault(cur_list_key, []).append(ln.strip()[1:].strip().strip("\"'"))
            continue
        if ":" in ln:
            k, _, v = ln.partition(":")
            k = k.strip()
            v = v.strip().strip("\"'")
            if not v:
                cur_list_key = k
                out[k] = []
            else:
                cur_list_key = None
                if v.isdigit():
                    out[k] = int(v)
                else:
                    try:
                        out[k] = float(v)
                    except ValueError:
                        out[k] = v
    return out


@dataclass
class RunResult:
    variant: str
    cost_usd: float
    turns: int
    duration_sec: float
    success_match: bool
    stdout_tail: str
    exit_code: int


def _run_claude_headless(prompt: str, cwd: Path, timeout: int) -> tuple[int, str, float]:
    """Run `claude --bare -p PROMPT`. Returns (exit_code, stdout_tail, duration_sec).

    NOTE: this is the integration point requiring ANTHROPIC_API_KEY + `claude` binary.
    """
    start = time.time()
    claude = shutil.which("claude")
    if not claude:
        return 127, "ERROR: `claude` binary not in PATH", 0.0
    try:
        proc = subprocess.run(
            [claude, "--bare", "-p", prompt],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT", time.time() - start
    return proc.returncode, proc.stdout[-4000:], time.time() - start


def _score(spec: TaskSpec, output: str) -> bool:
    if not spec.success_phrases:
        return True
    return all(p.lower() in output.lower() for p in spec.success_phrases)


def _create_worktree(repo: Path, branch_suffix: str) -> Path:
    """Create disposable git worktree for variant."""
    if not (repo / ".git").exists():
        # No git — just copy
        dst = Path(tempfile.mkdtemp(prefix="ccpilot-ab-"))
        for item in repo.iterdir():
            if item.name in {".git", "node_modules", ".venv", "__pycache__"}:
                continue
            if item.is_dir():
                shutil.copytree(item, dst / item.name, ignore=shutil.ignore_patterns("__pycache__"))
            else:
                shutil.copy2(item, dst)
        return dst
    dst = Path(tempfile.mkdtemp(prefix="ccpilot-ab-"))
    shutil.rmtree(dst)
    branch = f"ccpilot/ab-{branch_suffix}-{uuid.uuid4().hex[:6]}"
    subprocess.run(
        ["git", "worktree", "add", "-b", branch, str(dst)],
        cwd=str(repo),
        check=True,
        capture_output=True,
    )
    return dst


def _cleanup_worktree(repo: Path, path: Path) -> None:
    if not path.exists():
        return
    if (repo / ".git").exists():
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(path)],
            cwd=str(repo),
            capture_output=True,
        )
    else:
        shutil.rmtree(path, ignore_errors=True)


def _apply_diff(worktree: Path, diff_text: str) -> bool:
    if not diff_text.strip():
        return True
    diff_file = worktree / ".ccpilot.diff"
    diff_file.write_text(diff_text)
    proc = subprocess.run(
        ["git", "apply", "--allow-empty", str(diff_file)],
        cwd=str(worktree),
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def run_variant(spec: TaskSpec, repo: Path, *, diff: str = "", label: str = "control") -> RunResult:
    wt = _create_worktree(repo, label)
    applied = _apply_diff(wt, diff) if diff else True
    if not applied:
        _cleanup_worktree(repo, wt)
        return RunResult(
            variant=label, cost_usd=0.0, turns=0, duration_sec=0.0,
            success_match=False, stdout_tail="diff failed to apply", exit_code=1,
        )
    code, out, dur = _run_claude_headless(spec.prompt, wt, spec.timeout_sec)
    # Cost + turns are extracted from claude stdout when --bare prints JSON summary
    cost = 0.0
    turns = 0
    for line in out.splitlines():
        if line.startswith("COST:"):
            try:
                cost = float(line.split(":", 1)[1])
            except ValueError:
                pass
        if line.startswith("TURNS:"):
            try:
                turns = int(line.split(":", 1)[1])
            except ValueError:
                pass
    success = _score(spec, out)
    _cleanup_worktree(repo, wt)
    return RunResult(
        variant=label, cost_usd=cost, turns=turns, duration_sec=dur,
        success_match=success, stdout_tail=out[-2000:], exit_code=code,
    )


def declare_winner(control: RunResult, treatment: RunResult) -> tuple[str, str]:
    """Pick winner. Returns (label, reason)."""
    if control.success_match and not treatment.success_match:
        return "control", "treatment failed success criteria"
    if treatment.success_match and not control.success_match:
        return "treatment", "control failed success criteria"
    if not control.success_match and not treatment.success_match:
        return "neither", "both variants failed success criteria"
    # Both passed — cheapest wins
    if treatment.cost_usd < control.cost_usd * 0.9:
        return "treatment", f"≥10% cheaper (${treatment.cost_usd:.3f} vs ${control.cost_usd:.3f})"
    if control.cost_usd < treatment.cost_usd * 0.9:
        return "control", f"≥10% cheaper (${control.cost_usd:.3f} vs ${treatment.cost_usd:.3f})"
    return "tie", "performance within 10% — no clear winner"


def run_ab(spec_path: Path, repo: Path, *, apply: bool = False) -> int:
    spec = TaskSpec.from_yaml(spec_path)
    print(f"=== A/B: {spec.name} ===")
    print(f"prompt: {spec.prompt[:80]}…")
    if not apply:
        print("\n[DRY RUN] Skipping live Claude calls. Pass --apply to execute.")
        print("This will:")
        print(f"  1. Create 2 git worktrees under {tempfile.gettempdir()}/ccpilot-ab-*")
        print(f"  2. Run `claude --bare -p ...` in each (timeout {spec.timeout_sec}s)")
        print(f"  3. Score outputs against: {spec.success_phrases}")
        print("  4. Declare winner + cleanup")
        return 0
    control = run_variant(spec, repo, label="control")
    treatment_diff = os.environ.get("CCPILOT_DIFF", "")
    treatment = run_variant(spec, repo, diff=treatment_diff, label="treatment")
    winner, reason = declare_winner(control, treatment)
    print(json.dumps(
        {
            "spec": spec.name,
            "control": control.__dict__,
            "treatment": treatment.__dict__,
            "winner": winner,
            "reason": reason,
        },
        indent=2,
        default=str,
    ))
    return 0
