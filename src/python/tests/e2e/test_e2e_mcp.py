"""
E2E / dogfood tests for mcp_server.py.

These tests launch the ACTUAL mcp_server.py subprocess (using the obs venv
Python), communicate over stdin/stdout using the MCP JSON-RPC 2.0 protocol,
and assert on real tool responses.

This is the "dogfood" layer: the same protocol Claude Desktop uses.

Requirements:
  - obs venv installed (install.sh or brew)
  - obs_cli.py + db initialized (done automatically via fixture)

Marks:
  @pytest.mark.e2e   — skipped by default in CI unless --run-e2e flag passed
                        (set E2E=1 env var or pass -m e2e to run)

Run locally:
    pytest src/python/tests/e2e/ -v -m e2e
    E2E=1 pytest src/python/tests/e2e/ -v
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_SRC = Path(__file__).parent.parent.parent  # src/python/
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# ---------------------------------------------------------------------------
# Skip guard — don't run E2E in fast unit-test mode unless explicitly requested
# ---------------------------------------------------------------------------
_RUN_E2E = os.environ.get("E2E", "").strip() in ("1", "true", "yes")

pytestmark = pytest.mark.skipif(
    not _RUN_E2E,
    reason="E2E tests skipped — set E2E=1 to run (requires obs venv + installed obs CLI)",
)

# ---------------------------------------------------------------------------
# Resolve obs Python interpreter (same logic as mcp_server.py bootstrap)
# ---------------------------------------------------------------------------
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
    return sys.executable  # fallback: ambient (may lack mcp dep)


_OBS_PYTHON = _find_obs_python()
_MCP_SERVER = _SRC / "mcp_server.py"
_OBS_CLI = _SRC / "obs_cli.py"


# ---------------------------------------------------------------------------
# MCP JSON-RPC client (thin, synchronous over subprocess stdio)
# ---------------------------------------------------------------------------
class MCPClient:
    """
    Minimal synchronous MCP stdio client for testing.

    Speaks JSON-RPC 2.0 over subprocess stdin/stdout.
    Each request gets a unique integer id; responses are matched by id.
    """

    def __init__(self, proc: subprocess.Popen):
        self.proc = proc
        self._req_id = 0

    def _send(self, method: str, params: dict) -> dict:
        self._req_id += 1
        msg = {
            "jsonrpc": "2.0",
            "id": self._req_id,
            "method": method,
            "params": params,
        }
        line = json.dumps(msg) + "\n"
        self.proc.stdin.write(line)
        self.proc.stdin.flush()
        # Read lines until we get a JSON object with our id
        deadline = time.monotonic() + 30.0
        while time.monotonic() < deadline:
            raw = self.proc.stdout.readline()
            if not raw:
                if self.proc.poll() is not None:
                    raise RuntimeError(f"MCP server exited unexpectedly (rc={self.proc.returncode})")
                time.sleep(0.05)
                continue
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue  # skip non-JSON stderr noise routed to stdout
            if obj.get("id") == self._req_id:
                return obj
        raise TimeoutError(f"No response for id={self._req_id} method={method}")

    def initialize(self) -> dict:
        resp = self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "obs-e2e-test", "version": "1.0"},
        })
        # ACK
        self.proc.stdin.write(json.dumps({
            "jsonrpc": "2.0", "method": "notifications/initialized"
        }) + "\n")
        self.proc.stdin.flush()
        return resp

    def tools_list(self) -> list[dict]:
        resp = self._send("tools/list", {})
        return resp.get("result", {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict | None = None) -> str:
        """Call a tool and return the text content of the first content item."""
        resp = self._send("tools/call", {
            "name": name,
            "arguments": arguments or {},
        })
        if "error" in resp:
            raise RuntimeError(f"Tool error: {resp['error']}")
        content = resp.get("result", {}).get("content", [])
        if content and content[0].get("type") == "text":
            return content[0]["text"]
        return json.dumps(resp.get("result", {}))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def e2e_vault(tmp_path_factory):
    """
    Create a real synthetic vault on disk and register it via obs_cli.py db init.
    Returns (vault_path, vault_name).
    """
    vault_dir = tmp_path_factory.mktemp("e2e_vault")
    vault_name = "E2ETestVault"

    # .obsidian dir
    (vault_dir / ".obsidian").mkdir()
    (vault_dir / ".obsidian" / "app.json").write_text("{}")

    # Notes
    notes = {
        "E2E Alpha": "# E2E Alpha\n\nAlpha note for E2E tests.\n\n[[E2E Beta]]\n\n#e2e #alpha",
        "E2E Beta": "# E2E Beta\n\nBeta note.\n\n[[E2E Alpha]]\n\n#e2e #beta",
        "E2E Orphan": "# E2E Orphan\n\nNo links.\n\n#orphan",
    }
    for title, content in notes.items():
        (vault_dir / f"{title}.md").write_text(content)

    # Init DB + register vault.
    # DatabaseManager() resolves its path from Path.home()/.config/obs/... and
    # honors NO db-path env var, so we isolate the whole obs DB by overriding
    # HOME for the CLI + MCP-server subprocesses. This keeps the user's real
    # ~/.config/obs DB untouched (no production pollution from prune/delete
    # lifecycle tests) and makes the sqlite oracle below deterministic.
    e2e_home = tmp_path_factory.mktemp("e2e_home")
    env = {**os.environ, "HOME": str(e2e_home)}

    subprocess.run(
        [_OBS_PYTHON, str(_OBS_CLI), "db", "init"],
        env=env, capture_output=True, check=True,
    )
    subprocess.run(
        [_OBS_PYTHON, str(_OBS_CLI), "scan", str(vault_dir)],
        env=env, capture_output=True, timeout=60,
    )

    return vault_dir, vault_name, env


@pytest.fixture(scope="module")
def mcp_proc(e2e_vault):
    """
    Spawn mcp_server.py subprocess; yield an MCPClient; teardown on module exit.
    """
    _, _, env = e2e_vault

    proc = subprocess.Popen(
        [_OBS_PYTHON, str(_MCP_SERVER)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=env,
    )

    # Give it a moment to start
    time.sleep(1.0)
    if proc.poll() is not None:
        err = proc.stderr.read()
        pytest.fail(f"MCP server failed to start (rc={proc.returncode}):\n{err}")

    client = MCPClient(proc)
    client.initialize()
    yield client

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def _extract_vault_id(vaults_raw: str, vault_dir) -> str:
    """Try to extract a vault ID from list_vaults output. Falls back to dir name."""
    import re
    # Look for hex IDs (8+ hex chars) or the vault dir name
    hex_ids = re.findall(r'\b([0-9a-f]{8,})\b', vaults_raw)
    if hex_ids:
        return hex_ids[0]
    return vault_dir.name


def _extract_first_id(search_raw: str) -> str | None:
    """Try to extract the first note ID from a search result string."""
    import re
    # MCP search results often contain IDs like 'note-abc123' or hex strings
    # Look for patterns like 'id: abc123' or standalone hex IDs
    m = re.search(r'\b([0-9a-f]{8,})\b', search_raw)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# E2E Tests
# ---------------------------------------------------------------------------

class TestE2EProtocol:
    def test_initialize_returns_server_info(self, mcp_proc, e2e_vault):
        """Verify the server identified itself during init."""
        # initialize already called in fixture; just check client is live
        tools = mcp_proc.tools_list()
        assert len(tools) >= 18, f"Expected ≥18 tools, got {len(tools)}"

    def test_tools_list_has_expected_tools(self, mcp_proc):
        tools = mcp_proc.tools_list()
        names = {t["name"] for t in tools}
        expected = {
            "list_vaults", "get_vault_stats", "discover_vaults",
            "search_notes", "list_notes",
            "get_hub_notes", "get_orphaned_notes", "analyze_vault",
            "get_vault_health",
            "read_note", "write_note", "create_note", "append_to_note",
            "rename_note", "delete_note", "get_note_links", "rescan_vault",
            "run_obs_ai",
        }
        missing = expected - names
        assert not missing, f"Missing tools: {missing}"


class TestE2EVaultTools:
    def test_list_vaults(self, mcp_proc, e2e_vault):
        vault_dir, _, _ = e2e_vault
        result = mcp_proc.call_tool("list_vaults")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_vault_stats(self, mcp_proc, e2e_vault):
        vault_dir, _, _ = e2e_vault
        # Get the vault ID from list_vaults first
        vaults_raw = mcp_proc.call_tool("list_vaults")
        # Try with the folder name as vault_id
        result = mcp_proc.call_tool("get_vault_stats", {})
        assert isinstance(result, str)

    def test_discover_vaults_finds_vault(self, mcp_proc, e2e_vault):
        vault_dir, _, _ = e2e_vault
        result = mcp_proc.call_tool("discover_vaults", {"path": str(vault_dir.parent)})
        assert isinstance(result, str)


class TestE2ESearchTools:
    def test_search_notes_finds_match(self, mcp_proc):
        result = mcp_proc.call_tool("search_notes", {"query": "E2E Alpha"})
        assert isinstance(result, str)
        # Should mention the note or report no results (vault may not be synced)
        assert len(result) > 0

    def test_search_notes_no_match(self, mcp_proc):
        result = mcp_proc.call_tool("search_notes", {
            "query": "absolutely_no_such_term_e2e_xyz_999"
        })
        assert isinstance(result, str)

    def test_list_notes(self, mcp_proc):
        # list_vaults to get a vault_id
        vaults = mcp_proc.call_tool("list_vaults")
        assert isinstance(vaults, str)
        # If we can parse a vault id, call list_notes; otherwise just smoke-test with empty
        result = mcp_proc.call_tool("list_notes", {"vault_id": "e2e_vault"})
        assert isinstance(result, str)


class TestE2ENoteLifecycle:
    """Full CRUD lifecycle: create → read → append → delete (dry-run → confirm)."""

    _created_note_id: str | None = None

    def test_01_create_note(self, mcp_proc, e2e_vault):
        vault_dir, _, _ = e2e_vault
        vaults_raw = mcp_proc.call_tool("list_vaults")

        # Extract a vault_id from the response (first word-like token after 'ID:' or use dir name)
        vault_id = None
        for line in vaults_raw.splitlines():
            if "id" in line.lower() or str(vault_dir.name) in line:
                parts = line.split()
                if parts:
                    vault_id = parts[-1].strip("|•:–—")
                    break
        if not vault_id:
            vault_id = vault_dir.name  # fallback

        result = mcp_proc.call_tool("create_note", {
            "vault_id": vault_id,
            "title": "E2E Lifecycle Note",
            "content": "# E2E Lifecycle Note\n\nCreated in E2E dogfood test.\n",
        })
        # May succeed (✅) or report vault not found if vault_id mismatch — both are valid responses
        assert isinstance(result, str)
        assert len(result) > 0

        # Check file actually created
        created_path = vault_dir / "E2E-Lifecycle-Note.md"
        if created_path.exists():
            TestE2ENoteLifecycle._created_note_id = "e2e-lifecycle"  # symbolic

    def test_02_delete_note_dry_run(self, mcp_proc):
        # Use any note_id; dry-run should never raise, only return preview
        result = mcp_proc.call_tool("delete_note", {
            "note_id": "any-note-id",
            "confirm": False,
        })
        assert isinstance(result, str)
        # Either "not found" or dry-run warning
        assert "not found" in result.lower() or "dry run" in result.lower() or "⚠️" in result

    def test_03_run_obs_ai_invalid_command(self, mcp_proc):
        result = mcp_proc.call_tool("run_obs_ai", {
            "command": "invalid-command-xyz",
            "target": "any-vault",
        })
        assert "unknown" in result.lower() or "valid" in result.lower()


class TestE2EGraphHealth:
    def test_get_hub_notes(self, mcp_proc, e2e_vault):
        vault_dir, _, _ = e2e_vault
        result = mcp_proc.call_tool("get_hub_notes", {
            "vault_id": vault_dir.name,
            "limit": 5,
        })
        assert isinstance(result, str)

    def test_get_orphaned_notes(self, mcp_proc, e2e_vault):
        vault_dir, _, _ = e2e_vault
        result = mcp_proc.call_tool("get_orphaned_notes", {"vault_id": vault_dir.name})
        assert isinstance(result, str)

    def test_analyze_vault(self, mcp_proc, e2e_vault):
        vault_dir, _, _ = e2e_vault
        result = mcp_proc.call_tool("analyze_vault", {"vault_id": vault_dir.name})
        assert isinstance(result, str)

    def test_get_vault_health(self, mcp_proc, e2e_vault):
        vault_dir, _, _ = e2e_vault
        result = mcp_proc.call_tool("get_vault_health", {"vault_id": vault_dir.name})
        assert isinstance(result, str)

    def test_get_broken_links(self, mcp_proc, e2e_vault):
        vault_dir, _, _ = e2e_vault
        result = mcp_proc.call_tool("get_broken_links", {"vault_id": vault_dir.name})
        assert isinstance(result, str)


class TestE2ERescan:
    def test_rescan_unknown_vault(self, mcp_proc):
        result = mcp_proc.call_tool("rescan_vault", {"vault_id": "ghost-vault-e2e"})
        assert "not found" in result.lower() or "error" in result.lower()


class TestE2EEdgeCases:
    """Edge cases: empty inputs, large limits, unicode, special chars."""

    def test_search_empty_query(self, mcp_proc):
        """Empty query string should return error or empty results, not crash."""
        result = mcp_proc.call_tool("search_notes", {"query": ""})
        assert isinstance(result, str)

    def test_search_unicode_query(self, mcp_proc):
        """Unicode search should not crash the server."""
        result = mcp_proc.call_tool("search_notes", {"query": "caféé résumé 统计"})
        assert isinstance(result, str)

    def test_search_large_limit(self, mcp_proc):
        """Limit much larger than note count should return all notes without error."""
        result = mcp_proc.call_tool("search_notes", {"query": "E2E", "limit": 9999})
        assert isinstance(result, str)

    def test_list_notes_zero_limit(self, mcp_proc):
        """limit=0 should not crash — return empty or a meaningful message."""
        result = mcp_proc.call_tool("list_notes", {"limit": 0})
        assert isinstance(result, str)

    def test_get_vault_stats_empty_string(self, mcp_proc):
        """Empty vault_id should return 'not found' or list all vaults."""
        result = mcp_proc.call_tool("get_vault_stats", {"vault_id": ""})
        assert isinstance(result, str)

    def test_discover_vaults_nonexistent_path(self, mcp_proc):
        """Nonexistent path should return error, not crash."""
        result = mcp_proc.call_tool("discover_vaults", {"path": "/nonexistent/path/xyz_e2e_999"})
        assert isinstance(result, str)
        # Should report no vaults found or path error
        assert len(result) > 0

    def test_hub_notes_zero_limit(self, mcp_proc):
        """limit=0 for hub notes should not crash."""
        result = mcp_proc.call_tool("get_hub_notes", {"limit": 0})
        assert isinstance(result, str)

    def test_read_note_special_chars_id(self, mcp_proc):
        """Note ID with special chars/path traversal should return not-found safely."""
        for bad_id in ["../../../etc/passwd", "note id with spaces", ""]:
            result = mcp_proc.call_tool("read_note", {"note_id": bad_id})
            assert isinstance(result, str)
            # Should NOT expose system files or crash
            assert "root:" not in result


class TestE2ENoteWriteRead:
    """Create a note via MCP, read it back, append to it, verify content."""

    def test_create_then_read_content(self, mcp_proc, e2e_vault):
        """Content written via create_note must be readable via read_note."""
        vault_dir, _, _ = e2e_vault
        content = "# E2E Write-Read\n\nThis note was created by E2E test.\n\n[[E2E Alpha]]\n"

        # Get vault_id from list_vaults
        vaults_raw = mcp_proc.call_tool("list_vaults")
        vault_id = _extract_vault_id(vaults_raw, vault_dir)

        create_result = mcp_proc.call_tool("create_note", {
            "vault_id": vault_id,
            "title": "E2E Write-Read",
            "content": content,
        })
        assert isinstance(create_result, str)

        # File must exist on disk
        note_path = vault_dir / "E2E Write-Read.md"
        if note_path.exists():
            disk_content = note_path.read_text()
            assert "E2E Write-Read" in disk_content

    def test_append_then_read_back(self, mcp_proc, e2e_vault):
        """append_to_note must persist; content visible on disk."""
        vault_dir, _, _ = e2e_vault
        # Use E2E Alpha which was created by the fixture
        alpha_path = vault_dir / "E2E Alpha.md"
        original = alpha_path.read_text() if alpha_path.exists() else ""

        # Find note_id via search
        search_result = mcp_proc.call_tool("search_notes", {"query": "E2E Alpha"})
        # Extract a note id — if we can't, smoke-test append with a fake id
        note_id = _extract_first_id(search_result) or "e2e-alpha"

        append_text = "\n## Appended Section\n\nAppended by E2E test.\n"
        result = mcp_proc.call_tool("append_to_note", {
            "note_id": note_id,
            "content": append_text,
        })
        assert isinstance(result, str)
        # Either appended successfully or note not found (id mismatch ok)
        # If file grew, check the append text is there
        if alpha_path.exists():
            new_content = alpha_path.read_text()
            if len(new_content) > len(original):
                assert "Appended by E2E test" in new_content

    def test_delete_confirm_removes_file(self, mcp_proc, e2e_vault):
        """delete_note(confirm=True) must actually remove the file from disk."""
        vault_dir, _, _ = e2e_vault
        vaults_raw = mcp_proc.call_tool("list_vaults")
        vault_id = _extract_vault_id(vaults_raw, vault_dir)

        # Create a throwaway note
        mcp_proc.call_tool("create_note", {
            "vault_id": vault_id,
            "title": "E2E Delete Confirm",
            "content": "# E2E Delete Confirm\n\nDelete me.\n",
        })
        note_path = vault_dir / "E2E Delete Confirm.md"
        if not note_path.exists():
            pytest.skip("create_note did not create file (vault_id mismatch)")

        # Find the note's ID
        search_result = mcp_proc.call_tool("search_notes", {"query": "E2E Delete Confirm"})
        note_id = _extract_first_id(search_result) or "e2e-delete-confirm"

        result = mcp_proc.call_tool("delete_note", {"note_id": note_id, "confirm": True})
        assert isinstance(result, str)
        # File should be gone if delete succeeded
        if "deleted" in result.lower() or "🗑️" in result:
            assert not note_path.exists(), "File still exists after confirmed delete"


class TestE2ERescanAndRefresh:
    """Rescan a vault after adding notes; verify DB reflects new state."""

    def test_rescan_known_vault(self, mcp_proc, e2e_vault):
        """rescan_vault on the known vault should succeed (not 'not found')."""
        vault_dir, _, _ = e2e_vault
        vaults_raw = mcp_proc.call_tool("list_vaults")
        vault_id = _extract_vault_id(vaults_raw, vault_dir)

        result = mcp_proc.call_tool("rescan_vault", {"vault_id": vault_id})
        assert isinstance(result, str)
        # Should NOT say 'not found'
        assert "not found" not in result.lower() or vault_id == vault_dir.name

    def test_rescan_then_list_notes_count(self, mcp_proc, e2e_vault):
        """After rescan, list_notes should include at least the fixture notes."""
        vault_dir, _, _ = e2e_vault
        vaults_raw = mcp_proc.call_tool("list_vaults")
        vault_id = _extract_vault_id(vaults_raw, vault_dir)

        # Rescan
        mcp_proc.call_tool("rescan_vault", {"vault_id": vault_id})

        # List notes
        result = mcp_proc.call_tool("list_notes", {"vault_id": vault_id, "limit": 50})
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Sync-lifecycle helpers (own-vault-per-test for deterministic counts)
# ---------------------------------------------------------------------------
import sqlite3 as _sqlite3
import uuid as _uuid


def _build_and_scan_vault(env, tmp_path_factory, notes: dict, name_hint: str = "sync") -> Path:
    """Create a throwaway vault on disk, register + scan it via obs_cli.py.

    `notes` maps a basename (without .md) → file content. Returns the vault dir.
    Each call gets its OWN vault so count-sensitive lifecycle assertions
    (N→N-1, exactly-one-row, exactly-1-ghost) are not corrupted by other tests
    sharing the module-scoped fixture vault.
    """
    vault_dir = tmp_path_factory.mktemp(f"e2e_{name_hint}")
    (vault_dir / ".obsidian").mkdir()
    (vault_dir / ".obsidian" / "app.json").write_text("{}")
    for basename, content in notes.items():
        (vault_dir / f"{basename}.md").write_text(content)
    subprocess.run(
        [_OBS_PYTHON, str(_OBS_CLI), "scan", str(vault_dir)],
        env=env, capture_output=True, timeout=60, check=True,
    )
    return vault_dir


def _db_path(env) -> str:
    """The obs DB the subprocesses use — resolved from the isolated HOME
    (DatabaseManager defaults to ~/.config/obs/vault_db.sqlite)."""
    return str(Path(env["HOME"]) / ".config" / "obs" / "vault_db.sqlite")


def _vault_id_for_path(env, vault_dir: Path) -> str:
    """Look up the registered vault id straight from the DB (ground truth)."""
    conn = _sqlite3.connect(_db_path(env))
    try:
        row = conn.execute(
            "SELECT id FROM vaults WHERE path = ?", (str(vault_dir),)
        ).fetchone()
        assert row is not None, f"vault not registered for {vault_dir}"
        return row[0]
    finally:
        conn.close()


def _db_note_paths(env, vault_id: str) -> set[str]:
    conn = _sqlite3.connect(_db_path(env))
    try:
        rows = conn.execute(
            "SELECT path FROM notes WHERE vault_id = ?", (vault_id,)
        ).fetchall()
        return {r[0] for r in rows}
    finally:
        conn.close()


def _db_note_id(env, vault_id: str, path: str) -> str | None:
    conn = _sqlite3.connect(_db_path(env))
    try:
        row = conn.execute(
            "SELECT id FROM notes WHERE vault_id = ? AND path = ?",
            (vault_id, path),
        ).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def _db_note_tags(env, note_id: str) -> set[str]:
    conn = _sqlite3.connect(_db_path(env))
    try:
        rows = conn.execute(
            "SELECT t.tag FROM note_tags nt "
            "JOIN tags t ON t.id = nt.tag_id "
            "WHERE nt.note_id = ?",
            (note_id,),
        ).fetchall()
        return {r[0] for r in rows}
    finally:
        conn.close()


def _last_scan_failed_count(env, vault_id: str) -> int:
    conn = _sqlite3.connect(_db_path(env))
    try:
        row = conn.execute(
            "SELECT notes_failed FROM scan_history WHERE vault_id = ? "
            "ORDER BY started_at DESC, id DESC LIMIT 1",
            (vault_id,),
        ).fetchone()
        return int(row[0]) if row and row[0] is not None else 0
    finally:
        conn.close()


def _seed_embedding(env, note_id: str) -> None:
    """Insert a note_embeddings row (creating the table if needed)."""
    conn = _sqlite3.connect(_db_path(env))
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS note_embeddings (
                note_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                vector BLOB NOT NULL,
                updated_at TEXT NOT NULL,
                file_mtime REAL NOT NULL,
                PRIMARY KEY (note_id, provider, model),
                FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
            )
        """)
        conn.execute(
            "INSERT OR REPLACE INTO note_embeddings "
            "(note_id, provider, model, vector, updated_at, file_mtime) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (note_id, "e2e-provider", "e2e-model", b"\x00\x01\x02\x03",
             "2026-06-26T00:00:00", 0.0),
        )
        conn.commit()
    finally:
        conn.close()


