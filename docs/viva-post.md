# I built a free tool to watch (and cut) my Claude Code spend — sharing it with the team

> Open-sourced it this weekend. Found **$443/month** of waste on my own account in the first 5 minutes.

---

Hey all —

So here's the thing that's been bugging me for months: Claude Code is amazing, but it's a black box. You fire off a session, hooks fire, sub-agents spawn, MCP servers chatter, tokens vanish, and at the end of the week you've got a Stripe invoice and zero idea where the money went.

Last Friday I'd had enough. Saturday morning I started building. Today I'm sharing the result: **Claude Observatory** — a free, open-source toolkit that finally lets you see what your agent is actually doing, and tells you what to fix.

## Two tools, one workflow

🩺 **HealthDoctor** — like Chrome DevTools, but for Claude Code. A tiny shim wraps every hook fire and streams it into a local SQLite store. A terminal UI or a web dashboard shows the live timeline. Click any event for the full payload, duration, exit code, stdin/stdout.

❤️‍🩹 **HealthCheck** — reads your session logs and tells you what to fix. Five rules right now:

- **unused-tool** → you've got an MCP server bolted on that you've called twice in a month. It's eating ~3k tokens per turn in schema overhead. Disable it.
- **opus-for-trivial-work** → you ran a $1.85 session on Opus that Sonnet could've done for 35 cents. **In my data: 10 sessions like this in 30 days = $443/mo bleed.**
- **low-cache-hit** → you're editing CLAUDE.md mid-session and killing prompt cache. Stop doing that.
- **weak-claude-md** → your CLAUDE.md says "you should usually try to..." and the model is ignoring 80% of it. Use MUST/WILL/NEVER.
- **tool-concentration** → 73% of your tool calls are `Bash`. That's a workflow begging to be a skill.

Then it can A/B test the proposed change in a git worktree, and open a PR with the evidence in the body so you don't have to take its word for anything.

## A real example from my own data (today)

```
$ healthcheck suggest --days 30

1. [model-downgrade] 7b539d94-695…  (confidence 60%)
   Session used claude-opus-4-7 for $1.95. Low spend = simple work;
   sonnet would suffice at ~5× cheaper.
   Est. savings: $46.73/month

2. [model-downgrade] 6f9ebbc8-ead…  (confidence 60%)
   Session used claude-opus-4-7 for $1.89...
   Est. savings: $45.44/month

... 8 more ...
TOTAL est savings: $443.10/mo
```

That's real money. On one developer. In one month.

## Privacy

Everything runs on your machine. Reads only your local `~/.claude/projects/*.jsonl` (Claude Code already writes them — nothing new collected). No cloud, no analytics, no telemetry, no phone-home. ~1,500 lines of mostly-stdlib Python you can audit in an afternoon.

## Try it (5 minutes)

```bash
git clone https://github.com/ao92265/claude-observatory
cd claude-observatory
python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/core -e packages/healthdoctor -e packages/healthcheck -e packages/web

# Pull report on your last 7 days
observatory cost --days 7
healthcheck suggest --days 30 --claude-md ~/.claude/CLAUDE.md
```

Run it. Tell me what you find. If you save $20, buy yourself a coffee and call it even.

Apache 2.0 license. Issues and PRs very welcome — calling this v0.1, plenty of rough edges left to file off.

Happy to demo internally — drop a comment or ping me on Teams.

— Alex

---

**Tags:** Claude Code · Developer Tools · Cost Optimization · Open Source · Productivity
**Repo:** https://github.com/ao92265/claude-observatory
