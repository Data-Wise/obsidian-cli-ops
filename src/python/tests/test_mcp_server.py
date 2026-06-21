"""
Unit tests for mcp_server.py — all 26 MCP tools + 4 resources.

Strategy
--------
- The mcp_server module runs os.execv at import time if the interpreter
  doesn't match the obs venv. We pre-stub os.execv (and the _find_obs_python
  helper) before the import so the module loads under whichever Python is
  running pytest.
- Module-level singletons (db, vault_manager, graph_analyzer) are replaced
  with test instances after import.
- A `obs_vault` fixture builds a small synthetic vault on disk and registers
  it in the in-memory SQLite DB so every tool has real data to work with.
- Tools are called as plain Python functions — no MCP stdio transport needed.

Run:
    PYTHONPATH=src/python pytest src/python/tests/test_mcp_server.py -v
"""
from __future__ import annotations

import asyncio
import importlib
import os
import sys
import types
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Path setup — must be before any local imports
# ---------------------------------------------------------------------------
_SRC = Path(__file__).parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# ---------------------------------------------------------------------------
# Stub the `mcp` package so mcp_server.py can be imported without the obs venv.
# We only need FastMCP to be a no-op decorator factory at import time; tests
# call the underlying Python functions directly, not via MCP transport.
# ---------------------------------------------------------------------------
def _install_mcp_stub() -> None:
    """Inject a minimal mcp stub into sys.modules before mcp_server is loaded."""
    if "mcp" in sys.modules:
        return  # real mcp available (obs venv) — nothing to do

    # Build the stub hierarchy: mcp, mcp.server, mcp.server.fastmcp
    mcp_stub = types.ModuleType("mcp")
    server_stub = types.ModuleType("mcp.server")
    fastmcp_stub = types.ModuleType("mcp.server.fastmcp")

    class _FastMCP:
        """Minimal FastMCP stub — decorators are transparent pass-throughs."""
        def __init__(self, name: str = "", **kwargs):
            self.name = name

        def tool(self, *args, **kwargs):
            """Return a no-op decorator."""
            def decorator(fn):
                return fn
            # Handle both @mcp.tool and @mcp.tool()
            if args and callable(args[0]):
                return args[0]
            return decorator

        def resource(self, uri: str, **kwargs):
            def decorator(fn):
                return fn
            return decorator

        def run(self):
            pass

    fastmcp_stub.FastMCP = _FastMCP
    server_stub.fastmcp = fastmcp_stub
    mcp_stub.server = server_stub

    sys.modules["mcp"] = mcp_stub
    sys.modules["mcp.server"] = server_stub
    sys.modules["mcp.server.fastmcp"] = fastmcp_stub


_install_mcp_stub()


# ---------------------------------------------------------------------------
# Fixtures — DB and vault
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def real_db():
    """In-memory DatabaseManager with schema initialised once per module."""
    from db_manager import DatabaseManager
    db = DatabaseManager(db_path=":memory:")
    db.initialize_database()
    return db


@pytest.fixture(scope="module")
def obs_vault(tmp_path_factory, real_db):
    """
    Synthetic vault on disk + scanned into real_db.
    Returns (vault_id, vault_path, note_ids_by_title).
    """
    from vault_scanner import VaultScanner

    vault_dir = tmp_path_factory.mktemp("vault")
    (vault_dir / ".obsidian").mkdir()
    (vault_dir / ".obsidian" / "app.json").write_text("{}")

    notes = {
        "Alpha Note": (
            "# Alpha Note\n\nAlpha body.\n\n[[Beta Note]]\n\n#research #alpha"
        ),
        "Beta Note": (
            "# Beta Note\n\nBeta body.\n\n[[Alpha Note]] [[Gamma Note]]\n\n#research"
        ),
        "Gamma Note": (
            "# Gamma Note\n\nGamma body.\n\n[[Alpha Note]]\n\n#statistics"
        ),
        "Hub Note": (
            "# Hub Note\n\n[[Alpha Note]] [[Beta Note]] [[Gamma Note]]\n\n#hub"
        ),
        "Orphan Note": (
            "# Orphan Note\n\nNo incoming links.\n\n#orphan"
        ),
    }
    for title, content in notes.items():
        (vault_dir / f"{title}.md").write_text(content)

    vault_id = real_db.add_vault(vault_dir.name, str(vault_dir))
    scanner = VaultScanner(real_db)
    asyncio.run(scanner.scan_vault(str(vault_dir), vault_id))

    rows = real_db.list_notes(vault_id, limit=50)
    note_ids = {row["title"]: row["id"] for row in rows}
    return vault_id, vault_dir, note_ids


