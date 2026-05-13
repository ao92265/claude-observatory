"""FastAPI app: timeline, replay, search."""
from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from observatory_core.store import Store

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def create_app(db_path: Path) -> FastAPI:
    app = FastAPI(title="Claude Observatory")
    store = Store(db_path)
    app.state.store = store
    app.state.last_id = 0

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        return TEMPLATES.TemplateResponse(request, "index.html", {})

    @app.get("/events", response_class=HTMLResponse)
    async def events(
        request: Request,
        limit: int = 100,
        kind: str | None = None,
        q: str | None = Query(default=None),
    ) -> HTMLResponse:
        rows = store.recent_events(limit=limit)
        if kind:
            rows = [r for r in rows if r["kind"] == kind]
        if q:
            ql = q.lower()
            rows = [
                r
                for r in rows
                if ql
                in (
                    f"{r.get('hook') or ''} {r.get('tool') or ''} "
                    f"{json.dumps(r.get('payload') or '')}".lower()
                )
            ]
        for r in rows:
            r["ts_human"] = datetime.fromtimestamp(r["ts"]).strftime("%H:%M:%S")
        return TEMPLATES.TemplateResponse(
            request, "events.html", {"events": rows}
        )

    @app.get("/event/{event_id}", response_class=HTMLResponse)
    async def event_detail(request: Request, event_id: int) -> HTMLResponse:
        cur = store.conn.execute(
            "SELECT id, ts, session, kind, tool, hook, duration_ms, exit_code, cost_usd, payload "
            "FROM events WHERE id=?",
            (event_id,),
        )
        row = cur.fetchone()
        if not row:
            return HTMLResponse("<pre>not found</pre>", status_code=404)
        cols = [c[0] for c in cur.description]
        d = dict(zip(cols, row, strict=False))
        try:
            d["payload"] = json.loads(d["payload"])
        except (json.JSONDecodeError, TypeError):
            pass
        return TEMPLATES.TemplateResponse(
            request, "detail.html", {"event": d, "payload_pretty": json.dumps(d.get("payload"), indent=2, default=str)}
        )

    @app.get("/stream")
    async def stream() -> StreamingResponse:
        async def gen():
            while True:
                rows = store.recent_events(limit=50)
                new = [r for r in reversed(rows) if r["id"] > app.state.last_id]
                if new:
                    app.state.last_id = new[-1]["id"]
                    payload = json.dumps(
                        [
                            {
                                "id": r["id"],
                                "ts": r["ts"],
                                "kind": r["kind"],
                                "hook": r.get("hook"),
                                "tool": r.get("tool"),
                                "duration_ms": r.get("duration_ms"),
                                "exit_code": r.get("exit_code"),
                            }
                            for r in new
                        ]
                    )
                    yield f"data: {payload}\n\n"
                await asyncio.sleep(0.5)

        return StreamingResponse(gen(), media_type="text/event-stream")

    @app.get("/api/health")
    async def health() -> dict:
        return {"ok": True, "ts": time.time()}

    return app
