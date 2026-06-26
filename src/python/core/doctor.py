"""
obs doctor — self-diagnostic checks across five layers.

Each _check_* function returns list[DoctorResult]. Checks are independent;
a failure in one layer does not skip later layers (though vault checks short-
circuit gracefully when the DB is unavailable).
"""
from __future__ import annotations

import ast
import json
import os
import platform
import sqlite3
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Literal, Optional

Status = Literal["pass", "warn", "fail", "skip", "error", "info"]

_CLAUDE_DESKTOP_CONFIG_PATHS = [
    Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
    Path.home() / ".config" / "claude" / "claude_desktop_config.json",
]

_CORE_IMPORTS = ["rich", "networkx", "mcp"]   # sqlite3 is stdlib, checked separately


@dataclass
class DoctorResult:
    id: str
    layer: str
    label: str
    status: Status
    message: str
    fix_hint: str = ""

    def to_dict(self):
        return asdict(self)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_checks(vault_id: Optional[str] = None, layers: Optional[list[str]] = None) -> list[DoctorResult]:
    """Run all (or a subset of) checks and return results in layer order."""
    all_layers = {
        "python": _check_python,
        "database": _check_database,
        "vault": lambda: _check_vaults(vault_id),
        "sync": lambda: _check_sync(vault_id),
        "mcp": _check_mcp,
        "docs": _check_doc_counts,
        "icloud": _check_icloud,
    }
    selected = layers if layers else list(all_layers.keys())
    results: list[DoctorResult] = []
    db_ok = True
    for name in selected:
        fn = all_layers.get(name)
        if fn is None:
            continue
        if name in ("vault", "sync") and not db_ok:
            results.append(DoctorResult(
                id=f"{name}-skip", layer=name, label=f"{name.capitalize()} checks",
                status="skip", message="skipped: DB unavailable",
            ))
            continue
        layer_results = fn()
        results.extend(layer_results)
        if name == "database":
            db_ok = not any(r.status == "fail" for r in layer_results if r.id in ("db-exists", "db-query"))
    return results


# ---------------------------------------------------------------------------
# Layer 1 — Python runtime
# ---------------------------------------------------------------------------

def _check_python() -> list[DoctorResult]:
    results = []

    # py-version
    vi = sys.version_info
    version_str = f"Python {vi.major}.{vi.minor}.{vi.micro}"
    if vi >= (3, 10):
        results.append(DoctorResult("py-version", "python", "Python version", "pass", version_str))
    elif vi >= (3, 9):
        results.append(DoctorResult("py-version", "python", "Python version", "warn",
                                    f"{version_str} — 3.10+ recommended",
                                    "Upgrade: brew install python@3.12"))
    else:
        results.append(DoctorResult("py-version", "python", "Python version", "fail",
                                    f"{version_str} — 3.9+ required",
                                    "Upgrade: brew install python@3.12"))

    # py-resolver
    obs_python = os.environ.get("OBS_PYTHON", "")
    exe = sys.executable
    if obs_python and exe == obs_python:
        src = f"$OBS_PYTHON ({exe})"
        status: Status = "pass"
    elif ".local/share/obs/venv" in exe:
        src = f"user venv ({exe})"
        status = "pass"
    elif "libexec" in exe and "obs" in exe:
        src = f"Homebrew formula venv ({exe})"
        status = "pass"
    else:
        src = f"ambient ({exe})"
        # warn only if core imports are available, else fail is caught by py-imports
        status = "warn"
    results.append(DoctorResult("py-resolver", "python", "Interpreter source", status, src,
                                "" if status == "pass" else "Run: ./install.sh  or  brew reinstall obsidian-cli-ops"))

    # py-imports
    missing = []
    for mod in _CORE_IMPORTS:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    # sqlite3 is stdlib but confirm it
    try:
        import sqlite3 as _s3  # noqa: F401
    except ImportError:
        missing.append("sqlite3")

    if not missing:
        results.append(DoctorResult("py-imports", "python", "Core imports", "pass",
                                    f"All required: {', '.join(_CORE_IMPORTS + ['sqlite3'])}"))
    else:
        results.append(DoctorResult("py-imports", "python", "Core imports", "fail",
                                    f"Missing: {', '.join(missing)}",
                                    "Run: ./install.sh  or  brew reinstall obsidian-cli-ops"))
    return results


