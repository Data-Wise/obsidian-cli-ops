"""
E2E tests for `obs doctor --layer mcp` — mcp-interpreter edge cases.

These spawn the REAL obs_cli.py subprocess (the same CLI Claude Desktop's
troubleshooting docs point users at), pointed at a scratch HOME so it reads
a throwaway claude_desktop_config.json instead of the real one. This is the
live counterpart to the unit tests in tests/test_doctor.py, which call
_check_mcp() directly in-process — here the full path (argparse wiring,
Rich-table rendering, process exit code) is what's under test, using the
exact scenarios that motivated PR #96 and its adversarial-review follow-up
fixes (dead Homebrew Cellar path, revision-suffixed Cellar path, malformed
non-string command).

NOTE: `obs doctor --json` is currently broken on dev (pre-existing
UnboundLocalError in obs_cli.py's main(), unrelated to this PR — see the
spawned follow-up task). These tests use the human-readable table output
instead, parsing the status icon on the "obsidian-ops interpreter" row.

Requirements:
  - obs venv installed (install.sh or brew)

Marks:
  @pytest.mark.e2e   — skipped unless E2E=1 env var is set
"""
from __future__ import annotations

import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).parent.parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_RUN_E2E = os.environ.get("E2E", "").strip() in ("1", "true", "yes")
pytestmark = pytest.mark.skipif(
    not _RUN_E2E,
    reason="E2E tests skipped — set E2E=1 to run",
)


def _find_obs_python() -> str:
    if env := os.environ.get("OBS_PYTHON"):
        if Path(env).exists():
            return env
    candidates = [
        Path.home() / ".local/share/obs/venv/bin/python3",
        Path("/opt/homebrew/opt/obsidian-cli-ops/libexec/venv/bin/python3"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return sys.executable


_OBS_PYTHON = _find_obs_python()
_OBS_CLI = _SRC / "obs_cli.py"


def _write_scratch_config(home: Path, command) -> Path:
    """Write a claude_desktop_config.json under a scratch HOME, matching the
    layout obs doctor's _CLAUDE_DESKTOP_CONFIG_PATHS expects (Path.home()
    respects the HOME env var on POSIX, so pointing HOME at a tmp dir fully
    isolates this from the developer's real Claude Desktop config)."""
    config_dir = home / "Library" / "Application Support" / "Claude"
    config_dir.mkdir(parents=True)
    server_path = home / "mcp_server.py"
    server_path.touch()
    config_path = config_dir / "claude_desktop_config.json"
    config_path.write_text(json.dumps({
        "mcpServers": {
            "obsidian-ops": {
                "command": command,
                "args": [str(server_path)],
            }
        }
    }))
    return config_path


def _make_executable(path: Path) -> None:
    path.write_text("#!/bin/sh\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _run_doctor_mcp(home: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["HOME"] = str(home)
    return subprocess.run(
        [_OBS_PYTHON, str(_OBS_CLI), "doctor", "--layer", "mcp"],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


_ICON_STATUS = {
    "✅": "pass",
    "⚠️": "warn",
    "❌": "fail",
    "⬜": "skip",
    "🔥": "error",
    "ℹ️": "info",
}

_INTERPRETER_ROW_RE = re.compile(r"^\s*(\S+)\s+obsidian-ops interpreter", re.MULTILINE)


def _interpreter_status(stdout: str) -> str:
    """Parse the status icon on the 'obsidian-ops interpreter' table row from
    obs doctor's Rich-table text output (--json is broken on dev — see the
    module docstring)."""
    m = _INTERPRETER_ROW_RE.search(stdout)
    assert m, f"no 'obsidian-ops interpreter' row found in output:\n{stdout}"
    icon = m.group(1)
    assert icon in _ICON_STATUS, f"unrecognized status icon {icon!r} in row: {m.group(0)!r}"
    return _ICON_STATUS[icon]


class TestDoctorMcpInterpreterE2E:
    """Live `obs doctor --layer mcp` runs against a scratch Claude Desktop config."""

    def test_dead_cellar_path_fails_and_exits_nonzero(self, tmp_path):
        """Reproduces the exact outage this check exists to catch: a
        version-pinned Homebrew Cellar interpreter deleted by a patch bump."""
        _write_scratch_config(
            tmp_path,
            "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/"
            "Versions/3.14/bin/python3.14",
        )
        result = _run_doctor_mcp(tmp_path)
        assert _interpreter_status(result.stdout) == "fail"
        assert result.returncode == 1

    def test_revision_suffixed_cellar_path_warns_and_exits_zero(self, tmp_path):
        """3.14.6_1-style bottle-rebuild paths are equally fragile and must
        still warn — the regression this PR's adversarial-review fix covers."""
        cellar_bin = tmp_path / "Cellar" / "python@3.14" / "3.14.6_1" / "bin"
        cellar_bin.mkdir(parents=True)
        interpreter = cellar_bin / "python3.14"
        _make_executable(interpreter)
        _write_scratch_config(tmp_path, str(interpreter))
        result = _run_doctor_mcp(tmp_path)
        assert _interpreter_status(result.stdout) == "warn"
        assert result.returncode == 0

    def test_non_string_command_reports_fail_without_crashing(self, tmp_path):
        """A malformed-but-valid-JSON command (int, not a path string) must
        surface as a clean fail result, not an uncaught traceback — the
        crash bug the adversarial review caught."""
        _write_scratch_config(tmp_path, 123)
        result = _run_doctor_mcp(tmp_path)
        assert "Traceback" not in result.stderr
        assert _interpreter_status(result.stdout) == "fail"
        assert result.returncode == 1

    def test_stable_symlink_path_passes_and_exits_zero(self, tmp_path):
        """A non-Cellar, executable interpreter path is the healthy case."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        interpreter = bin_dir / "python3.14"
        _make_executable(interpreter)
        _write_scratch_config(tmp_path, str(interpreter))
        result = _run_doctor_mcp(tmp_path)
        assert _interpreter_status(result.stdout) == "pass"
        assert result.returncode == 0
