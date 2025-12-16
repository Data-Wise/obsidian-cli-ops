"""
Tests for Vault Browser Screen (Phase 4.2)

Tests for the VaultBrowserScreen which displays vaults and allows navigation.
"""

import pytest
from unittest.mock import Mock, patch, PropertyMock, call
from datetime import datetime
from tui.screens.vaults import VaultBrowserScreen
from core.models import Vault


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def mock_vault_manager():
    """Create a mock VaultManager."""
    vm = Mock()

    # Mock vault data as Vault objects
    vm.list_vaults.return_value = [
        Vault(
            id='1',
            name='Work Vault',
            path='/home/user/Documents/Work',
            note_count=150,
            link_count=320,
            tag_count=23,
            last_scanned=datetime(2025, 12, 15, 10, 30, 0)
        ),
        Vault(
            id='2',
            name='Personal Vault',
            path='/home/user/Documents/Personal',
            note_count=85,
            link_count=140,
            tag_count=15,
            last_scanned=datetime(2025, 12, 14, 15, 20, 0)
        ),
        Vault(
            id='3',
            name=None,  # Test unnamed vault
            path='/home/user/Documents/Unnamed',
            note_count=0,
            link_count=0,
            tag_count=0,
            last_scanned=None
        )
    ]

    # Mock vault details
    vm.get_vault.return_value = Vault(
        id='1',
        name='Work Vault',
        path='/home/user/Documents/Work',
        note_count=150,
        link_count=320,
        tag_count=23
    )

    return vm


@pytest.fixture
def mock_graph_analyzer():
    """Create a mock GraphAnalyzer."""
    ga = Mock()

    # Mock statistics (these remain as dicts since they're not domain models)
    ga.get_orphan_notes = Mock(return_value=[
        {'id': 10, 'title': 'Orphan 1'},
        {'id': 11, 'title': 'Orphan 2'}
    ])

    ga.get_hub_notes = Mock(return_value=[
        {'id': 5, 'title': 'Hub Note', 'total_degree': 45},
        {'id': 6, 'title': 'Another Hub', 'total_degree': 32}
    ])

    ga.get_broken_links = Mock(return_value=[
        {'source_id': 1, 'target_text': 'Missing Note'}
    ])

    return ga


@pytest.fixture
def mock_app():
    """Create a mock TUI app."""
    app = Mock()
    app.push_screen = Mock()
    app.pop_screen = Mock()
    app.exit = Mock()
    return app


@pytest.fixture
def vault_browser(mock_vault_manager, mock_graph_analyzer, mock_app):
    """Create a VaultBrowserScreen instance with mocks."""
    with patch('tui.screens.vaults.VaultManager') as MockVM, \
         patch('tui.screens.vaults.GraphAnalyzer') as MockGA:
        MockVM.return_value = mock_vault_manager
        MockGA.return_value = mock_graph_analyzer

        screen = VaultBrowserScreen()
        type(screen).app = PropertyMock(return_value=mock_app)
        screen.query_one = Mock(side_effect=lambda selector, widget_type=None: Mock())
        screen.notify = Mock()
        return screen


# ==============================================================================
# VaultBrowserScreen Tests
# ==============================================================================

