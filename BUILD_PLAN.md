# Claude Observatory — Build & Test Plan

> Working codename: **claude-observatory**. Alternates: `cc-flightdeck`, `cc-meta`, `claude-pulse`, `hookpilot`. Lock name at v0.2.

---

## 1. Product framing

Two products, one repo, shared data plane.

### Product A — HealthDoctor
Real-time DevTools for Claude Code. Live timeline of hook fires, MCP calls, tool invocations. Context-window forensics. Zero competition today.

### Product B — HealthCheck
Closed-loop optimizer. Reads telemetry, drafts CLAUDE.md / skill / hook changes, A/B tests, opens PR with evidence.

### Shared substrate
- JSONL session reader (already prototyped in `cc-tools/`)
- Hook lifecycle shim (new)
- Event bus / local SQLite store (new)
- Analyzer kernel (new)

HealthCheck depends on HealthDoctor telemetry. Build HealthDoctor first, harvest data, then bolt HealthCheck on top.

---

## 2. Repo layout (target)

```
claude-observatory/
├── packages/
│   ├── core/              shared: JSONL reader, schema, pricing, SQLite store
│   ├── healthdoctor/         live timeline TUI + web UI
│   ├── healthcheck/           recommendation + A/B engine
│   └── shim/              tiny bash wrapper for hook stdio capture
├── docs/
│   ├── architecture.md
│   ├── data-model.md
│   └── threat-model.md
├── tests/
│   ├── fixtures/          sanitized JSONL + hook traces
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── scripts/
│   ├── seed-fixtures.sh
│   └── bench.sh
├── BUILD_PLAN.md          (this file)
├── ROADMAP.md
└── .github/workflows/ci.yml
```

---

## 3. Tech decisions

| Concern | Choice | Reason |
|---|---|---|
| Core language | Python 3.11 + type hints | Matches cc-tools, stdlib-rich, fast to ship |
| TUI | Textual | Mature, themable, mouse + keyboard |
| Web UI | FastAPI + HTMX + SSE | No SPA build step, live-stream friendly |
| Storage | SQLite (WAL) + DuckDB read views | Zero-config, queryable, portable |
| Hook shim | Bash wrapper + Unix socket | No runtime dep, works on macOS + Linux |
| Packaging | `uv` + PEP 621 | Fast installs, lockfile, reproducible |
| Tests | pytest + hypothesis (property) | Property tests over JSONL parsing |
| CI | GitHub Actions | Matrix on 3.11/3.12/3.13, mac+ubuntu |
| Distribution | `pip install claude-observatory` + Homebrew tap | Low-friction CLI install |

No Rust / Go yet. If hot-path perf bites, port `core` reader.

---

## 4. Phased build plan

### Phase 0 — Scaffold (day 1-2)
- [ ] `uv init`, monorepo with workspace pyproject
- [ ] `core/` package: lift `cc-tools/cctools/jsonl.py` → `core/jsonl.py`, add SQLite schema
- [ ] Test fixtures: 3 sanitized JSONL transcripts (small/medium/large), generator script
- [ ] CI green on placeholder tests

**Exit:** `pytest` passes. `core` importable. Fixtures committed.

### Phase 1 — HealthDoctor MVP (week 1-2)
- [ ] Hook shim: Bash wrapper that prepends/appends timing + stdio capture, writes NDJSON to Unix socket
- [ ] Daemon: reads socket → SQLite, emits SSE
- [ ] TUI: Textual app with three panes — timeline, event detail, context diff
- [ ] CLI: `observatory healthdoctor` (start daemon + TUI), `observatory healthdoctor --install` (writes settings.json shim)
- [ ] Event correlator: stitches PreToolUse + PostToolUse pairs by tool_use_id

**Exit:** Demo video: live trace of a real Claude session with 5+ hook fires shown in TUI.

### Phase 2 — HealthDoctor web UI (week 3)
- [ ] FastAPI server, HTMX timeline, replay-from-disk mode
- [ ] Search + filter (by hook name, tool, duration, exit code)
- [ ] Export session → JSON for sharing bug reports

**Exit:** Web UI parity with TUI. Replay any past session.

### Phase 3 — HealthCheck recommender (week 4-6)
- [ ] Skill usage analyzer: invocation counts, abandon rate, trigger-match-but-no-fire
- [ ] CLAUDE.md violation tracker: parse rules → grep transcripts for violations
- [ ] MCP overhead profiler: per-server token cost, usage frequency
- [ ] Recommendation engine emits structured suggestions (JSON)
- [ ] `observatory healthcheck suggest` CLI prints ranked actions

**Exit:** On real data (your 263 sessions), engine produces ≥5 actionable, non-trivial recommendations.

### Phase 4 — HealthCheck A/B harness (week 7-9)
- [ ] Worktree orchestrator: clone repo to `/tmp`, apply proposed diff
- [ ] Task spec format: YAML — prompt, success criteria, max turns, max cost
- [ ] Runner: spawns headless Claude Code session, captures JSONL
- [ ] Scorer: rubric-based, uses Haiku judge for qualitative scoring
- [ ] `observatory healthcheck ab <suggestion-id>` runs and compares

