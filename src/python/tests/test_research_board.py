"""Tests for obs research board — the deterministic renderer + marker writer (SPEC-obs)."""
from research.research_board import (
    MARKER_END,
    MARKER_START,
    build_block,
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
     "progress": 100, "target": None, "next": "CRAN", "priority": "P0"},
]


def test_render_is_deterministic():
    assert render_action_board(FIX) == render_action_board(list(reversed(FIX)))


def test_render_has_sections_and_no_timestamp():
    out = render_action_board(FIX)
    assert "## 🎯 Research Action Board" in out
    assert "### Manuscripts" in out
    assert "### Programs" in out
    assert "### Packages & other" in out
    assert "🔴 revise & resubmit" in out
    assert "AMPPS" in out
    assert "generated" not in out.lower()


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
