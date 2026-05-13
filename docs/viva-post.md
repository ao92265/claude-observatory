# I spent $8k on Claude last month and couldn't tell you where it went

Last week I went to look at the Claude bill. Couldn't work out which sessions cost what. Sub-agents fork off everywhere, hooks fire in the background, MCP servers I forgot I installed are still chewing through tokens. The dashboard shows the total. Doesn't show why.

Lost a Saturday to it. Wrote a small Python thing. Posting it in case anyone else is in the same hole.

Two CLIs.

The first is `healthdoctor`. It watches a Claude Code session live. Every hook, every tool call, every MCP request lands in a terminal pane or a small web page. Click a row, you see what went in, what came out, how long it took, exit code. Not fancy.

The second is `healthcheck`. It reads the JSONL files Claude Code already writes to `~/.claude/projects/` and tells you where the money's going. Five rules so far:

```
unused-tool          MCP server invoked twice in 30 days.
                     Still costs ~3k tokens of schema per turn.
opus-for-trivial     Opus session under $2. Sonnet would do.
low-cache-hit        CLAUDE.md edited mid-session, killed cache.
weak-claude-md       "you should usually try to..." gets ignored.
tool-concentration   73% of tool calls are Bash. Write a skill.
```

Each suggestion has a confidence score and an estimated dollar saving. It can A/B test the change in a git worktree and open a PR with the evidence pasted in the body so you're not just trusting it.

My own 30 days: 263 sessions, $8,197 spent, 10 sessions where I'd grabbed Opus and Sonnet would have done fine. About $443/month I didn't know I was burning.

```
git clone https://github.com/ao92265/claude-observatory
cd claude-observatory
python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/core -e packages/healthdoctor \
            -e packages/healthcheck -e packages/web

observatory cost --days 7
healthcheck suggest --days 30 --claude-md ~/.claude/CLAUDE.md
```

Apache 2.0. Reads files Claude Code already writes. Nothing leaves your machine. v0.1, so rough edges aplenty. Issues and PRs welcome. Happy to do a 10-min demo on Teams if anyone wants one.

Alex

Repo: https://github.com/ao92265/claude-observatory
