# Claude Observatory — TL;DR

I built a small Python tool that reads the log files Claude Code already writes to disk and tells you what your usage would cost on the API, where you're wasting money or hitting rate limits, and what to change. It runs locally, doesn't send anything anywhere, and works whether you're on the flat Max plan or pay-per-token.

**What it gives you:**

- A live view of every hook, tool call, and MCP request as it happens
- A breakdown of cost per session and per tool, priced at Anthropic's public API rates
- Concrete suggestions: which MCP servers you don't really use, which sessions ran on Opus when Sonnet would have done, where your CLAUDE.md is being ignored
- An A/B test mode that runs the proposed change in a git worktree and opens a PR with the evidence

**What it found on me:**

- 2,583 sessions in the last 30 days
- $39,762 of usage at API rates
- I pay $200/month on the Max plan, so it's paying for itself ~200×
- About $443/month of that was me grabbing Opus for trivial work — now fixed

**What I changed because of it:**

- Added a "default to Sonnet" rule to my `~/.claude/CLAUDE.md`
- Set up a weekly audit script that re-runs the report and logs it
- Fixed a couple of bugs in the tool itself (the linter was overzealous about hedge words)

**Try it:**

```bash
git clone https://github.com/ao92265/claude-observatory
cd claude-observatory
python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/core -e packages/healthdoctor \
            -e packages/healthcheck -e packages/web

observatory cost --days 30
healthcheck suggest --days 30 --claude-md ~/.claude/CLAUDE.md
```

Apache 2.0, v0.1.0. https://github.com/ao92265/claude-observatory
