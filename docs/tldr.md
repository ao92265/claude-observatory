# Claude Observatory — TL;DR

## What it is

Local Python toolkit that reads the JSONL files Claude Code already writes to `~/.claude/projects/` and shows you:

1. **What you actually spent** (priced at API rates, even if you're on Max).
2. **Where the waste is** — unused MCP servers, Opus-on-trivial sessions, cache misses, weak CLAUDE.md rules, tool concentration.
3. **What to do about it** — A/B harness + auto-PR with evidence in the body.

Two CLIs: `healthdoctor` (live timeline of hooks / tools / MCP) and `healthcheck` (the recommender). Plus a web UI and a unified `observatory` ingest/report CLI.

## How it benefits others

- **Cost visibility on Max plans.** Max doesn't expose per-session cost. This does.
- **Cost visibility on API plans.** Per-session, per-skill, sidechain vs main split.
- **Live debugger for hooks.** Plugin authors finally have a way to see why a hook is blocking, slow, or eating tokens.
- **Automated CLAUDE.md hygiene.** Flags hedging language, dead rules, layer bloat. Tells you what model is ignoring.
- **Concrete recommendations.** Not "you should optimize". Specific session IDs, specific dollar numbers, specific diffs.
- **Local-only.** Reads files Claude Code already writes. No telemetry. No cloud. ~1,500 lines of stdlib Python you can audit.

## What I (Alex) did that benefited me

Ran the tool against my own 30 days of Claude Code usage:

- **2,583 sessions** over 30 days
- **$39,762.63** API-equivalent at Anthropic's public rates
- Paying **$200/mo** on Max → Max is paying for itself ~200×
- Tool flagged **10 sessions where I'd grabbed Opus and Sonnet would have done** = ~$443/mo of waste at API rates, or "stop burning your rate limit on this" on Max

Without the tool I had no per-session breakdown at all.

## Changes I made off the back of it

1. **Added a sonnet-first rule to `~/.claude/CLAUDE.md`** (line 71): "Main-loop default = sonnet. Start session with `/model sonnet`. Reach for opus ONLY: real architecture, hard debug after ≥2 sonnet passes, irreversible decisions."
2. **Added evidence inline:** "(2026-05-13 audit): top 10 opus-on-trivial sessions = est $443/mo waste."
3. **Cron-able weekly audit script:** `~/.claude/scripts/observatory-weekly.sh` — runs `observatory cost`, `observatory cache`, `healthcheck suggest` every Monday and logs to `~/.claude/observatory-logs/`.
4. **Tightened the linter** — false-positive on "USUALLY → skill" (mnemonic, not hedge). Pushed the fix upstream into the tool itself.
5. **Built a Viva post + cover image** to share internally and externally.

## Try it

```bash
git clone https://github.com/ao92265/claude-observatory
cd claude-observatory
python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/core -e packages/healthdoctor \
            -e packages/healthcheck -e packages/web

observatory cost --days 30
healthcheck suggest --days 30 --claude-md ~/.claude/CLAUDE.md
```

Apache 2.0. v0.1.0. Issues + PRs welcome.

https://github.com/ao92265/claude-observatory
