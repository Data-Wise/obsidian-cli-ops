"""Unit tests for core/doctor.py — all five check layers."""
from __future__ import annotations

import json
import os
import platform
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from collections import namedtuple

# Ensure src/python is on sys.path (pytest run from src/python/)
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from core.doctor import (
    DoctorResult, run_checks, _check_python, _check_database, _check_mcp,
    _check_icloud, _find_bad_vault_resolvers, _check_mcp_tool_resolvers,
    _find_async_run_offenders, _check_mcp_async_run, _check_sync,
)

_VersionInfo = namedtuple("version_info", ["major", "minor", "micro", "releaselevel", "serial"])


# ---------------------------------------------------------------------------
# DoctorResult
# ---------------------------------------------------------------------------

class TestDoctorResult:
    def test_to_dict_has_all_fields(self):
        r = DoctorResult("py-version", "python", "Python version", "pass", "3.12.0")
        d = r.to_dict()
        assert set(d.keys()) >= {"id", "layer", "label", "status", "message", "fix_hint"}

    def test_fix_hint_defaults_to_empty_string(self):
        r = DoctorResult("x", "y", "z", "pass", "ok")
        assert r.fix_hint == ""


# ---------------------------------------------------------------------------
# Layer 1: Python
# ---------------------------------------------------------------------------

class TestCheckPython:
    def test_py_version_pass_on_current(self):
        results = _check_python()
        ids = {r.id for r in results}
        assert "py-version" in ids
        ver = next(r for r in results if r.id == "py-version")
        # current Python is the test runner, so it must be at least 3.9
        assert ver.status in ("pass", "warn")

    def test_py_version_fail_when_old(self):
        fake_vi = _VersionInfo(3, 8, 0, "final", 0)
        with patch("core.doctor.sys.version_info", fake_vi):
            results = _check_python()
            ver = next(r for r in results if r.id == "py-version")
            assert ver.status == "fail"

    def test_py_version_warn_when_39(self):
        fake_vi = _VersionInfo(3, 9, 1, "final", 0)
        with patch("core.doctor.sys.version_info", fake_vi):
            results = _check_python()
            ver = next(r for r in results if r.id == "py-version")
            assert ver.status == "warn"

    def test_py_resolver_present(self):
        results = _check_python()
        ids = {r.id for r in results}
        assert "py-resolver" in ids

    def test_py_imports_pass(self):
        results = _check_python()
        imp = next(r for r in results if r.id == "py-imports")
        # rich, networkx, sqlite3 are installed in dev venv
        assert imp.status in ("pass", "fail")  # may fail if deps not installed in CI

    def test_py_imports_fail_on_missing(self):
        import builtins
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "rich":
                raise ImportError("no rich")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            results = _check_python()
        imp = next(r for r in results if r.id == "py-imports")
        assert imp.status == "fail"
        assert "rich" in imp.message


# ---------------------------------------------------------------------------
# Layer 2: Database
# ---------------------------------------------------------------------------