# ---------------------------------------------------------------------------
# Import mcp_server with the execv guard neutralised
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def mcp_mod(real_db, obs_vault):
    """
    Import (or retrieve) mcp_server with os.execv pre-stubbed so it can't
    re-exec the process, then replace the module-level singletons.
    """
    # If already loaded (e.g. prior parametrize run) just patch singletons.
    if "mcp_server" in sys.modules:
        mod = sys.modules["mcp_server"]
    else:
        # Stub os.execv before the module-level code runs
        _real_execv = os.execv
        os.execv = lambda *a, **kw: None  # no-op
        try:
            import mcp_server as mod
        finally:
            os.execv = _real_execv

    from core.vault_manager import VaultManager
    from core.graph_analyzer import GraphAnalyzer

    mod.db = real_db
    mod.vault_manager = VaultManager(real_db)
    mod.graph_analyzer = GraphAnalyzer(real_db)
    return mod


# ---------------------------------------------------------------------------
# Vault tools
# ---------------------------------------------------------------------------

class TestVaultTools:
    def test_list_vaults_returns_string(self, mcp_mod):
        result = mcp_mod.list_vaults()
        assert isinstance(result, str) and len(result) > 0

    def test_list_vaults_contains_vault(self, mcp_mod, obs_vault):
        vault_id, vault_dir, _ = obs_vault
        result = mcp_mod.list_vaults()
        assert vault_dir.name in result or vault_id in result

    def test_get_vault_stats_known(self, mcp_mod, obs_vault):
        vault_id, _, _ = obs_vault
        result = mcp_mod.get_vault_stats(vault_id)
        assert isinstance(result, str)
        assert any(kw in result.lower() for kw in ["note", "vault", "link"])

    def test_get_vault_stats_unknown(self, mcp_mod):
        result = mcp_mod.get_vault_stats("vault-does-not-exist")
        assert isinstance(result, str)
        assert any(kw in result.lower() for kw in ["not found", "error", "no vault"])

    def test_get_vault_stats_no_arg(self, mcp_mod):
        result = mcp_mod.get_vault_stats()
        assert isinstance(result, str)

    def test_discover_vaults_parent_dir(self, mcp_mod, obs_vault):
        _, vault_dir, _ = obs_vault
        result = mcp_mod.discover_vaults(str(vault_dir.parent))
        assert isinstance(result, str)

    def test_discover_vaults_nonexistent(self, mcp_mod):
        result = mcp_mod.discover_vaults("/no/such/path/e2e_xyz")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Search tools
# ---------------------------------------------------------------------------

class TestSearchTools:
    def test_search_notes_hit(self, mcp_mod, obs_vault):
        vault_id, _, _ = obs_vault
        result = mcp_mod.search_notes("alpha", vault_id=vault_id)
        assert isinstance(result, str)
        assert "Alpha" in result

    def test_search_notes_miss(self, mcp_mod, obs_vault):
        vault_id, _, _ = obs_vault
        result = mcp_mod.search_notes("zzznomatch999", vault_id=vault_id)
        assert isinstance(result, str)

    def test_search_notes_global(self, mcp_mod):
        result = mcp_mod.search_notes("note")
        assert isinstance(result, str)

    def test_search_notes_limit(self, mcp_mod, obs_vault):
        vault_id, _, _ = obs_vault
        result = mcp_mod.search_notes("note", vault_id=vault_id, limit=2)
        assert isinstance(result, str)

    def test_list_notes(self, mcp_mod, obs_vault):
        vault_id, _, _ = obs_vault
        result = mcp_mod.list_notes(vault_id)
        assert isinstance(result, str)
        assert any(t in result for t in ["Alpha Note", "Beta Note", "Hub Note"])

    def test_list_notes_limit(self, mcp_mod, obs_vault):
        vault_id, _, _ = obs_vault
        result = mcp_mod.list_notes(vault_id, limit=2)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Graph tools
# ---------------------------------------------------------------------------

