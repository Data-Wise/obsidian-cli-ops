"""
Tests for Graph Visualizer Screen (Phase 4.4)

Tests for the GraphVisualizerScreen which displays knowledge graph statistics and visualizations.
"""

import pytest
from unittest.mock import Mock, patch, PropertyMock
import networkx as nx
from tui.screens.graph import GraphVisualizerScreen


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def mock_graph():
    """Create a mock NetworkX graph."""
    G = nx.DiGraph()

    # Add nodes
    for i in range(1, 6):
        G.add_node(i, title=f"Note {i}")

    # Add edges
    G.add_edge(1, 2)
    G.add_edge(1, 3)
    G.add_edge(2, 3)
    G.add_edge(3, 4)
    G.add_edge(4, 5)

    return G


@pytest.fixture
def mock_db():
    """Create a mock DatabaseManager."""
    db = Mock()

    # Mock vault data
    db.get_vault.return_value = {
        'id': 'vault1',
        'name': 'Test Vault',
        'path': '/home/user/vaults/test'
    }

    # Mock hub notes
    db.get_hub_notes.return_value = [
        {'id': 1, 'title': 'Main Hub Note', 'total_degree': 45, 'pagerank': 0.0523},
        {'id': 2, 'title': 'Secondary Hub', 'total_degree': 32, 'pagerank': 0.0389},
        {'id': 3, 'title': 'Minor Hub', 'total_degree': 18, 'pagerank': 0.0245}
    ]

    # Mock orphan notes
    db.get_orphaned_notes.return_value = [
        {'id': 10, 'title': 'Orphan Note 1'},
        {'id': 11, 'title': 'Orphan Note 2'}
    ]

    # Mock single note
    db.get_note.return_value = {
        'id': 1,
        'title': 'Test Note',
        'path': '/home/user/vaults/test/Test Note.md'
    }

    # Mock graph metrics
    db.get_graph_metrics.return_value = {
        'in_degree': 5,
        'out_degree': 3,
        'pagerank': 0.0523,
        'betweenness': 0.125,
        'closeness': 0.678,
        'clustering': 0.333
    }

    return db


@pytest.fixture
def mock_builder(mock_graph):
    """Create a mock GraphBuilder."""
    builder = Mock()
    builder.build_graph.return_value = mock_graph

    # Mock ego graph
    ego_graph = nx.DiGraph()
    ego_graph.add_node(1, title="Center Note")
    ego_graph.add_node(2, title="Connected Note 1")
    ego_graph.add_node(3, title="Connected Note 2")
    ego_graph.add_edge(1, 2)
    ego_graph.add_edge(1, 3)

    builder.get_note_neighborhood.return_value = ego_graph

    return builder


@pytest.fixture
def mock_app():
    """Create a mock TUI app."""
    app = Mock()
    app.push_screen = Mock()
    app.pop_screen = Mock()
    app.exit = Mock()
    return app


@pytest.fixture
def graph_visualizer(mock_db, mock_builder, mock_app):
    """Create a GraphVisualizerScreen instance with mocks."""
    with patch('tui.screens.graph.DatabaseManager', return_value=mock_db):
        with patch('tui.screens.graph.GraphBuilder', return_value=mock_builder):
            screen = GraphVisualizerScreen(vault_id='vault1', vault_name='Test Vault')
            type(screen).app = PropertyMock(return_value=mock_app)
            screen.query_one = Mock(side_effect=lambda selector, widget_type=None: Mock())
            screen.notify = Mock()
            return screen


# ==============================================================================
# GraphVisualizerScreen Tests
# ==============================================================================