**Exit:** End-to-end A/B run: takes one recommendation, runs both variants, declares winner with confidence interval.

### Phase 5 — Auto-PR mode (week 10)
- [ ] Diff renderer: suggestion → unified diff against target repo
- [ ] `gh pr create` integration with measured-impact body
- [ ] Dry-run mode default; explicit `--apply` flag

**Exit:** PR opened against a sandbox repo with full A/B evidence in body.

### Phase 6 — Polish & marketing prep (week 11-12)
- [ ] Homebrew formula
- [ ] Demo screencasts (Asciinema for TUI, Loom for web)
- [ ] Landing page (single HTML, static)
- [ ] Now write the README

---

## 5. Test strategy

### Unit
- JSONL parser: malformed lines, truncated streams, unknown event types
- Pricing calc: every known model family, missing fields, sidechain flag
- Hook shim: stdio piping under load, broken sockets, slow hooks
- Recommender rules: each rule has a positive + negative fixture

### Property-based (hypothesis)
- JSONL reader is total: never raises on arbitrary bytes
- Pricing is monotonic: more tokens → strictly more cost
- Timeline correlation: PreToolUse always has matching PostToolUse or timeout marker

### Integration
- Fixture corpus: 3 sanitized real sessions (PII-stripped), checked in
- Replay test: feed fixture JSONL through full pipeline → assert recommendations stable across runs
- Hook shim end-to-end: spawn fake hook → verify SQLite row + SSE event

### E2E
- Headless Claude Code task: run scripted prompt with shim installed, assert events captured
- A/B harness self-test: synthetic "variant A always wins" task → scorer picks A

### Performance
- 100k-event JSONL parses in < 2s on M-series
- TUI maintains 60fps with 1k events/sec ingestion
- SQLite write batch < 5ms p99

### Security
- Shim never logs `ANTHROPIC_API_KEY` or `Authorization` headers
- Fixture sanitizer scrubs: emails, tokens, paths under `/Users/<name>/`
- Threat model doc enumerates: malicious hook stdout, settings.json poisoning, SSE CSRF

### Acceptance gates (per phase)
1. Phase exit demos recorded (Asciinema or Loom)
2. `pytest -q` green
3. Coverage ≥ 80% on `core/` and `healthcheck/recommender/`
4. Manual smoke on real session before merge to `main`

---

## 6. Marketing readiness checklist (gate before README)

- [ ] Two demo screencasts (HealthDoctor live, HealthCheck suggest+AB)
- [ ] One realistic case study: "I cut 32% of Sonnet spend in week 1"
- [ ] Threat model doc public
- [ ] Roadmap doc with dated milestones
- [ ] One-line elevator pitch tested on 3 strangers
- [ ] Pricing decision: OSS core + paid hosted? OSS-only? Sponsorware?
- [ ] License chosen: Apache 2.0 (permissive, enterprise-friendly) leaning
- [ ] Logo + brand mark (can be SVG primitive)

Only after that → write README.md.

---

## 7. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Anthropic ships native observability and obsoletes HealthDoctor | Move fast (6-week window). Focus on plugin-author niche they're unlikely to serve. |
| JSONL schema breaks on model upgrade | Fixture corpus + property tests catch immediately; pin schema version in core. |
| Hook shim breaks user's settings.json | `--install` writes backup, refuses overwrite, validates JSON before write. |
| HealthCheck suggests harmful CLAUDE.md edits | Default dry-run. Diff preview. A/B evidence required for `--apply`. |
| Privacy: telemetry contains secrets | Local-only by default. Cloud sync explicitly opt-in with redaction pipeline. |
| Solo bus factor | Apache 2.0 license, public roadmap, document architecture early. |

---

## 8. Open decisions (resolve at phase boundaries)

- **Phase 1 exit:** lock product name
- **Phase 3 exit:** decide pricing model (OSS vs SaaS split)
- **Phase 5 exit:** decide if SkillForge (3rd product) lives in same repo or sibling
- **Phase 6:** decide initial distribution channels (HN, r/ClaudeAI, X, Anthropic Discord)

---

## 9. What we are NOT building (yet)

- Multi-agent dashboards — Agent Control Tower already owns this
- Cloud-hosted telemetry — local-first first, cloud later
- Non-Claude-Code support (Cursor, Cline, Aider) — narrow focus until traction
- Skill marketplace (SkillForge) — sibling product, separate repo when ready
- LLM-router (Claude Code Router does this) — orthogonal

---

## 10. Definition of done for v1.0

- HealthDoctor: install in < 30s, captures every hook on macOS + Linux, ships with 5 built-in views
- HealthCheck: produces ≥ 1 high-confidence recommendation on any user with ≥ 50 sessions; A/B harness runs end-to-end on synthetic task
- < 5 critical bugs reported in first 30 days post-launch
- ≥ 100 GitHub stars in 60 days (signal, not goal)
- Pricing decision shipped + landing page live
