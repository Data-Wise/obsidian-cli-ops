#!/usr/bin/env python3
"""
Obsidian MCP Server v2.0

Exposes Obsidian vault operations as MCP tools for AI assistants (Claude Desktop,
Claude Code, Cowork). Covers vault metadata, graph analysis, health scoring,
full note read/write, and AI-powered ops via `obs` CLI subprocess.

Tools (39):
  Vault:    list_vaults, get_vault_stats, discover_vaults
  Search:   search_notes, find_similar_notes, unified_search
  Graph:    get_hub_notes, get_orphaned_notes, get_broken_links, analyze_vault
  Health:   get_vault_health
  Notes:    read_note, write_note, create_note, list_notes, append_to_note,
            insert_to_note, rename_note, delete_note, get_note_links, rescan_vault
  AI:       run_obs_ai
  Temporal: get_bridge_status, get_trends, get_stale_notes, get_daily_digest
  Config:   diagnose
  Zotero:   zotero_search, zotero_get, zotero_cite, zotero_recent
  PDF:      pdf_search
  Teaching: course_list, course_show, course_lectures
  Writing:  manuscript_list, manuscript_show, manuscript_stats
  Bib:      bib_check

Venv resolution (priority order):
  1. $OBS_PYTHON env var
  2. ~/.local/share/obs/venv/bin/python3  (install.sh user venv)
  3. /opt/homebrew/libexec/obs/venv/bin/python3  (Homebrew formula venv)
  4. ambient python3 (with warning to stderr)

If this script is launched by a non-obs python, it re-execs itself into the
correct interpreter so all imports resolve correctly.
"""

from __future__ import annotations

import os
import sys
import subprocess
import stat
from pathlib import Path

# ---------------------------------------------------------------------------
# Venv bootstrap — must happen before ANY local imports
# ---------------------------------------------------------------------------