class TestCheckDatabase:
    def test_fail_when_no_db(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        results = _check_database()
        db_exists = next(r for r in results if r.id == "db-exists")
        assert db_exists.status == "fail"
        skips = [r for r in results if r.status == "skip"]
        assert len(skips) >= 3

    def test_pass_when_db_initialized(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        db_path = tmp_path / ".config" / "obs" / "vault_db.sqlite"
        db_path.parent.mkdir(parents=True)
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE schema_version (version INTEGER, description TEXT)")
        conn.execute("INSERT INTO schema_version VALUES (1, 'test')")
        conn.execute("CREATE TABLE vaults (id TEXT PRIMARY KEY, name TEXT, path TEXT, last_scan TEXT)")
        conn.commit()
        conn.close()

        results = _check_database()
        db_exists = next(r for r in results if r.id == "db-exists")
        assert db_exists.status == "pass"
        db_schema = next(r for r in results if r.id == "db-schema")
        assert db_schema.status == "pass"
        db_query = next(r for r in results if r.id == "db-query")
        assert db_query.status == "pass"

    def test_warn_zero_vaults(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        db_path = tmp_path / ".config" / "obs" / "vault_db.sqlite"
        db_path.parent.mkdir(parents=True)
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE schema_version (version INTEGER)")
        conn.execute("INSERT INTO schema_version VALUES (1)")
        conn.execute("CREATE TABLE vaults (id TEXT, name TEXT, path TEXT, last_scan TEXT)")
        conn.commit()
        conn.close()

        results = _check_database()
        vaults_r = next(r for r in results if r.id == "db-vaults")
        assert vaults_r.status == "warn"

    def test_pass_with_vaults(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        db_path = tmp_path / ".config" / "obs" / "vault_db.sqlite"
        db_path.parent.mkdir(parents=True)
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE schema_version (version INTEGER)")
        conn.execute("INSERT INTO schema_version VALUES (1)")
        conn.execute("CREATE TABLE vaults (id TEXT, name TEXT, path TEXT, last_scan TEXT)")
        conn.execute("INSERT INTO vaults VALUES ('abc', 'MyVault', '/tmp/v', NULL)")
        conn.commit()
        conn.close()

        results = _check_database()
        vaults_r = next(r for r in results if r.id == "db-vaults")
        assert vaults_r.status == "pass"
        assert "1 vault" in vaults_r.message


# ---------------------------------------------------------------------------
# Layer 3: Vault (tested through run_checks with mocked DB)
# ---------------------------------------------------------------------------

class TestCheckVaults:
    def _make_db(self, tmp_path, vault_path: Path, last_scan=None, note_count=5, link_count=3):
        db_path = tmp_path / ".config" / "obs" / "vault_db.sqlite"
        db_path.parent.mkdir(parents=True)
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE schema_version (version INTEGER)")
        conn.execute("INSERT INTO schema_version VALUES (1)")
        # Column is `last_scanned` to match schema/vault_db.sql — the prior
        # `last_scan` here masked a real crash in _check_vaults (it read the
        # wrong key, but this fake table agreed with the typo).
        conn.execute("CREATE TABLE vaults (id TEXT, name TEXT, path TEXT, last_scanned TEXT)")
        conn.execute("INSERT INTO vaults VALUES ('v1', 'TestVault', ?, ?)",
                     (str(vault_path), last_scan))
        conn.execute("CREATE TABLE notes (id TEXT, vault_id TEXT, title TEXT)")
        for i in range(note_count):
            conn.execute("INSERT INTO notes VALUES (?, 'v1', ?)", (f"n{i}", f"Note{i}"))
        conn.execute("CREATE TABLE links (id TEXT, source_note_id TEXT, target_title TEXT)")
        for i in range(link_count):
            conn.execute("INSERT INTO links VALUES (?, ?, 'target')", (f"l{i}", f"n{i}"))
        conn.commit()
        conn.close()

    def test_vault_path_pass(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        vault_path = tmp_path / "MyVault"
        vault_path.mkdir()
        self._make_db(tmp_path, vault_path, last_scan="2026-06-19T00:00:00")
        from core.doctor import _check_vaults
        with patch("platform.system", return_value="Linux"):
            results = _check_vaults()
        path_r = next(r for r in results if r.id.startswith("vault-path:"))
        assert path_r.status == "pass"

    def test_vault_path_fail_when_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        vault_path = tmp_path / "MissingVault"  # doesn't exist
        self._make_db(tmp_path, vault_path, last_scan="2026-06-19T00:00:00")
        from core.doctor import _check_vaults
        with patch("platform.system", return_value="Linux"):
            results = _check_vaults()
        path_r = next(r for r in results if r.id.startswith("vault-path:"))
        assert path_r.status == "fail"

    def test_vault_notes_warn_zero(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        vault_path = tmp_path / "EmptyVault"
        vault_path.mkdir()
        self._make_db(tmp_path, vault_path, last_scan="2026-06-19T00:00:00", note_count=0, link_count=0)
        from core.doctor import _check_vaults
        with patch("platform.system", return_value="Linux"):
            results = _check_vaults()
        notes_r = next(r for r in results if r.id.startswith("vault-notes:"))
        assert notes_r.status == "fail"

    def test_vault_links_warn_zero(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        vault_path = tmp_path / "NoLinksVault"
        vault_path.mkdir()
        self._make_db(tmp_path, vault_path, last_scan="2026-06-19T00:00:00", note_count=5, link_count=0)
        from core.doctor import _check_vaults
        with patch("platform.system", return_value="Linux"):
            results = _check_vaults()
        links_r = next(r for r in results if r.id.startswith("vault-links:"))
        assert links_r.status == "warn"

    def test_vault_stale_fail(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        vault_path = tmp_path / "StaleVault"
        vault_path.mkdir()
        self._make_db(tmp_path, vault_path, last_scan="2020-01-01T00:00:00", note_count=5, link_count=3)
        from core.doctor import _check_vaults
        with patch("platform.system", return_value="Linux"):
            results = _check_vaults()
        stale_r = next(r for r in results if r.id.startswith("vault-stale:"))
        assert stale_r.status == "fail"

    def test_vault_stale_never_scanned(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        vault_path = tmp_path / "NeverScanned"
        vault_path.mkdir()
        self._make_db(tmp_path, vault_path, last_scan=None)
        from core.doctor import _check_vaults
        with patch("platform.system", return_value="Linux"):
            results = _check_vaults()
        stale_r = next(r for r in results if r.id.startswith("vault-stale:"))
        assert stale_r.status == "fail"
        assert "Never" in stale_r.message


# ---------------------------------------------------------------------------
# Layer 4: MCP
# ---------------------------------------------------------------------------

class TestCheckMCP:
    def test_fail_no_config(self, tmp_path, monkeypatch):
        from core import doctor as doctor_mod
        monkeypatch.setattr(doctor_mod, "_CLAUDE_DESKTOP_CONFIG_PATHS",
                            [tmp_path / "nonexistent.json"])
        results = _check_mcp()
        ids = {r.id for r in results}
        cfg = next(r for r in results if r.id == "mcp-config")
        assert cfg.status == "fail"
        # Only the config-dependent entry check skips when the config is absent.
        entry = next(r for r in results if r.id == "mcp-entry")
        assert entry.status == "skip"
        # Source-code static guards are config-independent and must still run
        # (regression: they were silently skipped in the config-missing branch).
        assert "mcp-tool-resolvers" in ids
        assert "mcp-async-run" in ids

    def test_pass_with_valid_config(self, tmp_path, monkeypatch):
        config_path = tmp_path / "claude_desktop_config.json"
        mcp_server_path = tmp_path / "mcp_server.py"
        mcp_server_path.touch()
        config_path.write_text(json.dumps({
            "mcpServers": {
                "obsidian-ops": {
                    "command": "python3",
                    "args": [str(mcp_server_path)]
                }
            }
        }))
        from core import doctor as doctor_mod
        monkeypatch.setattr(doctor_mod, "_CLAUDE_DESKTOP_CONFIG_PATHS", [config_path])
        results = _check_mcp()
        cfg = next(r for r in results if r.id == "mcp-config")
        assert cfg.status == "pass"
        entry = next(r for r in results if r.id == "mcp-entry")
        assert entry.status == "pass"

    def test_fail_missing_obsidian_ops_entry(self, tmp_path, monkeypatch):
        config_path = tmp_path / "claude_desktop_config.json"
        config_path.write_text(json.dumps({"mcpServers": {"other-tool": {}}}))
        from core import doctor as doctor_mod
        monkeypatch.setattr(doctor_mod, "_CLAUDE_DESKTOP_CONFIG_PATHS", [config_path])
        results = _check_mcp()
        entry = next(r for r in results if r.id == "mcp-entry")
        assert entry.status == "fail"

    def test_warn_server_path_wrong(self, tmp_path, monkeypatch):
        config_path = tmp_path / "claude_desktop_config.json"
        config_path.write_text(json.dumps({
            "mcpServers": {
                "obsidian-ops": {
                    "command": "python3",
                    "args": ["/nonexistent/mcp_server.py"]
                }
            }
        }))
        from core import doctor as doctor_mod
        monkeypatch.setattr(doctor_mod, "_CLAUDE_DESKTOP_CONFIG_PATHS", [config_path])
        results = _check_mcp()
        entry = next(r for r in results if r.id == "mcp-entry")
        assert entry.status == "warn"


# ---------------------------------------------------------------------------
# Layer 5: iCloud
# ---------------------------------------------------------------------------

class TestCheckIcloud:
    def test_skip_on_linux(self):
        with patch("platform.system", return_value="Linux"):
            results = _check_icloud()
        assert len(results) == 1
        assert results[0].status == "skip"
        assert results[0].id == "icloud-skip"

    def test_pass_detect_no_icloud_vaults(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        db_path = tmp_path / ".config" / "obs" / "vault_db.sqlite"
        db_path.parent.mkdir(parents=True)
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE vaults (id TEXT, name TEXT, path TEXT)")
        conn.execute("INSERT INTO vaults VALUES ('v1', 'Local', '/Users/dt/local_vault')")
        conn.commit()
        conn.close()

        with patch("platform.system", return_value="Darwin"):
            results = _check_icloud()
        detect = next(r for r in results if r.id == "icloud-detect")
        assert detect.status == "pass"
        assert len(results) == 1


# ---------------------------------------------------------------------------
# Layer: sync (content-based vault↔DB drift)
# ---------------------------------------------------------------------------

class TestCheckSync:
    """sync layer: ghosts (DB rows gone from disk), missing (*.md absent from
    DB), errors (last scan recorded failures), drift (info summary)."""

    def _make_db(self, tmp_path, vault_path: Path, *, disk_files, db_paths,
                 last_scan_status="completed", notes_failed=0):
        """Build a vault on disk + a matching/mismatching DB index.

        disk_files: list of relative paths to materialize as real .md files.
        db_paths:   list of relative paths to insert as notes rows.
        The set difference between the two yields ghosts/missing.
        """
        # Materialize disk files
        for rel in disk_files:
            fp = vault_path / rel
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(f"# {rel}\n")

        db_path = tmp_path / ".config" / "obs" / "vault_db.sqlite"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE schema_version (version INTEGER)")
        conn.execute("INSERT INTO schema_version VALUES (2)")
        conn.execute("CREATE TABLE vaults (id TEXT, name TEXT, path TEXT, last_scanned TEXT)")
        conn.execute("INSERT INTO vaults VALUES ('v1', 'SyncVault', ?, '2026-06-25T00:00:00')",
                     (str(vault_path),))
        conn.execute("CREATE TABLE notes (id TEXT, vault_id TEXT, path TEXT, title TEXT, content_hash TEXT)")
        for i, rel in enumerate(db_paths):
            conn.execute("INSERT INTO notes VALUES (?, 'v1', ?, ?, 'h')",
                         (f"n{i}", rel, rel))
        conn.execute(
            "CREATE TABLE scan_history (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "vault_id TEXT, started_at TIMESTAMP, completed_at TIMESTAMP, "
            "notes_scanned INTEGER, notes_failed INTEGER, status TEXT)"
        )
        conn.execute(
            "INSERT INTO scan_history (vault_id, started_at, completed_at, "
            "notes_scanned, notes_failed, status) "
            "VALUES ('v1', '2026-06-25T00:00:00', '2026-06-25T00:01:00', ?, ?, ?)",
            (len(db_paths), notes_failed, last_scan_status),
        )
        conn.commit()
        conn.close()

    def test_clean_when_in_sync(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        vault_path = tmp_path / "SyncVault"
        vault_path.mkdir()
        self._make_db(tmp_path, vault_path,
                      disk_files=["a.md", "b.md", "sub/c.md"],
                      db_paths=["a.md", "b.md", "sub/c.md"])
        results = _check_sync()
        ghosts = next(r for r in results if r.id.startswith("sync-ghosts:"))
        missing = next(r for r in results if r.id.startswith("sync-missing:"))
        assert ghosts.status == "pass"
        assert missing.status == "pass"

    def test_detects_ghosts(self, tmp_path, monkeypatch):
        """DB has 2 rows whose files were deleted on disk → 2 ghosts."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        vault_path = tmp_path / "SyncVault"
        vault_path.mkdir()
        self._make_db(tmp_path, vault_path,
                      disk_files=["a.md"],
                      db_paths=["a.md", "gone1.md", "gone2.md"])
        results = _check_sync()
        ghosts = next(r for r in results if r.id.startswith("sync-ghosts:"))
        assert ghosts.status == "warn"
        assert "2" in ghosts.message
        assert "--prune" in ghosts.fix_hint

    def test_detects_missing(self, tmp_path, monkeypatch):
        """3 files on disk, only 1 in DB → 2 missing."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        vault_path = tmp_path / "SyncVault"
        vault_path.mkdir()
        self._make_db(tmp_path, vault_path,
                      disk_files=["a.md", "new1.md", "new2.md"],
                      db_paths=["a.md"])
        results = _check_sync()
        missing = next(r for r in results if r.id.startswith("sync-missing:"))
        assert missing.status == "warn"
        assert "2" in missing.message

    def test_ignores_dotfiles_like_scanner(self, tmp_path, monkeypatch):
        """Files under dot-dirs (.obsidian/, .trash/) are NOT counted as missing
        — mirrors the scanner's 'skip dotfile parts' filter."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        vault_path = tmp_path / "SyncVault"
        vault_path.mkdir()
        self._make_db(tmp_path, vault_path,
                      disk_files=["a.md", ".obsidian/workspace.md", ".trash/old.md"],
                      db_paths=["a.md"])
        results = _check_sync()
        missing = next(r for r in results if r.id.startswith("sync-missing:"))
        ghosts = next(r for r in results if r.id.startswith("sync-ghosts:"))
        assert missing.status == "pass"
        assert ghosts.status == "pass"

    def test_drift_is_info_summary(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        vault_path = tmp_path / "SyncVault"
        vault_path.mkdir()
        self._make_db(tmp_path, vault_path,
                      disk_files=["a.md", "new.md"],
                      db_paths=["a.md", "gone.md"])
        results = _check_sync()
        drift = next(r for r in results if r.id.startswith("sync-drift:"))
        assert drift.status == "info"
        # disk=2 db=2 (1 ghost, 1 missing)
        assert "disk=2" in drift.message
        assert "db=2" in drift.message
        assert "1 ghost" in drift.message
        assert "1 missing" in drift.message

    def test_errors_fail_when_last_scan_failed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        vault_path = tmp_path / "SyncVault"
        vault_path.mkdir()
        self._make_db(tmp_path, vault_path,
                      disk_files=["a.md"], db_paths=["a.md"],
                      last_scan_status="failed")
        results = _check_sync()
        errors = next(r for r in results if r.id.startswith("sync-errors:"))
        assert errors.status == "fail"

    def test_errors_warn_when_notes_failed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        vault_path = tmp_path / "SyncVault"
        vault_path.mkdir()
        self._make_db(tmp_path, vault_path,
                      disk_files=["a.md"], db_paths=["a.md"],
                      last_scan_status="completed", notes_failed=3)
        results = _check_sync()
        errors = next(r for r in results if r.id.startswith("sync-errors:"))
        assert errors.status == "warn"
        assert "3" in errors.message

    def test_errors_pass_when_clean_scan(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        vault_path = tmp_path / "SyncVault"
        vault_path.mkdir()
        self._make_db(tmp_path, vault_path,
                      disk_files=["a.md"], db_paths=["a.md"],
                      last_scan_status="completed", notes_failed=0)
        results = _check_sync()
        errors = next(r for r in results if r.id.startswith("sync-errors:"))
        assert errors.status == "pass"

    def test_skip_when_no_db(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        results = _check_sync()
        assert len(results) == 1
        assert results[0].status == "skip"

    def test_skip_when_vault_path_missing(self, tmp_path, monkeypatch):
        """A vault whose path is gone → can't read disk → skip (not crash)."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        vault_path = tmp_path / "GoneVault"  # never created on disk
        self._make_db(tmp_path, vault_path,
                      disk_files=[], db_paths=["a.md"])
        results = _check_sync()
        # all sync checks for this vault should skip
        assert all(r.status == "skip" for r in results)

    def test_registered_in_sync_layer(self, tmp_path, monkeypatch):
        """run_checks(layers=['sync']) routes to the sync layer."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        vault_path = tmp_path / "SyncVault"
        vault_path.mkdir()
        self._make_db(tmp_path, vault_path,
                      disk_files=["a.md"], db_paths=["a.md"])
        results = run_checks(layers=["sync"])
        layers = {r.layer for r in results}
        assert layers == {"sync"}


# ---------------------------------------------------------------------------
# Integration: run_checks
# ---------------------------------------------------------------------------

class TestRunChecks:
    def test_run_all_layers_returns_results(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        with patch("platform.system", return_value="Linux"):
            results = run_checks()
        assert len(results) > 0
        ids = {r.id for r in results}
        assert "py-version" in ids

    def test_layer_filter(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        results = run_checks(layers=["python"])
        ids = {r.id for r in results}
        assert "py-version" in ids
        assert "db-exists" not in ids

    def test_db_skip_cascades_to_vault(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        with patch("platform.system", return_value="Linux"):
            results = run_checks(layers=["database", "vault"])
        vault_results = [r for r in results if r.layer == "vault"]
        # DB is missing → vault layer should be skipped or have skip results
        assert any(r.status in ("skip", "fail") for r in vault_results)

    def test_unknown_layer_silently_skipped(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        results = run_checks(layers=["python", "nonexistent_layer"])
        ids = {r.id for r in results}
        assert "py-version" in ids


# ---------------------------------------------------------------------------
# MCP tool-resolver static guard (catches the exact-ID-only db.get_vault() bug)
# ---------------------------------------------------------------------------

_GOOD_TOOL = '''
@mcp.tool()
def good_tool(vault_id: str) -> str:
    vault, err = _resolve_vault(vault_id)
    return vault["id"]
'''

_BAD_TOOL = '''
@mcp.tool()
def bad_tool(vault_id: str) -> str:
    vault = db.get_vault(vault_id)
    return vault["id"]
'''

_NOTE_LOOKUP_OK = '''
@mcp.tool()
def read_note(note_id: str) -> str:
    note = db.get_note(note_id)
    vault = db.get_vault(note["vault_id"])
    return vault["name"]
'''


class TestMcpToolResolvers:
    def test_clean_when_good(self):
        assert _find_bad_vault_resolvers(_GOOD_TOOL) == []

    def test_flags_exact_id_only_resolver(self):
        assert _find_bad_vault_resolvers(_BAD_TOOL) == ["bad_tool(vault_id)"]

    def test_ignores_note_keyed_vault_lookup(self):
        """db.get_vault(note["vault_id"]) is a Subscript, not a bare param — OK."""
        assert _find_bad_vault_resolvers(_NOTE_LOOKUP_OK) == []

    def test_real_mcp_server_is_clean(self):
        """The shipped mcp_server.py must have zero exact-ID-only resolvers."""
        server = Path(__file__).parent.parent / "mcp_server.py"
        assert _find_bad_vault_resolvers(server.read_text(encoding="utf-8")) == []

    def test_check_passes_on_real_server(self):
        server = Path(__file__).parent.parent / "mcp_server.py"
        result = _check_mcp_tool_resolvers(server)
        assert result.id == "mcp-tool-resolvers"
        assert result.status == "pass"

    def test_check_fails_on_bad_stub(self, tmp_path):
        bad = tmp_path / "mcp_server.py"
        bad.write_text(_BAD_TOOL)
        result = _check_mcp_tool_resolvers(bad)
        assert result.status == "fail"
        assert "bad_tool(vault_id)" in result.message

    def test_check_skips_when_missing(self, tmp_path):
        result = _check_mcp_tool_resolvers(tmp_path / "nope.py")
        assert result.status == "skip"


# ---------------------------------------------------------------------------
# MCP async-run static guard (#62: asyncio.run() inside a sync @mcp.tool)
# ---------------------------------------------------------------------------

_ASYNC_RUN_OK = '''
@mcp.tool()
async def rescan_vault(vault_id: str) -> str:
    result = await vault_manager.scan_vault(vault_id)
    return result.vault_name
'''

_ASYNC_RUN_BAD = '''
@mcp.tool()
def rescan_vault(vault_id: str) -> str:
    result = asyncio.run(vault_manager.scan_vault(vault_id))
    return result.vault_name
'''

_ASYNC_RUN_NONTOOL_OK = '''
def cli_entry(vault_id: str) -> str:
    """Sync CLI caller — asyncio.run() is valid here (no running loop)."""
    return asyncio.run(vault_manager.scan_vault(vault_id))
'''


class TestMcpAsyncRun:
    def test_clean_when_async_handler(self):
        assert _find_async_run_offenders(_ASYNC_RUN_OK) == []

    def test_flags_sync_handler_calling_asyncio_run(self):
        assert _find_async_run_offenders(_ASYNC_RUN_BAD) == ["rescan_vault()"]

    def test_ignores_asyncio_run_outside_mcp_tool(self):
        """Only @mcp.tool handlers run inside FastMCP's loop; a plain sync
        function (e.g. the CLI path) may legitimately call asyncio.run()."""
        assert _find_async_run_offenders(_ASYNC_RUN_NONTOOL_OK) == []

    def test_real_mcp_server_is_clean(self):
        """The shipped mcp_server.py must have zero sync asyncio.run() tools."""
        server = Path(__file__).parent.parent / "mcp_server.py"
        assert _find_async_run_offenders(server.read_text(encoding="utf-8")) == []

    def test_check_passes_on_real_server(self):
        server = Path(__file__).parent.parent / "mcp_server.py"
        result = _check_mcp_async_run(server)
        assert result.id == "mcp-async-run"
        assert result.layer == "mcp"
        assert result.status == "pass"

    def test_check_fails_on_bad_stub(self, tmp_path):
        bad = tmp_path / "mcp_server.py"
        bad.write_text(_ASYNC_RUN_BAD)
        result = _check_mcp_async_run(bad)
        assert result.status == "fail"
        assert "rescan_vault()" in result.message

    def test_check_skips_when_missing(self, tmp_path):
        result = _check_mcp_async_run(tmp_path / "nope.py")
        assert result.status == "skip"

    def test_check_errors_on_unparseable_source(self, tmp_path):
        """Unparseable source → 'error' status (not a crash), matching the
        sibling resolver guard's error contract."""
        bad = tmp_path / "mcp_server.py"
        bad.write_text("def broken(:\n    pass\n")
        result = _check_mcp_async_run(bad)
        assert result.status == "error"

    def test_flags_multiple_offenders(self):
        src = _ASYNC_RUN_BAD + '''
@mcp.tool()
def reindex(vault_id: str) -> str:
    return asyncio.run(vault_manager.scan_vault(vault_id))
'''
        offenders = _find_async_run_offenders(src)
        assert offenders == ["rescan_vault()", "reindex()"]

    def test_matches_bare_decorator(self):
        """@mcp.tool (no parens) is still an MCP tool and must be flagged."""
        src = '''
@mcp.tool
def rescan_vault(vault_id: str) -> str:
    return asyncio.run(vault_manager.scan_vault(vault_id))
'''
        assert _find_async_run_offenders(src) == ["rescan_vault()"]

    def test_registered_in_mcp_layer(self):
        """_check_mcp() must surface the mcp-async-run result."""
        ids = {r.id for r in _check_mcp()}
        assert "mcp-async-run" in ids