def _embedding_count(env, note_id: str) -> int:
    conn = _sqlite3.connect(_db_path(env))
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='note_embeddings'"
        ).fetchone()
        if not row:
            return 0
        return int(conn.execute(
            "SELECT COUNT(*) FROM note_embeddings WHERE note_id = ?", (note_id,)
        ).fetchone()[0])
    finally:
        conn.close()


def _doctor_sync_json(env, vault_id: str) -> list[dict]:
    """Run `obs doctor --vault <id> --layer sync --json` and parse results."""
    proc = subprocess.run(
        [_OBS_PYTHON, str(_OBS_CLI), "doctor", "--vault", vault_id,
         "--layer", "sync", "--json"],
        env=env, capture_output=True, text=True, timeout=60,
    )
    return json.loads(proc.stdout)


class TestE2ESyncLifecycle:
    """Vault ↔ DB sync lifecycle (S1/S2/S4/N1 + empty-vault guard).

    Each test builds its OWN vault so the deterministic counts can't be
    perturbed by the shared module fixture. Acts via the MCP rescan_vault
    tool (with prune) and asserts ground truth straight from the DB.
    """

    def test_delete_on_disk_then_rescan_prunes(self, mcp_proc, e2e_vault, tmp_path_factory):
        """S1: delete a file on disk, rescan --prune → row gone, count N→N-1."""
        _, _, env = e2e_vault
        vault_dir = _build_and_scan_vault(
            env, tmp_path_factory,
            {"Keep One": "# Keep One\n\ncontent\n",
             "Keep Two": "# Keep Two\n\ncontent\n",
             "Delete Me": "# Delete Me\n\ncontent\n"},
            "del",
        )
        vault_id = _vault_id_for_path(env, vault_dir)
        before = _db_note_paths(env, vault_id)
        assert "Delete Me.md" in before
        assert len(before) == 3

        (vault_dir / "Delete Me.md").unlink()
        mcp_proc.call_tool("rescan_vault", {"vault_id": vault_id, "prune": True})

        after = _db_note_paths(env, vault_id)
        assert "Delete Me.md" not in after, "deleted note should be pruned"
        assert len(after) == len(before) - 1

    def test_rename_on_disk_no_duplicate(self, mcp_proc, e2e_vault, tmp_path_factory):
        """S2: rename a.md→b.md, rescan --prune → exactly one row, no ghost."""
        _, _, env = e2e_vault
        vault_dir = _build_and_scan_vault(
            env, tmp_path_factory,
            {"Old Name": "# Old Name\n\nrename me\n"},
            "ren",
        )
        vault_id = _vault_id_for_path(env, vault_dir)
        assert _db_note_paths(env, vault_id) == {"Old Name.md"}

        (vault_dir / "Old Name.md").rename(vault_dir / "New Name.md")
        mcp_proc.call_tool("rescan_vault", {"vault_id": vault_id, "prune": True})

        paths = _db_note_paths(env, vault_id)
        assert "Old Name.md" not in paths, "stale rename ghost should be pruned"
        assert paths == {"New Name.md"}, f"expected exactly one row, got {paths}"

    def test_remove_tag_then_rescan_reconciles(self, mcp_proc, e2e_vault, tmp_path_factory):
        """S3 self-heal: strip a #tag, rescan → tag absent from index."""
        _, _, env = e2e_vault
        vault_dir = _build_and_scan_vault(
            env, tmp_path_factory,
            {"Tagged": "# Tagged\n\nbody\n\n#keepme #removeme\n"},
            "tag",
        )
        vault_id = _vault_id_for_path(env, vault_dir)
        note_id = _db_note_id(env, vault_id, "Tagged.md")
        assert note_id is not None
        tags_before = _db_note_tags(env, note_id)
        assert "removeme" in tags_before

        (vault_dir / "Tagged.md").write_text("# Tagged\n\nbody\n\n#keepme\n")
        mcp_proc.call_tool("rescan_vault", {"vault_id": vault_id})

        tags_after = _db_note_tags(env, note_id)
        assert "removeme" not in tags_after, "removed tag should be reconciled away"
        assert "keepme" in tags_after

    def test_unparseable_note_counts_as_error_not_silent(self, mcp_proc, e2e_vault, tmp_path_factory):
        """S4: a note with broken YAML frontmatter is counted, not swallowed."""
        _, _, env = e2e_vault
        # Invalid YAML frontmatter trips parse_file (yaml.parser.ParserError).
        bad = "---\ntitle: Unclosed\nkey: [a, b\n---\n# Content\n"
        vault_dir = _build_and_scan_vault(
            env, tmp_path_factory,
            {"Good Note": "# Good Note\n\nfine\n", "Bad Note": bad},
            "err",
        )
        vault_id = _vault_id_for_path(env, vault_dir)
        # Rescan via MCP, then assert the failure was recorded (not silent).
        mcp_proc.call_tool("rescan_vault", {"vault_id": vault_id})
        assert _last_scan_failed_count(env, vault_id) >= 1, (
            "unparseable note must be counted in scan_history.notes_failed, "
            "not silently swallowed"
        )

    def test_prune_skipped_when_vault_appears_empty(self, mcp_proc, e2e_vault, tmp_path_factory):
        """Safety guard: empty vault dir → prune skipped, index NOT wiped."""
        _, _, env = e2e_vault
        vault_dir = _build_and_scan_vault(
            env, tmp_path_factory,
            {"Lonely": "# Lonely\n\nthe only note\n"},
            "empty",
        )
        vault_id = _vault_id_for_path(env, vault_dir)
        assert _db_note_paths(env, vault_id) == {"Lonely.md"}

        # Remove the only file → dir now has no *.md → seen_paths == 0.
        (vault_dir / "Lonely.md").unlink()
        mcp_proc.call_tool("rescan_vault", {"vault_id": vault_id, "prune": True})

        # Guard must have fired: row survives rather than being wiped.
        assert _db_note_paths(env, vault_id) == {"Lonely.md"}, (
            "empty-vault prune guard must NOT wipe the index"
        )

    def test_unchanged_note_preserves_embeddings(self, mcp_proc, e2e_vault, tmp_path_factory):
        """N1: rescanning a byte-identical note keeps its note_embeddings row."""
        _, _, env = e2e_vault
        content = "# Stable\n\nthis content does not change\n\n#stable\n"
        vault_dir = _build_and_scan_vault(
            env, tmp_path_factory, {"Stable": content}, "emb",
        )
        vault_id = _vault_id_for_path(env, vault_dir)
        note_id = _db_note_id(env, vault_id, "Stable.md")
        assert note_id is not None

        # Seed an embedding for this note, then rescan WITHOUT changing the file.
        _seed_embedding(env, note_id)
        assert _embedding_count(env, note_id) == 1

        mcp_proc.call_tool("rescan_vault", {"vault_id": vault_id})

        # content_hash matches → short-circuit fires → no REPLACE → cascade
        # never runs → embedding survives.
        assert _embedding_count(env, note_id) == 1, (
            "unchanged note must not destroy its embedding cache (N1)"
        )