class TestGraphTools:
    def test_get_hub_notes(self, mcp_mod, obs_vault):
        vault_id, _, _ = obs_vault
        result = mcp_mod.get_hub_notes(vault_id, limit=3)
        assert isinstance(result, str)

    def test_get_orphaned_notes(self, mcp_mod, obs_vault):
        vault_id, _, _ = obs_vault
        result = mcp_mod.get_orphaned_notes(vault_id)
        assert isinstance(result, str)
        assert "Orphan" in result

    def test_get_broken_links(self, mcp_mod, obs_vault):
        vault_id, _, _ = obs_vault
        result = mcp_mod.get_broken_links(vault_id)
        assert isinstance(result, str)

    def test_analyze_vault_known(self, mcp_mod, obs_vault):
        vault_id, _, _ = obs_vault
        result = mcp_mod.analyze_vault(vault_id)
        assert isinstance(result, str)
        assert any(kw in result.lower() for kw in ["density", "notes", "links", "cluster"])

    def test_analyze_vault_unknown(self, mcp_mod):
        result = mcp_mod.analyze_vault("ghost-vault")
        assert isinstance(result, str)

    def test_find_similar_notes(self, mcp_mod, obs_vault):
        vault_id, _, _ = obs_vault
        result = mcp_mod.find_similar_notes("Alpha Note", vault_id=vault_id, limit=3)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Health tool
# ---------------------------------------------------------------------------

class TestHealthTool:
    def test_get_vault_health_known(self, mcp_mod, obs_vault):
        vault_id, _, _ = obs_vault
        result = mcp_mod.get_vault_health(vault_id)
        assert isinstance(result, str)
        assert any(kw in result.lower() for kw in [
            "health", "score", "connectivity", "freshness", "overall", "vault"
        ])

    def test_get_vault_health_unknown(self, mcp_mod):
        result = mcp_mod.get_vault_health("ghost-vault")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Note CRUD
# ---------------------------------------------------------------------------

