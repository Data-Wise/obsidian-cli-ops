#!/usr/bin/env python3
"""
configure_mcp.py — Safely configures absolute paths for obsidian-ops MCP server
in Claude Desktop configurations.
"""
import os
import sys
import json
import shutil
from pathlib import Path

def main():
    print("🤖 Configuring Claude Desktop MCP server entry for obsidian-cli-ops...")
    
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
        print(f"❌ Error: MCP server script not found at {server_script}", file=sys.stderr)
        sys.exit(1)
        
    if not venv_python.exists():
        # Fallback to the interpreter running this script if venv python doesn't exist yet
        venv_python = Path(sys.executable)
        
    # NOTE: venv_python is deliberately NOT .resolve()'d below -- both branches
    # above (the venv path and the sys.executable fallback) are already
    # absolute, and a venv's own bin/python is itself commonly a symlink to a
    # version-pinned Homebrew/system interpreter. Resolving it here would bake
    # that version-pinned path into claude_desktop_config.json, defeating the
    # venv's stable-symlink indirection -- exactly the fragility obs doctor's
    # mcp-interpreter check (added v4.3.1) warns about.
    print(f"   Python Interpreter: {venv_python}")
    print(f"   MCP Server Script:  {server_script.resolve()}")
    
    # 2. Locate configuration files
    config_paths = [
        Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
        Path.home() / "Library" / "Application Support" / "Claude-3p" / "claude_desktop_config.json",
        Path.home() / ".config" / "claude" / "claude_desktop_config.json"
    ]
    
    updated_any = False
    for path in config_paths:
        parent = path.parent
        if not parent.exists():
            continue
            
        print(f"📂 Updating: {path}")
        
        config = {}
        if path.exists():
            # Backup
            backup_path = path.with_suffix(".json.bak")
            try:
                shutil.copy2(path, backup_path)
                print(f"   Created backup at {backup_path}")
            except Exception as e:
                print(f"   ⚠️ Warning: failed to create backup: {e}")
                
            try:
                with open(path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception as e:
                print(f"   ⚠️ Warning: failed to parse existing JSON: {e}. Starting fresh.")
                config = {}
                
        if "mcpServers" not in config or not isinstance(config["mcpServers"], dict):
            config["mcpServers"] = {}
            
        config["mcpServers"]["obsidian-ops"] = {
            "command": str(venv_python),
            "args": [str(server_script.resolve())]
        }
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            print("   ✅ Configuration updated successfully.")
            updated_any = True
        except Exception as e:
            print(f"   ❌ Error writing to {path}: {e}", file=sys.stderr)
            
    if not updated_any:
        print("⚠️ No active Claude Desktop configuration directories found. Skipping auto-config.")
        print("To configure manually, add this to your claude_desktop_config.json:")
        manual_cfg = {
            "mcpServers": {
                "obsidian-ops": {
                    "command": str(venv_python),
                    "args": [str(server_script.resolve())]
                }
            }
        }
        print(json.dumps(manual_cfg, indent=2))

if __name__ == "__main__":
    main()
