"""
Unit tests for GraphAnalyzer (core business logic).

Tests graph analysis operations without presentation layer dependencies.
Uses mocks to isolate business logic from database and graph builder.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import networkx as nx

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.graph_analyzer import GraphAnalyzer
from core.models import GraphMetrics, VaultStats
from core.exceptions import AnalysisError, VaultNotFoundError


class TestGraphAnalyzerInit:
    """Test GraphAnalyzer initialization."""

    def test_init_with_db_manager(self, mock_db):
        """Test initialization with provided DatabaseManager."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        assert analyzer.db == mock_db
        assert analyzer.graph_builder is not None
        assert analyzer.resolver is not None

    def test_init_without_db_manager(self):
        """Test initialization creates DatabaseManager if not provided."""
        with patch('core.graph_analyzer.DatabaseManager') as mock_db_class:
            analyzer = GraphAnalyzer()
            mock_db_class.assert_called_once()


class TestAnalyzeVault:
    """Test complete vault analysis functionality."""

    def test_analyze_vault_success(self, mock_db, mock_graph_builder, mock_link_resolver):
        """Test successful vault analysis."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        analyzer.graph_builder = mock_graph_builder
        analyzer.resolver = mock_link_resolver

        # Mock vault exists
        mock_db.get_vault.return_value = {
            'id': 'vault-123',
            'name': 'Test Vault',
            'path': '/test/vault',
        }

        # Mock link resolution
        mock_link_resolver.resolve_all_links.return_value = {
            'resolved': 100,
            'broken': 5,
        }

        # Mock metrics calculation
        mock_graph_builder.calculate_metrics.return_value = {
            'notes': 50,
            'edges': 120,
            'density': 0.048,
        }

        # Mock cluster detection
        mock_graph_builder.find_clusters.return_value = [
            {'note-1', 'note-2', 'note-3'},
            {'note-4', 'note-5', 'note-6', 'note-7'},
            {'note-8', 'note-9', 'note-10'},
        ]

        result = analyzer.analyze_vault('vault-123')

        assert result['vault_id'] == 'vault-123'
        assert result['vault_name'] == 'Test Vault'
        assert result['links_resolved'] == 100
        assert result['links_broken'] == 5
        assert result['total_notes'] == 50
        assert result['total_edges'] == 120
        assert result['graph_density'] == 0.048
        assert result['clusters_found'] == 3
        assert result['largest_cluster_size'] == 4

        mock_link_resolver.resolve_all_links.assert_called_once_with('vault-123', verbose=False)
        mock_graph_builder.calculate_metrics.assert_called_once_with('vault-123', verbose=False)
        mock_graph_builder.find_clusters.assert_called_once_with('vault-123', min_size=3)

    def test_analyze_vault_not_found(self, mock_db):
        """Test analysis when vault doesn't exist."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        mock_db.get_vault.return_value = None

        with pytest.raises(VaultNotFoundError, match="Vault not found"):
            analyzer.analyze_vault('nonexistent')

    def test_analyze_vault_link_resolution_error(self, mock_db, mock_link_resolver):
        """Test analysis when link resolution fails."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        analyzer.resolver = mock_link_resolver

        mock_db.get_vault.return_value = {'id': 'vault-123', 'name': 'Test'}
        mock_link_resolver.resolve_all_links.side_effect = Exception("Link resolution failed")

        with pytest.raises(AnalysisError, match="Graph analysis failed"):
            analyzer.analyze_vault('vault-123')

    def test_analyze_vault_no_clusters(self, mock_db, mock_graph_builder, mock_link_resolver):
        """Test analysis when no clusters found."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        analyzer.graph_builder = mock_graph_builder
        analyzer.resolver = mock_link_resolver

        mock_db.get_vault.return_value = {'id': 'vault-123', 'name': 'Test'}
        mock_link_resolver.resolve_all_links.return_value = {'resolved': 10, 'broken': 0}
        mock_graph_builder.calculate_metrics.return_value = {'notes': 5, 'edges': 3, 'density': 0.3}
        mock_graph_builder.find_clusters.return_value = []

        result = analyzer.analyze_vault('vault-123')

        assert result['clusters_found'] == 0
        assert result['largest_cluster_size'] == 0


