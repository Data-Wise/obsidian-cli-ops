"""
Unit tests for GraphBuilder and LinkResolver classes.

Tests graph construction, link resolution, and metric calculation.
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from db_manager import DatabaseManager
from graph_builder import GraphBuilder, LinkResolver


@pytest.fixture
def temp_db():
    """Create temporary database."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
        db_path = f.name
    yield db_path
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def populated_db(temp_db):
    """Create database with sample notes and links."""
    db = DatabaseManager(temp_db)

    # Add vault
    vault_id = db.add_vault('/path/vault', 'Test Vault')

    # Add notes
    note1 = db.add_note(vault_id, 'note1.md', 'Note 1', '# 1', 'h1')
    note2 = db.add_note(vault_id, 'note2.md', 'Note 2', '# 2', 'h2')
    note3 = db.add_note(vault_id, 'note3.md', 'Note 3', '# 3', 'h3')
    note4 = db.add_note(vault_id, 'note4.md', 'Note 4', '# 4', 'h4')

    # Add links: 1->2, 1->3, 2->3
    db.add_link(note1, note2, 'Note 2')
    db.add_link(note1, note3, 'Note 3')
    db.add_link(note2, note3, 'Note 3')

    return db, vault_id, [note1, note2, note3, note4]


class TestGraphBuilder:
    """Test graph construction and analysis."""

    def test_build_graph(self, populated_db):
        """Test building NetworkX graph from database."""
        db, vault_id, notes = populated_db
        builder = GraphBuilder(db)

        graph = builder.build_graph(vault_id)

        assert graph is not None
        # Should have all 4 notes as nodes
        assert len(graph.nodes()) == 4
        # Should have 3 links as edges
        assert len(graph.edges()) == 3

    def test_graph_structure(self, populated_db):
        """Test that graph has correct structure."""
        db, vault_id, notes = populated_db
        builder = GraphBuilder(db)

        graph = builder.build_graph(vault_id)

        note1, note2, note3, note4 = notes

        # Check edges
        assert graph.has_edge(note1, note2)
        assert graph.has_edge(note1, note3)
        assert graph.has_edge(note2, note3)
        assert not graph.has_edge(note3, note1)  # Directed graph

    def test_calculate_metrics(self, populated_db):
        """Test calculating graph metrics."""
        db, vault_id, notes = populated_db
        builder = GraphBuilder(db)

        graph = builder.build_graph(vault_id)
        metrics = builder.calculate_metrics(graph)

        assert metrics is not None
        assert len(metrics) == 4  # One per note

        # Each metric should have node_id and values
        for metric in metrics.values():
            assert 'pagerank' in metric
            assert 'in_degree' in metric
            assert 'out_degree' in metric

    def test_pagerank_calculation(self, populated_db):
        """Test PageRank calculation."""
        db, vault_id, notes = populated_db
        builder = GraphBuilder(db)

        graph = builder.build_graph(vault_id)
        metrics = builder.calculate_metrics(graph)

        note1, note2, note3, note4 = notes

        # Note3 has most incoming links, should have high PageRank
        note3_pagerank = metrics[note3]['pagerank']
        note4_pagerank = metrics[note4]['pagerank']  # Orphan

        assert note3_pagerank > note4_pagerank

    def test_degree_calculation(self, populated_db):
        """Test in/out degree calculation."""
        db, vault_id, notes = populated_db
        builder = GraphBuilder(db)

        graph = builder.build_graph(vault_id)
        metrics = builder.calculate_metrics(graph)

        note1, note2, note3, note4 = notes

        # Note1 has 2 outgoing links
        assert metrics[note1]['out_degree'] == 2
        # Note3 has 2 incoming links
        assert metrics[note3]['in_degree'] == 2
        # Note4 has no links
        assert metrics[note4]['in_degree'] == 0
        assert metrics[note4]['out_degree'] == 0

    def test_analyze_vault(self, populated_db):
        """Test full vault analysis."""
        db, vault_id, notes = populated_db
        builder = GraphBuilder(db)

        result = builder.analyze_vault(vault_id)

        assert result is not None
        assert 'total_nodes' in result
        assert 'total_edges' in result
        assert result['total_nodes'] == 4
        assert result['total_edges'] == 3


