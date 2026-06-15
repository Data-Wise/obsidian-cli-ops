"""Tests for AI-powered vault refactor feature."""

import json
import pytest
pytest.importorskip("numpy", reason="numpy not installed in this Python env")
from unittest.mock import patch, MagicMock

from ai.features import (
    RefactorSuggestion,
    RefactorPlan,
    refactor_vault,
)


# ── Helpers ───────────────────────────────────────────────────────

def _make_vault():
    return {'id': 'vault-123', 'name': 'TestVault', 'path': '/tmp/testvault'}


def _make_note(title, path, note_id=None, modified_at='2025-01-01T00:00:00'):
    return {
        'id': note_id or f'note-{title.lower().replace(" ", "-")}',
        'title': title,
        'path': path,
        'vault_id': 'vault-123',
        'word_count': 200,
        'modified_at': modified_at,
    }


def _make_db(vault=None, notes=None, orphans=None, freshness=None, tag_stats=None):
    """Build a mock db_manager with sensible defaults."""
    db = MagicMock()
    db.get_vault_by_name_or_id.return_value = vault or _make_vault()
    db.list_notes.return_value = notes or []
    db.get_orphaned_notes.return_value = orphans or []
    db.get_note_freshness.return_value = freshness or {'total': 0, 'recent': 0, 'stale': 0}
    db.get_vault_tag_stats.return_value = tag_stats or []
    return db


# ── Dataclass Tests ───────────────────────────────────────────────

class TestRefactorSuggestion:

    def test_to_dict(self):
        s = RefactorSuggestion(
            category='move', priority='high',
            description='Move note.md to inbox/',
            affected_notes=['note'], reason='orphan', confidence=0.9,
        )
        d = s.to_dict()
        assert d['category'] == 'move'
        assert d['priority'] == 'high'
        assert d['confidence'] == 0.9


class TestRefactorPlan:

    def test_to_dict_round_trips(self):
        plan = RefactorPlan(
            vault_name='V', note_count=10, folder_count=3,
            suggestions=[
                RefactorSuggestion('move', 'high', 'desc1', confidence=0.9),
                RefactorSuggestion('archive', 'medium', 'desc2', confidence=0.6),
                RefactorSuggestion('merge-folder', 'low', 'desc3', confidence=0.3),
            ],
            summary='3 suggestions',
        )
        d = plan.to_dict()
        assert d['vault_name'] == 'V'
        assert len(d['suggestions']) == 3

    def test_to_json(self):
        plan = RefactorPlan(vault_name='V', note_count=5, folder_count=2)
        j = plan.to_json()
        parsed = json.loads(j)
        assert parsed['vault_name'] == 'V'
        assert parsed['suggestions'] == []

    def test_priority_properties(self):
        plan = RefactorPlan(
            vault_name='V', note_count=0, folder_count=0,
            suggestions=[
                RefactorSuggestion('move', 'high', 'h1'),
                RefactorSuggestion('move', 'high', 'h2'),
                RefactorSuggestion('archive', 'medium', 'm1'),
                RefactorSuggestion('merge-folder', 'low', 'l1'),
            ],
        )
        assert len(plan.high_priority) == 2
        assert len(plan.medium_priority) == 1
        assert len(plan.low_priority) == 1


# ── refactor_vault() Tests ────────────────────────────────────────