# ---------------------------------------------------------------------------
# Layer 2 — Database
# ---------------------------------------------------------------------------

def _check_database() -> list[DoctorResult]:
    results = []
    db_path = Path.home() / ".config" / "obs" / "vault_db.sqlite"

    # db-exists
    if not db_path.exists():
        results.append(DoctorResult("db-exists", "database", "DB file exists", "fail",
                                    f"Not found: {db_path}",
                                    "Run: obs db init"))
        # remaining checks can't run
        for cid, label in [("db-schema", "Schema version"), ("db-query", "Can query vaults"),
                            ("db-vaults", "Vault count")]:
            results.append(DoctorResult(cid, "database", label, "skip", "skipped: DB missing"))
        return results

    results.append(DoctorResult("db-exists", "database", "DB file exists", "pass", str(db_path)))

    # db-schema
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT MAX(version) AS v FROM schema_version").fetchone()
        version = row["v"] if row and row["v"] is not None else 0
        results.append(DoctorResult("db-schema", "database", "Schema version", "pass",
                                    f"schema v{version}"))
    except sqlite3.OperationalError as e:
        results.append(DoctorResult("db-schema", "database", "Schema version", "warn",
                                    f"schema_version table missing ({e})",
                                    "Run: obs db init"))
        conn = None
    except Exception as e:
        results.append(DoctorResult("db-schema", "database", "Schema version", "error",
                                    f"Unexpected error: {e}"))
        conn = None

    # db-query
    if conn is None:
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
        except Exception as e:
            results.append(DoctorResult("db-query", "database", "Can query vaults", "fail",
                                        f"Cannot open DB: {e}", "Run: obs db init"))
            results.append(DoctorResult("db-vaults", "database", "Vault count", "skip", "skipped: DB unavailable"))
            return results

    try:
        rows = conn.execute("SELECT COUNT(*) AS n FROM vaults").fetchone()
        count = rows["n"] if rows else 0
        results.append(DoctorResult("db-query", "database", "Can query vaults", "pass",
                                    "SELECT ok"))
    except sqlite3.OperationalError as e:
        results.append(DoctorResult("db-query", "database", "Can query vaults", "fail",
                                    f"Query failed: {e}", "Run: obs db init"))
        results.append(DoctorResult("db-vaults", "database", "Vault count", "skip", "skipped: query failed"))
        conn.close()
        return results

    # db-vaults
    if count == 0:
        results.append(DoctorResult("db-vaults", "database", "Vault count", "warn",
                                    "No vaults registered",
                                    "Run: obs discover <path>  to register a vault"))
    else:
        results.append(DoctorResult("db-vaults", "database", "Vault count", "pass",
                                    f"{count} vault{'s' if count != 1 else ''} registered"))
    conn.close()
    return results


# ---------------------------------------------------------------------------
# Layer 3 — Vault health (per registered vault)
# ---------------------------------------------------------------------------

