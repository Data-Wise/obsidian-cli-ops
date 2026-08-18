"""
Dogfood tests for `obs doctor --layer mcp` — mcp-interpreter edge cases.

Unlike tests/test_doctor.py (which calls _check_mcp()/_check_mcp_interpreter()
directly) or tests/e2e/test_e2e_doctor_mcp.py (which spawns a real obs_cli.py
subprocess), these call the actual obs_cli.main() entry point in-process:
real argv parsing, the real ObsCLI()/DatabaseManager() construction path, and
the real doctor dispatch branch (obs_cli.py's `elif args.command == 'doctor'`)
— everything except a separate OS process. This is the CLI-wiring layer the
unit tests in test_doctor.py don't exercise (they call the check functions
directly, bypassing argparse and main()'s dispatch/exit-code logic).

No E2E gate — safe to run in every CI invocation (in-process, no subprocess,
no real filesystem/config touched outside monkeypatched tmp_path).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import obs_cli
from core import doctor as doctor_mod


def _write_scratch_config(tmp_path: Path, command, monkeypatch) -> None:
    config_dir = tmp_path / "Library" / "Application Support" / "Claude"
    config_dir.mkdir(parents=True)
    server_path = tmp_path / "mcp_server.py"
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
    monkeypatch.setattr(doctor_mod, "_CLAUDE_DESKTOP_CONFIG_PATHS", [config_path])
    # ObsCLI() -> DatabaseManager() resolves its db path from Path.home();
    # isolate it from the developer's real ~/.config/obs.
    monkeypatch.setattr(Path, "home", lambda: tmp_path)


_ICON_STATUS = {
    "✅": "pass",
    "⚠️": "warn",
    "❌": "fail",
    "⬜": "skip",
    "🔥": "error",
    "ℹ️": "info",
}

_INTERPRETER_ROW_RE = re.compile(r"^\s*(\S+)\s+obsidian-ops interpreter", re.MULTILINE)


def _run_doctor_main(monkeypatch, capsys):
    """Run obs_cli.main() for `doctor --layer mcp` and return (exit_code,
    mcp-interpreter row status). The overall exit code isn't a reliable pass/
    warn signal on its own here — it reflects ALL mcp-layer checks (e.g.
    mcp-fastmcp, which fails whenever the `mcp` package isn't installed on
    whatever Python launched pytest, unrelated to this check) — so callers
    should assert on the returned status for pass/warn cases, and reserve the
    exit code assertion for cases where mcp-interpreter itself is the one
    expected to fail (which reliably forces the overall code nonzero)."""
    monkeypatch.setattr(sys, "argv", ["obs_cli.py", "doctor", "--layer", "mcp"])
    with pytest.raises(SystemExit) as exc_info:
        obs_cli.main()
    out = capsys.readouterr().out
    m = _INTERPRETER_ROW_RE.search(out)
    assert m, f"no 'obsidian-ops interpreter' row found in output:\n{out}"
    icon = m.group(1)
    assert icon in _ICON_STATUS, f"unrecognized status icon {icon!r} in row: {m.group(0)!r}"
    return exc_info.value.code, _ICON_STATUS[icon]


class TestDoctorMcpInterpreterDogfood:
    """obs_cli.main() dispatch for `doctor --layer mcp`, argv to exit code."""

    def test_dead_cellar_path_fails_and_exits_nonzero(self, tmp_path, monkeypatch, capsys):
        _write_scratch_config(
            tmp_path,
            "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/"
            "Versions/3.14/bin/python3.14",
            monkeypatch,
        )
        code, status = _run_doctor_main(monkeypatch, capsys)
        assert status == "fail"
        assert code == 1

    def test_revision_suffixed_cellar_path_warns(self, tmp_path, monkeypatch, capsys):
        cellar_bin = tmp_path / "Cellar" / "python@3.14" / "3.14.6_1" / "bin"
        cellar_bin.mkdir(parents=True)
        interpreter = cellar_bin / "python3.14"
        interpreter.write_text("#!/bin/sh\n")
        interpreter.chmod(0o755)
        _write_scratch_config(tmp_path, str(interpreter), monkeypatch)
        _, status = _run_doctor_main(monkeypatch, capsys)
        assert status == "warn"

    def test_non_string_command_reports_fail_without_crashing(self, tmp_path, monkeypatch, capsys):
        _write_scratch_config(tmp_path, 123, monkeypatch)
        code, status = _run_doctor_main(monkeypatch, capsys)
        assert status == "fail"
        assert code == 1

    def test_stable_symlink_path_passes(self, tmp_path, monkeypatch, capsys):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        interpreter = bin_dir / "python3.14"
        interpreter.write_text("#!/bin/sh\n")
        interpreter.chmod(0o755)
        _write_scratch_config(tmp_path, str(interpreter), monkeypatch)
        _, status = _run_doctor_main(monkeypatch, capsys)
        assert status == "pass"
