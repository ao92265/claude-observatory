"""Generate sanitized JSONL fixture files for tests + demos."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent


def session(sid: str, model: str, msgs: int = 5, sidechain: bool = False) -> list[dict]:
    out = []
    base = time.time() - 86400
    for i in range(msgs):
        out.append(
            {
                "type": "assistant",
                "sessionId": sid,
                "isSidechain": sidechain,
                "timestamp": time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime(base + i * 60)
                ),
                "uuid": f"{sid}-{i}",
                "message": {
                    "model": model,
                    "role": "assistant",
                    "type": "message",
                    "content": [
                        {"type": "text", "text": f"step {i}"},
                        {"type": "tool_use", "id": f"t{i}", "name": "Bash", "input": {"command": "ls"}},
                    ],
                    "usage": {
                        "input_tokens": 50,
                        "output_tokens": 200,
                        "cache_read_input_tokens": 10000 if i > 0 else 0,
                        "cache_creation_input_tokens": 5000 if i == 0 else 0,
                    },
                },
            }
        )
    return out


def write(path: Path, events: list[dict]) -> None:
    with path.open("w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    write(HERE / "small.jsonl", session("small-sess", "claude-sonnet-4-6", msgs=3))
    write(HERE / "medium.jsonl", session("medium-sess", "claude-opus-4-7", msgs=20))
    write(
        HERE / "sidechain.jsonl",
        session("main-sess", "claude-sonnet-4-6", msgs=5)
        + session("sub-sess", "claude-haiku-4-5", msgs=10, sidechain=True),
    )
    print(f"wrote 3 fixtures to {HERE}")


if __name__ == "__main__":
    sys.exit(main() or 0)