class TestRefactorVault:

    def test_missing_vault_raises(self):
        db = MagicMock()
        db.get_vault_by_name_or_id.return_value = None
        with pytest.raises(ValueError, match="Vault not found"):
            refactor_vault("nonexistent", db)

    def test_ambiguous_vault_raises(self):
        db = MagicMock()
        db.get_vault_by_name_or_id.side_effect = ValueError("Ambiguous prefix")
        with pytest.raises(ValueError, match="Ambiguous"):
            refactor_vault("amb", db)

    def test_empty_vault_no_suggestions(self):
        db = _make_db(notes=[], orphans=[])
        plan = refactor_vault("TestVault", db)
        assert plan.note_count == 0
        assert plan.suggestions == []

    def test_dry_run_includes_phase1_suggestions(self):
        """Dry run should include graph-only (Phase 1) suggestions but skip AI."""
        notes = [
            _make_note('Orphan', 'orphan.md'),
            _make_note('B', 'folder/b.md'),
        ]
        orphans = [_make_note('Orphan', 'orphan.md')]
        db = _make_db(notes=notes, orphans=orphans)
        plan = refactor_vault("TestVault", db, dry_run=True)
        assert plan.note_count == 2
        assert plan.folder_count == 2  # '.' and 'folder'
        assert 'Dry run' in plan.summary
        assert 'no AI calls' in plan.summary
        # Phase 1 suggestions should be present
        assert len(plan.suggestions) >= 1
        assert any(s.category == 'move' for s in plan.suggestions)

    def test_dry_run_empty_vault_no_suggestions(self):
        """Dry run on empty vault returns zero suggestions."""
        db = _make_db(notes=[], orphans=[])
        plan = refactor_vault("TestVault", db, dry_run=True)
        assert plan.suggestions == []
        assert 'Dry run' in plan.summary

    def test_root_orphans_get_move_suggestion(self):
        """Root-level orphans should get 'move' suggestions to inbox/."""
        notes = [_make_note('Orphan', 'orphan.md')]
        orphans = [_make_note('Orphan', 'orphan.md')]
        db = _make_db(notes=notes, orphans=orphans)

        plan = refactor_vault("TestVault", db)
        move_suggestions = [s for s in plan.suggestions if s.category == 'move']
        assert len(move_suggestions) >= 1
        assert move_suggestions[0].suggested_path == 'inbox/'
        assert move_suggestions[0].priority == 'high'

    def test_stale_folders_get_archive_suggestion(self):
        """Folders where all notes are >90 days old and orphaned get 'archive' suggestion."""
        old_date = '2020-01-01T00:00:00'
        notes = [
            _make_note('Old1', 'old-stuff/old1.md', modified_at=old_date),
            _make_note('Old2', 'old-stuff/old2.md', modified_at=old_date),
        ]
        orphans = [
            _make_note('Old1', 'old-stuff/old1.md', modified_at=old_date),
            _make_note('Old2', 'old-stuff/old2.md', modified_at=old_date),
        ]
        db = _make_db(notes=notes, orphans=orphans)

        plan = refactor_vault("TestVault", db)
        archive_suggestions = [s for s in plan.suggestions if s.category == 'archive']
        assert len(archive_suggestions) >= 1
        assert archive_suggestions[0].suggested_path == 'archive/'

    def test_small_folders_get_merge_suggestion(self):
        """Folders with <3 notes get 'merge-folder' suggestions."""
        notes = [
            _make_note('A', 'tiny1/a.md'),
            _make_note('B', 'tiny2/b.md'),
        ]
        db = _make_db(notes=notes)

        plan = refactor_vault("TestVault", db)
        merge_suggestions = [s for s in plan.suggestions if s.category == 'merge-folder']
        assert len(merge_suggestions) >= 2  # Both small folders flagged

    def test_tag_folder_mismatch_create_folder(self):
        """Tags with 5+ notes should suggest creating a folder."""
        notes = [_make_note(f'Note{i}', f'folder{i}/note{i}.md') for i in range(6)]
        tag_stats = [{'tag': 'python', 'note_count': 6}]
        db = _make_db(notes=notes, tag_stats=tag_stats)

        plan = refactor_vault("TestVault", db)
        create_suggestions = [s for s in plan.suggestions if s.category == 'create-folder']
        assert len(create_suggestions) >= 1
        assert 'python' in create_suggestions[0].description

    def test_suggestion_categories(self):
        """Verify all expected category types can be produced."""
        valid_categories = {'move', 'merge-folder', 'create-folder', 'connect', 'archive'}
        # Build a vault that triggers multiple categories
        old_date = '2020-01-01T00:00:00'
        notes = [
            _make_note('RootOrphan', 'root-orphan.md'),
            _make_note('Old1', 'stale/old1.md', modified_at=old_date),
            _make_note('Old2', 'stale/old2.md', modified_at=old_date),
            _make_note('Small', 'tiny1/small.md'),
            _make_note('Small2', 'tiny2/small2.md'),
        ]
        orphans = [
            _make_note('RootOrphan', 'root-orphan.md'),
            _make_note('Old1', 'stale/old1.md', modified_at=old_date),
            _make_note('Old2', 'stale/old2.md', modified_at=old_date),
        ]
        tag_stats = [{'tag': 'devops', 'note_count': 7}]
        db = _make_db(notes=notes, orphans=orphans, tag_stats=tag_stats)

        plan = refactor_vault("TestVault", db)
        categories_found = {s.category for s in plan.suggestions}
        # Should have at least move, archive, merge-folder, create-folder
        assert 'move' in categories_found
        assert 'archive' in categories_found
        assert 'merge-folder' in categories_found
        assert 'create-folder' in categories_found

    def test_verbose_prints_to_stderr(self, capsys):
        """Verbose mode should print progress to stderr."""
        notes = [_make_note('A', 'a.md')]
        db = _make_db(notes=notes)

        refactor_vault("TestVault", db, verbose=True)

        captured = capsys.readouterr()
        assert '[verbose]' in captured.err

    def test_basic_returns_refactor_plan(self):
        """Basic call should return a RefactorPlan with correct vault info."""
        notes = [
            _make_note('A', 'folder1/a.md'),
            _make_note('B', 'folder1/b.md'),
            _make_note('C', 'folder2/c.md'),
        ]
        db = _make_db(notes=notes)

        plan = refactor_vault("TestVault", db)
        assert isinstance(plan, RefactorPlan)
        assert plan.vault_name == 'TestVault'
        assert plan.note_count == 3
        assert plan.folder_count == 2

    def test_json_output_valid(self):
        """Plan.to_json() should produce valid JSON."""
        notes = [_make_note('A', 'a.md')]
        orphans = [_make_note('A', 'a.md')]
        db = _make_db(notes=notes, orphans=orphans)

        plan = refactor_vault("TestVault", db)
        j = plan.to_json()
        parsed = json.loads(j)
        assert 'suggestions' in parsed
        assert 'vault_name' in parsed
        assert parsed['vault_name'] == 'TestVault'

    def test_deep_folders_not_flagged_for_merge(self):
        """Deeply nested folders (depth > 2) should not get merge suggestions."""
        notes = [
            _make_note('Deep', 'a/b/c/d/deep.md'),      # folder depth 3 (a/b/c/d) — skip
            _make_note('Deep2', 'x/y/z/w/deep2.md'),     # folder depth 3 (x/y/z/w) — skip
            _make_note('Shallow', 'top/shallow.md'),      # folder depth 1 (top) — flag
            _make_note('Shallow2', 'other/shallow2.md'),  # folder depth 1 (other) — flag
        ]
        db = _make_db(notes=notes)

        plan = refactor_vault("TestVault", db)
        merge_suggestions = [s for s in plan.suggestions if s.category == 'merge-folder']
        merged_paths = [s.description for s in merge_suggestions]
        # Shallow folders flagged, deep ones not
        assert any('top/' in d for d in merged_paths)
        assert not any('a/b/c/d/' in d for d in merged_paths)

    def test_merge_suggestion_grammar_singular(self):
        """Merge suggestion for 1-note folder uses singular 'note'."""
        notes = [
            _make_note('Solo', 'solo-folder/only.md'),
            _make_note('Solo2', 'other-folder/only2.md'),
        ]
        db = _make_db(notes=notes)

        plan = refactor_vault("TestVault", db)
        merge_suggestions = [s for s in plan.suggestions if s.category == 'merge-folder']
        single_note = [s for s in merge_suggestions if '1' in s.description]
        assert len(single_note) >= 1
        assert 'note,' in single_note[0].reason or 'note, ' in single_note[0].reason or single_note[0].reason.endswith('note')
        assert 'note(s)' not in single_note[0].reason

    def test_merge_suggestion_grammar_plural(self):
        """Merge suggestion for 2-note folder uses plural 'notes'."""
        notes = [
            _make_note('A', 'pair/a.md'),
            _make_note('B', 'pair/b.md'),
            _make_note('C', 'other/c.md'),
        ]
        db = _make_db(notes=notes)

        plan = refactor_vault("TestVault", db)
        merge_suggestions = [s for s in plan.suggestions if s.category == 'merge-folder']
        two_note = [s for s in merge_suggestions if '2' in s.description]
        assert len(two_note) >= 1
        assert '2 notes' in two_note[0].reason
