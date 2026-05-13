# Claude Observatory

Local-first observability + closed-loop self-improvement for [Claude Code](https://claude.com/claude-code).

Two products, one data plane:

- **HookScope** — live timeline of hooks, tools, and MCP calls. DevTools for Claude Code plugin authors.
- **CCPilot** — recommends + A/B tests + opens PRs that optimize your CLAUDE.md, skills, hooks, and model routing.

No cloud. No telemetry. Reads your local `~/.claude/projects/**/*.jsonl`.

---

## Why

Claude Code is fast becoming a platform — hooks, skills, MCP servers, multi-agent orchestration. The ecosystem ships features faster than it ships tools to measure them. Today there is no live debugger for hooks, no per-skill cost attribution, no automated CLAUDE.md optimizer.

Observatory fills those gaps with a single, dependency-light Python toolkit.

---

## Install

Requires Python 3.11+.

```bash
git clone https://github.com/ao92265/claude-observatory.git
cd claude-observatory
python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/core -e packages/hookscope -e packages/ccpilot -e packages/web
```

---

## Quickstart

### 1. Ingest existing sessions

```bash
observatory ingest          # scans ~/.claude/projects/**/*.jsonl into local SQLite
observatory cost --days 7   # spend per session
observatory cache --days 30 # prompt-cache efficiency
observatory lint ~/.claude/CLAUDE.md
```

### 2. Live timeline (HookScope)

```bash
hookscope install           # adds shim to ~/.claude/settings.json (backed up first)
hookscope daemon &          # listens on /tmp/claude-observatory.sock
hookscope tui               # Textual UI
# OR
observatory-web             # web UI on http://127.0.0.1:8088
```

### 3. Recommendations + A/B (CCPilot)

```bash
ccpilot suggest --days 30 --claude-md ~/.claude/CLAUDE.md
ccpilot suggest --json | jq                 # machine-readable
ccpilot ab --spec examples/ab-spec.yaml --repo .   # dry-run
ccpilot pr --id opus-downgrade:abc123 --repo .     # dry-run PR preview
```

---

## Architecture

```
~/.claude/projects/*.jsonl ──┐
                             ├─► observatory_core.jsonl (parser)
                             │
   hook shim (NDJSON/socket) ┘
                             │
                             ▼
                       SQLite store (WAL)
                             │
                ┌────────────┼───────────────┐
                ▼            ▼               ▼
            hookscope     ccpilot         web UI
            (TUI/daemon)  (rules + A/B)   (FastAPI+HTMX)
```

See [`docs/architecture.md`](docs/architecture.md) and [`docs/threat-model.md`](docs/threat-model.md).

---

## Status

| Phase | Output | Status |
|---|---|---|
| 0 | Monorepo, core package, fixtures, CI | ✅ shipped |
| 1 | HookScope MVP (shim + daemon + TUI) | ✅ shipped |
| 2 | Web UI (FastAPI + HTMX) | ✅ shipped |
| 3 | CCPilot recommender (5 rules) | ✅ shipped |
| 4 | CCPilot A/B harness (worktree + scorer) | ✅ shipped |
| 5 | Auto-PR (gh integration) | ✅ shipped |
| 6 | Polish, README, landing | ✅ shipped |

All 36 tests passing on macOS+Linux, Python 3.11 / 3.12.

See [`ROADMAP.md`](ROADMAP.md) and [`BUILD_PLAN.md`](BUILD_PLAN.md).

---

## Security & privacy

- **Local-first.** No data leaves your machine. No analytics. No telemetry.
- **Hook shim** captures only stdio bytes the hook itself receives. Never reads environment variables, API keys, or files outside the hook's stdin.
- **Install** writes `~/.claude/settings.json.bak.observatory` before touching settings. `hookscope uninstall` removes shim cleanly.
- **A/B harness** is dry-run by default. `--apply` is required for live billed Claude calls.
- See [`docs/threat-model.md`](docs/threat-model.md).

---

## Contributing

Issues + PRs welcome. Phase-gated work — see [`BUILD_PLAN.md`](BUILD_PLAN.md).

```bash
pytest packages -q     # 36 tests, ~1s
ruff check packages
```

---

## License

Apache-2.0. See [`LICENSE`](LICENSE).
