"""Tests for v3.2.0 vault-level AI features (merge-suggest, tag-suggest, quality)."""

import json
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

from ai.features_vault import (
    merge_suggest_vault,
    tag_suggest_vault,
    note_quality_vault,
    note_quality_note,
    _batch_load_embeddings,
)
from ai.models import MergeCandidate, TagSuggestion, NoteQuality


# ── Helpers ───────────────────────────────────────────────────────

def _make_vault():
    return {'id': 'vault-123', 'name': 'TestVault', 'path': '/tmp/testvault'}


def _make_note(title, path, note_id=None, modified_at=None):
    if modified_at is None:
        modified_at = datetime.now(timezone.utc).isoformat()
    return {
        'id': note_id or f'note-{title.lower().replace(" ", "-")}',
        'title': title,
        'path': path,
        'vault_id': 'vault-123',
        'word_count': 200,
        'modified_at': modified_at,
    }


def _make_db(vault=None, notes=None, orphans=None, tags_by_note=None):
    """Build a mock db_manager."""
    db = MagicMock()
    db.get_vault_by_name_or_id.return_value = vault or _make_vault()
    db.get_vault.return_value = vault or _make_vault()
    db.list_notes.return_value = notes or []
    db.get_orphaned_notes.return_value = orphans or []
    db.get_note_freshness.return_value = {'total': 0, 'recent': 0, 'stale': 0}
    db.get_vault_tag_stats.return_value = []
    db.get_outgoing_links.return_value = []
    db.get_incoming_links.return_value = []
    db.get_note_tags.return_value = []

    # Allow per-note tag overrides
    if tags_by_note:
        def _get_tags(note_id):
            return tags_by_note.get(note_id, [])
        db.get_note_tags.side_effect = _get_tags

    return db


# ── merge_suggest_vault Tests ────────────────────────────────────


class TestMergeSuggestVault:

    def test_missing_vault_raises(self):
        db = _make_db()
        db.get_vault_by_name_or_id.return_value = None
        with pytest.raises(ValueError, match="Vault not found"):
            merge_suggest_vault("nonexistent", db)

    def test_empty_embeddings_returns_empty(self):
        db = _make_db()
        with patch('ai.features_vault._batch_load_embeddings', return_value={}):
            result = merge_suggest_vault("TestVault", db)
            assert result == []

    def test_one_embedding_returns_empty(self):
        db = _make_db()
        with patch('ai.features_vault._batch_load_embeddings',
                   return_value={"n1": np.array([1.0, 0.0])}):
            result = merge_suggest_vault("TestVault", db)
            assert result == []

    def test_high_similarity_pair_found(self):
        notes = [
            _make_note("Note A", "a.md", "n1"),
            _make_note("Note B", "b.md", "n2"),
        ]
        db = _make_db(notes=notes)
        # Nearly identical vectors → high cosine similarity
        embeddings = {
            "n1": np.array([1.0, 0.0, 0.0]) / np.linalg.norm([1.0, 0.0, 0.0]),
            "n2": np.array([0.99, 0.01, 0.0]) / np.linalg.norm([0.99, 0.01, 0.0]),
        }
        with patch('ai.features_vault._batch_load_embeddings', return_value=embeddings):
            result = merge_suggest_vault("TestVault", db, threshold=0.9)
            assert len(result) >= 1
            assert isinstance(result[0], MergeCandidate)
            assert result[0].similarity > 0.9

    def test_low_similarity_pair_filtered(self):
        notes = [
            _make_note("Note A", "a.md", "n1"),
            _make_note("Note B", "b.md", "n2"),
        ]
        db = _make_db(notes=notes)
        # Orthogonal vectors → 0 similarity
        embeddings = {
            "n1": np.array([1.0, 0.0]) / np.linalg.norm([1.0, 0.0]),
            "n2": np.array([0.0, 1.0]) / np.linalg.norm([0.0, 1.0]),
        }
        with patch('ai.features_vault._batch_load_embeddings', return_value=embeddings):
            result = merge_suggest_vault("TestVault", db, threshold=0.8)
            assert result == []

    def test_sorted_by_similarity_descending(self):
        notes = [
            _make_note("A", "a.md", "n1"),
            _make_note("B", "b.md", "n2"),
            _make_note("C", "c.md", "n3"),
        ]
        db = _make_db(notes=notes)
        # n1-n2 highly similar, n1-n3 less so
        embeddings = {
            "n1": np.array([1.0, 0.0, 0.0]) / np.linalg.norm([1.0, 0.0, 0.0]),
            "n2": np.array([0.99, 0.01, 0.0]) / np.linalg.norm([0.99, 0.01, 0.0]),
            "n3": np.array([0.85, 0.15, 0.0]) / np.linalg.norm([0.85, 0.15, 0.0]),
        }
        with patch('ai.features_vault._batch_load_embeddings', return_value=embeddings):
            result = merge_suggest_vault("TestVault", db, threshold=0.8)
            if len(result) >= 2:
                assert result[0].similarity >= result[1].similarity

    def test_json_output_valid(self):
        notes = [_make_note("A", "a.md", "n1"), _make_note("B", "b.md", "n2")]
        db = _make_db(notes=notes)
        embeddings = {
            "n1": np.array([1.0, 0.0]) / np.linalg.norm([1.0, 0.0]),
            "n2": np.array([0.99, 0.01]) / np.linalg.norm([0.99, 0.01]),
        }
        with patch('ai.features_vault._batch_load_embeddings', return_value=embeddings):
            result = merge_suggest_vault("TestVault", db, threshold=0.5)
            # Verify JSON serialization
            json_str = json.dumps([c.to_dict() for c in result])
            parsed = json.loads(json_str)
            assert isinstance(parsed, list)


