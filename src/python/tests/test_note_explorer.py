"""
Unit tests for NoteExplorerScreen class.

Tests the Note Explorer TUI screen including search, filtering, sorting,
preview, and metadata display functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open, PropertyMock
from pathlib import Path
from datetime import datetime
import os
import sys

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from tui.screens.notes import NoteExplorerScreen
from core.models import Note, Vault, GraphMetrics


@pytest.fixture
def mock_vault_manager():
    """Create a mock VaultManager."""
    vm = Mock()

    # Mock vault data
    vm.get_vault.return_value = Vault(
        id='vault1',
        name='Test Vault',
        path='/tmp/test_vault'
    )

    # Mock notes data using Note objects
    vm.get_notes.return_value = [
        Note(
            id='note1',
            vault_id='vault1',
            title='First Note',
            path='notes/first.md',
            word_count=100,
            modified_at=datetime(2025, 12, 15, 10, 0, 0)
        ),
        Note(
            id='note2',
            vault_id='vault1',
            title='Second Note',
            path='notes/second.md',
            word_count=200,
            modified_at=datetime(2025, 12, 14, 9, 0, 0)
        ),
        Note(
            id='note3',
            vault_id='vault1',
            title='Third Note About Mediation',
            path='notes/third.md',
            word_count=150,
            modified_at=datetime(2025, 12, 13, 8, 0, 0)
        )
    ]

    return vm


@pytest.fixture
def mock_graph_analyzer():
    """Create a mock GraphAnalyzer."""
    ga = Mock()
    ga.get_note_metrics.return_value = GraphMetrics(
        node_id='note1',
        vault_id='vault1',
        pagerank=0.5,
        in_degree=3,
        out_degree=2
    )
    return ga


@pytest.fixture
def mock_app():
    """Create a mock Textual App."""
    app = Mock()
    app.pop_screen = Mock()
    app.push_screen = Mock()
    app.exit = Mock()
    return app


@pytest.fixture
def note_explorer(mock_vault_manager, mock_graph_analyzer, mock_app):
    """Create a NoteExplorerScreen instance with mocks."""
    with patch('tui.screens.notes.VaultManager', return_value=mock_vault_manager), \
         patch('tui.screens.notes.GraphAnalyzer', return_value=mock_graph_analyzer), \
         patch('db_manager.DatabaseManager'):
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

    def test_initialization_with_vault_id(self):
        """Test that screen initializes with vault ID and name."""
        with patch('tui.screens.notes.VaultManager'), patch('tui.screens.notes.GraphAnalyzer'):
            screen = NoteExplorerScreen(vault_id='vault1', vault_name='Test Vault')

            assert screen.vault_id == 'vault1'
            assert screen.vault_name == 'Test Vault'
            assert screen.current_sort == 'title'
            assert screen.all_notes == []
            assert screen.filtered_notes == []
            assert screen.selected_note is None

    def test_vault_manager_created(self):
        """Test that VaultManager is instantiated."""
        with patch('tui.screens.notes.VaultManager') as MockVM, patch('tui.screens.notes.GraphAnalyzer'):
            screen = NoteExplorerScreen(vault_id='vault1', vault_name='Test Vault')
            MockVM.assert_called_once()
            assert screen.vault_manager is not None


class TestDataLoading:
    """Test note data loading and refreshing."""

    def test_refresh_data_loads_notes(self, note_explorer, mock_vault_manager):
        """Test that refresh_data loads notes from database."""
        note_explorer.update_table = Mock()
        note_explorer.update_result_count = Mock()

        note_explorer.refresh_data()

        mock_vault_manager.get_notes.assert_called_once_with(vault_id='vault1')
        assert len(note_explorer.all_notes) == 3
        assert len(note_explorer.filtered_notes) == 3


class TestDataLoadingMore:
    """More tests for data loading."""

    def test_refresh_data_handles_empty_vault(self, note_explorer, mock_vault_manager):
        """Test that empty vault is handled gracefully."""
        mock_vault_manager.get_notes.return_value = []
        note_explorer.update_table = Mock()
        note_explorer.update_result_count = Mock()

        note_explorer.refresh_data()

        assert note_explorer.all_notes == []
        assert note_explorer.filtered_notes == []

    def test_refresh_data_handles_database_error(self, note_explorer, mock_vault_manager):
        """Test that database errors are caught and handled."""
        mock_vault_manager.get_notes.side_effect = Exception("Database error")
        note_explorer.update_table = Mock()
        note_explorer.update_result_count = Mock()

        note_explorer.refresh_data()

        note_explorer.notify.assert_called_once()
        assert "Database error" in str(note_explorer.notify.call_args)
        assert note_explorer.all_notes == []

    def test_large_vault_shows_warning(self, note_explorer, mock_vault_manager):
        """Test that large vaults trigger a warning notification."""
        # Create 1500 mock notes
        large_note_list = [
            Note(id=f'note{i}', vault_id='vault1', title=f'Note {i}', path=f'note{i}.md')
            for i in range(1501)
        ]
        mock_vault_manager.get_notes.return_value = large_note_list

        note_explorer.update_table = Mock()
        note_explorer.update_result_count = Mock()

        note_explorer.refresh_data()

        # Should notify about large vault
        assert note_explorer.notify.called


class TestSortFunctionality:
    """Test note sorting functionality."""

    def test_sort_by_title(self, note_explorer):
        """Test sorting notes by title."""
        notes = [
            Note(id='1', vault_id='v1', title='Zebra', path='z.md'),
            Note(id='2', vault_id='v1', title='Apple', path='a.md'),
            Note(id='3', vault_id='v1', title='Mango', path='m.md')
        ]

        sorted_notes = note_explorer._sort_notes(notes, 'title')

        assert sorted_notes[0].title == 'Apple'
        assert sorted_notes[1].title == 'Mango'
        assert sorted_notes[2].title == 'Zebra'

    def test_sort_by_word_count(self, note_explorer):
        """Test sorting notes by word count (descending)."""
        notes = [
            Note(id='1', vault_id='v1', title='First', path='1.md', word_count=100),
            Note(id='2', vault_id='v1', title='Second', path='2.md', word_count=300),
            Note(id='3', vault_id='v1', title='Third', path='3.md', word_count=200)
        ]

        sorted_notes = note_explorer._sort_notes(notes, 'word_count')

        assert sorted_notes[0].word_count == 300
        assert sorted_notes[1].word_count == 200
        assert sorted_notes[2].word_count == 100

    def test_sort_by_modified_date(self, note_explorer):
        """Test sorting notes by modified date (descending)."""
        notes = [
            Note(id='1', vault_id='v1', title='First', path='1.md', modified_at=datetime(2025, 12, 13)),
            Note(id='2', vault_id='v1', title='Second', path='2.md', modified_at=datetime(2025, 12, 15)),
            Note(id='3', vault_id='v1', title='Third', path='3.md', modified_at=datetime(2025, 12, 14))
        ]

        sorted_notes = note_explorer._sort_notes(notes, 'modified_at')

        assert sorted_notes[0].modified_at == datetime(2025, 12, 15)
        assert sorted_notes[1].modified_at == datetime(2025, 12, 14)
        assert sorted_notes[2].modified_at == datetime(2025, 12, 13)


class TestSearchFiltering:
    """Test search and filtering functionality."""

    def test_search_filters_by_title(self, note_explorer):
        """Test that search filters notes by title."""
        note_explorer.all_notes = [
            Note(id='1', vault_id='v1', title='Causal Mediation Analysis', path='1.md'),
            Note(id='2', vault_id='v1', title='Direct Effects Study', path='2.md'),
            Note(id='3', vault_id='v1', title='Mediation Framework', path='3.md')
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
        assert note_explorer.filtered_notes[0].id == '1'
        assert note_explorer.filtered_notes[1].id == '3'


class TestPreviewDisplay:
    """Test note preview functionality."""

    def test_show_preview_reads_file(self, note_explorer, mock_vault_manager):
        """Test that show_preview reads and displays note content."""
        note_explorer.selected_note = Note(
            id='note1', vault_id='vault1', title='Test', path='notes/test.md'
        )

        file_content = "# Test Note\nContent"
        mock_preview_pane = Mock()
        note_explorer.query_one = Mock(return_value=mock_preview_pane)

        with patch('builtins.open', mock_open(read_data=file_content)):
            note_explorer.show_preview()

        mock_preview_pane.update.assert_called_once()
        assert "Test Note" in str(mock_preview_pane.update.call_args)

    def test_show_preview_with_no_selection(self, note_explorer):
        """Test preview with no note selected."""
        note_explorer.selected_note = None
        mock_preview_pane = Mock()
        note_explorer.query_one = Mock(return_value=mock_preview_pane)

        note_explorer.show_preview()

        mock_preview_pane.update.assert_called_once()
        assert "No note selected" in str(mock_preview_pane.update.call_args)


class TestMetadataDisplay:
    """Test metadata display functionality."""

    def test_show_metadata_displays_note_info(self, note_explorer):
        """Test that metadata displays note information."""
        note_explorer.selected_note = Note(
            id='note1', vault_id='vault1', title='Test', path='notes/test.md',
            word_count=500, modified_at=datetime(2025, 12, 15)
        )

        mock_metadata_pane = Mock()
        note_explorer.query_one = Mock(return_value=mock_metadata_pane)

        with patch('db_manager.DatabaseManager') as MockDB:
            db_instance = MockDB.return_value
            db_instance.get_outgoing_links.return_value = []
            db_instance.get_incoming_links.return_value = []
            db_instance.get_note_tags.return_value = []

            note_explorer.show_metadata()

        mock_metadata_pane.update.assert_called_once()
        update_call = str(mock_metadata_pane.update.call_args)
        assert "500" in update_call
        assert "notes/test.md" in update_call


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

    def test_action_refresh(self, note_explorer, mock_vault_manager):
        """Test refresh action reloads data."""
        note_explorer.update_table = Mock()
        note_explorer.update_result_count = Mock()

        note_explorer.action_refresh()

        mock_vault_manager.get_notes.assert_called()
        note_explorer.notify.assert_called()


class TestUpdateMethods:
    """Test table and UI update methods."""

    def test_update_result_count_shows_filtered_total(self, note_explorer):
        """Test that result count shows filtered/total."""
        note_explorer.all_notes = [Mock(), Mock(), Mock()]
        note_explorer.filtered_notes = [Mock(), Mock()]

        mock_count_widget = Mock()
        note_explorer.query_one = Mock(return_value=mock_count_widget)

        note_explorer.update_result_count()

        mock_count_widget.update.assert_called_once()
        update_call = str(mock_count_widget.update.call_args)
        assert "2" in update_call
        assert "3" in update_call

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
