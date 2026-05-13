# Watching my Claude Code spend (and a tool I made to do it)

Got fed up last week. Claude Code's a black box — sub-agents fan out, hooks fire, MCP servers eat tokens, and a week later there's a Stripe bill with no breakdown. So I built something. Sharing it in case any of you are in the same boat.

It's called **Claude Observatory**. Two pieces:

**HealthDoctor** — sits on top of Claude Code and shows every hook, tool call, and MCP request live. Either in your terminal or a little web dashboard. Click an event, see what came in, what came out, how long it took, what it cost. That's it.

**HealthCheck** — reads your `~/.claude/projects/` logs and tells you where the waste is. Five things it looks for right now:

```
unused-tool          MCP server you've called twice in 30 days, eating
                     ~3k tokens per turn in schema overhead.

opus-for-trivial     Opus session that cost $1.85 doing work sonnet
                     would've handled for 35c.

low-cache-hit        You edit CLAUDE.md mid-session and kill prompt
                     cache. Stop doing that.

weak-claude-md       Your CLAUDE.md says "you should usually try to..."
                     and the model ignores 80% of it.

tool-concentration   73% of your tool calls are Bash. That's a
                     workflow asking to be a skill.
```

Each suggestion has a confidence score and an estimated dollar savings. It can run an A/B test of the change in a git worktree and open a PR with the evidence in the body, so you're not just trusting it.

What I found on my own data (30 days):

```
$ healthcheck suggest --days 30

1. model-downgrade  7b539d94…   conf 60%   est $46.73/mo
2. model-downgrade  6f9ebbc8…   conf 60%   est $45.44/mo
3. model-downgrade  9588be80…   conf 60%   est $44.72/mo
... 7 more ...

TOTAL est savings: $443.10/mo
```

Ten sessions where I'd reached for Opus and Sonnet would've been fine. $443 a month I had no idea I was leaving on the table.

Local-only. Nothing leaves your machine. Reads files Claude Code already writes. ~1,500 lines of mostly-stdlib Python, all auditable.

Quickstart:

```
git clone https://github.com/ao92265/claude-observatory
cd claude-observatory
python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/core -e packages/healthdoctor -e packages/healthcheck -e packages/web

observatory cost --days 7
healthcheck suggest --days 30 --claude-md ~/.claude/CLAUDE.md
```

Apache 2.0. v0.1 so plenty of rough edges. Issues and PRs welcome.

If anyone wants a 10-minute demo, ping me on Teams.

Alex

---

Repo: https://github.com/ao92265/claude-observatory