class TestLinkResolver:
    """Test link resolution functionality."""

    def test_resolve_exact_path(self, populated_db):
        """Test resolving link by exact path."""
        db, vault_id, notes = populated_db
        resolver = LinkResolver(db, vault_id)

        # Build cache
        resolver.build_cache()

        # Try to resolve
        target_id = resolver.resolve('note2.md', notes[0])

        assert target_id is not None
        assert target_id == notes[1]

    def test_resolve_by_title(self, populated_db):
        """Test resolving link by title."""
        db, vault_id, notes = populated_db
        resolver = LinkResolver(db, vault_id)

        resolver.build_cache()

        target_id = resolver.resolve('Note 2', notes[0])

        # Should resolve to note2
        assert target_id is not None

    def test_resolve_nonexistent(self, populated_db):
        """Test resolving non-existent link."""
        db, vault_id, notes = populated_db
        resolver = LinkResolver(db, vault_id)

        resolver.build_cache()

        target_id = resolver.resolve('NonExistent', notes[0])

        # Should return None for unresolved
        assert target_id is None

    def test_cache_building(self, populated_db):
        """Test that cache is built properly."""
        db, vault_id, notes = populated_db
        resolver = LinkResolver(db, vault_id)

        resolver.build_cache()

        # Cache should have entries
        assert len(resolver.cache) > 0


@pytest.mark.unit
class TestGraphMetrics:
    """Test specific graph metric calculations."""

    def test_centrality_on_hub_note(self, populated_db):
        """Test centrality metrics on highly connected note."""
        db, vault_id, notes = populated_db
        builder = GraphBuilder(db)

        graph = builder.build_graph(vault_id)
        metrics = builder.calculate_metrics(graph)

        note3 = notes[2]  # Most connected

        # Should have non-zero centrality
        assert metrics[note3]['betweenness'] >= 0
        assert metrics[note3]['closeness'] >= 0

    def test_clustering_coefficient(self, populated_db):
        """Test clustering coefficient calculation."""
        db, vault_id, notes = populated_db
        builder = GraphBuilder(db)

        graph = builder.build_graph(vault_id)
        metrics = builder.calculate_metrics(graph)

        # Clustering coefficients should be between 0 and 1
        for metric in metrics.values():
            assert 0 <= metric['clustering'] <= 1


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_graph(self, temp_db):
        """Test building graph with no notes."""
        db = DatabaseManager(temp_db)
        vault_id = db.add_vault('/path/vault', 'Empty Vault')

        builder = GraphBuilder(db)
        graph = builder.build_graph(vault_id)

        assert len(graph.nodes()) == 0
        assert len(graph.edges()) == 0

    def test_graph_with_no_links(self, temp_db):
        """Test graph with notes but no links."""
        db = DatabaseManager(temp_db)
        vault_id = db.add_vault('/path/vault', 'Test Vault')

        # Add notes without links
        db.add_note(vault_id, 'note1.md', 'Note 1', '# 1', 'h1')
        db.add_note(vault_id, 'note2.md', 'Note 2', '# 2', 'h2')

        builder = GraphBuilder(db)
        graph = builder.build_graph(vault_id)

        assert len(graph.nodes()) == 2
        assert len(graph.edges()) == 0

    def test_self_referencing_link(self, temp_db):
        """Test note that links to itself."""
        db = DatabaseManager(temp_db)
        vault_id = db.add_vault('/path/vault', 'Test Vault')

        note1 = db.add_note(vault_id, 'note1.md', 'Note 1', '# 1', 'h1')

        # Add self-referencing link
        db.add_link(note1, note1, 'Note 1')

        builder = GraphBuilder(db)
        graph = builder.build_graph(vault_id)

        # Should handle gracefully
        assert len(graph.nodes()) == 1
