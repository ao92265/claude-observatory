"""ccpilot CLI."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ccpilot.analyze import build_analysis
from ccpilot.rules import run_all


def cmd_suggest(args: argparse.Namespace) -> int:
    claude_md = Path(args.claude_md).expanduser() if args.claude_md else None
    a = build_analysis(window_days=args.days, claude_md_path=claude_md)
    suggestions = run_all(a)

    if args.json:
        print(json.dumps([s.to_dict() for s in suggestions], indent=2, default=str))
        return 0

    print(
        f"\n=== ccpilot suggest (window={args.days}d, {a.total_events} events, "
        f"${a.total_cost():.2f} spent) ===\n"
    )
    if not suggestions:
        print("No suggestions — your setup looks healthy.")
        return 0
    for i, s in enumerate(suggestions[: args.top], 1):
        print(f"{i}. [{s.kind}] {s.target}  (confidence {s.confidence:.0%})")
        print(f"   {s.rationale}")
        if s.estimated_savings_usd_month:
            print(f"   Est. savings: ${s.estimated_savings_usd_month:.2f}/mo")
        print()
    return 0


def cmd_ab(args: argparse.Namespace) -> int:
    from ccpilot.ab import run_ab

    return run_ab(Path(args.spec), Path(args.repo), apply=args.apply)


def cmd_pr(args: argparse.Namespace) -> int:
    from ccpilot.pr import open_pr_from_suggestion

    return open_pr_from_suggestion(
        Path(args.repo), suggestion_id=args.id, dry_run=not args.apply
    )


def main() -> int:
    p = argparse.ArgumentParser(prog="ccpilot")
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("suggest", help="emit ranked optimization suggestions")
    ps.add_argument("--days", type=int, default=30)
    ps.add_argument("--top", type=int, default=15)
    ps.add_argument("--json", action="store_true")
    ps.add_argument("--claude-md", help="path to CLAUDE.md to lint")
    ps.set_defaults(func=cmd_suggest)

    pa = sub.add_parser("ab", help="run A/B variant comparison")
    pa.add_argument("--spec", required=True, help="task spec YAML")
    pa.add_argument("--repo", required=True, help="repo path to worktree from")
    pa.add_argument("--apply", action="store_true")
    pa.set_defaults(func=cmd_ab)

    pr = sub.add_parser("pr", help="open PR from a suggestion")
    pr.add_argument("--id", required=True, help="suggestion id")
    pr.add_argument("--repo", required=True)
    pr.add_argument("--apply", action="store_true", help="actually push + open PR")
    pr.set_defaults(func=cmd_pr)

    args = p.parse_args()
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