class TestGraphVisualizerScreen:
    """Tests for GraphVisualizerScreen."""

    def test_graph_visualizer_initialization(self, mock_db, mock_builder):
        """Test that GraphVisualizerScreen can be initialized."""
        with patch('tui.screens.graph.DatabaseManager', return_value=mock_db):
            with patch('tui.screens.graph.GraphBuilder', return_value=mock_builder):
                screen = GraphVisualizerScreen(vault_id='vault1', vault_name='Test Vault')
                assert screen is not None
                assert screen.vault_id == 'vault1'
                assert screen.vault_name == 'Test Vault'
                assert screen.graph is None
                assert screen.current_view == "hubs"
                assert screen.selected_note is None

    def test_graph_visualizer_bindings(self):
        """Test that GraphVisualizerScreen has correct key bindings."""
        bindings = {b.key: b.action for b in GraphVisualizerScreen.BINDINGS}

        assert "escape" in bindings
        assert bindings["escape"] == "back"

        assert "enter" in bindings
        assert bindings["enter"] == "view_neighborhood"

        assert "h" in bindings
        assert bindings["h"] == "toggle_hubs"

        assert "o" in bindings
        assert bindings["o"] == "toggle_orphans"

        assert "c" in bindings
        assert bindings["c"] == "toggle_clusters"

        assert "n" in bindings
        assert bindings["n"] == "view_note"

        assert "r" in bindings
        assert bindings["r"] == "refresh"

        assert "q" in bindings
        assert bindings["q"] == "quit"

    def test_graph_visualizer_has_css(self):
        """Test that GraphVisualizerScreen has CSS defined."""
        assert hasattr(GraphVisualizerScreen, 'CSS')
        assert len(GraphVisualizerScreen.CSS) > 0

    def test_load_graph(self, graph_visualizer, mock_builder, mock_graph):
        """Test that load_graph builds graph from database."""
        graph_visualizer.load_graph()

        # Verify builder was called
        mock_builder.build_graph.assert_called_once_with('vault1')

        # Verify graph was set
        assert graph_visualizer.graph is not None
        assert len(graph_visualizer.graph) == 5  # 5 nodes in mock graph

    def test_load_graph_empty(self, graph_visualizer, mock_builder):
        """Test load_graph with empty graph."""
        mock_builder.build_graph.return_value = nx.DiGraph()

        graph_visualizer.load_graph()

        # Should show warning
        graph_visualizer.notify.assert_called_once()
        args = graph_visualizer.notify.call_args
        assert "no graph" in args[0][0].lower()

    def test_load_graph_error(self, graph_visualizer, mock_builder):
        """Test load_graph with error."""
        mock_builder.build_graph.side_effect = Exception("Graph build failed")

        graph_visualizer.load_graph()

        # Should show error and set graph to None
        graph_visualizer.notify.assert_called_once()
        assert graph_visualizer.graph is None

    def test_update_stats_with_graph(self, graph_visualizer, mock_graph, mock_db):
        """Test update_stats displays graph statistics."""
        graph_visualizer.graph = mock_graph

        mock_panel = Mock()
        graph_visualizer.query_one = Mock(return_value=mock_panel)

        graph_visualizer.update_stats()

        # Verify panel was updated
        mock_panel.update.assert_called_once()
        stats_text = mock_panel.update.call_args[0][0]

        # Check for key statistics
        assert "5" in stats_text  # node count
        assert "Graph Statistics" in stats_text
        assert "Density" in stats_text
        assert "Degree Distribution" in stats_text

    def test_update_stats_no_graph(self, graph_visualizer):
        """Test update_stats with no graph."""
        graph_visualizer.graph = None

        mock_panel = Mock()
        graph_visualizer.query_one = Mock(return_value=mock_panel)

        graph_visualizer.update_stats()

        # Should show "no data" message
        mock_panel.update.assert_called_once()
        stats_text = mock_panel.update.call_args[0][0]
        assert "no graph" in stats_text.lower()

    def test_update_stats_empty_graph(self, graph_visualizer):
        """Test update_stats with empty graph."""
        graph_visualizer.graph = nx.DiGraph()

        mock_panel = Mock()
        graph_visualizer.query_one = Mock(return_value=mock_panel)

        graph_visualizer.update_stats()

        # Should show "no data" message
        mock_panel.update.assert_called_once()

    def test_update_node_list_hubs(self, graph_visualizer, mock_db):
        """Test update_node_list in hubs view."""
        graph_visualizer.current_view = "hubs"

        mock_table = Mock()
        mock_table.columns = []
        graph_visualizer.query_one = Mock(return_value=mock_table)

        graph_visualizer.update_node_list()

        # Verify database was queried
        mock_db.get_hub_notes.assert_called_once_with('vault1', limit=20)

        # Verify table was populated
        assert mock_table.add_row.call_count == 3  # 3 hubs in mock data

    def test_update_node_list_orphans(self, graph_visualizer, mock_db):
        """Test update_node_list in orphans view."""
        graph_visualizer.current_view = "orphans"

        mock_table = Mock()
        mock_table.columns = []
        graph_visualizer.query_one = Mock(return_value=mock_table)

        graph_visualizer.update_node_list()

        # Verify database was queried
        mock_db.get_orphaned_notes.assert_called_once_with('vault1')

        # Verify table was populated
        assert mock_table.add_row.call_count == 2  # 2 orphans in mock data

    def test_update_node_list_clusters(self, graph_visualizer):
        """Test update_node_list in clusters view (not yet implemented)."""
        graph_visualizer.current_view = "clusters"

        mock_table = Mock()
        mock_table.columns = []
        graph_visualizer.query_one = Mock(return_value=mock_table)

        graph_visualizer.update_node_list()

        # Should show "coming soon" message
        mock_table.add_row.assert_called_once()
        args = mock_table.add_row.call_args[0]
        assert "coming soon" in str(args).lower()

    def test_render_ascii_graph_simple_small_graph(self, graph_visualizer):
        """Test ASCII rendering for small graph."""
        graph = nx.DiGraph()
        graph.add_node(1, title="Note A")
        graph.add_node(2, title="Note B")
        graph.add_edge(1, 2)

        result = graph_visualizer.render_ascii_graph_simple(graph)

        assert "Note A" in result
        assert "Note B" in result
        assert "→" in result

    def test_render_ascii_graph_simple_empty_graph(self, graph_visualizer):
        """Test ASCII rendering for empty graph."""
        graph = nx.DiGraph()

        result = graph_visualizer.render_ascii_graph_simple(graph)

        assert "no nodes" in result.lower()

    def test_render_ascii_graph_simple_large_graph(self, graph_visualizer):
        """Test ASCII rendering warns for large graph."""
        graph = nx.DiGraph()
        for i in range(35):  # > 30 nodes
            graph.add_node(i, title=f"Note {i}")

        result = graph_visualizer.render_ascii_graph_simple(graph)

        assert "too large" in result.lower()

    def test_render_ascii_graph_limits_successors(self, graph_visualizer):
        """Test ASCII rendering limits successor display."""
        graph = nx.DiGraph()
        graph.add_node(1, title="Hub")
        for i in range(2, 12):  # 10 successors
            graph.add_node(i, title=f"Note {i}")
            graph.add_edge(1, i)

        result = graph_visualizer.render_ascii_graph_simple(graph)

        # Should show "more" indicator
        assert "more" in result.lower() or "+" in result

    def test_show_ego_graph_with_connections(self, graph_visualizer, mock_db, mock_builder):
        """Test show_ego_graph displays neighborhood."""
        graph_visualizer.selected_note = 1

        mock_panel = Mock()
        graph_visualizer.query_one = Mock(return_value=mock_panel)

        graph_visualizer.show_ego_graph()

        # Verify database was queried
        mock_db.get_note.assert_called_once_with(1)
        mock_builder.get_note_neighborhood.assert_called_once_with(1, depth=1)

        # Verify panel was updated
        mock_panel.update.assert_called_once()
        viz_text = mock_panel.update.call_args[0][0]

        assert "Neighborhood" in viz_text
        assert "Metrics" in viz_text

    def test_show_ego_graph_orphan_note(self, graph_visualizer, mock_db, mock_builder):
        """Test show_ego_graph for orphan note."""
        graph_visualizer.selected_note = 10

        mock_builder.get_note_neighborhood.return_value = nx.DiGraph()

        mock_panel = Mock()
        graph_visualizer.query_one = Mock(return_value=mock_panel)

        graph_visualizer.show_ego_graph()

        # Should show "orphan" message
        mock_panel.update.assert_called_once()
        viz_text = mock_panel.update.call_args[0][0]
        assert "orphan" in viz_text.lower()

    def test_show_ego_graph_note_not_found(self, graph_visualizer, mock_db):
        """Test show_ego_graph when note doesn't exist."""
        graph_visualizer.selected_note = 999
        mock_db.get_note.return_value = None

        mock_panel = Mock()
        graph_visualizer.query_one = Mock(return_value=mock_panel)

        graph_visualizer.show_ego_graph()

        # Should show error message
        mock_panel.update.assert_called_once()
        viz_text = mock_panel.update.call_args[0][0]
        assert "not found" in viz_text.lower()

    def test_show_ego_graph_no_selection(self, graph_visualizer):
        """Test show_ego_graph with no note selected."""
        graph_visualizer.selected_note = None

        graph_visualizer.show_ego_graph()

        # Should return early without errors
        # No assertions needed, just verify no exception

    def test_on_data_table_row_selected(self, graph_visualizer, mock_builder):
        """Test row selection handler."""
        class FakeRowKey:
            value = "1"

        class FakeEvent:
            row_key = FakeRowKey()

        graph_visualizer.on_data_table_row_selected(FakeEvent())

        # Verify note was selected and ego graph shown
        assert graph_visualizer.selected_note == "1"
        mock_builder.get_note_neighborhood.assert_called_once()

    def test_on_data_table_row_selected_empty_key(self, graph_visualizer):
        """Test row selection with empty key."""
        class FakeEvent:
            row_key = Mock(value="empty")

        graph_visualizer.on_data_table_row_selected(FakeEvent())

        # Should not select note
        assert graph_visualizer.selected_note is None

    def test_action_back(self, graph_visualizer, mock_app):
        """Test action_back pops the screen."""
        graph_visualizer.action_back()

        mock_app.pop_screen.assert_called_once()

    def test_action_quit(self, graph_visualizer, mock_app):
        """Test action_quit exits the application."""
        graph_visualizer.action_quit()

        mock_app.exit.assert_called_once()

    def test_action_refresh(self, graph_visualizer, mock_builder):
        """Test action_refresh reloads graph."""
        mock_table = Mock()
        mock_table.columns = []
        mock_panel = Mock()

        def query_side_effect(selector, widget_type=None):
            if "table" in selector:
                return mock_table
            return mock_panel

        graph_visualizer.query_one = Mock(side_effect=query_side_effect)

        graph_visualizer.action_refresh()

        # Verify graph was reloaded
        mock_builder.build_graph.assert_called()

        # Verify notification was shown
        graph_visualizer.notify.assert_called_once()
        args = graph_visualizer.notify.call_args
        assert "refreshed" in args[0][0].lower()

    def test_action_toggle_hubs(self, graph_visualizer, mock_db):
        """Test action_toggle_hubs switches to hubs view."""
        graph_visualizer.current_view = "orphans"

        mock_table = Mock()
        mock_table.columns = []
        graph_visualizer.query_one = Mock(return_value=mock_table)

        graph_visualizer.action_toggle_hubs()

        # Verify view was changed
        assert graph_visualizer.current_view == "hubs"

        # Verify database was queried
        mock_db.get_hub_notes.assert_called()

        # Verify notification was shown
        graph_visualizer.notify.assert_called_once()

    def test_action_toggle_orphans(self, graph_visualizer, mock_db):
        """Test action_toggle_orphans switches to orphans view."""
        graph_visualizer.current_view = "hubs"

        mock_table = Mock()
        mock_table.columns = []
        graph_visualizer.query_one = Mock(return_value=mock_table)

        graph_visualizer.action_toggle_orphans()

        # Verify view was changed
        assert graph_visualizer.current_view == "orphans"

        # Verify database was queried
        mock_db.get_orphaned_notes.assert_called()

        # Verify notification was shown
        graph_visualizer.notify.assert_called_once()

    def test_action_toggle_clusters(self, graph_visualizer):
        """Test action_toggle_clusters switches to clusters view."""
        graph_visualizer.current_view = "hubs"

        mock_table = Mock()
        mock_table.columns = []
        graph_visualizer.query_one = Mock(return_value=mock_table)

        graph_visualizer.action_toggle_clusters()

        # Verify view was changed
        assert graph_visualizer.current_view == "clusters"

        # Verify notification mentions "coming soon"
        graph_visualizer.notify.assert_called_once()
        args = graph_visualizer.notify.call_args
        assert "coming soon" in args[0][0].lower()

    def test_action_view_neighborhood_with_selection(self, graph_visualizer, mock_builder):
        """Test action_view_neighborhood with note selected."""
        graph_visualizer.selected_note = 1

        mock_panel = Mock()
        graph_visualizer.query_one = Mock(return_value=mock_panel)

        graph_visualizer.action_view_neighborhood()

        # Verify ego graph was shown
        mock_builder.get_note_neighborhood.assert_called()

    def test_action_view_neighborhood_no_selection(self, graph_visualizer):
        """Test action_view_neighborhood with no note selected."""
        graph_visualizer.selected_note = None

        graph_visualizer.action_view_neighborhood()

        # Should show warning notification
        graph_visualizer.notify.assert_called_once()
        args = graph_visualizer.notify.call_args
        assert "no note" in args[0][0].lower()

    def test_action_view_note_with_selection(self, graph_visualizer, mock_app, mock_db):
        """Test action_view_note navigates to note explorer."""
        graph_visualizer.selected_note = 1

        with patch('tui.screens.notes.NoteExplorerScreen') as MockNoteExplorer:
            graph_visualizer.action_view_note()

            # Verify NoteExplorerScreen was created
            MockNoteExplorer.assert_called_once()

            # Verify screen was pushed
            mock_app.push_screen.assert_called_once()

    def test_action_view_note_no_selection(self, graph_visualizer):
        """Test action_view_note with no note selected."""
        graph_visualizer.selected_note = None

        graph_visualizer.action_view_note()

        # Should show warning notification
        graph_visualizer.notify.assert_called_once()
        args = graph_visualizer.notify.call_args
        assert "no note" in args[0][0].lower()


