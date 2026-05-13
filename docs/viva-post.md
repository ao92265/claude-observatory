# My last 30 days on Claude Code: $200 on the Max plan, $39,762 at API rates

I was curious how much my Claude Code usage would have cost on pay-per-token instead of the Max subscription. So I wrote a small Python tool to read the JSONL files Claude Code writes to `~/.claude/projects/` and price them at Anthropic's public API rates.

The number: 2,583 sessions, **$39,762.63** API-equivalent. I pay $200/month on Max. So Max is paying for itself about 200x over for how I'm using it.

What I didn't expect: even at "free" usage, there's still waste. About $443/month of that was sessions where I'd reached for Opus when Sonnet would have done. On API that's real money; on Max it's still pressure on the rate limits I keep hitting.

Two CLIs.

`healthdoctor` taps your live session. Every hook, every tool call, every MCP request shows up in a terminal pane or a small web page. Click a row, you see the payload and the duration. Mostly you don't look at it. When something's stuck, you do.

`healthcheck` reads the historic logs and reports waste:

```
unused-tool          MCP server you've called twice in 30 days.
                     Still costs ~3k tokens of schema per turn.
opus-for-trivial     Opus session under $2 of usage. Sonnet would do.
low-cache-hit        CLAUDE.md edited mid-session, cache invalidated.
weak-claude-md       Hedging language in CLAUDE.md. Model ignores it.
tool-concentration   73% of tool calls are Bash. Worth turning into a skill.
```

Each suggestion has a confidence score and a dollar figure (API rates). It can also A/B a proposed change in a git worktree and open a PR with the evidence pasted in the body, if you want to verify before adopting.

```
git clone https://github.com/ao92265/claude-observatory
cd claude-observatory
python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/core -e packages/healthdoctor \
            -e packages/healthcheck -e packages/web

observatory cost --days 30
healthcheck suggest --days 30 --claude-md ~/.claude/CLAUDE.md
```

Apache 2.0. Local-only, no network calls, reads files Claude Code already writes. v0.1, the recommender's confidence scores are roughly vibes right now and the TUI doesn't redraw cleanly when you resize. Issues and feedback welcome. Happy to do a 10-minute demo on Teams.

Alex

https://github.com/ao92265/claude-observatory
