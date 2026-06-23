"""
Unit tests for mcp_server.py — all 24 MCP tools + 4 resources.

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
from unittest.mock import patch, MagicMock, AsyncMock

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


@pytest.fixture
def named_vault(mcp_mod, tmp_path):
    """A vault registered with a human-readable NAME distinct from its ID hash —
    mirrors a real `obs discover`/`scan` (name = directory basename). The shared
    obs_vault fixture registers name == id, so it can't exercise name resolution.

    Returns (vault_name, vault_id, vault_dir).
    """
    from vault_scanner import VaultScanner

    vault_dir = tmp_path / "ResearchVault"
    vault_dir.mkdir()
    (vault_dir / ".obsidian").mkdir()
    (vault_dir / ".obsidian" / "app.json").write_text("{}")
    (vault_dir / "Alpha.md").write_text("# Alpha\n\n[[Beta]]\n\n#research")
    (vault_dir / "Beta.md").write_text("# Beta\n\n[[Alpha]]")
    (vault_dir / "Lonely.md").write_text("# Lonely\n\nNo links here.")

    name = "ResearchVault"
    # 2nd positional arg is vault_name → stored name is "ResearchVault", id = hash(path)
    asyncio.run(VaultScanner(mcp_mod.db).scan_vault(str(vault_dir), name))
    vault = mcp_mod.db.get_vault_by_name_or_id(name)
    assert vault is not None and vault["name"] == name and vault["id"] != name
    return name, vault["id"], vault_dir


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
        assert "rescanned" in result.lower()
        assert "notes scanned" in result.lower()

    def test_rescan_vault_unknown(self, mcp_mod):
        result = mcp_mod.rescan_vault("ghost-vault-xyz")
        assert any(kw in result.lower() for kw in ["not found", "error"])

    def test_rescan_by_name(self, mcp_mod, named_vault):
        """Bug A guard: rescan resolves a vault NAME, not just an exact ID."""
        name, _, _ = named_vault
        result = mcp_mod.rescan_vault(name)
        assert "not found" not in result.lower()
        assert "rescanned" in result.lower()

    def test_rescan_actually_scans_not_stats(self, mcp_mod, obs_vault):
        """Bug B guard: rescan must call vault_manager.scan_vault(path, name),
        NOT shell out to the read-only `obs stats` subcommand."""
        vault_id, vault_dir, _ = obs_vault
        fake = MagicMock(vault_name=vault_dir.name, notes_scanned=5,
                         links_found=4, duration_seconds=0.1)
        scan_mock = AsyncMock(return_value=fake)
        with patch.object(mcp_mod.vault_manager, "scan_vault", scan_mock), \
                patch.object(mcp_mod, "_obs") as obs_mock:
            result = mcp_mod.rescan_vault(vault_id)
        scan_mock.assert_awaited_once()
        path_arg, name_arg = scan_mock.await_args[0][:2]
        assert str(path_arg) == str(vault_dir)
        obs_mock.assert_not_called()        # never the `stats` no-op path
        assert "notes scanned: 5" in result.lower()


# ---------------------------------------------------------------------------
# Vault resolution — Bug A regression: name / prefix must resolve, not just ID
# ---------------------------------------------------------------------------

class TestVaultResolution:
    """Every vault-taking tool must accept a vault NAME or ID PREFIX, not only
    an exact ID. Under the old db.get_vault() these silently returned
    "Vault not found" (or a misleading empty/healthy result)."""

    READ_TOOLS = [
        "get_vault_stats", "get_hub_notes", "get_orphaned_notes",
        "get_broken_links", "analyze_vault", "list_notes",
    ]

    @pytest.mark.parametrize("tool_name", READ_TOOLS)
    def test_resolve_by_name(self, mcp_mod, named_vault, tool_name):
        name, _, _ = named_vault
        result = getattr(mcp_mod, tool_name)(name)
        assert isinstance(result, str)
        assert "not found" not in result.lower()

    @pytest.mark.parametrize("tool_name", READ_TOOLS)
    def test_resolve_by_id_prefix(self, mcp_mod, named_vault, tool_name):
        _, vault_id, _ = named_vault
        result = getattr(mcp_mod, tool_name)(vault_id[:8])
        assert isinstance(result, str)
        assert "not found" not in result.lower()

    @pytest.mark.parametrize("tool_name", READ_TOOLS)
    def test_unknown_vault_still_reports_not_found(self, mcp_mod, tool_name):
        result = getattr(mcp_mod, tool_name)("definitely-not-a-vault")
        assert isinstance(result, str)
        assert any(kw in result.lower() for kw in ["not found", "error"])

    def test_create_note_by_name(self, mcp_mod, named_vault):
        name, _, _ = named_vault
        result = mcp_mod.create_note(name, "Resolved By Name", "body")
        assert "not found" not in result.lower()
        assert "created" in result.lower()

    def test_diagnose_resolves_name_to_canonical_id(self, mcp_mod, named_vault):
        """diagnose must pass the canonical id (not the raw name) to run_checks,
        whose vault layer does exact-match SQL."""
        name, vault_id, _ = named_vault
        with patch("core.doctor.run_checks", return_value=[]) as rc:
            mcp_mod.diagnose(vault_id=name)
        rc.assert_called_once()
        assert rc.call_args.kwargs.get("vault_id") == vault_id

    def test_diagnose_unknown_vault(self, mcp_mod):
        result = mcp_mod.diagnose(vault_id="no-such-vault")
        assert "not found" in result.lower() or "error" in result.lower()


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