# ==============================================================================
# CSS and Styling Tests
# ==============================================================================

class TestGraphVisualizerCSS:
    """Tests for GraphVisualizerScreen CSS."""

    def test_css_includes_container_styles(self):
        """Test that CSS includes container styles."""
        css = GraphVisualizerScreen.CSS

        assert "#graph-container" in css
        assert "#title" in css
        assert "#main-area" in css

    def test_css_includes_panel_styles(self):
        """Test that CSS includes panel styles."""
        css = GraphVisualizerScreen.CSS

        assert "#left-panel" in css
        assert "#stats-panel" in css
        assert "#viz-panel" in css

    def test_css_includes_table_styles(self):
        """Test that CSS includes table styles."""
        css = GraphVisualizerScreen.CSS

        assert "#node-table" in css


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestGraphVisualizerIntegration:
    """Integration tests for GraphVisualizerScreen."""

    def test_full_visualization_flow(self, graph_visualizer, mock_graph, mock_builder, mock_db):
        """Test complete visualization flow."""
        # Set up mocks
        mock_table = Mock()
        mock_table.columns = []
        mock_panel = Mock()

        def query_side_effect(selector, widget_type=None):
            if "table" in selector:
                return mock_table
            return mock_panel

        graph_visualizer.query_one = Mock(side_effect=query_side_effect)

        # 1. Load graph
        graph_visualizer.load_graph()
        assert graph_visualizer.graph is not None

        # 2. Update stats
        graph_visualizer.update_stats()
        assert mock_panel.update.called

        # 3. Update node list
        graph_visualizer.update_node_list()
        assert mock_db.get_hub_notes.called

        # 4. Select a node
        graph_visualizer.selected_note = 1

        # 5. Show ego graph
        graph_visualizer.show_ego_graph()
        assert mock_builder.get_note_neighborhood.called

    def test_view_switching_flow(self, graph_visualizer, mock_db):
        """Test switching between different views."""
        mock_table = Mock()
        mock_table.columns = []
        graph_visualizer.query_one = Mock(return_value=mock_table)

        # Start with hubs
        assert graph_visualizer.current_view == "hubs"

        # Switch to orphans
        graph_visualizer.action_toggle_orphans()
        assert graph_visualizer.current_view == "orphans"
        mock_db.get_orphaned_notes.assert_called()

        # Switch to clusters
        graph_visualizer.action_toggle_clusters()
        assert graph_visualizer.current_view == "clusters"

        # Switch back to hubs
        graph_visualizer.action_toggle_hubs()
        assert graph_visualizer.current_view == "hubs"

    def test_error_recovery(self, graph_visualizer, mock_builder):
        """Test error handling and recovery."""
        # Cause an error in graph loading
        mock_builder.build_graph.side_effect = Exception("Failed")

        graph_visualizer.load_graph()

        # Should handle error gracefully
        assert graph_visualizer.graph is None
        graph_visualizer.notify.assert_called()

        # Reset and try again
        mock_builder.build_graph.side_effect = None
        mock_builder.build_graph.return_value = nx.DiGraph()

        graph_visualizer.load_graph()

        # Should work now
        assert graph_visualizer.graph is not None