# ── note_quality_vault Tests ─────────────────────────────────────


class TestNoteQualityVault:

    def test_missing_vault_raises(self):
        db = _make_db()
        db.get_vault_by_name_or_id.return_value = None
        with pytest.raises(ValueError, match="Vault not found"):
            note_quality_vault("nonexistent", db)

    def test_empty_vault_returns_empty(self):
        db = _make_db(notes=[])
        result = note_quality_vault("TestVault", db)
        assert result == []

    @patch('ai.features_vault._get_note_content')
    def test_basic_scoring(self, mock_content):
        now = datetime.now(timezone.utc).isoformat()
        notes = [
            _make_note("Good Note", "good.md", "n1", modified_at=now),
            _make_note("Bad Note", "bad.md", "n2", modified_at="2020-01-01T00:00:00+00:00"),
        ]
        db = _make_db(notes=notes, orphans=[notes[1]])
        db.get_note_tags.side_effect = lambda nid: ["python"] if nid == "n1" else []

        def content_for(note, vault_path):
            if note['id'] == 'n1':
                return "---\ntitle: Good\n---\n# Heading\n" + "word " * 200
            return "short content"
        mock_content.side_effect = content_for

        result = note_quality_vault("TestVault", db)
        assert len(result) == 2
        assert all(isinstance(r, NoteQuality) for r in result)
        # Sorted worst first
        assert result[0].overall_score <= result[1].overall_score

    @patch('ai.features_vault._get_note_content')
    def test_orphan_gets_zero_connectivity(self, mock_content):
        notes = [_make_note("Orphan", "orphan.md", "n1")]
        db = _make_db(notes=notes, orphans=notes)
        mock_content.return_value = "Some content with enough words for the test"

        result = note_quality_vault("TestVault", db)
        assert result[0].dimensions['connectivity'] == 0.0
        assert any(i['severity'] == 'high' for i in result[0].issues)

    @patch('ai.features_vault._get_note_content')
    def test_dimensions_are_0_to_100(self, mock_content):
        notes = [_make_note("Note", "n.md", "n1")]
        db = _make_db(notes=notes)
        mock_content.return_value = "---\ntags: [test]\n---\n# Heading\n" + "word " * 300

        result = note_quality_vault("TestVault", db)
        for dim_value in result[0].dimensions.values():
            assert 0.0 <= dim_value <= 100.0

    @patch('ai.features_vault._get_note_content')
    def test_json_output_valid(self, mock_content):
        notes = [_make_note("Note", "n.md", "n1")]
        db = _make_db(notes=notes)
        mock_content.return_value = "content"

        result = note_quality_vault("TestVault", db)
        json_str = json.dumps([s.to_dict() for s in result])
        parsed = json.loads(json_str)
        assert isinstance(parsed, list)
        assert 'overall_score' in parsed[0]

    @patch('ai.features_vault._get_note_content')
    def test_verbose_prints_to_stderr(self, mock_content, capsys):
        notes = [_make_note("Note", "n.md", "n1")]
        db = _make_db(notes=notes)
        mock_content.return_value = "content"

        note_quality_vault("TestVault", db, verbose=True)
        captured = capsys.readouterr()
        assert "Scoring" in captured.err


# ── tag_suggest_vault Tests ──────────────────────────────────────


class TestTagSuggestVault:

    def test_missing_vault_raises(self):
        db = _make_db()
        db.get_vault_by_name_or_id.return_value = None
        with pytest.raises(ValueError, match="Vault not found"):
            tag_suggest_vault("nonexistent", db)

    def test_no_untagged_notes_returns_empty(self):
        notes = [_make_note("Tagged", "t.md", "n1")]
        db = _make_db(notes=notes,
                       tags_by_note={"n1": ["python", "dev"]})
        result = tag_suggest_vault("TestVault", db)
        assert result == []
