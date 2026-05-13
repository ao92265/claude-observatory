# Changes I made after running the tool on myself

- **Switched my default model to Sonnet.** Added a rule to `~/.claude/CLAUDE.md` so I start every session with `/model sonnet` and only reach for Opus when I actually need it (real architecture work, a hard debug, anything irreversible).
- **Stopped editing CLAUDE.md mid-session.** Was killing my prompt cache without realising. Edits now happen between sessions only.
- **Removed two MCP servers I never actually used.** They were costing ~3k tokens per turn just by existing in the schema.
- **Tightened a few weak rules in CLAUDE.md.** The tool flagged hedging language ("you should usually try to…") that the model was ignoring. Rewrote in MUST/WILL/NEVER form.
- **Set up a weekly self-audit.** `~/.claude/scripts/observatory-weekly.sh` re-runs the cost + cache + suggestion reports every Monday and logs them.

Net effect on the next 30 days: less Opus burn, fewer rate-limit hits on Max, cleaner CLAUDE.md the model actually follows.
