#!/usr/bin/env python3
"""
configure_mcp.py — Registers the obsidian-ops MCP server with Claude Code
via the `claude mcp add` CLI.

Previously this wrote directly into claude_desktop_config.json's
mcpServers key. On the unified Claude Code + Cowork desktop app that file
has been repurposed for unrelated UI-state preferences (sidebar mode, pane
layout, etc.) and carries no mcpServers key at all, so writes to it never
reached the app's actual MCP registry. Registration now goes through the
`claude` CLI, which writes to ~/.claude.json (user scope, used here) or a
project's .mcp.json (project scope).
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

SERVER_NAME = "obsidian-ops"


def _resolve_python() -> Path:
    """Mirror obs.zsh's _obs_resolve_python 4-tier priority: explicit
    OBS_PYTHON -> install.sh user venv -> Homebrew formula venv (via the
    stable `brew --prefix` symlink, not a version-pinned Cellar path) ->
    ambient python3 (warn -- deps may be missing)."""
    obs_python = os.environ.get("OBS_PYTHON")
    if obs_python and os.access(obs_python.split()[0], os.X_OK):
        return Path(obs_python)

    xdg_data = os.environ.get("XDG_DATA_HOME")
    data_dir = Path(xdg_data) / "obs" if xdg_data else Path.home() / ".local" / "share" / "obs"
    user_venv = data_dir / "venv" / "bin" / "python"
    if user_venv.is_file() and os.access(user_venv, os.X_OK):
        return user_venv

    brew_bin = shutil.which("brew")
    if brew_bin:
        result = subprocess.run(
            [brew_bin, "--prefix", "obsidian-cli-ops"], capture_output=True, text=True
        )
        if result.returncode == 0:
            brew_venv = Path(result.stdout.strip()) / "libexec" / "venv" / "bin" / "python"
            if brew_venv.is_file() and os.access(brew_venv, os.X_OK):
                return brew_venv

    ambient = shutil.which("python3")
    if ambient:
        print(f"WARN: no isolated environment found; falling back to ambient python3 ({ambient}).", file=sys.stderr)
        print("WARN: obs dependencies may be missing. Provision an isolated env:", file=sys.stderr)
        print("WARN:   brew reinstall obsidian-cli-ops   # Homebrew", file=sys.stderr)
        print("WARN:   ./install.sh                      # manual install", file=sys.stderr)
        return Path(ambient)

    print("Error: no python3 interpreter found on PATH.", file=sys.stderr)
    sys.exit(1)


def main():
    print(f"Registering {SERVER_NAME} MCP server via the claude CLI...")

    # 1. Resolve absolute paths. Deliberately NOT .resolve()'d -- see the
    # venv_python note below. When invoked via the Homebrew opt/ symlink
    # (`python3 $(brew --prefix obsidian-cli-ops)/libexec/scripts/configure_mcp.py`,
    # as the tap caveats suggest), .resolve() would dereference opt/ down to
    # the version-pinned Cellar path and bake that into the `claude mcp add`
    # args, breaking registration on the next `brew upgrade`.
    repo_dir = Path(__file__).parent.parent
    server_script = repo_dir / "src" / "python" / "mcp_server.py"

    if not server_script.exists():
        print(f"Error: MCP server script not found at {server_script}", file=sys.stderr)
        sys.exit(1)

    # NOTE: venv_python is deliberately NOT .resolve()'d below -- a venv's own
    # bin/python is itself commonly a symlink to a version-pinned Homebrew/
    # system interpreter. Resolving it here would bake that version-pinned
    # path into the registration, defeating the venv's stable-symlink
    # indirection -- exactly the fragility obs doctor's mcp-interpreter check
    # (added v4.3.1) warns about.
    venv_python = _resolve_python()
    print(f"   Python interpreter: {venv_python}")
    print(f"   MCP server script:  {server_script}")

    claude_bin = shutil.which("claude")
    if not claude_bin:
        print("Error: `claude` CLI not found on PATH -- cannot register MCP server.", file=sys.stderr)
        print("Install/update Claude Code, then re-run this script, or register manually:", file=sys.stderr)
        print(f"  claude mcp add {SERVER_NAME} -s user -- {venv_python} {server_script}", file=sys.stderr)
        sys.exit(1)

    # Remove any stale registration first so re-running this script (e.g.
    # after the venv path changes) is idempotent instead of erroring on
    # "server already exists". Ignore failure -- it's a no-op when absent.
    subprocess.run(
        [claude_bin, "mcp", "remove", SERVER_NAME, "-s", "user"],
        capture_output=True,
    )

    result = subprocess.run(
        [
            claude_bin, "mcp", "add", SERVER_NAME, "-s", "user", "--",
            str(venv_python), str(server_script),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Error: `claude mcp add` failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    print(f"Registered {SERVER_NAME} with the claude CLI (user scope).")
    print("Restart Claude Code / the desktop app's Code tab to pick it up.")


if __name__ == "__main__":
    main()
