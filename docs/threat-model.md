# Threat Model

## Assets we protect

1. User's Claude Code session transcripts (may contain proprietary code, secrets, internal paths).
2. User's `~/.claude/settings.json` (controls hook execution — high blast radius).
3. User's `ANTHROPIC_API_KEY` and other vended credentials.
4. The user's repos (CCPilot can modify CLAUDE.md and open PRs).

## Trust boundaries

- **Trusted:** the local user, the installed Observatory binaries, the local SQLite store.
- **Untrusted:** any hook command Claude Code invokes (third-party plugin code), any future cloud-sync destination, any A/B treatment diff (could be adversarial).

## Threats and mitigations

### T1 — Settings.json poisoning
A malicious actor with write access to `~/.claude/settings.json` could replace the shim with a credential-stealing command.
**Mitigation:** `hookscope install` writes a timestamped backup; `hookscope uninstall` removes only entries it added (marked with `__observatory__`); the shim path is logged on install.

### T2 — Shim leaks secrets
The shim captures stdin/stdout of hook commands.
**Mitigation:** Stdin capture is bounded (1MB). Stdout is forwarded to parent first, captured separately. Shim never reads environment variables or files outside its own stdin. A future redaction pipeline will scrub common secret patterns before write.

### T3 — Adversarial A/B diff
`ccpilot ab --apply` applies a treatment diff in a worktree and runs `claude` against it.
**Mitigation:** Worktrees are created under `/tmp/ccpilot-ab-*` and cleaned up after each run. The user must explicitly pass `--apply`; diffs are sourced from `CCPILOT_DIFF` env var or stdin (never auto-fetched from the network). The treatment runs Claude Code, which itself sandboxes file access.

### T4 — Auto-PR opens unwanted change
`ccpilot pr --apply` pushes a branch and opens a PR.
**Mitigation:** Default is `--dry-run` showing the full PR body. Diffs are scoped to known-safe operations (CLAUDE.md hedging rewrite, `ccpilot-notes.md` append). Anything more invasive requires future explicit consent flow.

### T5 — Database corruption
A crashing daemon could corrupt SQLite.
**Mitigation:** WAL mode + per-row inserts + `synchronous=NORMAL`. Worst case is loss of in-flight events; the store can be re-ingested from JSONL.

### T6 — Web UI cross-site request
The FastAPI app runs on `127.0.0.1` and has no auth.
**Mitigation:** Bind to loopback by default. Future: opt-in token + warning if `--host 0.0.0.0`. No POST endpoints currently exist that mutate state.

### T7 — Supply-chain attack on dependencies
HTMX is loaded from a CDN in the demo template.
**Mitigation:** Pre-1.0 acceptable; v1.0 will pin SRI hashes or self-host the script.

## Out of scope (today)

- Multi-user / shared-machine scenarios.
- Hardened cloud sync (opt-in only, redaction pipeline TBD).
- Defense against compromise of the user's local account.

## Reporting issues

Security issues: GitHub Security Advisory on `ao92265/claude-observatory`.