class TestGetGraph:
    """Test graph building functionality."""

    def test_get_graph_success(self, mock_db, mock_graph_builder, sample_graph):
        """Test successful graph building."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        analyzer.graph_builder = mock_graph_builder

        mock_db.get_vault.return_value = {'id': 'vault-123', 'name': 'Test'}
        mock_graph_builder.build_graph.return_value = sample_graph

        result = analyzer.get_graph('vault-123')

        assert isinstance(result, nx.DiGraph)
        assert result.number_of_nodes() == 3
        mock_graph_builder.build_graph.assert_called_once_with('vault-123')

    def test_get_graph_vault_not_found(self, mock_db):
        """Test graph building when vault doesn't exist."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        mock_db.get_vault.return_value = None

        with pytest.raises(VaultNotFoundError, match="Vault not found"):
            analyzer.get_graph('nonexistent')


class TestGetNoteMetrics:
    """Test note metrics retrieval."""

    def test_get_note_metrics_success(self, mock_db, sample_graph_metrics_row):
        """Test successful note metrics retrieval."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        mock_db.get_note_metrics.return_value = sample_graph_metrics_row

        result = analyzer.get_note_metrics('note-456')

        assert result is not None
        assert isinstance(result, GraphMetrics)
        assert result.node_id == 'note-456'
        assert result.pagerank == 0.05
        assert result.in_degree == 3
        assert result.out_degree == 5
        mock_db.get_note_metrics.assert_called_once_with('note-456')

    def test_get_note_metrics_not_found(self, mock_db):
        """Test metrics retrieval when note has no metrics."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        mock_db.get_note_metrics.return_value = None

        result = analyzer.get_note_metrics('nonexistent')

        assert result is None


class TestGetHubNotes:
    """Test hub note detection."""

    def test_get_hub_notes_success(self, mock_db):
        """Test successful hub note retrieval."""
        analyzer = GraphAnalyzer(db_manager=mock_db)

        mock_db.get_vault.return_value = {'id': 'vault-123', 'name': 'Test'}
        mock_db.get_hub_notes.return_value = [
            {'id': 'hub-1', 'title': 'Hub 1', 'in_degree': 15, 'out_degree': 8},
            {'id': 'hub-2', 'title': 'Hub 2', 'in_degree': 5, 'out_degree': 12},
            {'id': 'hub-3', 'title': 'Hub 3', 'in_degree': 20, 'out_degree': 3},
        ]

        result = analyzer.get_hub_notes('vault-123', limit=10, min_links=10)

        assert len(result) == 3
        assert all(hub['in_degree'] + hub['out_degree'] >= 10 for hub in result)
        mock_db.get_hub_notes.assert_called_once_with('vault-123', limit=10)

    def test_get_hub_notes_filtered_by_min_links(self, mock_db):
        """Test hub notes are filtered by minimum links threshold."""
        analyzer = GraphAnalyzer(db_manager=mock_db)

        mock_db.get_vault.return_value = {'id': 'vault-123', 'name': 'Test'}
        mock_db.get_hub_notes.return_value = [
            {'id': 'hub-1', 'in_degree': 15, 'out_degree': 8},   # 23 total - included
            {'id': 'hub-2', 'in_degree': 3, 'out_degree': 2},    # 5 total - excluded
            {'id': 'hub-3', 'in_degree': 10, 'out_degree': 10},  # 20 total - included
        ]

        result = analyzer.get_hub_notes('vault-123', min_links=15)

        assert len(result) == 2
        assert result[0]['id'] == 'hub-1'
        assert result[1]['id'] == 'hub-3'

    def test_get_hub_notes_vault_not_found(self, mock_db):
        """Test hub notes retrieval when vault doesn't exist."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        mock_db.get_vault.return_value = None

        result = analyzer.get_hub_notes('nonexistent')

        assert result == []

    def test_get_hub_notes_none_found(self, mock_db):
        """Test hub notes retrieval when none exist."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        mock_db.get_vault.return_value = {'id': 'vault-123', 'name': 'Test'}
        mock_db.get_hub_notes.return_value = []

        result = analyzer.get_hub_notes('vault-123')

        assert result == []


