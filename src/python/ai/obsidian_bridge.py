"""
Bridge to Obsidian's native CLI (v1.12.4+) for data sourcing.

Requires Obsidian to be running. Falls back silently if unavailable.
Data is used transiently — not synced to SQLite.

Usage:
    bridge = ObsidianBridge()
    backlinks = bridge.get_backlinks("my-note.md")  # [] if unavailable
    orphans = bridge.get_orphans()                    # [] if unavailable
    tags = bridge.get_tags()                          # {} if unavailable
    content = bridge.read_note("my-note.md")          # None if unavailable
"""

import subprocess
import json
from typing import List, Dict, Optional


class ObsidianBridge:
    """Bridge to Obsidian's native CLI for data sourcing.

    Every method returns an empty/None result if Obsidian CLI is
    unavailable, so callers don't need to check availability.
    """

    def __init__(self, verbose: bool = False):
        self._available: Optional[bool] = None
        self._verbose = verbose

    def is_available(self) -> bool:
        """Check if Obsidian CLI is installed and Obsidian is running.

        Result is cached after first check. Call reset() to re-check.
        """
        if self._available is None:
            try:
                result = subprocess.run(
                    ["obsidian", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                self._available = result.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                self._available = False
        if self._available is False and self._verbose:
            import sys
            print("  [verbose] Obsidian CLI not available, using file scanning fallback", file=sys.stderr)
        return self._available

    def reset(self):
        """Clear cached availability status."""
        self._available = None

    def get_backlinks(self, file: str) -> List[str]:
        """Get backlinks for a note. Returns empty list if unavailable."""
        if not self.is_available():
            return []
        try:
            result = subprocess.run(
                ["obsidian", "backlinks", f"file={file}", "format=json"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
            pass
        return []

    def get_orphans(self) -> List[str]:
        """Get orphaned notes. Returns empty list if unavailable."""
        if not self.is_available():
            return []
        try:
            result = subprocess.run(
                ["obsidian", "orphans", "format=json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
            pass
        return []

    def get_tags(self, sort: str = "count") -> Dict[str, int]:
        """Get vault tags with counts. Returns empty dict if unavailable."""
        if not self.is_available():
            return {}
        try:
            result = subprocess.run(
                ["obsidian", "tags", f"sort={sort}", "format=json"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
            pass
        return {}

    def get_status(self) -> 'BridgeStatus':
        """Check bridge status: CLI installation, app connection, capabilities.

        Refreshes the availability cache each call.
        """
        from ai.models import BridgeStatus

        cli_version = ""
        cli_installed = False
        try:
            result = subprocess.run(
                ["obsidian", "--version"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                cli_installed = True
                cli_version = result.stdout.strip()
                self._available = True
            else:
                self._available = False
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            self._available = False

        if not cli_installed:
            return BridgeStatus(
                cli_installed=False,
                cli_version="",
                app_running=False,
                capabilities=[],
            )

        # Check if Obsidian app is running (IPC-required command)
        app_running = False
        try:
            result = subprocess.run(
                ["obsidian", "vaults"],
                capture_output=True, text=True, timeout=5,
            )
            app_running = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass

        capabilities = ["search", "tags", "backlinks", "orphans", "read"]
        if app_running:
            capabilities += ["property:set", "daily-notes", "note:create", "note:append"]

        return BridgeStatus(
            cli_installed=cli_installed,
            cli_version=cli_version,
            app_running=app_running,
            capabilities=capabilities,
        )

    def read_note(self, file: str) -> Optional[str]:
        """Read note content via Obsidian CLI. Returns None if unavailable."""
        if not self.is_available():
            return None
        try:
            result = subprocess.run(
                ["obsidian", "read", f"file={file}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout
        except (subprocess.TimeoutExpired, OSError):
            pass
        return None