class TestVaultBrowserScreen:
    """Tests for VaultBrowserScreen."""

    def test_vault_browser_initialization(self):
        """Test that VaultBrowserScreen can be initialized."""
        with patch('tui.screens.vaults.VaultManager'), patch('tui.screens.vaults.GraphAnalyzer'):
            screen = VaultBrowserScreen()
            assert screen is not None
            assert screen.vaults == []
            assert screen.selected_vault is None

    def test_vault_browser_bindings(self):
        """Test that VaultBrowserScreen has correct key bindings."""
        bindings = {b.key: b.action for b in VaultBrowserScreen.BINDINGS}

        assert "escape" in bindings
        assert bindings["escape"] == "back"

        assert "enter" in bindings
        assert bindings["enter"] == "select_vault"

        assert "g" in bindings
        assert bindings["g"] == "view_graph"

        assert "r" in bindings
        assert bindings["r"] == "refresh"

        assert "q" in bindings
        assert bindings["q"] == "quit"

    def test_vault_browser_has_css(self):
        """Test that VaultBrowserScreen has CSS defined."""
        assert hasattr(VaultBrowserScreen, 'CSS')
        assert len(VaultBrowserScreen.CSS) > 0

    def test_refresh_vaults_loads_data(self, vault_browser, mock_vault_manager):
        """Test that refresh_vaults loads vault data from database."""
        # Create a mock table
        mock_table = Mock()
        vault_browser.query_one = Mock(return_value=mock_table)

        # Call refresh
        vault_browser.refresh_vaults()

        # Verify database was queried
        mock_vault_manager.list_vaults.assert_called_once()

        # Verify table was updated
        mock_table.clear.assert_called_once()
        assert mock_table.add_row.call_count == 3  # 3 vaults in mock data

    def test_refresh_vaults_empty_database(self, vault_browser, mock_vault_manager):
        """Test refresh_vaults with no vaults in database."""
        mock_vault_manager.list_vaults.return_value = []

        mock_table = Mock()
        vault_browser.query_one = Mock(return_value=mock_table)

        vault_browser.refresh_vaults()

        # Should add empty message row
        mock_table.add_row.assert_called_once()
        args = mock_table.add_row.call_args[0]
        assert "No vaults found" in str(args)

    def test_refresh_vaults_formats_timestamps(self, vault_browser):
        """Test that timestamps are formatted correctly."""
        mock_table = Mock()
        vault_browser.query_one = Mock(return_value=mock_table)

        vault_browser.refresh_vaults()

        # Check that timestamps were formatted
        calls = mock_table.add_row.call_args_list
        # First vault has timestamp
        assert "2025-12-15" in str(calls[0])

    def test_refresh_vaults_handles_unnamed_vault(self, vault_browser):
        """Test that unnamed vaults are handled gracefully."""
        mock_table = Mock()
        vault_browser.query_one = Mock(return_value=mock_table)

        vault_browser.refresh_vaults()

        # Third vault has no name
        calls = mock_table.add_row.call_args_list
        # Should contain "Unnamed" placeholder
        assert any("[dim]Unnamed[/]" in str(call) or "Unnamed" in str(call) for call in calls)

    def test_refresh_vaults_shortens_long_paths(self, vault_browser, mock_vault_manager):
        """Test that long paths are shortened."""
        mock_vault_manager.list_vaults.return_value = [
            Vault(
                id='1',
                name='Vault',
                path='/very/long/path/to/a/vault/that/exceeds/forty/five/characters/in/total/length',
                note_count=10,
                link_count=20,
                last_scanned=datetime(2025, 12, 15, 10, 0, 0)
            )
        ]

        mock_table = Mock()
        vault_browser.query_one = Mock(return_value=mock_table)

        vault_browser.refresh_vaults()

        # Path should be shortened with "..."
        call_args = str(mock_table.add_row.call_args)
        if len('/very/long/path/to/a/vault/that/exceeds/forty/five/characters/in/total/length') > 45:
            assert "..." in call_args

    def test_show_vault_details_displays_statistics(self, vault_browser, mock_graph_analyzer):
        """Test that vault details shows statistics."""
        vault_browser.selected_vault = Vault(
            id='1',
            name='Work Vault',
            path='/home/user/Documents/Work',
            note_count=150,
            link_count=320,
            tag_count=23,
            last_scanned=datetime(2025, 12, 15, 10, 30, 0)
        )

        mock_panel = Mock()
        vault_browser.query_one = Mock(return_value=mock_panel)

        vault_browser.show_vault_details()

        # Verify GraphAnalyzer queries were made with correct vault ID
        mock_graph_analyzer.get_orphan_notes.assert_called_once_with('1')
        mock_graph_analyzer.get_hub_notes.assert_called_once_with('1', limit=3)
        mock_graph_analyzer.get_broken_links.assert_called_once_with('1')

        # Verify panel was updated
        mock_panel.update.assert_called_once()
        details_text = mock_panel.update.call_args[0][0]

        assert "Work Vault" in details_text
        assert "150" in details_text  # note count
        assert "320" in details_text  # link count
        assert "2" in details_text    # orphan count
        assert "1" in details_text    # broken link count

    def test_show_vault_details_no_vault_selected(self, vault_browser):
        """Test show_vault_details when no vault is selected."""
        vault_browser.selected_vault = None

        vault_browser.show_vault_details()

        # Should return early without errors
        # No assertions needed, just verify no exception

    def test_on_data_table_row_selected(self, vault_browser, mock_vault_manager):
        """Test row selection handler."""
        # Set up vault data
        vault_browser.vaults = mock_vault_manager.list_vaults()

        # Create a fake event
        class FakeRowKey:
            value = "1"

        class FakeEvent:
            row_key = FakeRowKey()

        # Mock query_one to return mock panel
        vault_browser.query_one = Mock(return_value=Mock())

        # Call handler
        vault_browser.on_data_table_row_selected(FakeEvent())

        # Verify vault was selected (Vault object, not dict)
        assert vault_browser.selected_vault is not None
        assert vault_browser.selected_vault.id == '1'

    def test_on_data_table_row_selected_empty_list(self, vault_browser):
        """Test row selection with no vaults."""
        vault_browser.vaults = []

        class FakeEvent:
            row_key = Mock(value="1")

        vault_browser.on_data_table_row_selected(FakeEvent())

        # Should handle gracefully
        assert vault_browser.selected_vault is None

    def test_action_back(self, vault_browser, mock_app):
        """Test action_back pops the screen."""
        vault_browser.action_back()

        mock_app.pop_screen.assert_called_once()

    def test_action_select_vault_with_selection(self, vault_browser, mock_app):
        """Test action_select_vault with a vault selected."""
        vault_browser.selected_vault = Vault(
            id='1',
            name='Work Vault',
            path='/home/user/Documents/Work',
            note_count=150,
            link_count=320
        )

        with patch('tui.screens.notes.NoteExplorerScreen') as MockNoteExplorer:
            vault_browser.action_select_vault()

            # Verify NoteExplorerScreen was created with correct parameters
            MockNoteExplorer.assert_called_once_with(vault_id='1', vault_name='Work Vault')

            # Verify screen was pushed
            mock_app.push_screen.assert_called_once()

    def test_action_select_vault_no_selection(self, vault_browser):
        """Test action_select_vault with no vault selected."""
        vault_browser.selected_vault = None

        vault_browser.action_select_vault()

        # Should show warning notification
        vault_browser.notify.assert_called_once()
        args = vault_browser.notify.call_args
        assert "select a vault" in args[0][0].lower()
        assert args[1]['severity'] == 'warning'

    def test_action_view_graph_with_selection(self, vault_browser, mock_app):
        """Test action_view_graph with a vault selected."""
        vault_browser.selected_vault = Vault(
            id='1',
            name='Work Vault',
            path='/home/user/Documents/Work',
            note_count=150,
            link_count=320
        )

        with patch('tui.screens.graph.GraphVisualizerScreen') as MockGraphVisualizer:
            vault_browser.action_view_graph()

            # Verify GraphVisualizerScreen was created with correct parameters
            MockGraphVisualizer.assert_called_once_with(vault_id='1', vault_name='Work Vault')

            # Verify screen was pushed
            mock_app.push_screen.assert_called_once()

    def test_action_view_graph_no_selection(self, vault_browser):
        """Test action_view_graph with no vault selected."""
        vault_browser.selected_vault = None

        vault_browser.action_view_graph()

        # Should show warning notification
        vault_browser.notify.assert_called_once()
        args = vault_browser.notify.call_args
        assert "select a vault" in args[0][0].lower()
        assert args[1]['severity'] == 'warning'

    def test_action_refresh(self, vault_browser, mock_vault_manager):
        """Test action_refresh updates vault list."""
        mock_table = Mock()
        vault_browser.query_one = Mock(return_value=mock_table)

        vault_browser.action_refresh()

        # Verify vaults were refreshed
        mock_vault_manager.list_vaults.assert_called()
        mock_table.clear.assert_called()

        # Verify notification was shown
        vault_browser.notify.assert_called_once()
        args = vault_browser.notify.call_args
        assert "refreshed" in args[0][0].lower()

    def test_action_quit(self, vault_browser, mock_app):
        """Test action_quit exits the application."""
        vault_browser.action_quit()

        mock_app.exit.assert_called_once()


