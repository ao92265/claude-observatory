# Built a tool to see what Claude Code would cost without the Max plan

I'm on the Claude Max subscription, so I pay a flat fee and don't see per-session costs. But Max isn't infinite, and once you're running sub-agents, hooks, MCP servers and the rest, it's not obvious where your usage is going either. So I wrote a small Python tool that reads the JSONL files Claude Code already writes to `~/.claude/projects/` and shows you the breakdown.

Two CLIs.

`healthdoctor` taps your live session: every hook, every tool call, every MCP request shows up in a terminal pane or a small web page. Click a row, you see the payload and the duration. Mostly you don't look at it. When something's stuck, you do.

`healthcheck` reads the historic logs and reports waste. Five rules so far:

```
unused-tool          MCP server you've called twice in 30 days.
                     Still costs ~3k tokens of schema per turn.
opus-for-trivial     Opus session under $2 of usage. Sonnet would do.
low-cache-hit        CLAUDE.md edited mid-session, cache invalidated.
weak-claude-md       Hedging language in CLAUDE.md. Model ignores it.
tool-concentration   73% of tool calls are Bash. Worth turning into a skill.
```

Each suggestion has a confidence score and an estimated dollar figure (priced at Anthropic's public API rates, since Max doesn't expose per-call cost). On my last 30 days it flagged 10 sessions where I'd reached for Opus when Sonnet would have done the job. At API rates that's about $443/month — money I'd be paying if I weren't on Max, which is also a fair proxy for how hard those sessions were leaning on the cap.

It can also run an A/B of a proposed change in a git worktree and open a PR with the evidence in the body, if you want to verify before adopting.

Quickstart:

```
git clone https://github.com/ao92265/claude-observatory
cd claude-observatory
python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/core -e packages/healthdoctor \
            -e packages/healthcheck -e packages/web

observatory cost --days 7
healthcheck suggest --days 30 --claude-md ~/.claude/CLAUDE.md
```

Apache 2.0. Local-only, no network calls, reads files Claude Code already writes. v0.1, the recommender's confidence scores are roughly vibes right now and the TUI doesn't redraw cleanly when you resize the terminal. Issues and feedback welcome on the repo. Happy to do a 10-minute demo on Teams.

Alex

https://github.com/ao92265/claude-observatory
