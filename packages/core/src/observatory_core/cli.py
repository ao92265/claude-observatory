"""Unified `observatory` CLI."""
from __future__ import annotations

import argparse
import sys

USAGE = """observatory <command> [args]

Commands:
  hookscope         Live hook + tool timeline (TUI / web)
  ccpilot           Recommend + A/B test optimizations
  ingest            One-shot JSONL ingest into local store
  cost              Per-session cost ledger
  cache             Prompt-cache hit rate
  lint              CLAUDE.md / AGENTS.md linter
  version           Print version
"""


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help", "help"}:
        print(USAGE)
        return 0
    cmd = args.pop(0)
    sys.argv = ["observatory", *args]

    if cmd == "version":
        from observatory_core import __version__

        print(__version__)
        return 0
    if cmd == "ingest":
        from observatory_core.ingest import main as m

        return m() or 0
    if cmd == "cost":
        from observatory_core.reports import cost_main as m

        return m() or 0
    if cmd == "cache":
        from observatory_core.reports import cache_main as m

        return m() or 0
    if cmd == "lint":
        from observatory_core.lint import main as m

        return m() or 0
    if cmd == "hookscope":
        try:
            from hookscope.cli import main as m
        except ImportError:
            print("hookscope package not installed", file=sys.stderr)
            return 2
        return m() or 0
    if cmd == "ccpilot":
        try:
            from ccpilot.cli import main as m
        except ImportError:
            print("ccpilot package not installed", file=sys.stderr)
            return 2
        return m() or 0

    print(USAGE, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