# ==============================================================================
# CSS and Styling Tests
# ==============================================================================

class TestVaultBrowserCSS:
    """Tests for VaultBrowserScreen CSS."""

    def test_css_includes_container_styles(self):
        """Test that CSS includes container styles."""
        css = VaultBrowserScreen.CSS

        assert "#vault-container" in css
        assert "#title" in css
        assert "#content" in css

    def test_css_includes_table_styles(self):
        """Test that CSS includes table styles."""
        css = VaultBrowserScreen.CSS

        assert "#vault-table" in css

    def test_css_includes_details_panel_styles(self):
        """Test that CSS includes details panel styles."""
        css = VaultBrowserScreen.CSS

        assert "#details-panel" in css

    def test_css_includes_empty_message_styles(self):
        """Test that CSS includes empty message styles."""
        css = VaultBrowserScreen.CSS

        assert "#empty-message" in css


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestVaultBrowserIntegration:
    """Integration tests for VaultBrowserScreen."""

    def test_full_navigation_flow(self, vault_browser, mock_vault_manager, mock_graph_analyzer, mock_app):
        """Test complete navigation flow from vault selection to note explorer."""
        # Set up mocks - need mock_panel for show_vault_details
        mock_table = Mock()
        mock_panel = Mock()

        def query_side_effect(selector, widget_type=None):
            if "panel" in selector or "details" in selector:
                return mock_panel
            return mock_table

        vault_browser.query_one = Mock(side_effect=query_side_effect)

        # 1. Refresh vaults
        vault_browser.refresh_vaults()
        assert mock_vault_manager.list_vaults.called

        # 2. Select a vault
        vault_browser.vaults = mock_vault_manager.list_vaults()
        vault_browser.selected_vault = vault_browser.vaults[0]

        # 3. View details
        vault_browser.show_vault_details()
        assert mock_graph_analyzer.get_orphan_notes.called
        assert mock_graph_analyzer.get_hub_notes.called

        # 4. Navigate to notes
        with patch('tui.screens.notes.NoteExplorerScreen'):
            vault_browser.action_select_vault()
            assert mock_app.push_screen.called

    def test_full_graph_navigation_flow(self, vault_browser, mock_vault_manager, mock_app):
        """Test complete navigation flow to graph visualizer."""
        # Set up mocks
        mock_table = Mock()
        vault_browser.query_one = Mock(return_value=mock_table)

        # 1. Refresh vaults
        vault_browser.refresh_vaults()

        # 2. Select a vault
        vault_browser.vaults = mock_vault_manager.list_vaults()
        vault_browser.selected_vault = vault_browser.vaults[0]

        # 3. Navigate to graph
        with patch('tui.screens.graph.GraphVisualizerScreen'):
            vault_browser.action_view_graph()
            assert mock_app.push_screen.called

    def test_error_handling_with_database_issues(self, mock_app):
        """Test error handling when database has issues."""
        with patch('tui.screens.vaults.VaultManager') as MockVM, patch('tui.screens.vaults.GraphAnalyzer'):
            mock_vault_manager = Mock()
            mock_vault_manager.list_vaults.side_effect = Exception("Database error")
            MockVM.return_value = mock_vault_manager

            screen = VaultBrowserScreen()
            type(screen).app = PropertyMock(return_value=mock_app)
            screen.query_one = Mock(return_value=Mock())

            # Should propagate database errors
            with pytest.raises(Exception, match="Database error"):
                screen.refresh_vaults()
