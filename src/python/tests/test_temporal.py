"""
Tests for temporal analytics: compute_trends() and compute_stale().
"""

import os
import pytest
from datetime import datetime, timezone, timedelta
from db_manager import DatabaseManager
from core.temporal import compute_trends, compute_stale, _parse_dt


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_db(tmp_path):
    path = str(tmp_path / "test.sqlite")
    db = DatabaseManager(path)
    return db


def _add_note(db, vault_id, filename, modified_days_ago, created_days_ago=None):
    now = datetime.now(timezone.utc)
    modified_at = (now - timedelta(days=modified_days_ago)).strftime('%Y-%m-%d %H:%M:%S')
    created_at = (now - timedelta(days=created_days_ago or modified_days_ago)).strftime('%Y-%m-%d %H:%M:%S')
    note_id = db.add_note(
        vault_id, filename, f"Note {filename}", "content",
        metadata={"created_at": created_at, "modified_at": modified_at},
    )
    return note_id


def _set_pagerank(db, note_id, pagerank):
    with db.get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO graph_metrics (note_id, pagerank) VALUES (?, ?)",
            (note_id, pagerank),
        )


# ── _parse_dt ─────────────────────────────────────────────────────────────────

class TestParseDt:
    def test_iso_with_space(self):
        dt = _parse_dt("2026-01-15 10:30:00")
        assert dt.year == 2026 and dt.month == 1 and dt.tzinfo is not None

    def test_iso_with_t(self):
        dt = _parse_dt("2026-06-01T00:00:00")
        assert dt.year == 2026 and dt.month == 6

    def test_date_only(self):
        dt = _parse_dt("2026-03-01")
        assert dt.year == 2026 and dt.month == 3

    def test_passthrough_aware(self):
        orig = datetime(2026, 1, 1, tzinfo=timezone.utc)
        assert _parse_dt(orig) is orig

    def test_passthrough_naive_becomes_aware(self):
        orig = datetime(2026, 1, 1)
        result = _parse_dt(orig)
        assert result.tzinfo is not None

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            _parse_dt("not-a-date")


# ── compute_trends ────────────────────────────────────────────────────────────

class TestComputeTrends:
    def test_empty_vault(self, tmp_path):
        db = _make_db(tmp_path)
        vault_id = db.add_vault("empty", str(tmp_path))
        report = compute_trends(vault_id, db, lookback_days=90)
        assert report.vault_id == vault_id
        assert report.total_notes == 0
        assert report.buckets == []
        assert report.insufficient_data is True

    def test_single_week_insufficient(self, tmp_path):
        db = _make_db(tmp_path)
        vault_id = db.add_vault("v1", str(tmp_path))
        _add_note(db, vault_id, "a.md", modified_days_ago=5, created_days_ago=5)
        report = compute_trends(vault_id, db, lookback_days=90)
        assert report.insufficient_data is True
        assert len(report.buckets) == 1

    def test_multiple_weeks_sufficient(self, tmp_path):
        db = _make_db(tmp_path)
        vault_id = db.add_vault("v1", str(tmp_path))
        for d in [5, 15, 25, 35]:
            _add_note(db, vault_id, f"note{d}.md", modified_days_ago=d, created_days_ago=d)
        report = compute_trends(vault_id, db, lookback_days=90)
        assert report.insufficient_data is False
        assert len(report.buckets) >= 2

    def test_velocity_calculation(self, tmp_path):
        db = _make_db(tmp_path)
        vault_id = db.add_vault("v1", str(tmp_path))
        for d in [5, 15, 25]:
            _add_note(db, vault_id, f"n{d}.md", modified_days_ago=d, created_days_ago=d)
        report = compute_trends(vault_id, db, lookback_days=90)
        assert report.velocity_notes_per_week >= 0.0
        assert report.total_notes == 3

    def test_notes_outside_window_excluded(self, tmp_path):
        db = _make_db(tmp_path)
        vault_id = db.add_vault("v1", str(tmp_path))
        _add_note(db, vault_id, "old.md", modified_days_ago=200, created_days_ago=200)
        _add_note(db, vault_id, "recent.md", modified_days_ago=5, created_days_ago=5)
        report = compute_trends(vault_id, db, lookback_days=30)
        # old note outside 30-day window should not appear in buckets
        total_modified = sum(b.notes_modified for b in report.buckets)
        assert total_modified == 1  # only recent note


# ── compute_stale ─────────────────────────────────────────────────────────────

class TestComputeStale:
    def test_empty_vault(self, tmp_path):
        db = _make_db(tmp_path)
        vault_id = db.add_vault("empty", str(tmp_path))
        report = compute_stale(vault_id, db)
        assert report.notes == []
        assert report.has_graph_metrics is False

    def test_no_graph_metrics_date_sort(self, tmp_path):
        db = _make_db(tmp_path)
        vault_id = db.add_vault("v1", str(tmp_path))
        _add_note(db, vault_id, "new.md", modified_days_ago=10)
        _add_note(db, vault_id, "old.md", modified_days_ago=200)
        _add_note(db, vault_id, "medium.md", modified_days_ago=50)
        report = compute_stale(vault_id, db)
        assert report.has_graph_metrics is False
        # oldest note should be first
        assert report.notes[0].days_since_modified >= report.notes[1].days_since_modified

    def test_with_graph_metrics_pagerank_weighted(self, tmp_path):
        db = _make_db(tmp_path)
        vault_id = db.add_vault("v1", str(tmp_path))
        note_hub = _add_note(db, vault_id, "hub.md", modified_days_ago=100)
        note_leaf = _add_note(db, vault_id, "leaf.md", modified_days_ago=150)
        _set_pagerank(db, note_hub, 0.5)
        _set_pagerank(db, note_leaf, 0.01)

        report = compute_stale(vault_id, db)
        assert report.has_graph_metrics is True
        # hub: 0.5 × (100/365) ≈ 0.137; leaf: 0.01 × (150/365) ≈ 0.0041
        # hub should rank first despite being newer
        assert report.notes[0].note_id == str(note_hub)

    def test_limit_respected(self, tmp_path):
        db = _make_db(tmp_path)
        vault_id = db.add_vault("v1", str(tmp_path))
        for i in range(30):
            _add_note(db, vault_id, f"n{i}.md", modified_days_ago=i * 3)
        report = compute_stale(vault_id, db, limit=10)
        assert len(report.notes) <= 10

    def test_staleness_score_nonnegative(self, tmp_path):
        db = _make_db(tmp_path)
        vault_id = db.add_vault("v1", str(tmp_path))
        _add_note(db, vault_id, "a.md", modified_days_ago=30)
        report = compute_stale(vault_id, db)
        for n in report.notes:
            assert n.staleness_score >= 0.0

    def test_to_dict_shape(self, tmp_path):
        db = _make_db(tmp_path)
        vault_id = db.add_vault("v1", str(tmp_path))
        _add_note(db, vault_id, "a.md", modified_days_ago=50)
        report = compute_stale(vault_id, db)
        d = report.to_dict()
        assert "vault_id" in d
        assert "notes" in d
        assert "has_graph_metrics" in d
        assert isinstance(d["notes"], list)
