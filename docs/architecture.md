# Architecture

## Layers

```
┌────────────────────────────────────────────────────────────────┐
│  Sources                                                       │
│  ─ ~/.claude/projects/<project>/<session>.jsonl  (replay)      │
│  ─ healthdoctor-shim.sh → /tmp/claude-observatory.sock  (live)    │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│  observatory_core                                              │
│  ─ jsonl.py    total parser, never raises                      │
│  ─ pricing.py  Anthropic price table, monotonic cost_usd       │
│  ─ store.py    SQLite WAL, events + sessions + suggestions     │
│  ─ ingest.py   batch JSONL → store                             │
│  ─ reports.py  cost + cache aggregation                        │
│  ─ lint.py     CLAUDE.md linter                                │
│  ─ cli.py      `observatory` dispatcher                        │
└────────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼──────────────────┐
            ▼                 ▼                  ▼
┌─────────────────┐ ┌──────────────────┐ ┌────────────────────┐
│ healthdoctor       │ │ healthcheck          │ │ observatory_web    │
│ ─ daemon (sock) │ │ ─ analyze        │ │ ─ FastAPI app      │
│ ─ TUI (Textual) │ │ ─ rules (5)      │ │ ─ HTMX templates   │
│ ─ install/CLI   │ │ ─ ab harness     │ │ ─ SSE stream       │
│                 │ │ ─ auto-PR        │ │                    │
└─────────────────┘ └──────────────────┘ └────────────────────┘
```

## Data model

### `events` table
- `id INTEGER PRIMARY KEY`
- `ts REAL` — unix epoch seconds
- `session TEXT` — Claude Code sessionId
- `kind TEXT` — `usage` | `tool_use` | `hook` | `message`
- `tool TEXT` — tool name when kind=tool_use
- `hook TEXT` — hook name (PreToolUse, etc.)
- `duration_ms INTEGER`
- `exit_code INTEGER`
- `cost_usd REAL`
- `payload TEXT` — full JSON

### `sessions` table
- `id TEXT PRIMARY KEY` — sessionId
- `started_at REAL`, `last_seen_at REAL`
- `model TEXT`, `total_cost_usd REAL`, `project TEXT`

### `suggestions` table
- `id INTEGER PRIMARY KEY`
- `kind`, `target`, `diff`, `rationale`, `evidence`, `confidence`, `status`

## Hook shim protocol

Each shim invocation emits one NDJSON record to the Unix socket:

```json
{
  "ts": 1747958400.123,
  "kind": "hook",
  "hook": "PreToolUse",
  "exit_code": 0,
  "duration_ms": 12,
  "stdin": "...",
  "stdout": "..."
}
```

Failures in the shim never propagate to Claude Code: stdio is forwarded first, telemetry emission is best-effort and runs in a background subshell.

## Performance

- JSONL reader is streaming; constant memory regardless of file size.
- SQLite WAL mode supports concurrent reads from TUI/web while daemon writes.
- Recommendation engine is pure functions; analysis fits in memory for ≥10k sessions on a laptop.
