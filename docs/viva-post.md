# I spent $8k on Claude last month and couldn't tell you where it went

Went to look at the bill last week. Sub-agents fan out into more sub-agents, hooks fire on every keystroke, half the MCP servers in my config I don't even remember installing. The dashboard shows you one number. It doesn't show you the why.

So I lost a Saturday to it. Wrote a small Python thing. Sticking it here in case anyone else is staring at their bill wondering the same thing.

Two CLIs.

`healthdoctor` watches a Claude Code session live. Hooks, tool calls, MCP requests all show up in a terminal pane or a small web page. Click a row, you get the payload, duration, exit code. Boring on purpose.

`healthcheck` reads the JSONL files Claude Code already writes to `~/.claude/projects/` and tells you where the money's leaking. Five rules so far:

```
unused-tool          MCP server you've called twice in a month.
                     Still ~3k tokens of schema cost per turn.
opus-for-trivial     Opus session under $2. Sonnet would've done it.
low-cache-hit        You edited CLAUDE.md mid-session and torched the cache.
weak-claude-md       Your CLAUDE.md hedges. Model ignores it.
tool-concentration   73% of your calls are Bash. That's a skill, not a habit.
```

Each one has a confidence score and a dollar number. It can A/B the change in a git worktree and open a PR with the evidence in the body so you can argue with it.

What I found on myself: 263 sessions, $8,197 spent, 10 of those were on Opus when Sonnet would have been fine. Roughly $443/mo I was just lighting on fire because I'd forgotten to switch models.

```
git clone https://github.com/ao92265/claude-observatory
cd claude-observatory
python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/core -e packages/healthdoctor \
            -e packages/healthcheck -e packages/web

observatory cost --days 7
healthcheck suggest --days 30 --claude-md ~/.claude/CLAUDE.md
```

Apache 2.0. Local-only, nothing phones home. v0.1 so don't be surprised if something breaks. Happy to demo on Teams if you want a look before you install random Python off the internet.

Alex

https://github.com/ao92265/claude-observatory
