"""Daemon: Unix-socket listener → SQLite + in-memory subscribers."""
from __future__ import annotations

import asyncio
import json
import os
import time
from collections.abc import AsyncIterator
from pathlib import Path

from observatory_core.store import Store

from healthdoctor import SOCKET_PATH_DEFAULT


class Daemon:
    def __init__(self, db_path: Path, socket_path: str = SOCKET_PATH_DEFAULT):
        self.store = Store(db_path)
        self.socket_path = socket_path
        self.subscribers: set[asyncio.Queue] = set()
        self._server: asyncio.base_events.Server | None = None

    async def _broadcast(self, event: dict) -> None:
        for q in list(self.subscribers):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass  # drop on slow subscriber

    async def _handle_client(self, reader: asyncio.StreamReader, _w: asyncio.StreamWriter) -> None:
        while True:
            try:
                line = await reader.readline()
            except (ConnectionError, asyncio.IncompleteReadError):
                return
            if not line:
                return
            try:
                ev = json.loads(line.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                continue
            ev.setdefault("ts", time.time())
            self.store.insert_event(
                ts=ev.get("ts", time.time()),
                kind=ev.get("kind", "hook"),
                hook=ev.get("hook"),
                tool=ev.get("tool"),
                duration_ms=ev.get("duration_ms"),
                exit_code=ev.get("exit_code"),
                payload=ev,
            )
            await self._broadcast(ev)

    async def start(self) -> None:
        try:
            os.unlink(self.socket_path)
        except FileNotFoundError:
            pass
        self._server = await asyncio.start_unix_server(self._handle_client, path=self.socket_path)
        os.chmod(self.socket_path, 0o600)

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
        try:
            os.unlink(self.socket_path)
        except FileNotFoundError:
            pass
        self.store.close()

    async def serve_forever(self) -> None:
        assert self._server is not None
        async with self._server:
            await self._server.serve_forever()

    def subscribe(self) -> "Subscription":
        q: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.subscribers.add(q)
        return Subscription(self, q)


class Subscription:
    def __init__(self, daemon: Daemon, q: asyncio.Queue):
        self.daemon = daemon
        self.q = q

    async def __aiter__(self) -> AsyncIterator[dict]:
        try:
            while True:
                ev = await self.q.get()
                yield ev
        finally:
            self.daemon.subscribers.discard(self.q)
