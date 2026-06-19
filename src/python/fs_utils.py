"""
Shared filesystem utilities for obs — iCloud-aware FS ops.

Extracted from mcp_server.py so that both the MCP server and
core/doctor.py can share these without circular imports.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from pathlib import Path

# iCloud Drive: SF_DATALESS means the file/dir is a dataless placeholder (not materialized)
_SF_DATALESS = 0x40000000
_ICLOUD_MARKER = "iCloud~md~obsidian"

FS_WRITE_TIMEOUT = 30   # seconds before giving up on a blocked FS write
FS_PROBE_TIMEOUT = 5    # shorter timeout for doctor write-latency probe


def is_icloud_path(p: Path) -> bool:
    """Return True if the path lives under an iCloud Obsidian vault."""
    return _ICLOUD_MARKER in str(p)


def is_dataless(p: Path) -> bool:
    """Return True if path exists but is an iCloud dataless placeholder (not downloaded)."""
    try:
        st = os.stat(p)
        return bool(getattr(st, "st_flags", 0) & _SF_DATALESS)
    except OSError:
        return False


def fs_op(fn, timeout: int = FS_WRITE_TIMEOUT):
    """
    Run a blocking filesystem callable in a thread with a hard timeout.

    Raises TimeoutError with a human-readable message if the operation hangs
    (typical cause: iCloud Drive materializing an offloaded placeholder).
    """
    with ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(fn)
        try:
            return future.result(timeout=timeout)
        except FuturesTimeoutError:
            raise TimeoutError(
                f"Filesystem operation timed out after {timeout}s. "
                "The vault path may be an iCloud Drive placeholder that hasn't been "
                "downloaded. In Finder, right-click the vault folder → Download Now, "
                "or disable 'Optimize Mac Storage' in System Settings → Apple ID → iCloud."
            )
