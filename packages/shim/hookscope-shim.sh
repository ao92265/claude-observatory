#!/usr/bin/env bash
# hookscope-shim: wraps a Claude Code hook command, captures timing + stdio,
# emits a single NDJSON record on stdout (event-log channel) AND forwards
# original stdin/stdout/exit to the parent so Claude Code keeps working.
#
# Usage in ~/.claude/settings.json:
#   "PreToolUse": [{"hooks": [{"type": "command", "command": "hookscope-shim.sh PreToolUse <original-cmd>"}]}]
#
# Environment:
#   OBSERVATORY_SOCKET   Unix socket path (default /tmp/claude-observatory.sock)
#   OBSERVATORY_OFF=1    bypass shim entirely
set -uo pipefail

SOCKET="${OBSERVATORY_SOCKET:-/tmp/claude-observatory.sock}"
EVENT_KIND="${1:-unknown}"
shift || true

if [[ "${OBSERVATORY_OFF:-0}" == "1" || $# -eq 0 ]]; then
  exec "$@"
fi

START_NS=$(python3 -c 'import time;print(time.time_ns())')
STDIN_TMP=$(mktemp)
STDOUT_TMP=$(mktemp)
trap 'rm -f "$STDIN_TMP" "$STDOUT_TMP"' EXIT

# Capture stdin (limit 1MB to prevent runaway logging)
head -c 1048576 > "$STDIN_TMP"

# Run wrapped command
"$@" < "$STDIN_TMP" > "$STDOUT_TMP" 2>&1
EXIT_CODE=$?

END_NS=$(python3 -c 'import time;print(time.time_ns())')
DURATION_MS=$(( (END_NS - START_NS) / 1000000 ))

# Forward stdout to parent
cat "$STDOUT_TMP"

# Emit event to socket (best-effort; never fail the parent on logging issues)
{
  python3 - "$SOCKET" "$EVENT_KIND" "$EXIT_CODE" "$DURATION_MS" "$STDIN_TMP" "$STDOUT_TMP" <<'PY' 2>/dev/null || true
import json, os, socket, sys, time
sock_path, kind, exit_code, duration_ms, stdin_p, stdout_p = sys.argv[1:7]
def read(p, n=8192):
    try:
        with open(p, "rb") as f:
            return f.read(n).decode("utf-8", errors="replace")
    except Exception:
        return ""
ev = {
    "ts": time.time(),
    "kind": "hook",
    "hook": kind,
    "exit_code": int(exit_code),
    "duration_ms": int(duration_ms),
    "argv": os.environ.get("CLAUDE_HOOK_ARGV", ""),
    "stdin": read(stdin_p),
    "stdout": read(stdout_p),
}
try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(0.5)
    s.connect(sock_path)
    s.sendall((json.dumps(ev) + "\n").encode())
    s.close()
except Exception:
    pass
PY
} &

exit "$EXIT_CODE"