class TestGetOrphanNotes:
    """Test orphan note detection."""

    def test_get_orphan_notes_success(self, mock_db):
        """Test successful orphan note retrieval."""
        analyzer = GraphAnalyzer(db_manager=mock_db)

        mock_db.get_vault.return_value = {'id': 'vault-123', 'name': 'Test'}
        mock_db.get_orphaned_notes.return_value = [
            {'id': 'orphan-1', 'title': 'Orphan 1'},
            {'id': 'orphan-2', 'title': 'Orphan 2'},
        ]

        result = analyzer.get_orphan_notes('vault-123')

        assert len(result) == 2
        assert result[0]['id'] == 'orphan-1'
        mock_db.get_orphaned_notes.assert_called_once_with('vault-123', limit=None)

    def test_get_orphan_notes_with_limit(self, mock_db):
        """Test orphan notes retrieval with limit."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        mock_db.get_vault.return_value = {'id': 'vault-123', 'name': 'Test'}
        mock_db.get_orphaned_notes.return_value = []

        analyzer.get_orphan_notes('vault-123', limit=5)

        mock_db.get_orphaned_notes.assert_called_once_with('vault-123', limit=5)

    def test_get_orphan_notes_vault_not_found(self, mock_db):
        """Test orphan notes retrieval when vault doesn't exist."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        mock_db.get_vault.return_value = None

        result = analyzer.get_orphan_notes('nonexistent')

        assert result == []


class TestGetBrokenLinks:
    """Test broken link detection."""

    def test_get_broken_links_success(self, mock_db):
        """Test successful broken link retrieval."""
        analyzer = GraphAnalyzer(db_manager=mock_db)

        mock_db.get_vault.return_value = {'id': 'vault-123', 'name': 'Test'}
        mock_db.get_broken_links.return_value = [
            {'source': 'note-1', 'target': '[[Missing Note]]'},
            {'source': 'note-2', 'target': '[[Another Missing]]'},
        ]

        result = analyzer.get_broken_links('vault-123')

        assert len(result) == 2
        mock_db.get_broken_links.assert_called_once_with('vault-123', limit=None)

    def test_get_broken_links_with_limit(self, mock_db):
        """Test broken links retrieval with limit."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        mock_db.get_vault.return_value = {'id': 'vault-123', 'name': 'Test'}
        mock_db.get_broken_links.return_value = []

        analyzer.get_broken_links('vault-123', limit=10)

        mock_db.get_broken_links.assert_called_once_with('vault-123', limit=10)

    def test_get_broken_links_vault_not_found(self, mock_db):
        """Test broken links retrieval when vault doesn't exist."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        mock_db.get_vault.return_value = None

        result = analyzer.get_broken_links('nonexistent')

        assert result == []


