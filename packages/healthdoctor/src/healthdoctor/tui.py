"""Textual TUI for live hook timeline."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

from observatory_core.store import Store

try:
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.reactive import reactive
    from textual.widgets import DataTable, Footer, Header, Static
except ImportError:  # pragma: no cover
    App = None  # type: ignore[assignment]


class HookscopeApp(App):  # type: ignore[misc]
    CSS = """
    Screen { layout: vertical; }
    #table { height: 70%; }
    #detail { height: 30%; border: solid green; padding: 1; overflow: auto; }
    """
    BINDINGS = [("q", "quit", "Quit"), ("r", "refresh", "Refresh"), ("c", "clear", "Clear")]

    selected_id: reactive[int | None] = reactive(None)

    def __init__(self, store: Store, poll_interval: float = 0.5):
        super().__init__()
        self.store = store
        self.poll_interval = poll_interval
        self._last_id = 0
        self._events: dict[int, dict] = {}

    def compose(self) -> ComposeResult:
        yield Header()
        table = DataTable(id="table")
        table.add_columns("id", "ts", "kind", "hook/tool", "dur(ms)", "exit", "cost$")
        table.cursor_type = "row"
        yield table
        yield Static("Select a row for details.", id="detail")
        yield Footer()

    async def on_mount(self) -> None:
        self.set_interval(self.poll_interval, self._poll)
        await self._poll()

    async def _poll(self) -> None:
        rows = self.store.recent_events(limit=200)
        table = self.query_one("#table", DataTable)
        for row in reversed(rows):
            rid = row["id"]
            if rid <= self._last_id:
                continue
            self._last_id = rid
            self._events[rid] = row
            ts = datetime.fromtimestamp(row["ts"]).strftime("%H:%M:%S")
            table.add_row(
                str(rid),
                ts,
                row["kind"] or "",
                row.get("hook") or row.get("tool") or "",
                str(row.get("duration_ms") or ""),
                str(row.get("exit_code") if row.get("exit_code") is not None else ""),
                f"{row.get('cost_usd'):.4f}" if row.get("cost_usd") else "",
                key=str(rid),
            )

    def on_data_table_row_selected(self, event) -> None:  # type: ignore[no-untyped-def]
        try:
            rid = int(event.row_key.value)
        except (AttributeError, ValueError, TypeError):
            return
        ev = self._events.get(rid)
        if not ev:
            return
        detail = self.query_one("#detail", Static)
        detail.update(json.dumps(ev.get("payload", ev), indent=2, default=str))

    def action_clear(self) -> None:
        table = self.query_one("#table", DataTable)
        table.clear()
        self._last_id = 0
        self._events.clear()


async def run_tui(db_path: Path) -> None:
    if App is None:
        raise RuntimeError("textual not installed; pip install textual")
    store = Store(db_path)
    app = HookscopeApp(store)
    await app.run_async()
    store.close()


def main_tui(db_path: Path) -> None:
    asyncio.run(run_tui(db_path))