class TestNoteCRUD:

    # --- read ---

    def test_read_note_exists(self, mcp_mod, obs_vault):
        _, _, note_ids = obs_vault
        result = mcp_mod.read_note(note_ids["Alpha Note"])
        assert "Alpha" in result

    def test_read_note_not_found(self, mcp_mod):
        result = mcp_mod.read_note("note-id-ghost-xyz")
        assert "not found" in result.lower()

    # --- create ---

    def test_create_note_new(self, mcp_mod, obs_vault):
        vault_id, vault_dir, _ = obs_vault
        result = mcp_mod.create_note(
            vault_id=vault_id,
            title="Unit Test Created Note",
            content="# Unit Test Created Note\n\nCreated by unit test.\n",
        )
        assert "✅" in result or "created" in result.lower()
        assert (vault_dir / "Unit-Test-Created-Note.md").exists()

    def test_create_note_duplicate(self, mcp_mod, obs_vault):
        vault_id, _, _ = obs_vault
        mcp_mod.create_note(vault_id=vault_id, title="DupCheck", content="first")
        result = mcp_mod.create_note(vault_id=vault_id, title="DupCheck", content="second")
        assert "already exists" in result.lower() or "❌" in result

    def test_create_note_unknown_vault(self, mcp_mod):
        result = mcp_mod.create_note(vault_id="no-vault", title="Ghost", content="x")
        assert "not found" in result.lower()

    def test_create_note_with_subfolder(self, mcp_mod, obs_vault):
        vault_id, vault_dir, _ = obs_vault
        result = mcp_mod.create_note(
            vault_id=vault_id,
            title="SubfolderNote",
            content="# SubfolderNote\n\nIn subfolder.",
            subfolder="sub/dir",
        )
        assert "✅" in result or "created" in result.lower()
        assert (vault_dir / "sub" / "dir" / "SubfolderNote.md").exists()

    # --- write ---

    def test_write_note_overwrites(self, mcp_mod, obs_vault):
        _, vault_dir, note_ids = obs_vault
        note_id = note_ids["Gamma Note"]
        result = mcp_mod.write_note(note_id, "# Gamma\n\nOverwritten.\n", create_backup=True)
        assert "✅" in result or "written" in result.lower()
        # Backup created
        bak = vault_dir / "Gamma Note.md.bak"
        assert bak.exists(), "Backup file should exist"

    def test_write_note_no_backup(self, mcp_mod, obs_vault):
        _, _, note_ids = obs_vault
        note_id = note_ids["Beta Note"]
        result = mcp_mod.write_note(note_id, "# Beta\n\nNo backup.\n", create_backup=False)
        assert isinstance(result, str)
        assert "not found" not in result.lower() or "✅" in result

    def test_write_note_not_found(self, mcp_mod):
        result = mcp_mod.write_note("ghost-note-id-xyz", "content")
        assert "not found" in result.lower()

    # --- append ---

    def test_append_to_note(self, mcp_mod, obs_vault):
        _, vault_dir, note_ids = obs_vault
        note_id = note_ids["Alpha Note"]
        result = mcp_mod.append_to_note(note_id, "## Appended\n\nBy test.")
        assert "✅" in result or "append" in result.lower()
        content = (vault_dir / "Alpha Note.md").read_text()
        assert "Appended" in content

    def test_append_to_note_not_found(self, mcp_mod):
        result = mcp_mod.append_to_note("ghost-id-xyz", "x")
        assert "not found" in result.lower()

    # --- rename ---

    def test_rename_note(self, mcp_mod, obs_vault, real_db):
        vault_id, vault_dir, _ = obs_vault
        # Create a disposable note
        mcp_mod.create_note(vault_id, "RenameTarget", "# RenameTarget\n\nWill be renamed.")
        rows = real_db.list_notes(vault_id, limit=100)
        rename_id = next(
            (r["id"] for r in rows if "RenameTarget" in r["title"]), None
        )
        if rename_id is None:
            pytest.skip("RenameTarget not yet indexed in DB (scanner not re-run)")
        result = mcp_mod.rename_note(rename_id, "RenameSuccess")
        assert isinstance(result, str)

    # --- delete dry-run ---

    def test_delete_note_dry_run(self, mcp_mod, obs_vault):
        _, _, note_ids = obs_vault
        note_id = note_ids["Orphan Note"]
        result = mcp_mod.delete_note(note_id, confirm=False)
        assert "dry run" in result.lower() or "⚠️" in result
        # File must still exist
        assert (obs_vault[1] / "Orphan Note.md").exists()

    # --- delete confirm ---

    def test_delete_note_confirm(self, mcp_mod, obs_vault, real_db):
        vault_id, vault_dir, _ = obs_vault
        # Create a fresh note just for deletion
        mcp_mod.create_note(vault_id, "DeleteMe", "# DeleteMe\n\nSafe to delete.")
        target_path = vault_dir / "DeleteMe.md"
        assert target_path.exists()

        # Find ID in DB
        rows = real_db.list_notes(vault_id, limit=100)
        del_id = next((r["id"] for r in rows if "DeleteMe" in r["title"]), None)
        if del_id is None:
            # Insert manually so delete_note can find it
            del_id = real_db.add_note(
                vault_id=vault_id,
                path="DeleteMe.md",
                title="DeleteMe",
                content="# DeleteMe\n\nSafe to delete.",
            )
        result = mcp_mod.delete_note(del_id, confirm=True)
        assert "deleted" in result.lower() or "🗑️" in result
        assert not target_path.exists()

    # --- timeout / iCloud hang simulation ---

    def test_create_note_fs_timeout(self, mcp_mod, obs_vault):
        """_fs_op returns a structured error when a FS op blocks past the timeout."""
        from concurrent.futures import TimeoutError as FuturesTimeoutError
        from unittest.mock import MagicMock

        vault_id, _, _ = obs_vault

        mock_future = MagicMock()
        mock_future.result.side_effect = FuturesTimeoutError()

        mock_executor = MagicMock()
        mock_executor.__enter__ = MagicMock(return_value=mock_executor)
        mock_executor.__exit__ = MagicMock(return_value=False)
        mock_executor.submit.return_value = mock_future

        with patch("fs_utils.ThreadPoolExecutor", return_value=mock_executor):
            with patch.object(mcp_mod, "_FS_WRITE_TIMEOUT", 0.001):
                result = mcp_mod.create_note(vault_id, "HangTest", "content")

        assert "timed out" in result.lower() or "❌" in result

    # --- links ---

    def test_get_note_links(self, mcp_mod, obs_vault):
        _, _, note_ids = obs_vault
        result = mcp_mod.get_note_links(note_ids["Alpha Note"])
        assert any(kw in result.lower() for kw in ["outgoing", "incoming", "🔗", "link"])

    def test_get_note_links_not_found(self, mcp_mod):
        result = mcp_mod.get_note_links("ghost-note-xyz")
        assert "not found" in result.lower()


