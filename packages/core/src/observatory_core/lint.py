"""CLAUDE.md / AGENTS.md linter."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

LINE_CAP = 150
TOKEN_PER_CHAR = 0.25

CONTRADICTORY_PAIRS = [
    (re.compile(r"\bnever\b.*\bcommit\b", re.I), re.compile(r"\bauto.?commit\b", re.I)),
    (re.compile(r"\bno emoji", re.I), re.compile(r"\buse emoji", re.I)),
    (re.compile(r"\bdo not push\b", re.I), re.compile(r"\bauto.?push\b", re.I)),
]

WEAK_PHRASES = [
    "you should",
    "try to",
    "if possible",
    "where appropriate",
    "as needed",
    "generally",
    "usually",
    "typically",
]


def lint(path: Path) -> list[str]:
    issues: list[str] = []
    if not path.exists():
        return [f"{path}: missing"]
    text = path.read_text(errors="replace")
    lines = text.splitlines()
    est_tokens = int(len(text) * TOKEN_PER_CHAR)

    issues.append(f"{path}: {len(lines)} lines, ~{est_tokens} tokens")
    if len(lines) > LINE_CAP:
        issues.append(
            f"  [BLOAT] over {LINE_CAP}-line cap ({len(lines)}). Reference path:line, drop snippets."
        )

    seen: dict[str, int] = {}
    for i, ln in enumerate(lines, 1):
        norm = ln.strip().lower()
        if len(norm) < 20 or norm.startswith("#"):
            continue
        if norm in seen:
            issues.append(f"  [DUP] line {i} duplicates line {seen[norm]}: {ln.strip()[:60]}")
        else:
            seen[norm] = i

    for i, ln in enumerate(lines, 1):
        low = ln.lower()
        for w in WEAK_PHRASES:
            if w in low:
                issues.append(f"  [HEDGE] line {i}: '{w}' — use MUST/WILL/NEVER")
                break

    for a, b in CONTRADICTORY_PAIRS:
        if a.search(text) and b.search(text):
            issues.append(f"  [CONFLICT] both '{a.pattern}' and '{b.pattern}' present")

    fences = re.findall(r"```[\s\S]*?```", text)
    big = [f for f in fences if len(f) > 400]
    if big:
        issues.append(
            f"  [SNIPPET] {len(big)} large code fence(s) — move to repo, reference by path:line"
        )

    rule_lines = [ln for ln in lines if ln.lstrip().startswith("- ")]
    weak = [ln for ln in rule_lines if not re.search(r"\b(MUST|WILL|NEVER|ALWAYS)\b", ln)]
    if len(rule_lines) > 5 and len(weak) / len(rule_lines) > 0.6:
        issues.append(
            f"  [VOICE] {len(weak)}/{len(rule_lines)} bullets lack MUST/WILL/NEVER/ALWAYS anchor"
        )
    return issues


def discover(roots: list[Path]) -> list[Path]:
    out: list[Path] = []
    for r in roots:
        if r.is_file():
            out.append(r)
            continue
        for name in ("CLAUDE.md", "AGENTS.md"):
            for p in r.rglob(name):
                if ".git" in p.parts or "node_modules" in p.parts:
                    continue
                out.append(p)
    return out


def main() -> int:
    p = argparse.ArgumentParser(prog="observatory lint")
    p.add_argument("paths", nargs="*", default=["."])
    args = p.parse_args()
    targets = discover([Path(x).resolve() for x in args.paths])
    if not targets:
        print("No CLAUDE.md / AGENTS.md found.")
        return 0
    total = 0
    for t in targets:
        issues = lint(t)
        for line in issues:
            print(line)
        total += max(0, len(issues) - 1)
        print()
    print(f"=== {len(targets)} file(s), {total} issue(s) ===")
    return 1 if total else 0
