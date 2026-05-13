"""observatory-web CLI."""
from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_DB = Path.home() / ".claude-observatory" / "observatory.db"


def main() -> int:
    p = argparse.ArgumentParser(prog="observatory-web")
    p.add_argument("--db", default=str(DEFAULT_DB))
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8088)
    p.add_argument("--reload", action="store_true")
    args = p.parse_args()

    import uvicorn

    from observatory_web.app import create_app

    app = create_app(Path(args.db))
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