def _check_vaults(vault_id: Optional[str] = None) -> list[DoctorResult]:
    from fs_utils import is_icloud_path, is_dataless

    db_path = Path.home() / ".config" / "obs" / "vault_db.sqlite"
    if not db_path.exists():
        return [DoctorResult("vault-skip", "vault", "Vault checks", "skip", "skipped: DB missing")]

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        if vault_id:
            rows = conn.execute("SELECT * FROM vaults WHERE id = ?", (vault_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM vaults ORDER BY name").fetchall()
    except Exception as e:
        return [DoctorResult("vault-skip", "vault", "Vault checks", "skip", f"skipped: {e}")]

    if not rows:
        return [DoctorResult("vault-skip", "vault", "Vault checks", "skip",
                             "No vaults registered" if not vault_id else f"Vault {vault_id!r} not found")]

    results = []
    for vault in rows:
        vid = vault["id"]
        name = vault["name"]
        path = Path(vault["path"])
        prefix = f"{name} ({vid[:8]})"

        # vault-path
        if not path.exists():
            results.append(DoctorResult(f"vault-path:{vid}", "vault", f"{prefix}: Path accessible",
                                        "fail", f"Path missing: {path}",
                                        f"Re-register: obs discover {path.parent}"))
            for cid in ("vault-dataless", "vault-stale", "vault-notes", "vault-links"):
                results.append(DoctorResult(f"{cid}:{vid}", "vault", f"{prefix}: {cid}", "skip",
                                            "skipped: path missing"))
            continue

        if is_icloud_path(path):
            results.append(DoctorResult(f"vault-path:{vid}", "vault", f"{prefix}: Path accessible",
                                        "warn", f"iCloud path — writes may be slow: {path}",
                                        "Finder → right-click vault → Download Now"))
        else:
            results.append(DoctorResult(f"vault-path:{vid}", "vault", f"{prefix}: Path accessible",
                                        "pass", str(path)))

        # vault-dataless
        if platform.system() == "Darwin":
            if is_dataless(path):
                results.append(DoctorResult(f"vault-dataless:{vid}", "vault",
                                            f"{prefix}: iCloud materialized", "fail",
                                            "Vault root is a dataless placeholder",
                                            f'Run: brctl download "{path}"'))
            else:
                dataless_count = sum(1 for f in path.rglob("*.md") if is_dataless(f))
                if dataless_count > 0:
                    results.append(DoctorResult(f"vault-dataless:{vid}", "vault",
                                                f"{prefix}: iCloud materialized", "warn",
                                                f"{dataless_count} note files are offloaded placeholders",
                                                f'Run: brctl download "{path}"'))
                else:
                    results.append(DoctorResult(f"vault-dataless:{vid}", "vault",
                                                f"{prefix}: iCloud materialized", "pass",
                                                "All files materialized"))
        else:
            results.append(DoctorResult(f"vault-dataless:{vid}", "vault",
                                        f"{prefix}: iCloud materialized", "skip",
                                        "iCloud checks not applicable on Linux"))

        # vault-stale  (schema column is `last_scanned`, not `last_scan`)
        last_scan = vault["last_scanned"]
        warn_days = int(os.environ.get("OBS_DOCTOR_WARN_DAYS", "7"))
        fail_days = int(os.environ.get("OBS_DOCTOR_FAIL_DAYS", "30"))
        if not last_scan:
            results.append(DoctorResult(f"vault-stale:{vid}", "vault", f"{prefix}: Last scanned",
                                        "fail", "Never scanned",
                                        f"Run: obs scan {vid}"))
        else:
            from datetime import datetime, timezone
            try:
                ts = datetime.fromisoformat(last_scan.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                if ts.tzinfo is None:
                    from datetime import timezone as tz
                    ts = ts.replace(tzinfo=tz.utc)
                days = (now - ts).days
                if days >= fail_days:
                    results.append(DoctorResult(f"vault-stale:{vid}", "vault", f"{prefix}: Last scanned",
                                                "fail", f"{days} days since last scan",
                                                f"Run: obs scan {vid}"))
                elif days >= warn_days:
                    results.append(DoctorResult(f"vault-stale:{vid}", "vault", f"{prefix}: Last scanned",
                                                "warn", f"{days} days since last scan",
                                                f"Run: obs scan {vid}"))
                else:
                    results.append(DoctorResult(f"vault-stale:{vid}", "vault", f"{prefix}: Last scanned",
                                                "pass", f"Last scanned {days} day{'s' if days != 1 else ''} ago"))
            except Exception:
                results.append(DoctorResult(f"vault-stale:{vid}", "vault", f"{prefix}: Last scanned",
                                            "warn", f"Cannot parse timestamp: {last_scan}"))

        # vault-notes
        try:
            row = conn.execute("SELECT COUNT(*) AS n FROM notes WHERE vault_id = ?", (vid,)).fetchone()
            note_count = row["n"] if row else 0
            if note_count == 0:
                results.append(DoctorResult(f"vault-notes:{vid}", "vault", f"{prefix}: Note count",
                                            "fail", "0 notes — vault never scanned or empty",
                                            f"Run: obs scan {vid}"))
            else:
                results.append(DoctorResult(f"vault-notes:{vid}", "vault", f"{prefix}: Note count",
                                            "pass", f"{note_count:,} notes indexed"))
        except sqlite3.OperationalError as e:
            results.append(DoctorResult(f"vault-notes:{vid}", "vault", f"{prefix}: Note count",
                                        "error", f"Query failed: {e}"))

        # vault-links
        try:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM links l JOIN notes n ON l.source_note_id = n.id WHERE n.vault_id = ?",
                (vid,)
            ).fetchone()
            link_count = row["n"] if row else 0
            if link_count == 0:
                results.append(DoctorResult(f"vault-links:{vid}", "vault", f"{prefix}: Link graph",
                                            "warn", "0 links — graph not built",
                                            f"Run: obs analyze {vid}"))
            else:
                results.append(DoctorResult(f"vault-links:{vid}", "vault", f"{prefix}: Link graph",
                                            "pass", f"{link_count:,} links in graph"))
        except sqlite3.OperationalError as e:
            results.append(DoctorResult(f"vault-links:{vid}", "vault", f"{prefix}: Link graph",
                                        "error", f"Query failed: {e}"))

    conn.close()
    return results


# ---------------------------------------------------------------------------
# Layer — sync (content-based vault↔DB drift, per registered vault)
# ---------------------------------------------------------------------------

def _disk_md_paths(vault_path: Path) -> set[str]:
    """Relative *.md paths on disk, mirroring the scanner's dotfile filter
    (vault_scanner.py:232 — skip any path with a dot-prefixed part)."""
    return {
        str(p.relative_to(vault_path))
        for p in vault_path.rglob("*.md")
        if not any(part.startswith(".") for part in p.parts)
    }


def _check_sync(vault_id: Optional[str] = None) -> list[DoctorResult]:
    """Per-vault content-based sync drift between the DB index and disk.

    sync-ghosts (warn) : DB rows whose path no longer exists on disk (S1/S2).
    sync-missing (warn) : *.md on disk absent from the DB (S4 / never-scanned).
    sync-errors (warn/fail) : last scan_history row recorded failures (S4).
    sync-drift (info)  : one-line summary disk=N db=M (X ghost, Y missing).

    Each is a cheap rglob + SELECT path + set diff; deterministic, no AI.
    """
    db_path = Path.home() / ".config" / "obs" / "vault_db.sqlite"
    if not db_path.exists():
        return [DoctorResult("sync-skip", "sync", "Sync checks", "skip", "skipped: DB missing")]

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        if vault_id:
            rows = conn.execute("SELECT * FROM vaults WHERE id = ?", (vault_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM vaults ORDER BY name").fetchall()
    except sqlite3.OperationalError as e:
        return [DoctorResult("sync-skip", "sync", "Sync checks", "skip", f"skipped: {e}")]

    if not rows:
        conn.close()
        return [DoctorResult("sync-skip", "sync", "Sync checks", "skip",
                             "No vaults registered" if not vault_id else f"Vault {vault_id!r} not found")]

    results: list[DoctorResult] = []
    for vault in rows:
        vid = vault["id"]
        name = vault["name"]
        path = Path(vault["path"])
        prefix = f"{name} ({vid[:8]})"

        # Vault path gone → can't read disk; ghosts/missing are meaningless.
        if not path.exists():
            for cid, label in (("sync-ghosts", "Ghost rows"), ("sync-missing", "Missing on disk"),
                               ("sync-errors", "Last scan errors"), ("sync-drift", "Drift summary")):
                results.append(DoctorResult(f"{cid}:{vid}", "sync", f"{prefix}: {label}",
                                            "skip", "skipped: vault path missing"))
            continue

        try:
            disk_paths = _disk_md_paths(path)
        except OSError as e:
            for cid, label in (("sync-ghosts", "Ghost rows"), ("sync-missing", "Missing on disk"),
                               ("sync-errors", "Last scan errors"), ("sync-drift", "Drift summary")):
                results.append(DoctorResult(f"{cid}:{vid}", "sync", f"{prefix}: {label}",
                                            "skip", f"skipped: cannot read disk ({e})"))
            continue

        try:
            db_rows = conn.execute("SELECT path FROM notes WHERE vault_id = ?", (vid,)).fetchall()
            db_paths = {r["path"] for r in db_rows}
        except sqlite3.OperationalError as e:
            results.append(DoctorResult(f"sync-ghosts:{vid}", "sync", f"{prefix}: Ghost rows",
                                        "error", f"Query failed: {e}"))
            continue

        ghosts = db_paths - disk_paths
        missing = disk_paths - db_paths

        # sync-ghosts
        if ghosts:
            results.append(DoctorResult(f"sync-ghosts:{vid}", "sync", f"{prefix}: Ghost rows",
                                        "warn", f"{len(ghosts)} DB row(s) point to files gone from disk",
                                        f"Run: obs scan {vid} --prune"))
        else:
            results.append(DoctorResult(f"sync-ghosts:{vid}", "sync", f"{prefix}: Ghost rows",
                                        "pass", "no ghost rows"))

        # sync-missing
        if missing:
            results.append(DoctorResult(f"sync-missing:{vid}", "sync", f"{prefix}: Missing on disk",
                                        "warn", f"{len(missing)} disk file(s) absent from the index",
                                        f"Run: obs scan {vid}  (re-scan; check logs for errors)"))
        else:
            results.append(DoctorResult(f"sync-missing:{vid}", "sync", f"{prefix}: Missing on disk",
                                        "pass", "all disk files indexed"))

        # sync-errors — verdict from the latest scan_history row
        results.append(_sync_errors_result(conn, vid, prefix))

        # sync-drift — info summary line
        results.append(DoctorResult(
            f"sync-drift:{vid}", "sync", f"{prefix}: Drift summary", "info",
            f"disk={len(disk_paths)} db={len(db_paths)} "
            f"({len(ghosts)} ghost, {len(missing)} missing)"))

    conn.close()
    return results


def _sync_errors_result(conn: sqlite3.Connection, vid: str, prefix: str) -> DoctorResult:
    """warn/fail from the most-recent scan_history row (post-S4):
    status=='failed' → fail; completed but notes_failed>0 → warn; else pass;
    no scan history → skip."""
    label = f"{prefix}: Last scan errors"
    try:
        row = conn.execute(
            "SELECT status, notes_failed FROM scan_history "
            "WHERE vault_id = ? ORDER BY started_at DESC, id DESC LIMIT 1",
            (vid,),
        ).fetchone()
    except sqlite3.OperationalError as e:
        return DoctorResult(f"sync-errors:{vid}", "sync", label, "error", f"Query failed: {e}")

    if row is None:
        return DoctorResult(f"sync-errors:{vid}", "sync", label, "skip", "no scan history")

    status = row["status"]
    failed = row["notes_failed"] or 0
    if status == "failed":
        return DoctorResult(f"sync-errors:{vid}", "sync", label, "fail",
                            "last scan aborted (status=failed)",
                            f"Run: obs scan {vid} --verbose  to see the error")
    if failed > 0:
        return DoctorResult(f"sync-errors:{vid}", "sync", label, "warn",
                            f"last scan recorded {failed} per-note error(s)",
                            "inspect failing paths in the scan log")
    return DoctorResult(f"sync-errors:{vid}", "sync", label, "pass", "last scan had no errors")


# ---------------------------------------------------------------------------
# Layer 4 — MCP server
# ---------------------------------------------------------------------------

def _check_mcp() -> list[DoctorResult]:
    results = []

    # --- Config-independent checks: source code + package availability ---
    # These inspect the installed source / environment, NOT the Claude Desktop
    # config, so they must run even when that config is absent (CI, servers, a
    # fresh checkout). Previously they sat after an early `return` in the
    # config-missing branch and were silently skipped there — which let the
    # mcp-tool-resolvers / mcp-async-run static guards (#62) go unrun on any
    # host without Claude Desktop configured.

    # mcp-server (check mcp_server.py exists alongside this file)
    candidate = Path(__file__).parent.parent / "mcp_server.py"
    if candidate.exists():
        results.append(DoctorResult("mcp-server", "mcp", "mcp_server.py importable", "pass",
                                    str(candidate)))
    else:
        results.append(DoctorResult("mcp-server", "mcp", "mcp_server.py importable", "fail",
                                    f"mcp_server.py not found at {candidate}",
                                    "Reinstall: brew reinstall obsidian-cli-ops"))

    # mcp-tool-resolvers — static guard against the exact-ID-only resolver bug
    results.append(_check_mcp_tool_resolvers(candidate))

    # mcp-async-run — static guard against asyncio.run() in a sync @mcp.tool (#62)
    results.append(_check_mcp_async_run(candidate))

    # mcp-fastmcp
    try:
        import mcp  # noqa: F401
        results.append(DoctorResult("mcp-fastmcp", "mcp", "FastMCP available", "pass",
                                    f"mcp package importable"))
    except ImportError:
        results.append(DoctorResult("mcp-fastmcp", "mcp", "FastMCP available", "fail",
                                    "mcp package not importable",
                                    "Run: ./install.sh  or  brew reinstall obsidian-cli-ops"))

    # --- Claude Desktop config checks ---
    config_path = None
    for p in _CLAUDE_DESKTOP_CONFIG_PATHS:
        if p.exists():
            config_path = p
            break

    if config_path is None:
        results.append(DoctorResult("mcp-config", "mcp", "Claude Desktop config", "fail",
                                    "claude_desktop_config.json not found",
                                    f"Expected at: {_CLAUDE_DESKTOP_CONFIG_PATHS[0]}"))
        results.append(DoctorResult("mcp-entry", "mcp", "obsidian-ops entry", "skip",
                                    "skipped: config missing"))
        return results

    results.append(DoctorResult("mcp-config", "mcp", "Claude Desktop config", "pass", str(config_path)))

    # mcp-entry
    try:
        with open(config_path) as f:
            config = json.load(f)
        servers = config.get("mcpServers", {})
        entry = servers.get("obsidian-ops")
        if entry is None:
            results.append(DoctorResult("mcp-entry", "mcp", "obsidian-ops entry", "fail",
                                        "obsidian-ops not found in mcpServers",
                                        'Add "obsidian-ops" entry to claude_desktop_config.json'))
        else:
            cmd = entry.get("command", "")
            # Resolve the script path from the command args if present
            args = entry.get("args", [])
            server_path = None
            for a in args:
                if "mcp_server.py" in a:
                    server_path = Path(a)
                    break
            if server_path and not server_path.exists():
                results.append(DoctorResult("mcp-entry", "mcp", "obsidian-ops entry", "warn",
                                            f"Entry exists but mcp_server.py path is wrong: {server_path}",
                                            f"Update path in {config_path}"))
            else:
                results.append(DoctorResult("mcp-entry", "mcp", "obsidian-ops entry", "pass",
                                            f"Entry present (command: {cmd})"))
    except (json.JSONDecodeError, OSError) as e:
        results.append(DoctorResult("mcp-entry", "mcp", "obsidian-ops entry", "error",
                                    f"Cannot parse config: {e}"))

    return results


def _find_bad_vault_resolvers(source: str) -> list[str]:
    """Return "<tool>(<arg>)" for each @mcp.tool function that calls
    db.get_vault(<its own vault param>) — the exact-ID-only anti-pattern that
    silently fails when a caller passes a vault NAME or prefix.

    Correct tools route through db.get_vault_by_name_or_id() (3-tier lookup),
    typically via the _resolve_vault() helper. Lookups keyed off a note's
    canonical id (db.get_vault(note["vault_id"])) use a Subscript, not a bare
    parameter Name, so they are correctly ignored.
    """
    tree = ast.parse(source)
    offenders: list[str] = []

    def is_mcp_tool(fn: ast.FunctionDef) -> bool:
        for dec in fn.decorator_list:
            # matches both @mcp.tool and @mcp.tool(...)
            target = dec.func if isinstance(dec, ast.Call) else dec
            if isinstance(target, ast.Attribute) and target.attr == "tool" \
                    and isinstance(target.value, ast.Name) and target.value.id == "mcp":
                return True
        return False

    for fn in ast.walk(tree):
        if not isinstance(fn, ast.FunctionDef) or not is_mcp_tool(fn):
            continue
        params = {a.arg for a in fn.args.args} | {a.arg for a in fn.args.kwonlyargs}
        for node in ast.walk(fn):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            if isinstance(f, ast.Attribute) and f.attr == "get_vault" \
                    and isinstance(f.value, ast.Name) and f.value.id == "db" \
                    and node.args and isinstance(node.args[0], ast.Name) \
                    and node.args[0].id in params:
                offenders.append(f"{fn.name}({node.args[0].id})")
    return offenders


def _check_mcp_tool_resolvers(server_path: Path) -> DoctorResult:
    """Flag MCP tools that resolve vaults with the exact-ID-only db.get_vault()."""
    label = "MCP tool vault resolvers"
    if not server_path.exists():
        return DoctorResult("mcp-tool-resolvers", "mcp", label, "skip",
                            "skipped: mcp_server.py not found")
    try:
        offenders = _find_bad_vault_resolvers(server_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as e:
        return DoctorResult("mcp-tool-resolvers", "mcp", label, "error",
                            f"Cannot analyze mcp_server.py: {e}")
    if offenders:
        return DoctorResult(
            "mcp-tool-resolvers", "mcp", label, "fail",
            f"{len(offenders)} tool(s) use exact-ID-only db.get_vault(): "
            + ", ".join(offenders),
            "Resolve via _resolve_vault()/db.get_vault_by_name_or_id() so vault "
            "names and ID prefixes work, not just exact IDs.",
        )
    return DoctorResult("mcp-tool-resolvers", "mcp", label, "pass",
                        "all vault-taking tools use name/ID/prefix resolution")


def _find_async_run_offenders(source: str) -> list[str]:
    """Return "<tool>()" for each SYNC @mcp.tool function whose body calls
    asyncio.run(...) — the #62 anti-pattern. FastMCP dispatches tool handlers
    inside an already-running event loop, so asyncio.run() raises
    `RuntimeError: asyncio.run() cannot be called from a running event loop`.

    Only sync `def` handlers are flagged: an `async def` that awaits its
    coroutine is the correct fix, and `isinstance(node, ast.FunctionDef)` is
    False for ast.AsyncFunctionDef, so async handlers are skipped automatically.
    """
    tree = ast.parse(source)
    offenders: list[str] = []

    def is_mcp_tool(fn: ast.FunctionDef) -> bool:
        for dec in fn.decorator_list:
            # matches both @mcp.tool and @mcp.tool(...)
            target = dec.func if isinstance(dec, ast.Call) else dec
            if isinstance(target, ast.Attribute) and target.attr == "tool" \
                    and isinstance(target.value, ast.Name) and target.value.id == "mcp":
                return True
        return False

    for fn in ast.walk(tree):
        # ast.FunctionDef excludes ast.AsyncFunctionDef → only sync handlers
        if not isinstance(fn, ast.FunctionDef) or not is_mcp_tool(fn):
            continue
        for node in ast.walk(fn):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            if isinstance(f, ast.Attribute) and f.attr == "run" \
                    and isinstance(f.value, ast.Name) and f.value.id == "asyncio":
                offenders.append(f"{fn.name}()")
                break
    return offenders


def _check_mcp_async_run(server_path: Path) -> DoctorResult:
    """Flag sync MCP tools that call asyncio.run() (crashes inside FastMCP's
    running event loop — see #62)."""
    label = "MCP tools free of asyncio.run() in sync handlers"
    if not server_path.exists():
        return DoctorResult("mcp-async-run", "mcp", label, "skip",
                            "skipped: mcp_server.py not found")
    try:
        offenders = _find_async_run_offenders(server_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as e:
        return DoctorResult("mcp-async-run", "mcp", label, "error",
                            f"Cannot analyze mcp_server.py: {e}")
    if offenders:
        return DoctorResult(
            "mcp-async-run", "mcp", label, "fail",
            f"{len(offenders)} sync @mcp.tool call asyncio.run(): "
            + ", ".join(offenders),
            "Make the handler `async def` and `await` the coroutine. FastMCP "
            "dispatches tools inside a running event loop, where asyncio.run() "
            "raises RuntimeError (#62).",
        )
    return DoctorResult("mcp-async-run", "mcp", label, "pass",
                        "no sync @mcp.tool handler calls asyncio.run()")


# ---------------------------------------------------------------------------
# Layer 5 — documentation count consistency
# ---------------------------------------------------------------------------

def _check_doc_counts() -> list[DoctorResult]:
    """Flag docs whose stated MCP-tool / resource / provider counts disagree
    with the source of truth in mcp_server.py. Catches the v4.0.0 "25 vs 38"
    drift class. Shares logic with scripts/validate-counts.sh + the CI test."""
    try:
        from core.doc_counts import source_counts, find_mismatches
    except ImportError:
        return [DoctorResult("doc-counts", "docs", "Doc count consistency", "skip",
                             "skipped: core.doc_counts unavailable")]
    counts = source_counts()
    mismatches = find_mismatches(counts)
    summary = (f"commands={counts['obs_commands']} tools={counts['mcp_tools']} "
               f"resources={counts['mcp_resources']} providers={counts['ai_providers']}")
    if not mismatches:
        return [DoctorResult("doc-counts", "docs", "Doc count consistency", "pass",
                             f"docs aligned with source ({summary})")]
    files = sorted({m.file for m in mismatches})
    head = "; ".join(f"{m.file}:{m.line} says {m.stated} (want {m.expected})"
                     for m in mismatches[:3])
    more = f" (+{len(mismatches) - 3} more)" if len(mismatches) > 3 else ""
    return [DoctorResult("doc-counts", "docs", "Doc count consistency", "warn",
                         f"{len(mismatches)} stale count(s) in {len(files)} file(s): {head}{more}",
                         "scripts/validate-counts.sh --fix")]


# ---------------------------------------------------------------------------
# Layer 6 — iCloud write path
# ---------------------------------------------------------------------------

def _check_icloud() -> list[DoctorResult]:
    from fs_utils import is_icloud_path, is_dataless, fs_op, FS_PROBE_TIMEOUT

    if platform.system() != "Darwin":
        return [DoctorResult("icloud-skip", "icloud", "iCloud checks", "skip",
                             "iCloud checks not applicable on Linux")]

    results = []

    # Find iCloud vaults
    db_path = Path.home() / ".config" / "obs" / "vault_db.sqlite"
    icloud_vaults: list[Path] = []
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT path FROM vaults").fetchall()
            icloud_vaults = [Path(r["path"]) for r in rows if is_icloud_path(Path(r["path"]))]
            conn.close()
        except Exception:
            pass

    # icloud-detect
    if not icloud_vaults:
        results.append(DoctorResult("icloud-detect", "icloud", "Vault on iCloud Drive", "pass",
                                    "No iCloud-backed vaults detected"))
        return results

    results.append(DoctorResult("icloud-detect", "icloud", "Vault on iCloud Drive", "warn",
                                f"{len(icloud_vaults)} iCloud vault(s) — writes may be slow",
                                "Monitor 'bird' / 'fileproviderd' in Activity Monitor during operations"))

    # icloud-write — test write latency using the first iCloud vault
    probe_vault = icloud_vaults[0]
    probe_file = probe_vault / ".obs-doctor-probe"
    start = time.monotonic()
    timed_out = False
    write_error: Optional[str] = None
    try:
        def _write():
            probe_file.write_bytes(b"x")
            probe_file.unlink(missing_ok=True)

        fs_op(_write, timeout=FS_PROBE_TIMEOUT)
    except TimeoutError:
        timed_out = True
    except Exception as e:
        write_error = str(e)
    latency = time.monotonic() - start

    if timed_out:
        results.append(DoctorResult("icloud-write", "icloud", "Write latency", "fail",
                                    f"Write timed out after {FS_PROBE_TIMEOUT}s (iCloud placeholder not materialized)",
                                    f'Run: brctl download "{probe_vault}"  or Finder → Download Now'))
    elif write_error:
        results.append(DoctorResult("icloud-write", "icloud", "Write latency", "error",
                                    f"Write failed: {write_error}"))
    elif latency > 5.0:
        results.append(DoctorResult("icloud-write", "icloud", "Write latency", "fail",
                                    f"Write took {latency:.1f}s (>{FS_PROBE_TIMEOUT}s threshold)",
                                    f'Run: brctl download "{probe_vault}"'))
    elif latency > 1.0:
        results.append(DoctorResult("icloud-write", "icloud", "Write latency", "warn",
                                    f"Write took {latency:.1f}s (1–5s range, iCloud may be syncing)",
                                    "Check Activity Monitor for 'bird' CPU usage"))
    else:
        results.append(DoctorResult("icloud-write", "icloud", "Write latency", "pass",
                                    f"Write latency {latency:.2f}s"))

    # icloud-offload — check if Optimize Mac Storage is likely active
    offloaded = sum(1 for v in icloud_vaults for f in v.rglob("*.md") if is_dataless(f))
    if offloaded > 50:
        results.append(DoctorResult("icloud-offload", "icloud", "Optimize Mac Storage", "fail",
                                    f"{offloaded} vault files are offloaded (dataless placeholders)",
                                    "System Settings → Apple ID → iCloud → disable 'Optimize Mac Storage'"))
    elif offloaded > 0:
        results.append(DoctorResult("icloud-offload", "icloud", "Optimize Mac Storage", "warn",
                                    f"{offloaded} files are offloaded placeholders",
                                    f'Run: brctl download "{probe_vault}"'))
    else:
        results.append(DoctorResult("icloud-offload", "icloud", "Optimize Mac Storage", "pass",
                                    "No offloaded files detected"))

    return results
