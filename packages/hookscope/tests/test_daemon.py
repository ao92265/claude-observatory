"""End-to-end test: socket client → daemon → SQLite."""
from __future__ import annotations

import asyncio
import json
import socket
from pathlib import Path

import pytest

from hookscope.daemon import Daemon


@pytest.mark.asyncio
async def test_daemon_ingests_socket_event(tmp_path: Path) -> None:
    import tempfile, uuid
    sock_path = f"{tempfile.gettempdir()}/obs-{uuid.uuid4().hex[:8]}.sock"
    d = Daemon(tmp_path / "t.db", socket_path=sock_path)
    await d.start()
    serve = asyncio.create_task(d.serve_forever())
    try:

        def send() -> None:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(sock_path)
            s.sendall(
                (
                    json.dumps(
                        {
                            "ts": 1.5,
                            "kind": "hook",
                            "hook": "PreToolUse",
                            "duration_ms": 12,
                            "exit_code": 0,
                        }
                    )
                    + "\n"
                ).encode()
            )
            s.close()

        await asyncio.to_thread(send)
        await asyncio.sleep(0.1)

        rows = d.store.recent_events(5)
        assert len(rows) == 1
        assert rows[0]["hook"] == "PreToolUse"
        assert rows[0]["duration_ms"] == 12
    finally:
        serve.cancel()
        try:
            await serve
        except (asyncio.CancelledError, Exception):
            pass
        await d.stop()


@pytest.mark.asyncio
async def test_daemon_skips_malformed(tmp_path: Path) -> None:
    import tempfile, uuid
    sock_path = f"{tempfile.gettempdir()}/obs-{uuid.uuid4().hex[:8]}.sock"
    d = Daemon(tmp_path / "t.db", socket_path=sock_path)
    await d.start()
    serve = asyncio.create_task(d.serve_forever())
    try:

        def send() -> None:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(sock_path)
            s.sendall(b"NOT JSON\n")
            s.sendall((json.dumps({"kind": "hook", "hook": "X"}) + "\n").encode())
            s.close()

        await asyncio.to_thread(send)
        await asyncio.sleep(0.1)

        rows = d.store.recent_events(5)
        assert len(rows) == 1
        assert rows[0]["hook"] == "X"
    finally:
        serve.cancel()
        try:
            await serve
        except (asyncio.CancelledError, Exception):
            pass
        await d.stop()
