"""Tests for core/board.py board refresh engine."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.board import (
    AtlasConnector,
    BoardEngine,
    BoardRenderer,
    Connector,
    Merger,
    ProjectStatus,
    StatusConnector,
    VaultConnector,
    VaultWriter,
)


# ── Data model ──────────────────────────────────────────────────────────────

def test_project_status_defaults():
    p = ProjectStatus(name="foo")
    assert p.name == "foo"
    assert p.kind == "manuscript"
    assert p.progress == 0
    assert p.source == ""


# ── Atlas connector ─────────────────────────────────────────────────────────

class _CompletedProcess:
    def __init__(self, stdout: str):
        self.stdout = stdout


def test_atlas_connector_fetch(monkeypatch):
    def fake_run(cmd, **kwargs):
        kind = cmd[cmd.index("--kind") + 1]
        if kind == "manuscript":
            data = [
                {"name": "m1", "target": "JASA", "status": "active", "progress": 50, "priority": "P1", "next": "write"},
            ]
        else:
            data = [
                {"name": "p1", "target": "", "status": "planning", "progress": 10, "priority": "P2", "next": "scope"},
            ]
        return _CompletedProcess(json.dumps(data))

    monkeypatch.setattr(subprocess, "run", fake_run)
    conn = AtlasConnector(atlas_bin="atlas")
    items = conn.fetch()
    assert len(items) == 2
    manuscript = next(i for i in items if i.kind == "manuscript")
    program = next(i for i in items if i.kind == "program")
    assert manuscript.name == "m1"
    assert manuscript.venue == "JASA"
    assert manuscript.source == "atlas"
    assert program.name == "p1"


def test_atlas_connector_fetch_empty_json(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kwargs: _CompletedProcess("[]"))
    conn = AtlasConnector()
    assert conn.fetch() == []


# ── STATUS connector ────────────────────────────────────────────────────────

def test_status_connector_parses_yaml_frontmatter(tmp_path):
    proj_dir = tmp_path / "test-proj"
    proj_dir.mkdir()
    (proj_dir / ".STATUS").write_text(
        "status: active\n"
        "priority: P1\n"
        "progress: 75\n"
        "next: submit\n"
        "target: JASA\n"
        "kind: manuscript\n"
        "tasks:\n"
        "  - text: do thing\n"
        "    done: false\n",
        encoding="utf-8",
    )
    conn = StatusConnector(research_dirs=[str(tmp_path)])
    items = conn.fetch()
    assert len(items) == 1
    p = items[0]
    assert p.name == "test-proj"
    assert p.kind == "manuscript"
    assert p.status == "active"
    assert p.priority == "P1"
    assert p.progress == 75
    assert p.next_action == "submit"
    assert p.venue == "JASA"
    assert p.source == "status"


def test_status_connector_package_kind(tmp_path):
    root = tmp_path / "r-packages" / "active"
    root.mkdir(parents=True)
    pkg_dir = root / "foo"
    pkg_dir.mkdir()
    (pkg_dir / ".STATUS").write_text("status: ready\n", encoding="utf-8")
    conn = StatusConnector(research_dirs=[str(root)])
    items = conn.fetch()
    assert items[0].kind == "package"


def test_status_connector_missing_dir_is_noop():
    conn = StatusConnector(research_dirs=["/does/not/exist"])
    assert conn.fetch() == []


def test_status_connector_fallback_line_parser(tmp_path):
    proj_dir = tmp_path / "bad-yaml"
    proj_dir.mkdir()
    (proj_dir / ".STATUS").write_text(
        "status: active\n"
        "priority: P2\n"
        "progress: 42\n"
        "next: fix\n"
        "\n"
        "📦 project name\n"
        "not: yaml: ::\n",
        encoding="utf-8",
    )
    conn = StatusConnector(research_dirs=[str(tmp_path)])
    items = conn.fetch()
    assert len(items) == 1
    assert items[0].progress == 42


# ── Vault connector ─────────────────────────────────────────────────────────

@dataclass
class _FakeVault:
    id: str
    name: str
    path: str
    last_scanned: str = ""


@dataclass
class _FakeStats:
    total_notes: int = 10
    total_links: int = 5


def test_vault_connector_healthy_vault(monkeypatch, tmp_path):
    db = MagicMock()
    db.get_vaults.return_value = [_FakeVault(id="v1", name="Docs", path=str(tmp_path))]
    db.get_vault_stats.return_value = _FakeStats()
    db.execute.return_value = []

    monkeypatch.setattr("core.board.DatabaseManager", lambda db_path=None: db)
    conn = VaultConnector()
    items = conn.fetch()
    assert len(items) == 1
    assert items[0].name == "Docs"
    assert items[0].kind == "vault"
    assert items[0].status == "healthy"
    assert items[0].progress == 100
    assert items[0].next_action == ""


def test_vault_connector_drift_vault(monkeypatch, tmp_path):
    gone = tmp_path / "gone.md"
    db = MagicMock()
    db.get_vaults.return_value = [_FakeVault(id="v1", name="Docs", path=str(tmp_path), last_scanned="2024-01-01")]
    db.get_vault_stats.return_value = _FakeStats()
    db.execute.return_value = [[str(gone)]]

    monkeypatch.setattr("core.board.DatabaseManager", lambda db_path=None: db)
    conn = VaultConnector()
    items = conn.fetch()
    assert items[0].status == "drift"
    assert items[0].next_action == "prune 1 ghost(s)"


# ── Merger ──────────────────────────────────────────────────────────────────

def test_merger_deduplicates_and_prefers_atlas():
    atlas = [ProjectStatus(name="x", kind="manuscript", status="atlas-status", source="atlas")]
    status = [ProjectStatus(name="x", kind="manuscript", status="status-status", source="status")]
    merged = Merger().merge([atlas, status])
    assert len(merged) == 1
    assert merged[0].status == "atlas-status"


def test_merger_keeps_distinct_keys():
    a = [ProjectStatus(name="x", kind="manuscript", source="atlas")]
    b = [ProjectStatus(name="y", kind="manuscript", source="status")]
    merged = Merger().merge([a, b])
    assert len(merged) == 2


def test_merger_later_wins_when_neither_is_atlas():
    a = [ProjectStatus(name="x", kind="manuscript", status="a", source="status")]
    b = [ProjectStatus(name="x", kind="manuscript", status="b", source="other")]
    merged = Merger().merge([a, b])
    assert merged[0].status == "b"


# ── Renderer ────────────────────────────────────────────────────────────────

def test_renderer_includes_all_sections():
    projects = [
        ProjectStatus(name="m1", kind="manuscript", venue="JASA", status="active", progress=50, priority="P1", next_action="write"),
        ProjectStatus(name="p1", kind="program", status="planning", progress=20, priority="P2", next_action="scope"),
        ProjectStatus(name="pkg1", kind="package", status="ready", progress=100, priority="P0", next_action="submit"),
    ]
    out = BoardRenderer().render(projects)
    assert "# 🎯 Research Action Board" in out
    assert "## 🎯 Act on now" in out
    assert "### Manuscripts" in out
    assert "### Programs" in out
    assert "### Packages" in out
    assert "## 💡 Future ideas" in out
    assert "## 🔴 Threats" in out
    assert "## ⏭️ This week" in out


def test_renderer_action_ranking_prefers_ready_p0():
    projects = [
        ProjectStatus(name="done", kind="manuscript", status="complete", progress=100, priority="P0", next_action="ship"),
        ProjectStatus(name="ready", kind="manuscript", status="active", progress=75, priority="P0", next_action="submit"),
        ProjectStatus(name="new", kind="manuscript", status="planning", progress=5, priority="P0", next_action="start"),
        ProjectStatus(name="low", kind="manuscript", status="active", progress=75, priority="P2", next_action="submit"),
    ]
    actions = BoardRenderer()._pick_action_items(projects)
    names = [a.name for a in actions]
    assert "done" not in names
    assert names[0] == "ready"


def test_renderer_progress_bar():
    r = BoardRenderer()
    assert "50%" in r._progress_bar(50)
    assert r._progress_bar("bad") == "—"


def test_renderer_status_icon():
    r = BoardRenderer()
    assert r._status_icon("blocked") == "🔴"
    assert r._status_icon("active") == "🟢"
    assert r._status_icon("") == "⚪"


def test_renderer_shortens_long_text():
    r = BoardRenderer()
    assert r._shorten("short") == "short"
    long_text = "a " * 50
    assert len(r._shorten(long_text)) <= 73
    assert r._shorten(long_text).endswith("…")


# ── Vault writer ────────────────────────────────────────────────────────────

def test_writer_creates_new_file(tmp_path):
    p = tmp_path / "board.md"
    result = VaultWriter().write(str(p), "<!-- x -->\ncontent\n<!-- y -->")
    assert result["changed"] is True
    assert result["action"] == "write"
    assert p.exists()


def test_writer_overwrites_when_no_markers(tmp_path):
    p = tmp_path / "board.md"
    p.write_text("old content", encoding="utf-8")
    result = VaultWriter().write(str(p), "new content")
    assert result["changed"] is True
    assert p.read_text(encoding="utf-8") == "new content"


def test_writer_replaces_markers_preserving_surroundings(tmp_path):
    p = tmp_path / "board.md"
    p.write_text("pre\n<!-- obs:board:start -->\nold\n<!-- obs:board:end -->\npost", encoding="utf-8")
    result = VaultWriter().write(str(p), "<!-- obs:board:start -->\nnew\n<!-- obs:board:end -->\n")
    assert result["changed"] is True
    text = p.read_text(encoding="utf-8")
    assert "pre" in text
    assert "post" in text
    assert "new" in text
    assert "old" not in text


def test_writer_dry_run_does_not_write(tmp_path):
    p = tmp_path / "board.md"
    result = VaultWriter().write(str(p), "content", dry_run=True)
    assert result["action"] == "dry-run"
    assert not p.exists()


def test_writer_no_change_when_same_content(tmp_path):
    p = tmp_path / "board.md"
    VaultWriter().write(str(p), "content")
    result = VaultWriter().write(str(p), "content")
    assert result["changed"] is False


# ── Engine ──────────────────────────────────────────────────────────────────

def test_engine_refresh_writes_board(tmp_path, monkeypatch):
    vault = _FakeVault(id="v1", name="Docs", path=str(tmp_path))
    vm = MagicMock()
    vm.get_vault.return_value = vault
    vm.list_vaults.return_value = [vault]

    engine = BoardEngine(vault_manager=vm)
    # Avoid external connectors by patching collect to return a known list.
    monkeypatch.setattr(engine, "_collect_projects", lambda: [
        ProjectStatus(name="m1", kind="manuscript", status="active", progress=50, priority="P1", next_action="write"),
    ])

    result = engine.refresh("v1")
    assert "error" not in result
    assert result["changed"] is True
    board_path = tmp_path / "Engineering" / "_ACTION-BOARD.md"
    assert board_path.exists()
    text = board_path.read_text(encoding="utf-8")
    assert "# 🎯 Research Action Board" in text


def test_engine_refresh_unknown_vault():
    vm = MagicMock()
    vm.get_vault.return_value = None
    engine = BoardEngine(vault_manager=vm)
    result = engine.refresh("missing")
    assert "error" in result
    assert result["changed"] is False


def test_engine_status_existing_board(tmp_path, monkeypatch):
    vault = _FakeVault(id="v1", name="Docs", path=str(tmp_path))
    board_path = tmp_path / "Engineering" / "_ACTION-BOARD.md"
    board_path.parent.mkdir(parents=True)
    board_path.write_text("<!-- obs:board:start -->\n> generated: 2026-01-01\n<!-- obs:board:end -->", encoding="utf-8")

    vm = MagicMock()
    vm.get_vault.return_value = vault
    engine = BoardEngine(vault_manager=vm)
    monkeypatch.setattr(engine, "_has_drift", lambda vault_id: False)

    result = engine.status("v1")
    assert result["board_exists"] is True
    assert result["last_refreshed_days_ago"] >= 100


def test_engine_status_missing_board(tmp_path, monkeypatch):
    vault = _FakeVault(id="v1", name="Docs", path=str(tmp_path))
    vm = MagicMock()
    vm.get_vault.return_value = vault
    engine = BoardEngine(vault_manager=vm)
    monkeypatch.setattr(engine, "_has_drift", lambda vault_id: True)

    result = engine.status("v1")
    assert result["board_exists"] is False
    assert result["drift"] is True


def test_engine_resolve_prefers_research_subdirectory(tmp_path):
    vault = _FakeVault(id="v1", name="Docs", path=str(tmp_path))
    research = tmp_path / "Research"
    research.mkdir()
    engine = BoardEngine(vault_manager=MagicMock())
    resolved = engine._resolve_board_path(vault)
    assert resolved == tmp_path / "Research" / "00_meta" / "_ACTION-BOARD.md"


def test_engine_resolve_falls_back_to_vault_root(tmp_path):
    vault = _FakeVault(id="v1", name="Docs", path=str(tmp_path))
    engine = BoardEngine(vault_manager=MagicMock())
    resolved = engine._resolve_board_path(vault)
    assert resolved == tmp_path / "Engineering" / "_ACTION-BOARD.md"
