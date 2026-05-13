"""install / uninstall idempotency."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

from healthdoctor.cli import cmd_install, cmd_uninstall


def _run(tmp_home: Path, *, install: bool = False, uninstall: bool = False) -> dict:
    settings = tmp_home / ".claude" / "settings.json"
    args = argparse.Namespace(dry_run=False)
    with patch("pathlib.Path.home", return_value=tmp_home):
        if install:
            cmd_install(args)
        if uninstall:
            cmd_uninstall(args)
    return json.loads(settings.read_text())


def test_install_then_uninstall_is_idempotent(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    (home / ".claude" / "settings.json").write_text("{}")

    after_install = _run(home, install=True)
    assert any(
        h.get("__observatory__")
        for h in after_install.get("hooks", {}).get("PreToolUse", [])
    )

    # second install is a no-op
    _run(home, install=True)
    count_after_double = sum(
        1
        for h in json.loads((home / ".claude" / "settings.json").read_text())
        .get("hooks", {})
        .get("PreToolUse", [])
        if h.get("__observatory__")
    )
    assert count_after_double == 1

    after_uninstall = _run(home, uninstall=True)
    assert not any(
        h.get("__observatory__")
        for h in after_uninstall.get("hooks", {}).get("PreToolUse", [])
    )