# ---------------------------------------------------------------------------
# Rescan tool
# ---------------------------------------------------------------------------

class TestRescanTool:
    def test_rescan_vault_known(self, mcp_mod, obs_vault):
        vault_id, _, _ = obs_vault
        result = mcp_mod.rescan_vault(vault_id)
        assert isinstance(result, str)
        assert any(kw in result.lower() for kw in ["scan", "note", "✅", "rescan"])

    def test_rescan_vault_unknown(self, mcp_mod):
        result = mcp_mod.rescan_vault("ghost-vault-xyz")
        assert any(kw in result.lower() for kw in ["not found", "error"])


# ---------------------------------------------------------------------------
# run_obs_ai (subprocess mocked)
# ---------------------------------------------------------------------------

class TestRunObsAI:
    def test_invalid_command(self, mcp_mod):
        result = mcp_mod.run_obs_ai("not-a-real-command", "MyVault")
        assert "unknown" in result.lower() or "valid" in result.lower()

    @pytest.mark.parametrize("cmd", [
        "gaps", "quality", "merge-suggest", "tag-suggest", "summarize",
        "similar", "analyze", "duplicates", "suggest-links",
    ])
    def test_valid_command_dispatches_to_obs(self, mcp_mod, cmd):
        """Valid commands must reach _obs() with the right args — no real subprocess."""
        with patch.object(mcp_mod, "_obs", return_value='{"ok": true}') as mock_obs:
            result = mcp_mod.run_obs_ai(cmd, "test-target")
        mock_obs.assert_called_once()
        args_list = mock_obs.call_args[0][0]
        assert "ai" in args_list
        assert cmd in args_list
        assert "--json" in args_list


# ---------------------------------------------------------------------------
# Temporal tools — get_bridge_status, get_trends, get_stale_notes, get_daily_digest
# ---------------------------------------------------------------------------

