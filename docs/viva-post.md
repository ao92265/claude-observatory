# I spent $8k on Claude last month and couldn't tell you where it went

Right. So the Claude bill came in for last month and it was $8,197. Which is a lot. The annoying part is I genuinely could not tell you what most of it was. Like, you can see the total in the dashboard, fine, but there's no per-session breakdown. No "this skill cost you X". You just get a number and a vibe.

I had a free Saturday so I went and pulled all the JSONL files out of `~/.claude/projects/` (those exist, by the way — Claude Code has been writing them the whole time, nobody really talks about it) and wrote a thing that reads them.

Two parts.

One sits over your live sessions and prints what's happening. Every hook firing, every tool call, every MCP server it pokes. I called it `healthdoctor` because it sounded better than "live event tap". You can either watch it in your terminal or open a tiny web page. Click a row, you get the payload and the exit code and how long it took. Most of the time you don't need it. The rest of the time it saves you an hour.

The other one is `healthcheck` and this is the bit that paid for the Saturday. It reads the JSONL history and just tells you where you're being dumb. Mine:

```
unused-tool          MCP server you've called twice in a month.
                     Still ~3k tokens of schema cost per turn.
opus-for-trivial     Opus session under $2. Sonnet would've done it.
low-cache-hit        You edited CLAUDE.md mid-session and torched the cache.
weak-claude-md       Your CLAUDE.md hedges. Model ignores it.
tool-concentration   73% of your calls are Bash. That's a skill, not a habit.
```

I had 10 sessions in the last 30 days where I'd reached for Opus and Sonnet would have done it. That's about $443/mo. Just out the window. I was that guy.

It scores each suggestion, gives you a number, and if you want it'll A/B the change in a git worktree and open a PR with the evidence pasted in so you don't have to take its word.

```
git clone https://github.com/ao92265/claude-observatory
cd claude-observatory
python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/core -e packages/healthdoctor \
            -e packages/healthcheck -e packages/web

observatory cost --days 7
healthcheck suggest --days 30 --claude-md ~/.claude/CLAUDE.md
```

Apache 2.0. Runs locally, doesn't phone home, I wouldn't put it on a production box yet. If you try it and it breaks, tell me. If you try it and it tells you something embarrassing, you don't have to.

Alex

https://github.com/ao92265/claude-observatory
