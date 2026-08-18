"""Tests for obs research board — the deterministic renderer + marker writer (SPEC-obs)."""
import json
import subprocess
from unittest.mock import patch

import pytest

from research.research_board import (
    MARKER_END,
    MARKER_START,
    AtlasIntegrationError,
    build_block,
    format_warnings,
    load_projects,
    load_research_projects,
    progress_bar,
    rank,
    render_action_board,
    status_icon,
    write_marked_block,
)

FIX = [
    {"name": "collider", "kind": "manuscript", "status": "revise & resubmit",
     "progress": 95, "target": "AMPPS", "next": "upload rev1", "priority": "P0"},
    {"name": "product of three", "kind": "manuscript", "status": "draft",
     "progress": 95, "target": "JASA", "next": "final proofread", "priority": "P1"},
    {"name": "pmed-modern", "kind": "program", "status": "active",
     "progress": 92, "target": "Epidemiology", "next": "advance 05", "priority": "P1", "taskCount": 5},
    {"name": "medfit", "kind": "package", "status": "active",
     "progress": 100, "target": None, "next": "CRAN", "priority": "P0", "cranState": "planned"},
]


def test_render_is_deterministic():
    assert render_action_board(FIX) == render_action_board(list(reversed(FIX)))


def test_render_has_sections_and_no_timestamp():
    out = render_action_board(FIX)
    assert "## 🎯 Research Action Board" in out
    assert "### Manuscripts" in out
    assert "### Programs" in out
    assert "### Packages" in out
    assert "🔴 revise & resubmit" in out
    assert "AMPPS" in out
    assert "generated" not in out.lower()


# ── package-kind rows: CRAN-state column instead of venue (item 3) ──

def test_package_row_uses_cran_column_not_venue():
    out = render_action_board(FIX)
    assert "| Package | CRAN | Status | Progress | Next |" in out
    assert "🔜 planned" in out  # medfit's cranState badge


def test_package_with_no_cran_state_shows_em_dash():
    projects = FIX + [{"name": "missingmed", "kind": "package", "status": "active", "progress": 100}]
    out = render_action_board(projects)
    lines = [ln for ln in out.splitlines() if ln.startswith("| missingmed")]
    assert lines and "| — |" in lines[0]


def test_other_kind_still_gets_its_own_section():
    projects = FIX + [{"name": "some-tool", "kind": "tool", "status": "active", "progress": 50}]
    out = render_action_board(projects)
    assert "### Other" in out
    assert "| Project | Venue | Status | Progress | Next |" in out


def test_progress_bar():
    assert progress_bar(0) == "░░░░░░░░ 0%"
    assert progress_bar(100) == "████████ 100%"
    assert progress_bar(None) == "—"


def test_status_icon():
    assert status_icon("revise & resubmit") == "🔴"
    assert status_icon("active") == "🟢"
    assert status_icon("paused") == "🟡"
    assert status_icon("weird") == "⚪"


def test_rank_order_p0_then_progress():
    names = [p["name"] for p in rank(FIX)]
    assert names.index("medfit") < names.index("product of three")  # P0 before P1
    assert names.index("medfit") < names.index("collider")          # P0 100% before P0 95%


def test_write_is_idempotent(tmp_path):
    f = tmp_path / "board.md"
    blk = build_block(FIX)
    assert write_marked_block(f, blk)["changed"] is True
    assert write_marked_block(f, blk)["changed"] is False  # zero diff on unchanged state


def test_write_preserves_out_of_marker_prose(tmp_path):
    f = tmp_path / "board.md"
    f.write_text(f"# Notes\n\nHand prose.\n\n{MARKER_START}\nOLD\n{MARKER_END}\n\nMore prose.\n")
    write_marked_block(f, build_block(FIX))
    text = f.read_text()
    assert "Hand prose." in text
    assert "More prose." in text
    assert "OLD" not in text       # marker region replaced
    assert "collider" in text       # new content present


def test_dry_run_writes_nothing(tmp_path):
    f = tmp_path / "board.md"
    res = write_marked_block(f, build_block(FIX), dry_run=True)
    assert res["action"] == "dry-run"
    assert res["changed"] is True
    assert not f.exists()


# ── atlas integration error handling (SPEC-cross-repo-research-ops-integration-2026-07-16, item 4) ──

def _completed(stdout: str) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=["atlas"], returncode=0, stdout=stdout, stderr="")


def test_load_projects_returns_data_on_success():
    with patch("subprocess.run", return_value=_completed(json.dumps(FIX))):
        assert load_projects(kind="manuscript") == FIX


def test_load_projects_raises_atlas_integration_error_on_missing_binary():
    with patch("subprocess.run", side_effect=FileNotFoundError("no such file")):
        with pytest.raises(AtlasIntegrationError, match="atlas binary not found"):
            load_projects(kind="manuscript")


def test_load_projects_raises_atlas_integration_error_on_nonzero_exit():
    err = subprocess.CalledProcessError(returncode=1, cmd=["atlas"], stderr="boom")
    with patch("subprocess.run", side_effect=err):
        with pytest.raises(AtlasIntegrationError, match="exited 1"):
            load_projects(kind="manuscript")


def test_load_projects_raises_atlas_integration_error_on_malformed_json():
    with patch("subprocess.run", return_value=_completed("not json {{{")):
        with pytest.raises(AtlasIntegrationError, match="invalid JSON"):
            load_projects(kind="manuscript")


def test_load_research_projects_degrades_to_partial_data_on_one_kind_failure():
    """One kind's atlas call fails (deliberately broken, per spec acceptance) — the
    other kinds' data still comes back, with a warning naming the failure."""
    def side_effect(cmd, **kwargs):
        if "manuscript" in cmd:
            raise subprocess.CalledProcessError(returncode=1, cmd=cmd, stderr="atlas is down")
        if "program" in cmd:
            return _completed(json.dumps([FIX[2]]))  # pmed-modern, kind=program
        return _completed(json.dumps([FIX[3]]))  # medfit, kind=package

    with patch("subprocess.run", side_effect=side_effect):
        items, warnings = load_research_projects()

    assert items == [FIX[2], FIX[3]]
    assert len(warnings) == 1
    assert "manuscript" in warnings[0]
    assert "atlas is down" in warnings[0]


def test_load_research_projects_fetches_package_kind_too():
    """Item 3 acceptance: load_research_projects is no longer hardcoded to
    manuscript+program only — package-kind projects reach the renderer."""
    def side_effect(cmd, **kwargs):
        if "package" in cmd:
            return _completed(json.dumps([FIX[3]]))
        return _completed("[]")

    with patch("subprocess.run", side_effect=side_effect):
        items, warnings = load_research_projects()

    assert items == [FIX[3]]
    assert warnings == []


def test_load_research_projects_no_warnings_on_full_success():
    with patch("subprocess.run", return_value=_completed("[]")):
        items, warnings = load_research_projects()
    assert items == []
    assert warnings == []


def test_format_warnings_empty_when_no_warnings():
    assert format_warnings([]) == ""


def test_format_warnings_banner_lists_each_warning():
    out = format_warnings(["manuscript: atlas is down", "program: bad json"])
    assert "atlas is down" in out
    assert "bad json" in out
    assert out.startswith("⚠️")
