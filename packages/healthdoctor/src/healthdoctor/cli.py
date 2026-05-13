"""healthdoctor CLI: install shim, run daemon, run TUI."""
from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import sys
from pathlib import Path

from observatory_core.store import Store

from healthdoctor import SOCKET_PATH_DEFAULT
from healthdoctor.daemon import Daemon

DEFAULT_DB = Path.home() / ".claude-observatory" / "observatory.db"


def cmd_daemon(args: argparse.Namespace) -> int:
    async def run() -> None:
        d = Daemon(Path(args.db), socket_path=args.socket)
        await d.start()
        print(f"daemon listening on {args.socket}; db={args.db}", flush=True)
        try:
            await d.serve_forever()
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            await d.stop()

    asyncio.run(run())
    return 0


def cmd_tail(args: argparse.Namespace) -> int:
    store = Store(Path(args.db))
    rows = store.recent_events(limit=args.n)
    for r in reversed(rows):
        print(
            f"[{r['id']:>5}] {r['kind']:<10} "
            f"{(r.get('hook') or r.get('tool') or ''):<18} "
            f"dur={r.get('duration_ms')} exit={r.get('exit_code')}"
        )
    store.close()
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    settings = Path.home() / ".claude" / "settings.json"
    if not settings.exists():
        print(f"no {settings} — Claude Code not installed?", file=sys.stderr)
        return 2
    backup = settings.with_suffix(".json.bak.observatory")
    if not backup.exists():
        shutil.copy2(settings, backup)
        print(f"backup written → {backup}")
    data = json.loads(settings.read_text())
    hooks = data.setdefault("hooks", {})

    shim_path = Path(__file__).resolve().parents[4] / "packages" / "shim" / "healthdoctor-shim.sh"
    if not shim_path.exists():
        # fall back to PATH lookup
        sh = shutil.which("healthdoctor-shim.sh")
        if sh:
            shim_path = Path(sh)

    marker = "__observatory__"
    for kind in ("PreToolUse", "PostToolUse", "UserPromptSubmit"):
        arr = hooks.setdefault(kind, [])
        if any(h.get(marker) for h in arr if isinstance(h, dict)):
            continue
        arr.append(
            {
                marker: True,
                "matcher": ".*",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"{shim_path} {kind} true",
                    }
                ],
            }
        )
    if args.dry_run:
        print(json.dumps(data, indent=2))
        return 0
    settings.write_text(json.dumps(data, indent=2))
    print(f"installed observatory shim in {settings}")
    print(f"  shim path: {shim_path}")
    print("  uninstall: healthdoctor uninstall")
    return 0


def cmd_uninstall(args: argparse.Namespace) -> int:
    settings = Path.home() / ".claude" / "settings.json"
    if not settings.exists():
        return 0
    data = json.loads(settings.read_text())
    hooks = data.get("hooks", {})
    for kind, arr in list(hooks.items()):
        if isinstance(arr, list):
            hooks[kind] = [h for h in arr if not (isinstance(h, dict) and h.get("__observatory__"))]
    settings.write_text(json.dumps(data, indent=2))
    print("uninstalled observatory shim")
    return 0


def cmd_tui(args: argparse.Namespace) -> int:
    from healthdoctor.tui import main_tui

    main_tui(Path(args.db))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="healthdoctor")
    sub = p.add_subparsers(dest="cmd", required=True)

    pd = sub.add_parser("daemon", help="run socket listener daemon")
    pd.add_argument("--db", default=str(DEFAULT_DB))
    pd.add_argument("--socket", default=SOCKET_PATH_DEFAULT)
    pd.set_defaults(func=cmd_daemon)

    pt = sub.add_parser("tui", help="open live timeline TUI")
    pt.add_argument("--db", default=str(DEFAULT_DB))
    pt.set_defaults(func=cmd_tui)

    pl = sub.add_parser("tail", help="dump last N events")
    pl.add_argument("--db", default=str(DEFAULT_DB))
    pl.add_argument("-n", type=int, default=20)
    pl.set_defaults(func=cmd_tail)

    pi = sub.add_parser("install", help="install shim into ~/.claude/settings.json")
    pi.add_argument("--dry-run", action="store_true")
    pi.set_defaults(func=cmd_install)

    pu = sub.add_parser("uninstall", help="remove shim from ~/.claude/settings.json")
    pu.set_defaults(func=cmd_uninstall)

    args = p.parse_args()
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