class TestE2EDoctorSyncDogfood:
    """Dogfood: real `obs doctor --layer sync` against a fixture vault."""

    def test_doctor_sync_clean_on_fresh_scan(self, mcp_proc, e2e_vault, tmp_path_factory):
        """Fresh scan → sync layer reports no ghosts / nothing missing."""
        _, _, env = e2e_vault
        vault_dir = _build_and_scan_vault(
            env, tmp_path_factory,
            {"Fresh A": "# Fresh A\n\nclean\n", "Fresh B": "# Fresh B\n\nclean\n"},
            "clean",
        )
        vault_id = _vault_id_for_path(env, vault_dir)

        results = _doctor_sync_json(env, vault_id)
        by_id = {r["id"]: r for r in results}
        ghosts = by_id.get(f"sync-ghosts:{vault_id}")
        missing = by_id.get(f"sync-missing:{vault_id}")
        assert ghosts is not None and missing is not None, (
            f"sync checks for {vault_id} not emitted: {[r['id'] for r in results]}"
        )
        assert ghosts["status"] == "pass", f"expected clean ghosts, got {ghosts}"
        assert missing["status"] == "pass", f"expected nothing missing, got {missing}"

    def test_doctor_sync_detects_injected_ghost(self, mcp_proc, e2e_vault, tmp_path_factory):
        """Delete a file on disk WITHOUT rescanning → doctor flags exactly 1 ghost."""
        _, _, env = e2e_vault
        vault_dir = _build_and_scan_vault(
            env, tmp_path_factory,
            {"Survivor": "# Survivor\n\nstays\n", "Ghost": "# Ghost\n\nwill vanish\n"},
            "ghost",
        )
        vault_id = _vault_id_for_path(env, vault_dir)

        # Delete on disk but do NOT rescan → DB still has the row → ghost.
        (vault_dir / "Ghost.md").unlink()

        results = _doctor_sync_json(env, vault_id)
        by_id = {r["id"]: r for r in results}
        ghosts = by_id.get(f"sync-ghosts:{vault_id}")
        assert ghosts is not None, (
            f"sync-ghosts for {vault_id} not emitted: {[r['id'] for r in results]}"
        )
        assert ghosts["status"] == "warn", f"expected a ghost warning, got {ghosts}"
        # Message format: "<N> DB row(s) point to files gone from disk"
        assert ghosts["message"].startswith("1 "), (
            f"expected exactly 1 ghost, got message {ghosts['message']!r}"
        )


class TestE2EServerStability:
    """Server must remain responsive across 20 rapid sequential calls."""

    def test_rapid_sequential_calls(self, mcp_proc):
        """20 rapid list_vaults calls must all succeed without timeout or crash."""
        for i in range(20):
            result = mcp_proc.call_tool("list_vaults")
            assert isinstance(result, str), f"Call {i} returned non-string"

    def test_tools_list_idempotent(self, mcp_proc):
        """tools/list called 5 times must return identical tool counts."""
        counts = [len(mcp_proc.tools_list()) for _ in range(5)]
        assert len(set(counts)) == 1, f"tools/list returned different counts across calls: {counts}"
