# I spent $8k on Claude last month and couldn't tell you where it went

Last week I went to look at the Claude bill and could not work out which sessions cost what. Sub-agents fork off everywhere, hooks fire in the background, MCP servers I forgot I installed are still chewing through tokens. The dashboard shows you the total. It does not show you why.

Wasted a weekend on it. Wrote a small Python thing. Posting in case anyone else is in the same hole.

Two CLIs.

`healthdoctor` watches a live Claude Code session. Every hook, tool call, and MCP request shows up in a terminal pane or a small web page. Click a row, you get the inputs, outputs, duration, exit code. Nothing fancy.

`healthcheck` reads the JSONL files Claude Code already writes to `~/.claude/projects/` and tells you where the money's going. Five rules so far:

```
unused-tool          MCP server invoked twice in 30 days,
                     ~3k tokens of schema cost per turn.
opus-for-trivial     Opus session under $2 — sonnet would do.
low-cache-hit        CLAUDE.md edited mid-session, killed cache.
weak-claude-md       "you should usually try to..." gets ignored.
tool-concentration   73% of tool calls are Bash. Write a skill.
```

It scores each suggestion, estimates dollar savings, and can open a PR with the change plus the evidence so you're not just trusting it.

My own 30 days: 263 sessions, $8,197 spent, 10 of them where I'd reached for Opus and didn't actually need to. About $443/month I had no idea about.

```
git clone https://github.com/ao92265/claude-observatory
cd claude-observatory
python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/core -e packages/healthdoctor \
            -e packages/healthcheck -e packages/web

observatory cost --days 7
healthcheck suggest --days 30 --claude-md ~/.claude/CLAUDE.md
```

Apache 2.0. Local-only — reads files Claude Code already writes, nothing leaves your machine. v0.1 so plenty of rough edges. Issues and PRs welcome. Happy to do a 10-min demo on Teams.

Alex

Repo: https://github.com/ao92265/claude-observatory