class TestCalculateMetrics:
    """Test metrics calculation functionality."""

    def test_calculate_metrics_success(self, mock_db, mock_graph_builder):
        """Test successful metrics calculation."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        analyzer.graph_builder = mock_graph_builder

        mock_db.get_vault.return_value = {'id': 'vault-123', 'name': 'Test'}
        mock_graph_builder.calculate_metrics.return_value = {
            'notes': 100,
            'edges': 250,
            'density': 0.025,
            'avg_degree': 5.0,
        }

        result = analyzer.calculate_metrics('vault-123')

        assert result['notes'] == 100
        assert result['edges'] == 250
        mock_graph_builder.calculate_metrics.assert_called_once_with('vault-123', verbose=False)

    def test_calculate_metrics_vault_not_found(self, mock_db):
        """Test metrics calculation when vault doesn't exist."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        mock_db.get_vault.return_value = None

        with pytest.raises(VaultNotFoundError, match="Vault not found"):
            analyzer.calculate_metrics('nonexistent')

    def test_calculate_metrics_calculation_error(self, mock_db, mock_graph_builder):
        """Test metrics calculation when graph builder fails."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        analyzer.graph_builder = mock_graph_builder

        mock_db.get_vault.return_value = {'id': 'vault-123', 'name': 'Test'}
        mock_graph_builder.calculate_metrics.side_effect = Exception("Calculation failed")

        with pytest.raises(AnalysisError, match="Metric calculation failed"):
            analyzer.calculate_metrics('vault-123')


class TestResolveLinks:
    """Test link resolution functionality."""

    def test_resolve_links_success(self, mock_db, mock_link_resolver):
        """Test successful link resolution."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        analyzer.resolver = mock_link_resolver

        mock_db.get_vault.return_value = {'id': 'vault-123', 'name': 'Test'}
        mock_link_resolver.resolve_all_links.return_value = {
            'resolved': 150,
            'broken': 10,
        }

        result = analyzer.resolve_links('vault-123')

        assert result['resolved'] == 150
        assert result['broken'] == 10
        mock_link_resolver.resolve_all_links.assert_called_once_with('vault-123', verbose=False)

    def test_resolve_links_vault_not_found(self, mock_db):
        """Test link resolution when vault doesn't exist."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        mock_db.get_vault.return_value = None

        with pytest.raises(VaultNotFoundError, match="Vault not found"):
            analyzer.resolve_links('nonexistent')


class TestFindClusters:
    """Test cluster detection functionality."""

    def test_find_clusters_success(self, mock_db, mock_graph_builder):
        """Test successful cluster detection."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        analyzer.graph_builder = mock_graph_builder

        mock_db.get_vault.return_value = {'id': 'vault-123', 'name': 'Test'}
        mock_graph_builder.find_clusters.return_value = [
            {'note-1', 'note-2', 'note-3'},
            {'note-4', 'note-5', 'note-6', 'note-7'},
        ]

        result = analyzer.find_clusters('vault-123', min_size=3)

        assert len(result) == 2
        assert len(result[0]) == 3
        assert len(result[1]) == 4
        mock_graph_builder.find_clusters.assert_called_once_with('vault-123', min_size=3)

    def test_find_clusters_custom_min_size(self, mock_db, mock_graph_builder):
        """Test cluster detection with custom minimum size."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        analyzer.graph_builder = mock_graph_builder

        mock_db.get_vault.return_value = {'id': 'vault-123', 'name': 'Test'}
        mock_graph_builder.find_clusters.return_value = []

        analyzer.find_clusters('vault-123', min_size=10)

        mock_graph_builder.find_clusters.assert_called_once_with('vault-123', min_size=10)

    def test_find_clusters_vault_not_found(self, mock_db):
        """Test cluster detection when vault doesn't exist."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        mock_db.get_vault.return_value = None

        with pytest.raises(VaultNotFoundError, match="Vault not found"):
            analyzer.find_clusters('nonexistent')


class TestGetEgoGraph:
    """Test ego graph extraction functionality."""

    def test_get_ego_graph_success(self, mock_db, mock_graph_builder, sample_graph):
        """Test successful ego graph extraction."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        analyzer.graph_builder = mock_graph_builder

        mock_db.get_note.return_value = {
            'id': 'note-1',
            'vault_id': 'vault-123',
            'title': 'Note 1',
        }
        mock_graph_builder.build_graph.return_value = sample_graph

        result = analyzer.get_ego_graph('note-1', radius=1)

        assert isinstance(result, nx.DiGraph)
        assert 'note-1' in result.nodes()

    def test_get_ego_graph_note_not_found(self, mock_db):
        """Test ego graph extraction when note doesn't exist."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        mock_db.get_note.return_value = None

        with pytest.raises(ValueError, match="Note not found"):
            analyzer.get_ego_graph('nonexistent')

    def test_get_ego_graph_note_not_in_graph(self, mock_db, mock_graph_builder):
        """Test ego graph extraction when note not in graph."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        analyzer.graph_builder = mock_graph_builder

        mock_db.get_note.return_value = {
            'id': 'note-999',
            'vault_id': 'vault-123',
        }

        # Create empty graph
        empty_graph = nx.DiGraph()
        mock_graph_builder.build_graph.return_value = empty_graph

        with pytest.raises(ValueError, match="Note not in graph"):
            analyzer.get_ego_graph('note-999')

    def test_get_ego_graph_custom_radius(self, mock_db, mock_graph_builder, sample_graph):
        """Test ego graph with custom radius."""
        analyzer = GraphAnalyzer(db_manager=mock_db)
        analyzer.graph_builder = mock_graph_builder

        mock_db.get_note.return_value = {
            'id': 'note-1',
            'vault_id': 'vault-123',
        }
        mock_graph_builder.build_graph.return_value = sample_graph

        result = analyzer.get_ego_graph('note-1', radius=2)

        assert isinstance(result, nx.DiGraph)
