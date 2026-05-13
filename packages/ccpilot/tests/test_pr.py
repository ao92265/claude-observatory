from __future__ import annotations

from pathlib import Path

from ccpilot.pr import _suggestion_to_diff
from ccpilot.types import Suggestion


def test_claude_md_rewrite(tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").write_text("You should test. Try to be careful. Usually works.")
    s = Suggestion(
        id="x", kind="claude-md-rule", target="CLAUDE.md",
        rationale="hedging detected", confidence=0.5,
    )
    note = _suggestion_to_diff(s, tmp_path)
    assert note
    new = (tmp_path / "CLAUDE.md").read_text()
    assert "You should" not in new
    assert "Try to" not in new
    assert "Usually" not in new
    assert "MUST" in new


def test_fallback_writes_notes(tmp_path: Path) -> None:
    s = Suggestion(
        id="y", kind="tool-archive", target="MyTool",
        rationale="never used", confidence=0.7, evidence={"invocations": 0},
    )
    note = _suggestion_to_diff(s, tmp_path)
    assert note
    assert (tmp_path / "ccpilot-notes.md").exists()
    assert "never used" in (tmp_path / "ccpilot-notes.md").read_text()


def test_dry_run_no_repo(tmp_path: Path) -> None:
    from ccpilot.pr import open_pr_from_suggestion

    # No .git → should error 2
    rc = open_pr_from_suggestion(tmp_path, suggestion_id="x", dry_run=True)
    assert rc == 2