class TestTemporalTools:
    def test_bridge_status_returns_json_string(self, mcp_mod):
        """get_bridge_status() always returns a JSON string (subprocess mocked)."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
            result = mcp_mod.get_bridge_status()
        assert isinstance(result, str)
        import json
        data = json.loads(result)
        assert "cli_installed" in data
        assert isinstance(data["cli_installed"], bool)

    def test_bridge_status_error_returns_string(self, mcp_mod):
        """get_bridge_status() returns error string on unexpected failure."""
        with patch.object(mcp_mod.vault_manager, "get_bridge_status", side_effect=RuntimeError("boom")):
            result = mcp_mod.get_bridge_status()
        assert "Error" in result or "boom" in result

    def test_get_trends_returns_json_string(self, mcp_mod, obs_vault):
        """get_trends() returns JSON with expected keys."""
        vault_id, _, _ = obs_vault
        result = mcp_mod.get_trends(vault_id, days=90)
        assert isinstance(result, str)
        import json
        data = json.loads(result)
        assert "vault_id" in data
        assert "buckets" in data
        assert isinstance(data["buckets"], list)

    def test_get_trends_unknown_vault(self, mcp_mod):
        """get_trends() with unknown vault returns error string."""
        result = mcp_mod.get_trends("vault-xyz-does-not-exist")
        assert isinstance(result, str)
        assert "Error" in result or "not found" in result.lower()

    def test_get_stale_notes_returns_json_string(self, mcp_mod, obs_vault):
        """get_stale_notes() returns JSON with notes list."""
        vault_id, _, _ = obs_vault
        result = mcp_mod.get_stale_notes(vault_id, limit=5)
        assert isinstance(result, str)
        import json
        data = json.loads(result)
        assert "vault_id" in data
        assert "notes" in data
        assert isinstance(data["notes"], list)
        assert len(data["notes"]) <= 5

    def test_get_stale_notes_unknown_vault(self, mcp_mod):
        """get_stale_notes() with unknown vault returns error string."""
        result = mcp_mod.get_stale_notes("vault-xyz-does-not-exist")
        assert isinstance(result, str)
        assert "Error" in result or "not found" in result.lower()

    def test_get_daily_digest_returns_json_string(self, mcp_mod, obs_vault):
        """get_daily_digest() returns JSON with bridge, trends, and stale sub-objects."""
        vault_id, _, _ = obs_vault
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
            result = mcp_mod.get_daily_digest(vault_id, days=90, limit=3)
        assert isinstance(result, str)
        import json
        data = json.loads(result)
        assert "bridge" in data
        assert "trends" in data
        assert "stale" in data
        assert "cli_installed" in data["bridge"]
        assert "buckets" in data["trends"]
        assert "notes" in data["stale"]

    def test_get_daily_digest_unknown_vault(self, mcp_mod):
        """get_daily_digest() with unknown vault returns error string."""
        result = mcp_mod.get_daily_digest("vault-xyz-does-not-exist")
        assert isinstance(result, str)
        assert "Error" in result or "not found" in result.lower()


# ---------------------------------------------------------------------------
# MCP Resources (delegate to tool functions)
# ---------------------------------------------------------------------------

class TestResources:
    def test_vault_stats_resource(self, mcp_mod, obs_vault):
        vault_id, _, _ = obs_vault
        result = mcp_mod.vault_stats_resource(vault_id)
        assert isinstance(result, str)

    def test_vault_health_resource(self, mcp_mod, obs_vault):
        vault_id, _, _ = obs_vault
        result = mcp_mod.vault_health_resource(vault_id)
        assert isinstance(result, str)

    def test_overview_resource(self, mcp_mod):
        result = mcp_mod.overview_resource()
        assert isinstance(result, str)

    def test_note_resource(self, mcp_mod, obs_vault):
        _, _, note_ids = obs_vault
        result = mcp_mod.note_resource(note_ids["Alpha Note"])
        assert "Alpha" in result


# ---------------------------------------------------------------------------
# unified_search
# ---------------------------------------------------------------------------

class TestUnifiedSearch:
    def test_returns_vault_results(self, mcp_mod, obs_vault):
        """vault section appears and contains a hit when notes exist."""
        result = mcp_mod.unified_search("Alpha")
        assert "Vault Notes" in result
        assert "Alpha" in result

    def test_no_vault_hit(self, mcp_mod, obs_vault):
        """missing query still produces vault section, no crash."""
        result = mcp_mod.unified_search("xyzzy_no_such_note_42")
        assert "Vault Notes" in result
        assert isinstance(result, str)

    def test_unconfigured_zotero_note(self, mcp_mod, monkeypatch):
        """zotero section says 'not configured' when config has no research block."""
        import config_loader as cl
        monkeypatch.setattr(cl, "load", lambda: None)
        result = mcp_mod.unified_search("test")
        assert "Zotero Library" in result
        assert "Not configured" in result or "not configured" in result

    def test_unconfigured_pdf_note(self, mcp_mod, monkeypatch):
        """pdf section says 'not configured' when config has no pdf block."""
        import config_loader as cl
        monkeypatch.setattr(cl, "load", lambda: None)
        result = mcp_mod.unified_search("test")
        assert "PDF Documents" in result
        assert "Not configured" in result or "not configured" in result

    def test_header_contains_query(self, mcp_mod, obs_vault):
        """output header names the query."""
        result = mcp_mod.unified_search("Beta", limit=5)
        assert "Beta" in result
        assert "Unified Search" in result


# ---------------------------------------------------------------------------
# Phase 4 — Research Domain Tools
# ---------------------------------------------------------------------------

class TestPhase4NoConfig:
    """All Phase 4 tools return a helpful 'not configured' string when config is absent."""

    def _patch_cfg(self, mcp_mod, monkeypatch):
        """Make _load_cfg return None for all tools in this class."""
        monkeypatch.setattr(mcp_mod, "_load_cfg", lambda: None)

    def test_zotero_search_no_config(self, mcp_mod, monkeypatch):
        self._patch_cfg(mcp_mod, monkeypatch)
        result = mcp_mod.zotero_search("test")
        assert "not configured" in result.lower() or "not config" in result.lower()

    def test_zotero_get_no_config(self, mcp_mod, monkeypatch):
        self._patch_cfg(mcp_mod, monkeypatch)
        result = mcp_mod.zotero_get("ABC12345")
        assert "not configured" in result.lower()

    def test_zotero_cite_no_config(self, mcp_mod, monkeypatch):
        self._patch_cfg(mcp_mod, monkeypatch)
        result = mcp_mod.zotero_cite("ABC12345")
        assert "not configured" in result.lower()

    def test_zotero_recent_no_config(self, mcp_mod, monkeypatch):
        self._patch_cfg(mcp_mod, monkeypatch)
        result = mcp_mod.zotero_recent()
        assert "not configured" in result.lower()

    def test_pdf_search_no_config(self, mcp_mod, monkeypatch):
        self._patch_cfg(mcp_mod, monkeypatch)
        result = mcp_mod.pdf_search("test")
        assert "not configured" in result.lower()

    def test_course_list_no_config(self, mcp_mod, monkeypatch):
        self._patch_cfg(mcp_mod, monkeypatch)
        result = mcp_mod.course_list()
        assert "not configured" in result.lower()

    def test_course_show_no_config(self, mcp_mod, monkeypatch):
        self._patch_cfg(mcp_mod, monkeypatch)
        result = mcp_mod.course_show("my-course")
        assert "not configured" in result.lower()

    def test_course_lectures_no_config(self, mcp_mod, monkeypatch):
        self._patch_cfg(mcp_mod, monkeypatch)
        result = mcp_mod.course_lectures("my-course")
        assert "not configured" in result.lower()

    def test_manuscript_list_no_config(self, mcp_mod, monkeypatch):
        self._patch_cfg(mcp_mod, monkeypatch)
        result = mcp_mod.manuscript_list()
        assert "not configured" in result.lower()

    def test_manuscript_show_no_config(self, mcp_mod, monkeypatch):
        self._patch_cfg(mcp_mod, monkeypatch)
        result = mcp_mod.manuscript_show("my-paper")
        assert "not configured" in result.lower()

    def test_manuscript_stats_no_config(self, mcp_mod, monkeypatch):
        self._patch_cfg(mcp_mod, monkeypatch)
        result = mcp_mod.manuscript_stats()
        assert "not configured" in result.lower()

    def test_bib_check_no_config(self, mcp_mod, monkeypatch):
        self._patch_cfg(mcp_mod, monkeypatch)
        result = mcp_mod.bib_check("my-paper")
        assert "not configured" in result.lower()


class TestPhase4WithConfig:
    """Phase 4 tools with synthetic on-disk fixtures and minimal config stubs."""

    @pytest.fixture
    def teaching_dir(self, tmp_path):
        """Synthetic courses directory with one course."""
        courses = tmp_path / "courses"
        courses.mkdir()
        course = courses / "stats101"
        course.mkdir()
        (course / ".STATUS").write_text(
            "status: active\npriority: P1\nprogress: 40\nnext: prepare week 5\nweek: 4\n"
        )
        (course / "_quarto.yml").write_text(
            "project:\n  type: book\nbook:\n  title: Introduction to Statistics\n"
        )
        lectures = course / "lectures"
        lectures.mkdir()
        (lectures / "week-01.qmd").write_text('---\ntitle: "Week 1: Intro"\n---\n\nContent.')
        (lectures / "week-02.qmd").write_text('---\ntitle: "Week 2: Probability"\n---\n\nContent.')
        return courses

    @pytest.fixture
    def writing_dir(self, tmp_path):
        """Synthetic manuscripts directory with one manuscript."""
        manuscripts = tmp_path / "manuscripts"
        manuscripts.mkdir()
        paper = manuscripts / "mediation-paper"
        paper.mkdir()
        (paper / ".STATUS").write_text(
            "status: active\npriority: P1\nprogress: 65\nnext: finish results\ntarget: JASA\n"
        )
        (paper / "_quarto.yml").write_text(
            "project:\n  type: manuscript\ntitle: Causal Mediation Analysis\n"
            "author:\n  - name: D. Tofighi\n"
        )
        bib = paper / "refs.bib"
        bib.write_text(
            "@article{smith2020,\n  title = {Test Article},\n  author = {Smith, John},\n"
            "  year = {2020},\n  journal = {JASA},\n}\n"
            "@article{jones2021,\n  title = {Another Article},\n  author = {Jones, Jane},\n"
            "  year = {2021},\n  journal = {Biometrika},\n}\n"
        )
        main = paper / "index.qmd"
        main.write_text(
            "---\ntitle: Causal Mediation\n---\n\nSome text [@smith2020] and more text.\n"
        )
        return manuscripts

    @pytest.fixture
    def teaching_cfg(self, teaching_dir):
        """ObsConfig stub with teaching configured."""
        import config_loader as cl
        teaching = cl.TeachingConfig(courses_dir=teaching_dir)
        research = cl.ResearchConfig(teaching=teaching)
        return cl.ObsConfig(root=teaching_dir.parent, research=research)

    @pytest.fixture
    def writing_cfg(self, writing_dir):
        """ObsConfig stub with writing configured."""
        import config_loader as cl
        writing = cl.WritingConfig(manuscripts_dir=writing_dir)
        research = cl.ResearchConfig(writing=writing)
        return cl.ObsConfig(root=writing_dir.parent, research=research)

    def test_course_list_returns_table(self, mcp_mod, monkeypatch, teaching_cfg):
        monkeypatch.setattr(mcp_mod, "_load_cfg", lambda: teaching_cfg)
        result = mcp_mod.course_list()
        assert "stats101" in result
        assert "active" in result.lower()

    def test_course_show_details(self, mcp_mod, monkeypatch, teaching_cfg):
        monkeypatch.setattr(mcp_mod, "_load_cfg", lambda: teaching_cfg)
        result = mcp_mod.course_show("stats101")
        assert "Introduction to Statistics" in result or "stats101" in result
        assert "40" in result  # progress

    def test_course_lectures_lists_qmds(self, mcp_mod, monkeypatch, teaching_cfg):
        monkeypatch.setattr(mcp_mod, "_load_cfg", lambda: teaching_cfg)
        result = mcp_mod.course_lectures("stats101")
        assert "week-01" in result or "Week 1" in result

    def test_course_show_not_found(self, mcp_mod, monkeypatch, teaching_cfg):
        monkeypatch.setattr(mcp_mod, "_load_cfg", lambda: teaching_cfg)
        result = mcp_mod.course_show("nonexistent-course")
        assert "not found" in result.lower()

    def test_manuscript_list_returns_table(self, mcp_mod, monkeypatch, writing_cfg):
        monkeypatch.setattr(mcp_mod, "_load_cfg", lambda: writing_cfg)
        result = mcp_mod.manuscript_list()
        assert "mediation-paper" in result or "Causal Mediation" in result

    def test_manuscript_show_details(self, mcp_mod, monkeypatch, writing_cfg):
        monkeypatch.setattr(mcp_mod, "_load_cfg", lambda: writing_cfg)
        result = mcp_mod.manuscript_show("mediation-paper")
        assert "65" in result  # progress
        assert "active" in result.lower()

    def test_manuscript_stats_counts(self, mcp_mod, monkeypatch, writing_cfg):
        monkeypatch.setattr(mcp_mod, "_load_cfg", lambda: writing_cfg)
        result = mcp_mod.manuscript_stats()
        assert "Total manuscripts" in result
        assert "1" in result

    def test_manuscript_show_not_found(self, mcp_mod, monkeypatch, writing_cfg):
        monkeypatch.setattr(mcp_mod, "_load_cfg", lambda: writing_cfg)
        result = mcp_mod.manuscript_show("nonexistent-paper")
        assert "not found" in result.lower()

    def test_bib_check_detects_unused(self, mcp_mod, monkeypatch, writing_cfg):
        monkeypatch.setattr(mcp_mod, "_load_cfg", lambda: writing_cfg)
        result = mcp_mod.bib_check("mediation-paper")
        # jones2021 is in .bib but not cited in index.qmd
        assert "jones2021" in result or "unused" in result.lower()

    def test_bib_check_missing_key(self, mcp_mod, monkeypatch, writing_dir, writing_cfg):
        # Add a citation to a key that's not in refs.bib
        paper = writing_dir / "mediation-paper"
        (paper / "index.qmd").write_text(
            "---\ntitle: x\n---\nText [@smith2020] and [@ghost2099].\n"
        )
        monkeypatch.setattr(mcp_mod, "_load_cfg", lambda: writing_cfg)
        result = mcp_mod.bib_check("mediation-paper")
        assert "ghost2099" in result or "missing" in result.lower()

    def test_pdf_search_no_poppler(self, mcp_mod, monkeypatch, writing_cfg):
        """When pdftotext is absent, pdf_search returns install hint."""
        import config_loader as cl
        research = cl.ResearchConfig(pdf_directories=[writing_dir if False else writing_cfg.root])
        cfg = cl.ObsConfig(root=writing_cfg.root, research=research)
        monkeypatch.setattr(mcp_mod, "_load_cfg", lambda: cfg)
        with patch("research.pdf.shutil.which", return_value=None):
            result = mcp_mod.pdf_search("causal")
        assert "pdftotext" in result or "not installed" in result.lower() or "not configured" in result.lower()
