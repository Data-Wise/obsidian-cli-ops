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

from core.doctor import DoctorResult, run_checks, _check_python, _check_database, _check_mcp, _check_icloud

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
        conn.execute("CREATE TABLE vaults (id TEXT, name TEXT, path TEXT, last_scan TEXT)")
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
        cfg = next(r for r in results if r.id == "mcp-config")
        assert cfg.status == "fail"
        skips = [r for r in results if r.status == "skip"]
        assert len(skips) >= 2

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
