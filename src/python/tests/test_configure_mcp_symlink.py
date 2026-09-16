"""
Regression test for scripts/configure_mcp.py's repo/server-script path
resolution through a Homebrew `opt/` stable symlink.

Background: the script previously called `.resolve()` on `Path(__file__)`
(and again on the derived `server_script` path used for both the printed
diagnostics and the `claude mcp add` args). When invoked via Homebrew's
`opt/` symlink -- the exact command the tap's caveats suggest,
`python3 $(brew --prefix obsidian-cli-ops)/libexec/scripts/configure_mcp.py`
-- `.resolve()` dereferences `opt/` down to the version-pinned Cellar path
(e.g. `Cellar/obsidian-cli-ops/4.4.1_1/...`), baking a path that `brew
upgrade` deletes into the registered MCP server args. This is the same
fragility class as the venv_python `.resolve()` bug already fixed here
(see docs_mkdocs/changelog.md, "scripts/configure_mcp.py interpreter
pinning") -- except that one covered the interpreter, not the server
script path.

Runs configure_mcp.py as a real subprocess (not imported) because the bug
is specifically about how `__file__` reads through symlink indirection at
process-launch time -- importing the module directly bypasses that.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_SCRIPT = Path(__file__).parent.parent.parent.parent / "scripts" / "configure_mcp.py"


def _run_via_opt_symlink(tmp_path: Path) -> tuple[subprocess.CompletedProcess, Path]:
    """Lay out a Cellar/opt symlink pair mirroring Homebrew's layout and
    invoke configure_mcp.py through the opt/ symlink, the way the tap's own
    caveats tell users to run it. No `claude` binary on PATH, so the script
    exits at the "claude CLI not found" branch and prints the would-be
    registration command -- exercising the path logic with no side effects
    on the real `claude mcp` registry."""
    cellar_root = tmp_path / "Cellar" / "obsidian-cli-ops" / "4.4.1_1"
    (cellar_root / "libexec" / "scripts").mkdir(parents=True)
    (cellar_root / "libexec" / "src" / "python").mkdir(parents=True)
    (cellar_root / "libexec" / "src" / "python" / "mcp_server.py").write_text("")
    (cellar_root / "libexec" / "scripts" / "configure_mcp.py").write_text(_SCRIPT.read_text())

    opt_dir = tmp_path / "opt"
    opt_dir.mkdir()
    (opt_dir / "obsidian-cli-ops").symlink_to(cellar_root)

    script_via_symlink = opt_dir / "obsidian-cli-ops" / "libexec" / "scripts" / "configure_mcp.py"
    expected_server_script = opt_dir / "obsidian-cli-ops" / "libexec" / "src" / "python" / "mcp_server.py"

    env = dict(os.environ)
    env["PATH"] = "/usr/bin:/bin"
    env["OBS_PYTHON"] = sys.executable
    env.pop("XDG_DATA_HOME", None)

    result = subprocess.run(
        [sys.executable, str(script_via_symlink)],
        capture_output=True,
        text=True,
        env=env,
    )
    return result, expected_server_script


def test_server_script_path_keeps_opt_symlink_not_cellar(tmp_path):
    result, expected_server_script = _run_via_opt_symlink(tmp_path)
    output = result.stdout + result.stderr

    assert result.returncode == 1
    assert "claude` CLI not found" in output
    assert "Cellar" not in output, f"expected no Cellar-pinned path in output:\n{output}"
    assert str(expected_server_script) in output, f"expected opt/-based path in output:\n{output}"
