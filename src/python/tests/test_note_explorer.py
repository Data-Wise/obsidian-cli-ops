"""
Unit tests for NoteExplorerScreen class.

Tests the Note Explorer TUI screen including search, filtering, sorting,
preview, and metadata display functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open, PropertyMock
from pathlib import Path
import tempfile
import os
import sys

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from tui.screens.notes import NoteExplorerScreen


@pytest.fixture
def mock_db():
    """Create a mock DatabaseManager."""
    db = Mock()

    # Mock vault data
    db.get_vault.return_value = {
        'id': 'vault1',
        'name': 'Test Vault',
        'path': '/tmp/test_vault'
    }

    # Mock notes data
    db.list_notes.return_value = [
        {
            'id': 'note1',
            'title': 'First Note',
            'path': 'notes/first.md',
            'word_count': 100,
            'char_count': 500,
            'modified_at': '2025-12-15T10:00:00'
        },
        {
            'id': 'note2',
            'title': 'Second Note',
            'path': 'notes/second.md',
            'word_count': 200,
            'char_count': 1000,
            'modified_at': '2025-12-14T09:00:00'
        },
        {
            'id': 'note3',
            'title': 'Third Note About Mediation',
            'path': 'notes/third.md',
            'word_count': 150,
            'char_count': 750,
            'modified_at': '2025-12-13T08:00:00'
        }
    ]

    # Mock graph metrics
    db.get_graph_metrics.return_value = {
        'pagerank': 0.5,
        'in_degree': 3,
        'out_degree': 2,
        'betweenness': 0.25,
        'closeness': 0.75,
        'clustering_coefficient': 0.1
    }

    # Mock links
    db.get_outgoing_links.return_value = [
        {'target_note_id': 'note2', 'link_text': 'Link 1'},
        {'target_note_id': 'note3', 'link_text': 'Link 2'}
    ]

    db.get_incoming_links.return_value = [
        {'source_note_id': 'note1', 'link_text': 'Back Link'}
    ]

    # Mock tags
    db.get_note_tags.return_value = ['statistics', 'research', 'methodology']

    return db


@pytest.fixture
def mock_app():
    """Create a mock Textual App."""
    app = Mock()
    app.pop_screen = Mock()
    app.push_screen = Mock()
    app.exit = Mock()
    return app


@pytest.fixture
def note_explorer(mock_db, mock_app):
    """Create a NoteExplorerScreen instance with mocks."""
    with patch('tui.screens.notes.DatabaseManager', return_value=mock_db):
        screen = NoteExplorerScreen(vault_id='vault1', vault_name='Test Vault')

        # Mock the app property using PropertyMock
        type(screen).app = PropertyMock(return_value=mock_app)

        # Mock query_one to return mocks for widgets
        screen.query_one = Mock(side_effect=lambda selector, widget_type=None: Mock())

        # Mock notify
        screen.notify = Mock()

        return screen


class TestNoteExplorerInitialization:
    """Test Note Explorer initialization."""

    def test_initialization_with_vault_id(self, mock_db):
        """Test that screen initializes with vault ID and name."""
        with patch('tui.screens.notes.DatabaseManager', return_value=mock_db):
            screen = NoteExplorerScreen(vault_id='vault1', vault_name='Test Vault')

            assert screen.vault_id == 'vault1'
            assert screen.vault_name == 'Test Vault'
            assert screen.current_sort == 'title'
            assert screen.all_notes == []
            assert screen.filtered_notes == []
            assert screen.selected_note is None

    def test_database_manager_created(self, mock_db):
        """Test that DatabaseManager is instantiated."""
        with patch('tui.screens.notes.DatabaseManager', return_value=mock_db) as mock_dm:
            screen = NoteExplorerScreen(vault_id='vault1', vault_name='Test Vault')
            mock_dm.assert_called_once()
            assert screen.db is not None


class TestDataLoading:
    """Test note data loading and refreshing."""

    def test_refresh_data_loads_notes(self, note_explorer, mock_db):
        """Test that refresh_data loads notes from database."""
        note_explorer.update_table = Mock()
        note_explorer.update_result_count = Mock()

        note_explorer.refresh_data()

        mock_db.list_notes.assert_called_once_with(vault_id='vault1')
        assert len(note_explorer.all_notes) == 3
        assert len(note_explorer.filtered_notes) == 3

    def test_refresh_data_handles_empty_vault(self, note_explorer, mock_db):
        """Test that empty vault is handled gracefully."""
        mock_db.list_notes.return_value = []
        note_explorer.update_table = Mock()
        note_explorer.update_result_count = Mock()

        note_explorer.refresh_data()

        assert note_explorer.all_notes == []
        assert note_explorer.filtered_notes == []

    def test_refresh_data_handles_database_error(self, note_explorer, mock_db):
        """Test that database errors are caught and handled."""
        mock_db.list_notes.side_effect = Exception("Database error")
        note_explorer.update_table = Mock()
        note_explorer.update_result_count = Mock()

        note_explorer.refresh_data()

        note_explorer.notify.assert_called_once()
        assert "Database error" in str(note_explorer.notify.call_args)
        assert note_explorer.all_notes == []

    def test_large_vault_shows_warning(self, note_explorer, mock_db):
        """Test that large vaults trigger a warning notification."""
        # Create 1500 mock notes
        large_note_list = [
            {'id': f'note{i}', 'title': f'Note {i}', 'path': f'note{i}.md',
             'word_count': 100, 'char_count': 500, 'modified_at': '2025-12-15T10:00:00'}
            for i in range(1500)
        ]
        mock_db.list_notes.return_value = large_note_list

        note_explorer.update_table = Mock()
        note_explorer.update_result_count = Mock()

        note_explorer.refresh_data()

        # Should notify about large vault
        assert note_explorer.notify.called
        notify_call = str(note_explorer.notify.call_args)
        assert "1500" in notify_call or "Large vault" in notify_call


class TestSortFunctionality:
    """Test note sorting functionality."""

    def test_sort_by_title(self, note_explorer):
        """Test sorting notes by title."""
        notes = [
            {'id': '1', 'title': 'Zebra', 'word_count': 100, 'modified_at': '2025-12-15'},
            {'id': '2', 'title': 'Apple', 'word_count': 200, 'modified_at': '2025-12-14'},
            {'id': '3', 'title': 'Mango', 'word_count': 150, 'modified_at': '2025-12-13'}
        ]

        sorted_notes = note_explorer._sort_notes(notes, 'title')

        assert sorted_notes[0]['title'] == 'Apple'
        assert sorted_notes[1]['title'] == 'Mango'
        assert sorted_notes[2]['title'] == 'Zebra'

    def test_sort_by_word_count(self, note_explorer):
        """Test sorting notes by word count (descending)."""
        notes = [
            {'id': '1', 'title': 'First', 'word_count': 100, 'modified_at': '2025-12-15'},
            {'id': '2', 'title': 'Second', 'word_count': 300, 'modified_at': '2025-12-14'},
            {'id': '3', 'title': 'Third', 'word_count': 200, 'modified_at': '2025-12-13'}
        ]

        sorted_notes = note_explorer._sort_notes(notes, 'word_count')

        assert sorted_notes[0]['word_count'] == 300
        assert sorted_notes[1]['word_count'] == 200
        assert sorted_notes[2]['word_count'] == 100

    def test_sort_by_modified_date(self, note_explorer):
        """Test sorting notes by modified date (descending)."""
        notes = [
            {'id': '1', 'title': 'First', 'word_count': 100, 'modified_at': '2025-12-13'},
            {'id': '2', 'title': 'Second', 'word_count': 200, 'modified_at': '2025-12-15'},
            {'id': '3', 'title': 'Third', 'word_count': 150, 'modified_at': '2025-12-14'}
        ]

        sorted_notes = note_explorer._sort_notes(notes, 'modified_at')

        assert sorted_notes[0]['modified_at'] == '2025-12-15'
        assert sorted_notes[1]['modified_at'] == '2025-12-14'
        assert sorted_notes[2]['modified_at'] == '2025-12-13'

    def test_sort_handles_missing_values(self, note_explorer):
        """Test that sorting handles missing values gracefully."""
        notes = [
            {'id': '1', 'title': 'First'},
            {'id': '2', 'title': 'Second', 'word_count': 200}
        ]

        # Should not crash on missing word_count
        sorted_notes = note_explorer._sort_notes(notes, 'word_count')
        assert len(sorted_notes) == 2


class TestSearchFiltering:
    """Test search and filtering functionality."""

    def test_search_filters_by_title(self, note_explorer, mock_db):
        """Test that search filters notes by title."""
        # Use real dict objects with string titles (not Mocks)
        note_explorer.all_notes = [
            dict(id='1', title='Causal Mediation Analysis'),
            dict(id='2', title='Direct Effects Study'),
            dict(id='3', title='Mediation Framework')
        ]
        note_explorer.update_table = Mock()
        note_explorer.update_result_count = Mock()

        # Create simple class for input event
        class FakeInput:
            id = "search-box"

        class FakeEvent:
            input = FakeInput()
            value = "mediation"

        note_explorer.on_input_changed(FakeEvent())

        assert len(note_explorer.filtered_notes) == 2
        assert note_explorer.filtered_notes[0]['id'] == '1'
        assert note_explorer.filtered_notes[1]['id'] == '3'

    def test_search_is_case_insensitive(self, note_explorer):
        """Test that search is case-insensitive."""
        note_explorer.all_notes = [
            dict(id='1', title='UPPERCASE NOTE'),
            dict(id='2', title='lowercase note'),
            dict(id='3', title='MiXeD CaSe NoTe')
        ]
        note_explorer.update_table = Mock()
        note_explorer.update_result_count = Mock()

        class FakeInput:
            id = "search-box"

        class FakeEvent:
            input = FakeInput()
            value = "NOTE"

        note_explorer.on_input_changed(FakeEvent())

        assert len(note_explorer.filtered_notes) == 3

    def test_empty_search_shows_all_notes(self, note_explorer):
        """Test that empty search shows all notes."""
        note_explorer.all_notes = [
            dict(id='1', title='Note 1'),
            dict(id='2', title='Note 2'),
            dict(id='3', title='Note 3')
        ]
        note_explorer.update_table = Mock()
        note_explorer.update_result_count = Mock()

        class FakeInput:
            id = "search-box"

        class FakeEvent:
            input = FakeInput()
            value = ""

        note_explorer.on_input_changed(FakeEvent())

        assert len(note_explorer.filtered_notes) == 3

    def test_search_with_no_results(self, note_explorer):
        """Test search with no matching results."""
        note_explorer.all_notes = [
            dict(id='1', title='Statistics'),
            dict(id='2', title='Mathematics')
        ]
        note_explorer.update_table = Mock()
        note_explorer.update_result_count = Mock()

        class FakeInput:
            id = "search-box"

        class FakeEvent:
            input = FakeInput()
            value = "nonexistent"

        note_explorer.on_input_changed(FakeEvent())

        assert len(note_explorer.filtered_notes) == 0


class TestPreviewDisplay:
    """Test note preview functionality."""

    def test_show_preview_reads_file(self, note_explorer, mock_db):
        """Test that show_preview reads and displays note content."""
        note_explorer.selected_note = {
            'id': 'note1',
            'path': 'notes/test.md'
        }

        file_content = """# Test Note