def _find_obs_python() -> str:
    """Locate the obs-managed Python interpreter."""
    if env := os.environ.get("OBS_PYTHON"):
        if Path(env).exists():
            return env

    candidates = [
        Path.home() / ".local/share/obs/venv/bin/python3",
        # Homebrew `opt` prefix is a stable symlink to the active Cellar version,
        # so this covers any brew-installed version without a per-release pin.
        Path("/opt/homebrew/opt/obsidian-cli-ops/libexec/venv/bin/python3"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)

    print(
        "[obs-mcp] WARN: obs venv not found; using ambient python3. "
        "Run install.sh or brew reinstall obsidian-cli-ops to fix.",
        file=sys.stderr,
    )
    return sys.executable


_obs_python = _find_obs_python()
if Path(sys.executable).resolve() != Path(_obs_python).resolve():
    # Re-exec into the correct interpreter
    os.execv(_obs_python, [_obs_python] + sys.argv)

# ---------------------------------------------------------------------------
# Normal imports (now running inside obs venv)
# ---------------------------------------------------------------------------

from typing import Optional
from datetime import datetime

# Ensure src/python is on path
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP

from db_manager import DatabaseManager
from core.vault_manager import VaultManager
from core.graph_analyzer import GraphAnalyzer
from utils import format_relative_time

# ---------------------------------------------------------------------------
# Server + service init
# ---------------------------------------------------------------------------

mcp = FastMCP("obsidian-ops")

db = DatabaseManager()
vault_manager = VaultManager(db)
graph_analyzer = GraphAnalyzer(db)

# ---------------------------------------------------------------------------
# Server identity / staleness detection (#53)
# ---------------------------------------------------------------------------
# An in-process MCP server keeps the OLD code in memory after an upgrade — this
# is exactly what masked the v4.0.0 fix and motivated #53 (a v4.0.0-fixed tool
# still failed because the running server predated the fix). We freeze the
# version this process loaded at import time and compare it, on request, with
# the version currently on disk; a mismatch means the host is running stale code.
import re as _re
from datetime import timezone as _timezone

_VERSION_FILE = Path(__file__).parent / "__init__.py"


def _read_disk_version() -> str:
    """Parse __version__ from __init__.py on disk — the repo's single source of
    truth (same regex as `obs version` / test_version_consistency). Read fresh
    each call so a post-upgrade change is observable from a long-running process.
    """
    try:
        m = _re.search(r'__version__\s*=\s*"([^"]+)"',
                       _VERSION_FILE.read_text(encoding="utf-8"))
        return m.group(1) if m else "unknown"
    except OSError:
        return "unknown"


# Frozen at import = the version of the code THIS process is actually running.
_SERVER_VERSION = _read_disk_version()
_SERVER_STARTED_AT = datetime.now(_timezone.utc).isoformat()

# Path to obs CLI (for AI subcommand subprocess calls)
_OBS_CLI = Path(__file__).parent / "obs_cli.py"
_PYTHON = sys.executable  # already the obs venv python


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _obs(args: list[str], timeout: int = 60) -> str:
    """Run obs_cli.py with given args, return stdout+stderr as string."""
    cmd = [_PYTHON, str(_OBS_CLI)] + args
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        if result.returncode != 0 and err:
            return f"[obs error {result.returncode}] {err}\n{out}".strip()
        return out or err or "(no output)"
    except subprocess.TimeoutExpired:
        return f"[obs timeout] Command took >{timeout}s: {' '.join(args)}"
    except Exception as e:
        return f"[obs exception] {e}"


def _vault_path(vault_id: str) -> Optional[Path]:
    """Return the filesystem path for a vault_id, or None."""
    row = db.get_vault(vault_id)
    return Path(row["path"]) if row else None


def _resolve_vault(vault_id: str):
    """Resolve a user-supplied vault identifier to a vault row.

    Accepts a vault **name**, full **ID**, or unambiguous **ID prefix** — the
    same 3-tier lookup the CLI uses (db.get_vault_by_name_or_id). MCP tools must
    route through this, never db.get_vault() (exact-ID-only), so that callers
    passing a vault name don't silently get "Vault not found".

    Returns (vault_dict, None) on success, or (None, error_message) on failure.
    """
    try:
        vault = db.get_vault_by_name_or_id(vault_id)
    except ValueError as e:  # ambiguous ID prefix
        return None, f"Ambiguous vault '{vault_id}': {e}"
    if not vault:
        return None, f"Vault not found: {vault_id}"
    return vault, None


# iCloud / FS utilities — shared with core/doctor.py via fs_utils
from fs_utils import is_icloud_path as _is_icloud_path, is_dataless as _is_dataless, fs_op as _fs_op, FS_WRITE_TIMEOUT as _FS_WRITE_TIMEOUT


# ---------------------------------------------------------------------------
# TOOLS — Vault
# ---------------------------------------------------------------------------

@mcp.tool()
def list_vaults() -> str:
    """
    List all Obsidian vaults registered in the obs database.

    Returns vault names, note/link counts, and last-scan timestamps.
    Call this first to get vault_id values needed by other tools.
    """
    try:
        vaults = vault_manager.list_vaults()
        if not vaults:
            return "No vaults found. Use discover_vaults(path) to register one."

        lines = ["📚 **Obsidian Vaults**\n"]
        for v in vaults:
            status = "✓ Scanned" if v.last_scanned else "⊘ Not scanned"
            lines += [
                f"- **{v.name}** ({status})",
                f"  - Notes: {v.note_count} | Links: {v.link_count}",
                f"  - Last scanned: {format_relative_time(v.last_scanned)}",
                f"  - ID: `{v.id}`",
                f"  - Path: {v.path}",
                "",
            ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing vaults: {e}"


@mcp.tool()
def get_vault_stats(vault_id: Optional[str] = None) -> str:
    """
    Get statistics for a specific vault or the entire obs database.

    Args:
        vault_id: Vault name or ID (accepts name, full ID, or unambiguous ID
                  prefix), or omit for global stats.

    Returns notes, links, tags, orphan count, broken link count.
    """
    try:
        if vault_id:
            vault, err = _resolve_vault(vault_id)
            if err:
                return err
            vault_id = vault["id"]  # canonical id for downstream db queries
            notes = db.list_notes(vault_id)
            orphans = db.get_orphaned_notes(vault_id)
            broken = db.get_broken_links(vault_id)
            broken_count = sum(b.get("broken_count", 0) for b in broken)
            tags = db.get_vault_tag_stats(vault_id)
            return (
                f"📊 **{vault['name']}**\n\n"
                f"**Content**\n"
                f"- Notes: {len(notes)}\n"
                f"- Tags: {len(tags)} unique tags\n"
                f"- Path: {vault['path']}\n"
                f"- Last scanned: {format_relative_time(vault.get('last_scanned'))}\n\n"
                f"**Graph Health**\n"
                f"- Orphaned notes: {len(orphans)} ({len(orphans)*100//max(len(notes),1)}%)\n"
                f"- Broken links: {broken_count} across {len(broken)} notes\n"
            )
        else:
            s = db.get_stats()
            return (
                f"📊 **Database Overview**\n\n"
                f"- Vaults: {s['vaults']}\n"
                f"- Notes: {s['notes']}\n"
                f"- Links: {s['links']}\n"
                f"- Tags: {s['tags']}\n"
                f"- Orphaned notes: {s['orphaned_notes']}\n"
                f"- Broken links: {s['broken_links']}\n"
            )
    except Exception as e:
        return f"Error getting stats: {e}"


@mcp.tool()
def discover_vaults(path: str) -> str:
    """
    Scan a filesystem path to discover and register Obsidian vaults.

    Args:
        path: Directory to search (e.g. '/Users/dt' or '~/Documents').

    Use this when a vault is missing from list_vaults().
    """
    try:
        expanded = str(Path(path).expanduser().resolve())
        found = vault_manager.discover_vaults(expanded)
        if not found:
            return f"No Obsidian vaults found under {expanded}"
        lines = [f"Found {len(found)} vault(s) under {expanded}:\n"]
        for p in found:
            lines.append(f"  - {p}")
        lines.append("\nRun get_vault_stats() to see registered vaults.")
        return "\n".join(lines)
    except Exception as e:
        return f"Error discovering vaults: {e}"


# ---------------------------------------------------------------------------
# TOOLS — Search
# ---------------------------------------------------------------------------

@mcp.tool()
def search_notes(query: str, vault_id: Optional[str] = None, limit: int = 10) -> str:
    """
    Search notes by title and content across vaults.

    Args:
        query: Search term (title or body text).
        vault_id: Scope to a specific vault (optional).
        limit: Max results (default 10).

    Returns matching notes with vault, path, and content snippet.
    """
    try:
        results = vault_manager.search_notes(query, vault_id=vault_id)
        results = results[:limit]
        if not results:
            return f"No notes found matching '{query}'"

        lines = [f"Found {len(results)} notes matching '{query}':\n"]
        for i, note in enumerate(results, 1):
            lines += [
                f"{i}. **{note['title']}**",
                f"   Vault: {note.get('vault_name', 'Unknown')}",
                f"   Path: {note['path']}",
                f"   ID: `{note['id']}`",
            ]
            if note.get("snippet"):
                lines.append(f"   Snippet: ...{note['snippet']}...")
            lines.append("")
        return "\n".join(lines)
    except Exception as e:
        return f"Error searching notes: {e}"


@mcp.tool()
def find_similar_notes(note_title: str, vault_id: Optional[str] = None, limit: int = 5) -> str:
    """
    Find notes similar to a given title or topic.

    Args:
        note_title: Title or topic to find similar notes for.
        vault_id: Scope to a specific vault (optional).
        limit: Max results (default 5).

    Uses title-based search as a similarity proxy. For embedding-based
    similarity, use run_obs_ai('similar', note_id).
    """
    try:
        results = vault_manager.search_notes(note_title, vault_id=vault_id)
        results = results[:limit]
        if not results:
            return f"No similar notes found for '{note_title}'"

        lines = [f"Notes related to '{note_title}':\n"]
        for i, note in enumerate(results, 1):
            lines += [
                f"{i}. **{note['title']}**",
                f"   Path: {note['path']}",
                f"   ID: `{note['id']}`",
                "",
            ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error finding similar notes: {e}"


# ---------------------------------------------------------------------------
# TOOLS — Graph
# ---------------------------------------------------------------------------

@mcp.tool()
def get_hub_notes(vault_id: str, limit: int = 10) -> str:
    """
    Get the most connected (hub) notes in a vault by total link degree.

    Args:
        vault_id: Vault name or ID (accepts name, full ID, or unambiguous ID prefix).
        limit: Max notes to return (default 10).

    Hub notes are high-PageRank nodes — good candidates for index/MOC pages.
    """
    try:
        vault, err = _resolve_vault(vault_id)
        if err:
            return err
        hubs = graph_analyzer.get_hub_notes(vault["id"], limit=limit)
        if not hubs:
            return "No hub notes found. The vault may need more internal linking."

        lines = ["🌟 **Hub Notes** (most connected)\n"]
        for i, hub in enumerate(hubs, 1):
            ind = hub.get("in_degree", 0)
            outd = hub.get("out_degree", 0)
            lines += [
                f"{i}. **{hub['title']}** ({ind + outd} connections)",
                f"   ↙️ {ind} incoming  ↗️ {outd} outgoing",
                f"   ID: `{hub.get('id', hub.get('note_id', '?'))}`",
                "",
            ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error getting hub notes: {e}"


@mcp.tool()
def get_orphaned_notes(vault_id: str, limit: int = 20) -> str:
    """
    Get notes with no incoming or outgoing links (isolated notes).

    Args:
        vault_id: Vault name or ID (accepts name, full ID, or unambiguous ID prefix).
        limit: Max notes to return (default 20).

    Orphaned notes are candidates for deletion, merging, or linking.
    """
    try:
        vault, err = _resolve_vault(vault_id)
        if err:
            return err
        orphans = db.get_orphaned_notes(vault["id"])
        if not orphans:
            return "✅ No orphaned notes! Your vault is well-connected."

        lines = [
            f"🏝️ **{len(orphans)} Orphaned Notes** (showing {min(limit, len(orphans))})\n",
            "These notes have no links to or from other notes:\n",
        ]
        for i, o in enumerate(orphans[:limit], 1):
            lines += [
                f"{i}. **{o['title']}**",
                f"   Path: {o['path']}",
                f"   ID: `{o['id']}`",
                "",
            ]
        if len(orphans) > limit:
            lines.append(f"... and {len(orphans) - limit} more")
        return "\n".join(lines)
    except Exception as e:
        return f"Error getting orphaned notes: {e}"


@mcp.tool()
def get_broken_links(vault_id: str) -> str:
    """
    Get notes that contain broken wikilinks (links to non-existent notes).

    Args:
        vault_id: Vault name or ID (accepts name, full ID, or unambiguous ID prefix).

    Returns notes with broken link counts. Fix by updating or removing links.
    """
    try:
        vault, err = _resolve_vault(vault_id)
        if err:
            return err
        broken = db.get_broken_links(vault["id"])
        if not broken:
            return "✅ No broken links found!"

        total = sum(b.get("broken_count", 0) for b in broken)
        lines = [f"🔗 **{total} Broken Links** across {len(broken)} notes\n"]
        for b in broken:
            lines += [
                f"- **{b.get('title', 'Unknown')}** — {b['broken_count']} broken link(s)",
                f"  Path: {b.get('path', '?')}",
                "",
            ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error getting broken links: {e}"


@mcp.tool()
def analyze_vault(vault_id: str) -> str:
    """
    Run full graph analysis on a vault (link resolution, PageRank, clustering).

    Args:
        vault_id: Vault name or ID (accepts name, full ID, or unambiguous ID prefix).

    This is the equivalent of `obs analyze <vault>`. Updates graph_metrics
    in the database and returns a summary. May take 5–30s for large vaults.
    """
    try:
        vault, err = _resolve_vault(vault_id)
        if err:
            return err
        result = graph_analyzer.analyze_vault(vault["id"])
        return (
            f"🔬 **Graph Analysis: {result['vault_name']}**\n\n"
            f"- Notes: {result['total_notes']}\n"
            f"- Edges: {result['total_edges']}\n"
            f"- Graph density: {result['graph_density']:.4f}\n"
            f"- Links resolved: {result['links_resolved']}\n"
            f"- Broken links: {result['links_broken']}\n"
            f"- Clusters found: {result['clusters_found']}\n"
            f"- Largest cluster: {result['largest_cluster_size']} notes\n"
        )
    except Exception as e:
        return f"Error analyzing vault: {e}"


# ---------------------------------------------------------------------------
# TOOLS — Health
# ---------------------------------------------------------------------------

@mcp.tool()
def get_vault_health(vault_id: str) -> str:
    """
    Get the 4-dimension health score for a vault.

    Args:
        vault_id: Vault ID or name from list_vaults().

    Dimensions: Connectivity (30%), Link Integrity (25%), Structure (25%),
    Freshness (20%). Returns scores 0–100 with recommendations.
    Equivalent to `obs health <vault>`.
    """
    try:
        health = vault_manager.get_vault_health(vault_id)

        def bar(score: int) -> str:
            filled = score // 10
            return "█" * filled + "░" * (10 - filled) + f" {score}/100"

        lines = [
            f"🏥 **Vault Health: {health.vault_name}**",
            f"Overall: {bar(health.overall)}\n",
            f"**Connectivity** (30%): {bar(health.connectivity.score)}",
        ]
        for d in health.connectivity.details:
            lines.append(f"  - {d}")
        for r in health.connectivity.recommendations:
            lines.append(f"  ⚠️  {r}")

        lines += ["", f"**Link Integrity** (25%): {bar(health.link_integrity.score)}"]
        for d in health.link_integrity.details:
            lines.append(f"  - {d}")
        for r in health.link_integrity.recommendations:
            lines.append(f"  ⚠️  {r}")

        lines += ["", f"**Structure** (25%): {bar(health.structure.score)}"]
        for d in health.structure.details:
            lines.append(f"  - {d}")
        for r in health.structure.recommendations:
            lines.append(f"  ⚠️  {r}")

        lines += ["", f"**Freshness** (20%): {bar(health.freshness.score)}"]
        for d in health.freshness.details:
            lines.append(f"  - {d}")
        for r in health.freshness.recommendations:
            lines.append(f"  ⚠️  {r}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting vault health: {e}"


# ---------------------------------------------------------------------------
# TOOLS — Note read/write
# ---------------------------------------------------------------------------

@mcp.tool()
def list_notes(vault_id: str, limit: int = 50, offset: int = 0) -> str:
    """
    List notes in a vault with their IDs and paths.

    Args:
        vault_id: Vault name or ID (accepts name, full ID, or unambiguous ID prefix).
        limit: Max notes to return (default 50).
        offset: Pagination offset (default 0).

    Use note IDs returned here with read_note() and write_note().
    """
    try:
        vault, err = _resolve_vault(vault_id)
        if err:
            return err
        vault_id = vault["id"]  # canonical id for downstream db queries
        notes = db.list_notes(vault_id, limit=limit, offset=offset)
        if not notes:
            return f"No notes found in vault {vault['name']}. Try scanning it first."

        lines = [f"📝 **{len(notes)} Notes** (offset={offset})\n"]
        for n in notes:
            lines.append(f"- **{n['title']}**  `{n['id']}`")
            lines.append(f"  {n['path']}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing notes: {e}"


@mcp.tool()
def read_note(note_id: str) -> str:
    """
    Read the full markdown content of a note by its ID.

    Args:
        note_id: Note ID from search_notes(), list_notes(), or get_hub_notes().

    Returns the raw markdown content of the note file from disk.
    Use search_notes() first to find the note_id if you only know the title.
    """
    try:
        note = db.get_note(note_id)
        if not note:
            return f"Note not found: {note_id}. Use search_notes() to find valid IDs."

        vault = db.get_vault(note["vault_id"])
        if not vault:
            return f"Vault not found for note {note_id}"

        # note['path'] is relative to vault root
        note_path = Path(vault["path"]) / note["path"]
        if not note_path.exists():
            return f"Note file not found on disk: {note_path}"

        content = note_path.read_text(encoding="utf-8")
        return (
            f"# {note['title']}\n"
            f"**Path**: {note_path}\n"
            f"**ID**: `{note_id}`\n"
            f"**Word count**: {note.get('word_count', '?')}\n"
            f"**Last modified**: {format_relative_time(note.get('modified_at'))}\n\n"
            f"---\n\n"
            f"{content}"
        )
    except Exception as e:
        return f"Error reading note: {e}"


@mcp.tool()
def write_note(note_id: str, content: str, create_backup: bool = True) -> str:
    """
    Overwrite the content of an existing note.

    Args:
        note_id: Note ID from search_notes() or list_notes().
        content: New markdown content to write (replaces existing content).
        create_backup: If True (default), saves a .bak file before overwriting.

    IMPORTANT: This writes directly to the vault filesystem. The obs database
    will be out of sync until the vault is rescanned. After writing, the note
    will appear stale in graph analysis until you run analyze_vault().

    Use create_note() to create a new note instead of overwriting.
    """
    try:
        note = db.get_note(note_id)
        if not note:
            return f"Note not found: {note_id}"

        vault = db.get_vault(note["vault_id"])
        if not vault:
            return f"Vault not found for note {note_id}"

        note_path = Path(vault["path"]) / note["path"]
        if not note_path.exists():
            return f"Note file not found on disk: {note_path}"

        if _is_dataless(note_path):
            return (
                f"❌ Note is an iCloud placeholder (not downloaded): {note_path}\n"
                "In Finder, right-click the file → Download Now before writing."
            )

        icloud_warn = "\n⚠️  iCloud path detected — write may be slow if parent dirs are not materialized." if _is_icloud_path(note_path) else ""

        def _do_write():
            bak_path = None
            if create_backup:
                bak_path = note_path.with_suffix(".md.bak")
                bak_path.write_text(note_path.read_text(encoding="utf-8"), encoding="utf-8")
            note_path.write_text(content, encoding="utf-8")
            return bak_path

        bak_path = _fs_op(_do_write)
        word_count = len(content.split())

        return (
            f"✅ **Note written**: {note['title']}\n"
            f"- Path: {note_path}\n"
            f"- Words: {word_count}\n"
            + (f"- Backup: {bak_path}\n" if bak_path else "")
            + f"\n⚠️  Run analyze_vault('{note['vault_id']}') to update graph metrics."
            + icloud_warn
        )
    except TimeoutError as e:
        return f"❌ Write timed out: {e}"
    except Exception as e:
        return f"Error writing note: {e}"


@mcp.tool()
def create_note(
    vault_id: str,
    title: str,
    content: str,
    subfolder: str = "",
) -> str:
    """
    Create a new markdown note in a vault.

    Args:
        vault_id: Vault name or ID (accepts name, full ID, or unambiguous ID prefix).
        title: Note title (used as filename, spaces → hyphens).
        content: Markdown content for the note.
        subfolder: Optional subfolder within the vault (e.g. 'research/causal').

    Creates the file at <vault_path>/<subfolder>/<title>.md.
    Returns error if the file already exists (use write_note() to overwrite).
    After creation, run analyze_vault() to index the note in graph analysis.
    """
    try:
        vault, err = _resolve_vault(vault_id)
        if err:
            return err

        vault_root = Path(vault["path"])
        safe_title = title.replace(" ", "-").replace("/", "-").strip("-")
        if not safe_title.endswith(".md"):
            safe_title += ".md"

        note_dir = (vault_root / subfolder) if subfolder else vault_root
        note_path = note_dir / safe_title

        if note_path.exists():
            return (
                f"❌ Note already exists: {note_path}\n"
                f"Use write_note() with the existing note's ID to overwrite."
            )

        if _is_dataless(note_dir) or (not note_dir.exists() and _is_icloud_path(note_dir)):
            icloud_warn = (
                f"\n⚠️  Target directory is an iCloud placeholder or doesn't exist yet: {note_dir}\n"
                "mkdir + write may be slow. If it times out, download the vault in Finder first."
            )
        else:
            icloud_warn = ""

        def _do_create():
            note_dir.mkdir(parents=True, exist_ok=True)
            note_path.write_text(content, encoding="utf-8")

        _fs_op(_do_create)
        word_count = len(content.split())
        rel_path = note_path.relative_to(vault_root)

        return (
            f"✅ **Note created**: {title}\n"
            f"- Path: {note_path}\n"
            f"- Relative: {rel_path}\n"
            f"- Words: {word_count}\n\n"
            f"⚠️  Run analyze_vault('{vault_id}') to index the note in graph analysis."
            + icloud_warn
        )
    except TimeoutError as e:
        return f"❌ Create timed out: {e}"
    except Exception as e:
        return f"Error creating note: {e}"


# ---------------------------------------------------------------------------
# TOOLS — Additional note manipulation
# ---------------------------------------------------------------------------

@mcp.tool()
def append_to_note(note_id: str, content: str, separator: str = "\n\n") -> str:
    """
    Append content to the end of an existing note without overwriting it.

    Args:
        note_id: Note ID from search_notes() or list_notes().
        content: Markdown content to append.
        separator: Text inserted between existing content and appended content
                   (default: two newlines).

    Safer than write_note() when you only want to add content rather than
    replace it. No backup is created (appending is non-destructive).
    """
    try:
        note = db.get_note(note_id)
        if not note:
            return f"Note not found: {note_id}"

        vault = db.get_vault(note["vault_id"])
        if not vault:
            return f"Vault not found for note {note_id}"

        note_path = Path(vault["path"]) / note["path"]
        if not note_path.exists():
            return f"Note file not found on disk: {note_path}"

        if _is_dataless(note_path):
            return (
                f"❌ Note is an iCloud placeholder (not downloaded): {note_path}\n"
                "In Finder, right-click the file → Download Now before appending."
            )

        def _do_append():
            existing = note_path.read_text(encoding="utf-8")
            new_content = existing.rstrip() + separator + content
            note_path.write_text(new_content, encoding="utf-8")
            return new_content

        new_content = _fs_op(_do_append)
        added_words = len(content.split())
        return (
            f"✅ **Appended to**: {note['title']}\n"
            f"- Path: {note_path}\n"
            f"- Added: {added_words} words\n"
            f"- Total: {len(new_content.split())} words\n\n"
            f"⚠️  Run analyze_vault('{note['vault_id']}') to update graph metrics."
        )
    except TimeoutError as e:
        return f"❌ Append timed out: {e}"
    except Exception as e:
        return f"Error appending to note: {e}"


@mcp.tool()
def insert_to_note(
    note_id: str,
    content: str,
    after_heading: Optional[str] = None,
    before_heading: Optional[str] = None,
    as_table_row: bool = False,
    replace_section: Optional[str] = None,
) -> str:
    """
    Insert content into a note at a heading-relative position.

    Exactly one of after_heading, before_heading, or replace_section must be
    set, or none (EOF append, equivalent to append_to_note).

    Args:
        note_id: Note ID from search_notes() or list_notes().
        content: Markdown content to insert.
        after_heading: Heading text (case-insensitive) — insert after this heading.
        before_heading: Heading text (case-insensitive) — insert before this heading.
        as_table_row: When True and after_heading is set, appends content as a
                      table row to the table found under that heading.
        replace_section: Heading text — replaces all content between this heading
                         and the next same-level heading with content.
    """
    from core.note_inserter import (
        insert_after_heading,
        insert_before_heading,
        append_table_row,
        replace_section as _replace_section,
    )

    modes_set = sum([
        after_heading is not None,
        before_heading is not None,
        replace_section is not None,
    ])
    if modes_set > 1:
        return "❌ Only one of after_heading, before_heading, replace_section may be set."
    if as_table_row and after_heading is None:
        return "❌ as_table_row requires after_heading to locate the table."

    try:
        note = db.get_note(note_id)
        if not note:
            return f"Note not found: {note_id}"

        vault = db.get_vault(note["vault_id"])
        if not vault:
            return f"Vault not found for note {note_id}"

        note_path = Path(vault["path"]) / note["path"]
        if not note_path.exists():
            return f"Note file not found on disk: {note_path}"

        if _is_dataless(note_path):
            return (
                f"❌ Note is an iCloud placeholder (not downloaded): {note_path}\n"
                "In Finder, right-click the file → Download Now before inserting."
            )

        def _do_insert():
            text = note_path.read_text(encoding="utf-8")
            if after_heading is not None and as_table_row:
                new_text = append_table_row(text, after_heading, content)
            elif after_heading is not None:
                new_text = insert_after_heading(text, after_heading, content)
            elif before_heading is not None:
                new_text = insert_before_heading(text, before_heading, content)
            elif replace_section is not None:
                new_text = _replace_section(text, replace_section, content)
            else:
                new_text = text.rstrip() + "\n\n" + content
            note_path.write_text(new_text, encoding="utf-8")
            return new_text

        new_text = _fs_op(_do_insert)
        added_words = len(content.split())
        mode_desc = (
            f"after heading '{after_heading}'"
            if after_heading and not as_table_row
            else f"as table row under '{after_heading}'"
            if as_table_row
            else f"before heading '{before_heading}'"
            if before_heading
            else f"replacing section '{replace_section}'"
            if replace_section
            else "at EOF"
        )
        return (
            f"✅ **Inserted into**: {note['title']}\n"
            f"- Mode: {mode_desc}\n"
            f"- Path: {note_path}\n"
            f"- Added: {added_words} words\n"
            f"- Total: {len(new_text.split())} words\n\n"
            f"⚠️  Run analyze_vault('{note['vault_id']}') to update graph metrics."
        )
    except ValueError as e:
        return f"❌ {e}"
    except TimeoutError as e:
        return f"❌ Insert timed out: {e}"
    except Exception as e:
        return f"Error inserting into note: {e}"


@mcp.tool()
def rename_note(note_id: str, new_title: str, subfolder: str = "") -> str:
    """
    Rename a note (changes filename on disk; does NOT update wikilinks in other notes).

    Args:
        note_id: Note ID from search_notes() or list_notes().
        new_title: New title/filename (spaces → hyphens, .md appended automatically).
        subfolder: Move to a different subfolder within the vault (optional;
                   omit to keep same directory).

    WARNING: Renaming breaks wikilinks in other notes that reference the old
    title. After renaming, run analyze_vault() to find newly broken links,
    then fix them manually or use run_obs_ai('suggest-links', ...) to reconnect.
    """
    try:
        note = db.get_note(note_id)
        if not note:
            return f"Note not found: {note_id}"

        vault = db.get_vault(note["vault_id"])
        if not vault:
            return f"Vault not found for note {note_id}"

        vault_root = Path(vault["path"])
        old_path = vault_root / note["path"]
        if not old_path.exists():
            return f"Note file not found on disk: {old_path}"

        safe_title = new_title.replace(" ", "-").replace("/", "-").strip("-")
        if not safe_title.endswith(".md"):
            safe_title += ".md"

        target_dir = (vault_root / subfolder) if subfolder else old_path.parent
        new_path = target_dir / safe_title
        if new_path.exists():
            return f"❌ A note already exists at: {new_path}"

        def _do_rename():
            target_dir.mkdir(parents=True, exist_ok=True)
            old_path.rename(new_path)

        _fs_op(_do_rename)
        old_rel = old_path.relative_to(vault_root)
        new_rel = new_path.relative_to(vault_root)

        return (
            f"✅ **Note renamed**\n"
            f"- Old: {old_rel}\n"
            f"- New: {new_rel}\n\n"
            f"⚠️  Wikilinks to '{note['title']}' in other notes are now broken.\n"
            f"   Run analyze_vault('{note['vault_id']}') then get_broken_links() to find them."
        )
    except TimeoutError as e:
        return f"❌ Rename timed out: {e}"
    except Exception as e:
        return f"Error renaming note: {e}"


@mcp.tool()
def delete_note(note_id: str, confirm: bool = False) -> str:
    """
    Delete a note from the vault filesystem and obs database.

    Args:
        note_id: Note ID from search_notes() or list_notes().
        confirm: Must be True to actually delete. Pass False (default) to
                 preview what would be deleted without doing it.

    This is IRREVERSIBLE — the file is permanently deleted.
    Use confirm=False first to see what will be removed, then confirm=True.
    """
    try:
        note = db.get_note(note_id)
        if not note:
            return f"Note not found: {note_id}"

        vault = db.get_vault(note["vault_id"])
        if not vault:
            return f"Vault not found for note {note_id}"

        note_path = Path(vault["path"]) / note["path"]

        if not confirm:
            return (
                f"⚠️  **DRY RUN — nothing deleted**\n\n"
                f"Would delete: **{note['title']}**\n"
                f"- Path: {note_path}\n"
                f"- Exists on disk: {note_path.exists()}\n"
                f"- Word count: {note.get('word_count', '?')}\n\n"
                f"To actually delete, call delete_note('{note_id}', confirm=True)"
            )

        # Delete from filesystem
        deleted_from_disk = False
        if note_path.exists():
            _fs_op(note_path.unlink)
            deleted_from_disk = True

        return (
            f"🗑️ **Note deleted**: {note['title']}\n"
            f"- File removed from disk: {deleted_from_disk}\n"
            f"- Path was: {note_path}\n\n"
            f"⚠️  Run analyze_vault('{note['vault_id']}') to remove it from graph metrics."
        )
    except TimeoutError as e:
        return f"❌ Delete timed out: {e}"
    except Exception as e:
        return f"Error deleting note: {e}"


@mcp.tool()
def get_note_links(note_id: str) -> str:
    """
    Get all outgoing links from a note and all incoming backlinks to it.

    Args:
        note_id: Note ID from search_notes() or list_notes().

    Returns both outgoing wikilinks and incoming backlinks with note titles.
    Useful for understanding a note's position in the knowledge graph before
    renaming or deleting it.
    """
    try:
        note = db.get_note(note_id)
        if not note:
            return f"Note not found: {note_id}"

        outgoing = db.get_outgoing_links(note_id)
        incoming = db.get_incoming_links(note_id)

        lines = [f"🔗 **Links for: {note['title']}**\n"]

        lines.append(f"**Outgoing** ({len(outgoing)} links):")
        if outgoing:
            for lnk in outgoing:
                target = db.get_note(lnk["target_note_id"]) if lnk.get("target_note_id") else None
                title = target["title"] if target else lnk.get("target_path", "?")
                status = "✓" if lnk.get("is_resolved") else "❌ broken"
                lines.append(f"  - [[{title}]] ({status})")
        else:
            lines.append("  (none)")

        lines.append(f"\n**Incoming backlinks** ({len(incoming)} notes link here):")
        if incoming:
            for lnk in incoming:
                source = db.get_note(lnk["source_note_id"])
                title = source["title"] if source else lnk.get("source_note_id", "?")
                lines.append(f"  - [[{title}]]")
        else:
            lines.append("  (none)")

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting note links: {e}"


@mcp.tool()
async def rescan_vault(vault_id: str) -> str:
    """
    Rescan a vault to sync the obs database with current filesystem state.

    Args:
        vault_id: Vault name or ID (accepts name, full ID, or unambiguous ID prefix).

    Run this after write_note(), create_note(), rename_note(), or delete_note()
    to bring graph metrics and search indexes up to date. Re-scans the vault on
    disk and updates the obs database. May take 5–60s for large vaults.
    """
    try:
        vault, err = _resolve_vault(vault_id)
        if err:
            return err
        # Real scan: vault_manager.scan_vault re-reads the filesystem and updates
        # the DB. (The old code shelled to `obs stats`, which is READ-ONLY and
        # never rescanned — it reported success while changing nothing.)
        #
        # FastMCP dispatches this handler inside an already-running event loop,
        # so we `await` the coroutine directly. The previous asyncio.run() raised
        # `RuntimeError: asyncio.run() cannot be called from a running event
        # loop` on every MCP call (#62), leaving the DB/index silently stale.
        result = await vault_manager.scan_vault(vault["path"], vault["name"])
        return (
            f"🔄 **Rescanned {result.vault_name}**\n"
            f"- Notes scanned: {result.notes_scanned}\n"
            f"- Links found: {result.links_found}\n"
            f"- Duration: {result.duration_seconds:.1f}s"
        )
    except Exception as e:
        return f"Error rescanning vault: {e}"


# ---------------------------------------------------------------------------
# TOOLS — AI (subprocess bridge to obs ai subcommands)
# ---------------------------------------------------------------------------

@mcp.tool()
def run_obs_ai(
    command: str,
    target: str,
    vault_id: Optional[str] = None,
) -> str:
    """
    Run an obs AI command on a note or vault.

    Args:
        command: One of: similar, analyze, duplicates, suggest-links, gaps,
                 summarize, quality, tag-suggest, merge-suggest.
        target: Note ID (for note-level commands) or vault name/ID
                (for vault-level commands: duplicates, gaps, summarize,
                 merge-suggest, tag-suggest).
        vault_id: Required for note-level commands to scope the vault context.

    Examples:
        run_obs_ai('summarize', 'my-research-vault')
        run_obs_ai('similar', '<note_id>')
        run_obs_ai('tag-suggest', 'my-research-vault')
        run_obs_ai('quality', '<note_id>')

    Note-level commands: similar, analyze, suggest-links, quality
    Vault-level commands: duplicates, gaps, summarize, merge-suggest, tag-suggest

    First invocation may be slow (30–60s) if embedding model needs to load.
    Returns JSON-formatted results when available.
    """
    NOTE_COMMANDS = {"similar", "analyze", "suggest-links", "quality"}
    VAULT_COMMANDS = {"duplicates", "gaps", "summarize", "merge-suggest", "tag-suggest"}

    if command not in NOTE_COMMANDS | VAULT_COMMANDS:
        valid = ", ".join(sorted(NOTE_COMMANDS | VAULT_COMMANDS))
        return f"Unknown command '{command}'. Valid: {valid}"

    args = ["ai", command, target, "--json"]
    return _obs(args, timeout=120)


# ---------------------------------------------------------------------------
# TOOLS — Bridge & Temporal (offline, zero-dep)
# ---------------------------------------------------------------------------

@mcp.tool()
def get_bridge_status() -> str:
    """
    Check whether the Obsidian official CLI is installed and the app is running.

    Returns a JSON object with:
      cli_installed (bool), cli_version (str), app_running (bool),
      capabilities (list of command strings available right now).

    Use this before calling obsidian CLI commands to understand what's available.
    """
    try:
        result = vault_manager.get_bridge_status()
        import json
        return json.dumps(result.to_dict(), indent=2)
    except Exception as e:
        return f"Error checking bridge status: {e}"


@mcp.tool()
def server_info() -> str:
    """
    Report this running obs MCP server's identity and whether it is stale.

    An in-process MCP server keeps the code it loaded at startup in memory, so
    after an `obs` upgrade the host can keep serving OLD tool code until it is
    restarted (this is what masked the v4.0.0 fix and motivated #53). Call this
    when a tool behaves as if a known fix is missing.

    Returns a JSON object with:
      server_version (str)       — version of the code THIS process loaded
                                   (frozen when the server started).
      installed_version (str)    — version currently on disk.
      started_at (str)           — ISO-8601 UTC timestamp of server start.
      restart_recommended (bool) — True when server_version != installed_version
                                   (the host is running stale code).
      hint (str)                 — guidance, present only when restart_recommended.

    If restart_recommended is True, reload/restart the MCP host (Cowork/Claude)
    so the freshly installed server loads.
    """
    try:
        installed = _read_disk_version()
        stale = installed != "unknown" and installed != _SERVER_VERSION
        info = {
            "server_version": _SERVER_VERSION,
            "installed_version": installed,
            "started_at": _SERVER_STARTED_AT,
            "restart_recommended": stale,
        }
        if stale:
            info["hint"] = (
                f"Running server is v{_SERVER_VERSION} but v{installed} is "
                "installed — restart the MCP host (Cowork/Claude) to load it."
            )
        import json
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Error reading server info: {e}"


@mcp.tool()
def get_trends(vault_id: str, days: int = 90) -> str:
    """
    Get weekly activity trends for a vault (notes created and modified per week).

    Args:
        vault_id: Vault name or ID.
        days:     Lookback window in days (default 90).

    Returns JSON with:
      total_notes, lookback_days, velocity_notes_per_week,
      insufficient_data (True when < 2 weeks of data),
      buckets (list of {week, notes_created, notes_modified}).

    Use to understand vault growth rate and activity patterns over time.
    Requires notes to have been scanned (run analyze_vault first if empty).
    """
    try:
        report = vault_manager.get_trends(vault_id, lookback_days=days)
        import json
        return json.dumps(report.to_dict(), indent=2)
    except Exception as e:
        return f"Error getting trends: {e}"


@mcp.tool()
def get_stale_notes(vault_id: str, limit: int = 20) -> str:
    """
    Find the most stale high-importance notes in a vault.

    Staleness score = pagerank × (days_since_modified / 365).
    Falls back to date-only ranking when graph metrics are unavailable.

    Args:
        vault_id: Vault name or ID.
        limit:    Max notes to return (default 20).

    Returns JSON with:
      has_graph_metrics (bool),
      notes (list of {note_id, title, path, days_since_modified,
                       pagerank, staleness_score}).

    High staleness_score = important note that hasn't been touched in a long time.
    Use to surface review candidates that matter most to the knowledge graph.
    """
    try:
        report = vault_manager.get_stale_notes(vault_id, limit=limit)
        import json
        return json.dumps(report.to_dict(), indent=2)
    except Exception as e:
        return f"Error getting stale notes: {e}"


@mcp.tool()
def get_daily_digest(vault_id: str, days: int = 90, limit: int = 5) -> str:
    """
    Combined daily-digest: bridge status + weekly trends + top stale notes.

    Combines get_bridge_status, get_trends, and get_stale_notes in one call.

    Args:
        vault_id: Vault name or ID.
        days:     Trend lookback window in days (default 90).
        limit:    Max stale notes to include (default 5).

    Returns JSON with bridge, trends, and stale sub-objects.
    Use for a morning-briefing view of vault health and activity.
    """
    try:
        report = vault_manager.get_daily_digest(vault_id, lookback_days=days, stale_limit=limit)
        import json
        return json.dumps(report.to_dict(), indent=2)
    except Exception as e:
        return f"Error getting daily digest: {e}"


@mcp.tool()
def diagnose(vault_id: str = "", layers: str = "") -> str:
    """
    Run self-diagnostic checks and return a structured health report.

    Runs five check layers: python (runtime & imports), database (SQLite integrity),
    vault (path, freshness, note/link counts), mcp (Claude Desktop config), and
    icloud (macOS iCloud write latency and offload detection).

    Args:
        vault_id: Optional vault name or ID (accepts name, full ID, or unambiguous
                  ID prefix) to scope vault-layer checks. Empty = all vaults.
        layers:   Comma-separated subset of layers to run. Empty = all layers.
                  Valid values: python, database, vault, mcp, icloud.

    Returns JSON array of check results. Each result has:
      id, layer, label, status (pass/warn/fail/skip/error), message, fix_hint.

    Exit interpretation: any 'fail' result means obs is misconfigured or data is stale.
    'warn' results are advisory. 'skip' results indicate inapplicable checks.
    """
    import json as _json
    try:
        from core.doctor import run_checks
        _vault_id = vault_id.strip() or None
        if _vault_id:
            # Resolve name/prefix → canonical id so run_checks (exact-match) sees it.
            vault, err = _resolve_vault(_vault_id)
            if err:
                return _json.dumps({"error": err})
            _vault_id = vault["id"]
        _layers_list = [l.strip() for l in layers.split(",") if l.strip()] if layers.strip() else None
        results = run_checks(vault_id=_vault_id, layers=_layers_list)
        return _json.dumps([r.to_dict() for r in results], indent=2)
    except Exception as e:
        return _json.dumps({"error": f"diagnose failed: {e}"})


# ---------------------------------------------------------------------------
# UNIFIED SEARCH — cross-source fan-out (Phase 2 of nexus-cli absorption)
# ---------------------------------------------------------------------------

@mcp.tool()
def unified_search(query: str, limit: int = 20) -> str:
    """
    Search across all configured knowledge sources simultaneously.

    Fans out to: Obsidian vault notes (always), Zotero library (if configured),
    PDF directories (if configured). Results are grouped by source and ranked
    by relevance within each group.

    Args:
        query: Search term or phrase.
        limit: Max total results across all sources (default 20).

    Each source receives a proportional share of the limit:
      - Vault: 50% (always active)
      - Zotero: 25% (requires research.zotero config)
      - PDF: 25% (requires research.pdf.directories config)

    When a source is not configured, its allocation is redistributed to the vault.
    Phase 4 will activate Zotero and PDF backends; until then those sections
    report "not configured" rather than failing.
    """
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    import config_loader as _cl

    cfg = _cl.load()
    sections: list[str] = []
    total_found = 0

    # --- Vault (always active) ---
    has_zotero = cfg and cfg.research and cfg.research.zotero
    has_pdf = cfg and cfg.research and cfg.research.pdf_directories
    active_backends = 1 + (1 if has_zotero else 0) + (1 if has_pdf else 0)
    vault_limit = max(limit - (limit // 4) * (active_backends - 1), limit // 2)

    try:
        vault_results = vault_manager.search_notes(query)[:vault_limit]
        if vault_results:
            total_found += len(vault_results)
            lines = [f"## Vault Notes ({len(vault_results)} results)\n"]
            for i, note in enumerate(vault_results, 1):
                lines += [
                    f"{i}. **{note['title']}**",
                    f"   Vault: {note.get('vault_name', 'Unknown')} | ID: `{note['id']}`",
                ]
                if note.get("snippet"):
                    lines.append(f"   _{note['snippet']}_")
                lines.append("")
            sections.append("\n".join(lines))
        else:
            sections.append(f"## Vault Notes\n\nNo notes matching '{query}'.\n")
    except Exception as e:
        sections.append(f"## Vault Notes\n\nSearch error: {e}\n")

    # --- Zotero (Phase 4 backend) ---
    zotero_limit = limit // 4
    if has_zotero:
        try:
            from research.zotero import ZoteroClient
            zc = ZoteroClient(
                db_path=cfg.research.zotero.database,
                storage_path=cfg.research.zotero.storage,
            )
            items = zc.search(query, limit=zotero_limit)
            if items:
                total_found += len(items)
                lines = [f"## Zotero Library ({len(items)} results)\n"]
                for i, item in enumerate(items, 1):
                    authors = ", ".join(item.authors[:2]) + (" et al." if len(item.authors) > 2 else "")
                    lines += [
                        f"{i}. **{item.title}**",
                        f"   {authors} ({item.date[:4] if item.date else 'n.d.'}) | Key: `{item.key}`",
                    ]
                    if item.abstract:
                        lines.append(f"   _{item.abstract[:120]}..._")
                    lines.append("")
                sections.append("\n".join(lines))
            else:
                sections.append(f"## Zotero Library\n\nNo items matching '{query}'.\n")
        except ImportError:
            sections.append("## Zotero Library\n\n_Backend not yet installed (Phase 4)._\n")
        except Exception as e:
            sections.append(f"## Zotero Library\n\nSearch error: {e}\n")
    else:
        sections.append("## Zotero Library\n\n_Not configured. Add `research.zotero` to `~/.config/obs/config.yaml`._\n")

    # --- PDF (Phase 4 backend) ---
    pdf_limit = limit // 4
    if has_pdf:
        try:
            from research.pdf import PDFExtractor
            extractor = PDFExtractor(directories=[Path(d) for d in cfg.research.pdf_directories])
            if extractor.available():
                results = extractor.search(query, limit=pdf_limit)
                if results:
                    total_found += len(results)
                    lines = [f"## PDF Documents ({len(results)} results)\n"]
                    for i, r in enumerate(results, 1):
                        lines += [
                            f"{i}. **{r.document.title or r.document.filename}**",
                            f"   {r.document.path}",
                            f"   _{r.context}_",
                            "",
                        ]
                    sections.append("\n".join(lines))
                else:
                    sections.append(f"## PDF Documents\n\nNo PDFs matching '{query}'.\n")
            else:
                sections.append("## PDF Documents\n\n_`pdftotext` not installed. Run: `brew install poppler`_\n")
        except ImportError:
            sections.append("## PDF Documents\n\n_Backend not yet installed (Phase 4)._\n")
        except Exception as e:
            sections.append(f"## PDF Documents\n\nSearch error: {e}\n")
    else:
        sections.append("## PDF Documents\n\n_Not configured. Add `research.pdf.directories` to `~/.config/obs/config.yaml`._\n")

    header = f"# Unified Search: '{query}' — {total_found} result(s) across {active_backends} source(s)\n"
    return header + "\n".join(sections)


# ---------------------------------------------------------------------------
# RESEARCH DOMAIN TOOLS — Phase 4 (Zotero, PDF, Teaching, Writing, Bib)
# ---------------------------------------------------------------------------

def _load_cfg():
    """Load obs config; returns None if no config found."""
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    import config_loader as _cl
    return _cl.load()

@mcp.tool()
def zotero_search(query: str, limit: int = 20, item_type: str = "", tag: str = "") -> str:
    """Search the Zotero library by title, author, or abstract.

    Args:
        query: Search query string
        limit: Maximum number of results (default 20)
        item_type: Filter by item type (e.g. 'journalArticle', 'book')
        tag: Filter by Zotero tag
    """
    cfg = _load_cfg()
    if not (cfg and cfg.research and cfg.research.zotero):
        return "_Zotero not configured. Add `research.zotero` to `~/.config/obs/config.yaml`._"
    try:
        from research.zotero import ZoteroClient
        client = ZoteroClient(cfg.research.zotero.database, cfg.research.zotero.storage)
        if not client.exists():
            return f"_Zotero database not found: {cfg.research.zotero.database}_"
        results = client.search(query, limit=limit, item_type=item_type or None, tag=tag or None)
        if not results:
            return f"No Zotero items matching '{query}'."
        lines = [f"# Zotero Search: '{query}' — {len(results)} result(s)\n"]
        for i, item in enumerate(results, 1):
            authors = ", ".join(item.authors[:3]) + (" et al." if len(item.authors) > 3 else "")
            year = item.date[:4] if item.date else "n.d."
            lines.append(f"{i}. **{item.title}** ({year})")
            if authors:
                lines.append(f"   {authors}")
            lines.append(f"   Key: `{item.key}` · Type: {item.item_type}")
            if item.tags:
                lines.append(f"   Tags: {', '.join(item.tags[:5])}")
            lines.append("")
        return "\n".join(lines)
    except ImportError:
        return "_Research backend not available._"
    except Exception as e:
        return f"Zotero search error: {e}"


@mcp.tool()
def zotero_get(key: str, format: str = "apa") -> str:
    """Get a Zotero item by key with full details.

    Args:
        key: Zotero item key (8-char alphanumeric)
        format: Output format: 'apa', 'bibtex', or 'full' (default: apa)
    """
    cfg = _load_cfg()
    if not (cfg and cfg.research and cfg.research.zotero):
        return "_Zotero not configured._"
    try:
        from research.zotero import ZoteroClient
        client = ZoteroClient(cfg.research.zotero.database, cfg.research.zotero.storage)
        item = client.get(key)
        if not item:
            return f"No Zotero item found with key `{key}`."
        if format == "bibtex":
            return f"```bibtex\n{item.citation_bibtex()}\n```"
        if format == "apa":
            return item.citation_apa()
        d = item.to_dict()
        lines = [f"# {d['title']}\n"]
        lines.append(f"**Key**: `{d['key']}` · **Type**: {d['item_type']} · **Year**: {d['date'][:4] if d['date'] else 'n.d.'}")
        if d["authors"]:
            lines.append(f"**Authors**: {', '.join(d['authors'])}")
        if d["doi"]:
            lines.append(f"**DOI**: {d['doi']}")
        if d["url"]:
            lines.append(f"**URL**: {d['url']}")
        if d["tags"]:
            lines.append(f"**Tags**: {', '.join(d['tags'])}")
        if d["abstract"]:
            lines.append(f"\n**Abstract**: {d['abstract']}")
        return "\n".join(lines)
    except ImportError:
        return "_Research backend not available._"
    except Exception as e:
        return f"Zotero get error: {e}"


@mcp.tool()
def zotero_cite(key: str, format: str = "apa") -> str:
    """Get a citation string for a Zotero item.

    Args:
        key: Zotero item key
        format: Citation format: 'apa' or 'bibtex' (default: apa)
    """
    cfg = _load_cfg()
    if not (cfg and cfg.research and cfg.research.zotero):
        return "_Zotero not configured._"
    try:
        from research.zotero import ZoteroClient
        client = ZoteroClient(cfg.research.zotero.database, cfg.research.zotero.storage)
        item = client.get(key)
        if not item:
            return f"No Zotero item found with key `{key}`."
        if format == "bibtex":
            return item.citation_bibtex()
        return item.citation_apa()
    except ImportError:
        return "_Research backend not available._"
    except Exception as e:
        return f"Zotero cite error: {e}"


@mcp.tool()
def zotero_recent(limit: int = 10) -> str:
    """List recently modified Zotero items.

    Args:
        limit: Number of items to return (default 10)
    """
    cfg = _load_cfg()
    if not (cfg and cfg.research and cfg.research.zotero):
        return "_Zotero not configured. Add `research.zotero` to `~/.config/obs/config.yaml`._"
    try:
        from research.zotero import ZoteroClient
        client = ZoteroClient(cfg.research.zotero.database, cfg.research.zotero.storage)
        if not client.exists():
            return f"_Zotero database not found: {cfg.research.zotero.database}_"
        items = client.recent(limit=limit)
        if not items:
            return "No items in Zotero library."
        lines = [f"# Recent Zotero Items ({len(items)})\n"]
        for i, item in enumerate(items, 1):
            year = item.date[:4] if item.date else "n.d."
            authors = item.authors[0].split()[-1] if item.authors else "Unknown"
            lines.append(f"{i}. **{item.title}** — {authors}, {year} · `{item.key}`")
        return "\n".join(lines)
    except ImportError:
        return "_Research backend not available._"
    except Exception as e:
        return f"Zotero recent error: {e}"


@mcp.tool()
def pdf_search(query: str, limit: int = 10) -> str:
    """Search PDF documents in configured directories.

    Args:
        query: Search query (matches filename and content)
        limit: Maximum number of results (default 10)
    """
    cfg = _load_cfg()
    if not (cfg and cfg.research and cfg.research.pdf_directories):
        return "_PDF search not configured. Add `research.pdf.directories` to `~/.config/obs/config.yaml`._"
    try:
        from research.pdf import PDFExtractor
        extractor = PDFExtractor(cfg.research.pdf_directories)
        if not extractor.available():
            return "_`pdftotext` not installed. Run: `brew install poppler`_"
        results = extractor.search(query, limit=limit)
        if not results:
            return f"No PDFs matching '{query}'."
        lines = [f"# PDF Search: '{query}' — {len(results)} result(s)\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **{r.filename}**")
            lines.append(f"   `{r.path}`")
            if r.context:
                lines.append(f"   _{r.context[:200]}_")
            lines.append("")
        return "\n".join(lines)
    except ImportError:
        return "_Research backend not available._"
    except Exception as e:
        return f"PDF search error: {e}"


@mcp.tool()
def course_list() -> str:
    """List all teaching courses with status and progress."""
    cfg = _load_cfg()
    if not (cfg and cfg.research and cfg.research.teaching):
        return "_Teaching not configured. Add `research.teaching.courses_dir` to `~/.config/obs/config.yaml`._"
    try:
        from research.courses import CourseManager
        mgr = CourseManager(
            cfg.research.teaching.courses_dir,
            cfg.research.teaching.materials_dir,
        )
        if not mgr.exists():
            return f"_Courses directory not found: {cfg.research.teaching.courses_dir}_"
        courses = mgr.list_courses()
        if not courses:
            return "No courses found."
        lines = ["# Teaching Courses\n"]
        lines.append(f"{'Course':<30} {'Status':<12} {'Progress':>8} {'Week':>5} {'Lectures':>8}")
        lines.append("-" * 68)
        for c in courses:
            week_str = str(c.week) if c.week is not None else "-"
            lines.append(
                f"{c.name:<30} {c.status:<12} {c.progress:>7}% {week_str:>5} {c.lecture_count:>8}"
            )
        return "\n".join(lines)
    except ImportError:
        return "_Research backend not available._"
    except Exception as e:
        return f"Course list error: {e}"


@mcp.tool()
def course_show(name: str) -> str:
    """Show details for a specific course.

    Args:
        name: Course directory name (exact or partial match)
    """
    cfg = _load_cfg()
    if not (cfg and cfg.research and cfg.research.teaching):
        return "_Teaching not configured._"
    try:
        from research.courses import CourseManager
        mgr = CourseManager(cfg.research.teaching.courses_dir, cfg.research.teaching.materials_dir)
        course = mgr.get_course(name)
        if not course:
            return f"Course '{name}' not found."
        d = course.to_dict()
        lines = [f"# {d['title']}\n"]
        lines.append(f"**Status**: {d['status']} · **Progress**: {d['progress']}%")
        if d["week"] is not None:
            lines.append(f"**Current Week**: {d['week']}")
        if d["next_action"]:
            lines.append(f"**Next**: {d['next_action']}")
        lines.append(f"**Lectures**: {d['lecture_count']} · **Assignments**: {d['assignment_count']}")
        if d["formats"]:
            lines.append(f"**Formats**: {', '.join(d['formats'])}")
        lines.append(f"\n**Path**: `{d['path']}`")
        return "\n".join(lines)
    except ImportError:
        return "_Research backend not available._"
    except Exception as e:
        return f"Course show error: {e}"


@mcp.tool()
def course_lectures(name: str) -> str:
    """List lectures for a specific course.

    Args:
        name: Course directory name
    """
    cfg = _load_cfg()
    if not (cfg and cfg.research and cfg.research.teaching):
        return "_Teaching not configured._"
    try:
        from research.courses import CourseManager
        mgr = CourseManager(cfg.research.teaching.courses_dir, cfg.research.teaching.materials_dir)
        lectures = mgr.list_lectures(name)
        if not lectures:
            return f"No lectures found for course '{name}'."
        lines = [f"# Lectures: {name} ({len(lectures)} total)\n"]
        for lec in sorted(lectures, key=lambda x: (x.week or 0, x.name)):
            week_str = f"Week {lec.week}" if lec.week is not None else "      "
            lines.append(f"- {week_str}: **{lec.title}** (`{lec.name}.qmd`)")
        return "\n".join(lines)
    except ImportError:
        return "_Research backend not available._"
    except Exception as e:
        return f"Course lectures error: {e}"


@mcp.tool()
def manuscript_list(include_archived: bool = False) -> str:
    """List research manuscripts with status and progress.

    Args:
        include_archived: Include archived/completed manuscripts (default False)
    """
    cfg = _load_cfg()
    if not (cfg and cfg.research and cfg.research.writing):
        return "_Writing not configured. Add `research.writing.manuscripts_dir` to `~/.config/obs/config.yaml`._"
    try:
        from research.manuscript import ManuscriptManager
        mgr = ManuscriptManager(
            cfg.research.writing.manuscripts_dir,
            cfg.research.writing.templates_dir,
        )
        if not mgr.exists():
            return f"_Manuscripts directory not found: {cfg.research.writing.manuscripts_dir}_"
        manuscripts = mgr.list_manuscripts(include_archived=include_archived)
        if not manuscripts:
            return "No manuscripts found."
        lines = ["# Research Manuscripts\n"]
        lines.append(f"{'Manuscript':<35} {'Status':<12} {'Progress':>8} {'Words':>7}")
        lines.append("-" * 65)
        for m in manuscripts:
            title_short = m.title[:33] + ".." if len(m.title) > 35 else m.title
            lines.append(
                f"{title_short:<35} {m.status:<12} {m.progress:>7}% {m.word_count:>7,}"
            )
        return "\n".join(lines)
    except ImportError:
        return "_Research backend not available._"
    except Exception as e:
        return f"Manuscript list error: {e}"


@mcp.tool()
def manuscript_show(name: str) -> str:
    """Show details for a specific manuscript.

    Args:
        name: Manuscript directory name (exact or partial match)
    """
    cfg = _load_cfg()
    if not (cfg and cfg.research and cfg.research.writing):
        return "_Writing not configured._"
    try:
        from research.manuscript import ManuscriptManager
        mgr = ManuscriptManager(cfg.research.writing.manuscripts_dir, cfg.research.writing.templates_dir)
        manuscript = mgr.get_manuscript(name)
        if not manuscript:
            return f"Manuscript '{name}' not found."
        d = manuscript.to_dict()
        lines = [f"# {d['title']}\n"]
        lines.append(f"**Status**: {d['status']} · **Progress**: {d['progress']}%")
        if d["target"]:
            lines.append(f"**Target**: {d['target']}")
        if d["next_action"]:
            lines.append(f"**Next**: {d['next_action']}")
        if d["authors"]:
            lines.append(f"**Authors**: {', '.join(d['authors'])}")
        lines.append(f"**Format**: {d['format_type']} · **Words**: {d['word_count']:,}")
        if d["main_file"]:
            lines.append(f"**Main file**: `{d['main_file']}`")
        if d["last_modified"]:
            lines.append(f"**Modified**: {d['last_modified'][:10]}")
        lines.append(f"\n**Path**: `{d['path']}`")
        return "\n".join(lines)
    except ImportError:
        return "_Research backend not available._"
    except Exception as e:
        return f"Manuscript show error: {e}"


@mcp.tool()
def manuscript_stats() -> str:
    """Get aggregate statistics across all manuscripts."""
    cfg = _load_cfg()
    if not (cfg and cfg.research and cfg.research.writing):
        return "_Writing not configured. Add `research.writing.manuscripts_dir` to `~/.config/obs/config.yaml`._"
    try:
        from research.manuscript import ManuscriptManager
        mgr = ManuscriptManager(cfg.research.writing.manuscripts_dir, cfg.research.writing.templates_dir)
        if not mgr.exists():
            return f"_Manuscripts directory not found: {cfg.research.writing.manuscripts_dir}_"
        stats = mgr.get_statistics()
        lines = ["# Manuscript Statistics\n"]
        lines.append(f"**Total manuscripts**: {stats['total']}")
        lines.append(f"**Total words**: {stats['total_words']:,}")
        if stats["by_status"]:
            lines.append("\n**By status**:")
            for status, count in sorted(stats["by_status"].items(), key=lambda x: -x[1]):
                lines.append(f"  - {status}: {count}")
        if stats["by_format"]:
            lines.append("\n**By format**:")
            for fmt, count in sorted(stats["by_format"].items(), key=lambda x: -x[1]):
                lines.append(f"  - {fmt}: {count}")
        return "\n".join(lines)
    except ImportError:
        return "_Research backend not available._"
    except Exception as e:
        return f"Manuscript stats error: {e}"


@mcp.tool()
def bib_check(manuscript_name: str) -> str:
    """Check bibliography consistency for a manuscript (missing/unused keys).

    Args:
        manuscript_name: Manuscript directory name (exact or partial match)
    """
    cfg = _load_cfg()
    if not (cfg and cfg.research and cfg.research.writing):
        return "_Writing not configured. Add `research.writing.manuscripts_dir` to `~/.config/obs/config.yaml`._"
    try:
        from research.bibliography import BibliographyManager
        from research.manuscript import ManuscriptManager
        mgr = ManuscriptManager(cfg.research.writing.manuscripts_dir, cfg.research.writing.templates_dir)
        manuscript = mgr.get_manuscript(manuscript_name)
        if not manuscript:
            return f"Manuscript '{manuscript_name}' not found."
        zotero_db = cfg.research.zotero.database if (cfg.research and cfg.research.zotero) else None
        bib_mgr = BibliographyManager(zotero_db)
        from pathlib import Path
        result = bib_mgr.check_citations(Path(manuscript.path))
        lines = [f"# Bibliography Check: {manuscript.name}\n"]
        lines.append(f"**Cited keys**: {result['cited_count']} · **In .bib files**: {result['bibliography_count']}")
        if result["all_good"]:
            lines.append("\n✅ All cited keys found in bibliography.")
        else:
            lines.append(f"\n❌ **{len(result['missing'])} missing** (cited but not in .bib):")
            for key in result["missing"][:20]:
                lines.append(f"  - `{key}`")
        if result["unused"]:
            lines.append(f"\n⚠️  **{len(result['unused'])} unused** (in .bib but not cited):")
            for key in result["unused"][:20]:
                lines.append(f"  - `{key}`")
        return "\n".join(lines)
    except ImportError:
        return "_Research backend not available._"
    except Exception as e:
        return f"Bibliography check error: {e}"


# ---------------------------------------------------------------------------
# RESOURCES — read-only snapshots for Claude context
# ---------------------------------------------------------------------------

@mcp.resource("vault://{vault_id}/stats")
def vault_stats_resource(vault_id: str) -> str:
    """Vault statistics as a resource."""
    return get_vault_stats(vault_id)


@mcp.resource("vault://{vault_id}/health")
def vault_health_resource(vault_id: str) -> str:
    """Vault health scores as a resource."""
    return get_vault_health(vault_id)


@mcp.resource("obsidian://overview")
def overview_resource() -> str:
    """Overall obs database overview."""
    return get_vault_stats()


@mcp.resource("note://{note_id}")
def note_resource(note_id: str) -> str:
    """Note content as a resource."""
    return read_note(note_id)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
