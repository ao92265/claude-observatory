<div align="center">

# 🔭 Claude Observatory

**Local-first observability and closed-loop self-improvement for Claude Code.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![tests](https://img.shields.io/badge/tests-36%20passing-brightgreen.svg)](#)
[![status](https://img.shields.io/badge/status-v0.1.0-orange.svg)](ROADMAP.md)

*Two products, one toolkit, zero telemetry.*

</div>

---

## What is this?

Claude Code is a great platform — but it's a black box. You can't see which hooks fire, which skills get invoked, where your tokens are burning, or which CLAUDE.md rules are silently ignored.

**Claude Observatory fixes that.** Two tightly-integrated tools share one local data plane:

| Tool | What it does |
|---|---|
| 🩺 **HealthDoctor** | Live timeline of every hook, tool call, and MCP request — like Chrome DevTools for Claude Code. |
| ❤️‍🩹 **HealthCheck** | Reads your usage history, suggests fixes (drop unused tools, downgrade opus-on-trivial, strengthen CLAUDE.md), then A/B tests them and opens evidence-backed PRs. |

Everything runs on your machine. No cloud. No analytics. No telemetry. Just your own `~/.claude/projects/**/*.jsonl` surfaced and acted on.

---

## ⚡ 60-second tour

```bash
# 1. Install
git clone https://github.com/ao92265/claude-observatory.git
cd claude-observatory && python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/core -e packages/healthdoctor -e packages/healthcheck -e packages/web

# 2. See what you've spent + where your cache is leaking
observatory cost --days 7
observatory cache --days 30

# 3. Get ranked optimization suggestions
healthcheck suggest --days 30 --claude-md ~/.claude/CLAUDE.md

# 4. Watch hooks fire live
healthdoctor install      # one-time, backs up settings.json
healthdoctor daemon &     # listener
observatory-web           # http://127.0.0.1:8088
```

---

## 🩺 HealthDoctor — live observability

A drop-in shim wraps every Claude Code hook, captures stdio + timing, and streams the events into a local SQLite store. Two viewers ship out of the box:

- **Terminal UI** (Textual) — `healthdoctor tui`
- **Web UI** (FastAPI + HTMX + SSE) — `observatory-web`

You see, in real time:

- Every `PreToolUse` / `PostToolUse` / `UserPromptSubmit` hook fire
- Hook duration, exit code, stdin/stdout payload
- Tool invocations correlated with usage events
- Filter by kind, search by tool name, click any row for the raw JSON

Install is reversible: `healthdoctor uninstall` removes the shim and restores your settings backup.

---

## ❤️‍🩹 HealthCheck — closed-loop optimizer

HealthCheck reads the same JSONL transcripts and emits ranked, evidence-backed suggestions across five built-in rules:

| Rule | Catches |
|---|---|
| `unused-tool` | Tools / MCP servers invoked < 5× in 30 days — schema overhead with no payoff |
| `opus-for-simple-work` | Opus sessions under $2 — sonnet would do the job at ~5× cheaper |
| `low-cache-hit` | Sessions burning `cache_creation` without reads — CLAUDE.md churn or session length |
| `weak-claude-md` | Hedging phrases ("you should", "usually") that get ignored more than imperatives |
| `high-tool-concentration` | One tool dominating > 60% of calls — a workflow worth abstracting |

Each suggestion includes confidence, projected $/mo savings, raw evidence, and a structured `diff`. Pipe them anywhere:

```bash
healthcheck suggest --json | jq '.[] | select(.confidence > 0.6)'
```

Then A/B test the change before adopting it:

```bash
healthcheck ab --spec examples/ab-spec.yaml --repo .          # dry-run preview
healthcheck ab --spec examples/ab-spec.yaml --repo . --apply  # runs claude in worktree
```

Or open a PR with the suggestion already applied and the evidence in the body:

```bash
healthcheck pr --id opus-downgrade:abc123 --repo .          # dry-run
healthcheck pr --id opus-downgrade:abc123 --repo . --apply  # branch + commit + gh pr create
```

---

## 🏗️ Architecture

```
~/.claude/projects/*.jsonl ──┐
                             ├──► observatory_core (parser, pricing, store)
   healthdoctor-shim.sh ─────┘                │
   (NDJSON / Unix socket)                     ▼
                                  ┌────  SQLite WAL  ────┐
                                  ▼          ▼            ▼
                            healthdoctor  healthcheck  observatory_web
                            (TUI/daemon)  (rules+A/B)  (FastAPI+HTMX)
```

- **Total parser** — never raises on malformed JSONL; property-tested with Hypothesis
- **WAL-mode SQLite** — concurrent reads from TUI/web while daemon writes
- **Pure rules engine** — recommendations are deterministic, replayable, machine-readable
- **Shim** — fail-safe; telemetry emission is best-effort and never blocks the parent hook

Full details: [`docs/architecture.md`](docs/architecture.md) · [`docs/threat-model.md`](docs/threat-model.md)

---

## 📊 Status

| Phase | Output | Status |
|---|---|---|
| 0 | Monorepo, core package, fixtures, CI | ✅ shipped |
| 1 | HealthDoctor MVP (shim + daemon + TUI) | ✅ shipped |
| 2 | Web UI (FastAPI + HTMX + SSE) | ✅ shipped |
| 3 | HealthCheck recommender (5 rules) | ✅ shipped |
| 4 | HealthCheck A/B harness (worktree + scorer) | ✅ shipped |
| 5 | Auto-PR with evidence body | ✅ shipped |
| 6 | README, docs, threat model, landing | ✅ shipped |
| v1.0 | Demo screencasts, PyPI/Homebrew | ⏳ pending |

**36/36 tests passing.** macOS + Linux, Python 3.11 / 3.12.

See [`ROADMAP.md`](ROADMAP.md) and [`BUILD_PLAN.md`](BUILD_PLAN.md).

---

## 🔒 Security & privacy

- **Local-first.** Nothing leaves your machine. No analytics. No telemetry. No phone-home.
- **Audit-friendly.** ~1500 lines of pure stdlib + FastAPI + Textual. Read it all in an afternoon.
- **Shim is fail-safe.** Stdio forwarded to parent first; telemetry emission is best-effort.
- **Install backs up settings.json.** `healthdoctor uninstall` cleanly removes only what it added.
- **Destructive ops are dry-run by default.** `--apply` required for live billed Claude calls, PR creation, file writes.
- **Threat model is public.** See [`docs/threat-model.md`](docs/threat-model.md).

---

## 🤝 Contributing

Issues + PRs welcome. The codebase is organized as a uv-style workspace under `packages/`:

```
packages/
├── core/          shared JSONL reader, pricing, SQLite store, observatory CLI
├── healthdoctor/  shim, daemon, TUI
├── healthcheck/   recommender, A/B harness, auto-PR
├── web/           FastAPI + HTMX + SSE
└── shim/          bash hook wrapper
```

Run the suite:

```bash
pytest packages -q     # 36 tests, ~1s
ruff check packages
```

---

## 📜 License

Apache 2.0. See [`LICENSE`](LICENSE).

---

<div align="center">

Built by [@ao92265](https://github.com/ao92265). The CLI you wish came with Claude Code.

</div>