This is a test note with some content.
It has multiple lines.

## Section 1
More content here."""

        mock_preview_pane = Mock()
        note_explorer.query_one = Mock(return_value=mock_preview_pane)

        with patch('builtins.open', mock_open(read_data=file_content)):
            note_explorer.show_preview()

        # Verify preview pane was updated
        mock_preview_pane.update.assert_called_once()
        update_call = str(mock_preview_pane.update.call_args)
        assert "Test Note" in update_call

    def test_show_preview_handles_missing_file(self, note_explorer, mock_db):
        """Test that missing files are handled gracefully."""
        note_explorer.selected_note = {
            'id': 'note1',
            'path': 'notes/missing.md'
        }

        mock_preview_pane = Mock()
        note_explorer.query_one = Mock(return_value=mock_preview_pane)

        with patch('builtins.open', side_effect=FileNotFoundError()):
            note_explorer.show_preview()

        # Should show file not found message
        mock_preview_pane.update.assert_called_once()
        update_call = str(mock_preview_pane.update.call_args)
        assert "File not found" in update_call or "⚠️" in update_call

    def test_show_preview_handles_permission_error(self, note_explorer, mock_db):
        """Test that permission errors are handled."""
        note_explorer.selected_note = {
            'id': 'note1',
            'path': 'notes/protected.md'
        }

        mock_preview_pane = Mock()
        note_explorer.query_one = Mock(return_value=mock_preview_pane)

        with patch('builtins.open', side_effect=PermissionError()):
            note_explorer.show_preview()

        # Should show permission denied message
        mock_preview_pane.update.assert_called_once()
        update_call = str(mock_preview_pane.update.call_args)
        assert "Permission denied" in update_call or "❌" in update_call

    def test_show_preview_handles_encoding_error(self, note_explorer, mock_db):
        """Test that encoding errors are handled."""
        note_explorer.selected_note = {
            'id': 'note1',
            'path': 'notes/binary.md'
        }

        mock_preview_pane = Mock()
        note_explorer.query_one = Mock(return_value=mock_preview_pane)

        with patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid')):
            note_explorer.show_preview()

        # Should show encoding error message
        mock_preview_pane.update.assert_called_once()
        update_call = str(mock_preview_pane.update.call_args)
        assert "encoding" in update_call.lower() or "❌" in update_call

    def test_show_preview_handles_empty_file(self, note_explorer, mock_db):
        """Test that empty files are handled."""
        note_explorer.selected_note = {
            'id': 'note1',
            'path': 'notes/empty.md'
        }

        mock_preview_pane = Mock()
        note_explorer.query_one = Mock(return_value=mock_preview_pane)

        with patch('builtins.open', mock_open(read_data="")):
            note_explorer.show_preview()

        # Should show empty note message
        mock_preview_pane.update.assert_called_once()
        update_call = str(mock_preview_pane.update.call_args)
        assert "Empty note" in update_call or "📄" in update_call

    def test_show_preview_truncates_long_content(self, note_explorer, mock_db):
        """Test that long notes are truncated to 20 lines."""
        note_explorer.selected_note = {
            'id': 'note1',
            'path': 'notes/long.md'
        }

        # Create content with 30 lines
        long_content = '\n'.join([f'Line {i}' for i in range(30)])

        mock_preview_pane = Mock()
        note_explorer.query_one = Mock(return_value=mock_preview_pane)

        with patch('builtins.open', mock_open(read_data=long_content)):
            note_explorer.show_preview()

        # Should show truncation indicator
        mock_preview_pane.update.assert_called_once()
        update_call = str(mock_preview_pane.update.call_args)
        assert "..." in update_call

    def test_show_preview_with_no_selection(self, note_explorer):
        """Test preview with no note selected."""
        note_explorer.selected_note = None

        mock_preview_pane = Mock()
        note_explorer.query_one = Mock(return_value=mock_preview_pane)

        note_explorer.show_preview()

        mock_preview_pane.update.assert_called_once()
        update_call = str(mock_preview_pane.update.call_args)
        assert "No note selected" in update_call


class TestMetadataDisplay:
    """Test metadata display functionality."""

    def test_show_metadata_displays_note_info(self, note_explorer, mock_db):
        """Test that metadata displays note information."""
        note_explorer.selected_note = {
            'id': 'note1',
            'path': 'notes/test.md',
            'word_count': 500,
            'char_count': 2500,
            'modified_at': '2025-12-15T10:30:00'
        }

        mock_metadata_pane = Mock()
        note_explorer.query_one = Mock(return_value=mock_metadata_pane)

        note_explorer.show_metadata()

        mock_metadata_pane.update.assert_called_once()
        update_call = str(mock_metadata_pane.update.call_args)

        # Should contain key metadata
        assert "500" in update_call  # word count
        assert "2500" in update_call  # char count
        assert "notes/test.md" in update_call  # path

    def test_show_metadata_displays_links(self, note_explorer, mock_db):
        """Test that metadata displays link counts."""
        note_explorer.selected_note = {'id': 'note1', 'path': 'test.md'}

        mock_metadata_pane = Mock()
        note_explorer.query_one = Mock(return_value=mock_metadata_pane)

        note_explorer.show_metadata()

        mock_db.get_outgoing_links.assert_called_once_with('note1')
        mock_db.get_incoming_links.assert_called_once_with('note1')

        mock_metadata_pane.update.assert_called_once()
        update_call = str(mock_metadata_pane.update.call_args)
        assert "Outgoing" in update_call or "→" in update_call
        assert "Incoming" in update_call or "←" in update_call

    def test_show_metadata_displays_tags(self, note_explorer, mock_db):
        """Test that metadata displays tags."""
        note_explorer.selected_note = {'id': 'note1', 'path': 'test.md'}

        mock_metadata_pane = Mock()
        note_explorer.query_one = Mock(return_value=mock_metadata_pane)

        note_explorer.show_metadata()

        mock_db.get_note_tags.assert_called_once_with('note1')

        mock_metadata_pane.update.assert_called_once()
        update_call = str(mock_metadata_pane.update.call_args)
        assert "statistics" in update_call
        assert "research" in update_call

    def test_show_metadata_displays_graph_metrics(self, note_explorer, mock_db):
        """Test that metadata displays graph metrics."""
        note_explorer.selected_note = {'id': 'note1', 'path': 'test.md'}

        mock_metadata_pane = Mock()
        note_explorer.query_one = Mock(return_value=mock_metadata_pane)

        note_explorer.show_metadata()

        mock_db.get_graph_metrics.assert_called_once_with('note1')

        mock_metadata_pane.update.assert_called_once()
        update_call = str(mock_metadata_pane.update.call_args)
        assert "PageRank" in update_call
        assert "0.5" in update_call  # PageRank value

    def test_show_metadata_with_no_tags(self, note_explorer, mock_db):
        """Test metadata display when note has no tags."""
        note_explorer.selected_note = {'id': 'note1', 'path': 'test.md'}
        mock_db.get_note_tags.return_value = []

        mock_metadata_pane = Mock()
        note_explorer.query_one = Mock(return_value=mock_metadata_pane)

        note_explorer.show_metadata()

        mock_metadata_pane.update.assert_called_once()
        update_call = str(mock_metadata_pane.update.call_args)
        assert "No tags" in update_call


class TestActionMethods:
    """Test action methods (keyboard shortcuts)."""

    def test_action_back(self, note_explorer, mock_app):
        """Test back action pops screen."""
        note_explorer.action_back()
        mock_app.pop_screen.assert_called_once()

    def test_action_quit(self, note_explorer, mock_app):
        """Test quit action exits app."""
        note_explorer.action_quit()
        mock_app.exit.assert_called_once()

    def test_action_refresh(self, note_explorer, mock_db):
        """Test refresh action reloads data."""
        note_explorer.update_table = Mock()
        note_explorer.update_result_count = Mock()

        note_explorer.action_refresh()

        mock_db.list_notes.assert_called()
        note_explorer.notify.assert_called()

    def test_action_focus_search(self, note_explorer):
        """Test focus search action focuses search box."""
        mock_search_box = Mock()
        note_explorer.query_one = Mock(return_value=mock_search_box)

        note_explorer.action_focus_search()

        mock_search_box.focus.assert_called_once()

    def test_action_toggle_sort(self, note_explorer, mock_db):
        """Test toggle sort cycles through sort options."""
        note_explorer.update_table = Mock()
        note_explorer.update_result_count = Mock()

        # Initial sort is 'title'
        assert note_explorer.current_sort == 'title'

        # Toggle to 'word_count'
        note_explorer.action_toggle_sort()
        assert note_explorer.current_sort == 'word_count'

        # Toggle to 'modified_at'
        note_explorer.action_toggle_sort()
        assert note_explorer.current_sort == 'modified_at'

        # Toggle back to 'title'
        note_explorer.action_toggle_sort()
        assert note_explorer.current_sort == 'title'

    def test_action_view_note(self, note_explorer):
        """Test view note action (future feature)."""
        note_explorer.selected_note = {'id': 'note1', 'title': 'Test'}

        note_explorer.action_view_note()

        # Should show notification about future feature
        note_explorer.notify.assert_called_once()
        notify_call = str(note_explorer.notify.call_args)
        assert "future" in notify_call.lower()


class TestHelperMethods:
    """Test helper methods."""

    def test_format_datetime_valid_iso(self, note_explorer):
        """Test datetime formatting with valid ISO string."""
        dt_str = "2025-12-15T10:30:45"
        result = note_explorer._format_datetime(dt_str)

        assert "2025-12-15" in result
        assert "10:30" in result

    def test_format_datetime_with_timezone(self, note_explorer):
        """Test datetime formatting with timezone."""
        dt_str = "2025-12-15T10:30:45Z"
        result = note_explorer._format_datetime(dt_str)

        assert "2025-12-15" in result

    def test_format_datetime_empty_string(self, note_explorer):
        """Test datetime formatting with empty string."""
        result = note_explorer._format_datetime("")
        assert "Unknown" in result

    def test_format_datetime_invalid_format(self, note_explorer):
        """Test datetime formatting with invalid format."""
        result = note_explorer._format_datetime("not a date")
        assert "Invalid" in result

    def test_format_datetime_none(self, note_explorer):
        """Test datetime formatting with None."""
        result = note_explorer._format_datetime(None)
        assert "Unknown" in result


class TestUpdateMethods:
    """Test table and UI update methods."""

    def test_update_result_count_shows_filtered_total(self, note_explorer):
        """Test that result count shows filtered/total."""
        note_explorer.all_notes = [{'id': '1'}, {'id': '2'}, {'id': '3'}]
        note_explorer.filtered_notes = [{'id': '1'}, {'id': '2'}]

        mock_count_widget = Mock()
        note_explorer.query_one = Mock(return_value=mock_count_widget)

        note_explorer.update_result_count()

        mock_count_widget.update.assert_called_once()
        update_call = str(mock_count_widget.update.call_args)
        assert "2" in update_call  # filtered count
        assert "3" in update_call  # total count

    def test_update_table_with_empty_results(self, note_explorer, mock_db):
        """Test update_table shows message for empty results."""
        note_explorer.filtered_notes = []

        mock_table = Mock()
        note_explorer.query_one = Mock(return_value=mock_table)

        note_explorer.update_table()

        mock_table.clear.assert_called_once()
        mock_table.add_row.assert_called_once()

        # First argument should be "No notes found" message
        first_arg = mock_table.add_row.call_args[0][0]
        assert "No notes found" in first_arg


class TestEventHandlers:
    """Test event handler methods."""

    def test_on_data_table_row_selected(self, note_explorer):
        """Test row selection handler."""
        note_explorer.filtered_notes = [
            {'id': 'note1', 'title': 'First'},
            {'id': 'note2', 'title': 'Second'}
        ]
        note_explorer.show_preview = Mock()
        note_explorer.show_metadata = Mock()

        # Mock event with row key
        mock_event = Mock()
        mock_event.row_key.value = 'note2'

        note_explorer.on_data_table_row_selected(mock_event)

        assert note_explorer.selected_note['id'] == 'note2'
        note_explorer.show_preview.assert_called_once()
        note_explorer.show_metadata.assert_called_once()

    def test_on_data_table_row_selected_empty_state(self, note_explorer):
        """Test row selection with empty state key."""
        note_explorer.show_preview = Mock()
        note_explorer.show_metadata = Mock()

        mock_event = Mock()
        mock_event.row_key.value = 'empty'

        note_explorer.on_data_table_row_selected(mock_event)

        # Should not update preview/metadata for empty state
        note_explorer.show_preview.assert_not_called()
        note_explorer.show_metadata.assert_not_called()


# Integration test
class TestIntegration:
    """Integration tests for complete workflows."""

    def test_search_and_select_workflow(self, note_explorer, mock_db):
        """Test complete search and selection workflow."""
        # Setup - use dict() to create real dicts, not Mocks
        note_explorer.all_notes = [
            dict(id='1', title='Mediation Analysis', path='med.md'),
            dict(id='2', title='Causal Inference', path='causal.md'),
            dict(id='3', title='Mediation Framework', path='framework.md')
        ]
        note_explorer.update_table = Mock()
        note_explorer.update_result_count = Mock()
        note_explorer.show_preview = Mock()
        note_explorer.show_metadata = Mock()

        # Step 1: Search for "mediation"
        class FakeInput:
            id = "search-box"

        class FakeEvent:
            input = FakeInput()
            value = "mediation"

        note_explorer.on_input_changed(FakeEvent())

        # Should filter to 2 notes
        assert len(note_explorer.filtered_notes) == 2

        # Step 2: Select first result
        mock_select_event = Mock()
        mock_select_event.row_key.value = '1'

        note_explorer.on_data_table_row_selected(mock_select_event)

        # Should update preview and metadata
        assert note_explorer.selected_note['id'] == '1'
        note_explorer.show_preview.assert_called_once()
        note_explorer.show_metadata.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
