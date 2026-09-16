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


def main():
    print(f"Registering {SERVER_NAME} MCP server via the claude CLI...")

    # 1. Resolve absolute paths
    repo_dir = Path(__file__).resolve().parent.parent
    server_script = repo_dir / "src" / "python" / "mcp_server.py"

    # Resolve the virtual environment path
    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        data_dir = Path(xdg_data) / "obs"
    else:
        data_dir = Path.home() / ".local" / "share" / "obs"

    venv_python = data_dir / "venv" / "bin" / "python"

    if not server_script.exists():
        print(f"Error: MCP server script not found at {server_script}", file=sys.stderr)
        sys.exit(1)

    if not venv_python.exists():
        # Fallback to the interpreter running this script if venv python doesn't exist yet
        venv_python = Path(sys.executable)

    # NOTE: venv_python is deliberately NOT .resolve()'d below -- both branches
    # above (the venv path and the sys.executable fallback) are already
    # absolute, and a venv's own bin/python is itself commonly a symlink to a
    # version-pinned Homebrew/system interpreter. Resolving it here would bake
    # that version-pinned path into the registration, defeating the venv's
    # stable-symlink indirection -- exactly the fragility obs doctor's
    # mcp-interpreter check (added v4.3.1) warns about.
    print(f"   Python interpreter: {venv_python}")
    print(f"   MCP server script:  {server_script.resolve()}")

    claude_bin = shutil.which("claude")
    if not claude_bin:
        print("Error: `claude` CLI not found on PATH -- cannot register MCP server.", file=sys.stderr)
        print("Install/update Claude Code, then re-run this script, or register manually:", file=sys.stderr)
        print(f"  claude mcp add {SERVER_NAME} -s user -- {venv_python} {server_script.resolve()}", file=sys.stderr)
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
            str(venv_python), str(server_script.resolve()),
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
