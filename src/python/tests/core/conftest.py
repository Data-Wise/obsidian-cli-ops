"""
Pytest fixtures for core layer tests.

Provides common mocks and test data for business logic testing.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
import networkx as nx

# Import core modules
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.models import Vault, Note, ScanResult, GraphMetrics, VaultStats
from core.exceptions import VaultNotFoundError, ScanError, AnalysisError


@pytest.fixture
def mock_db():
    """Mock DatabaseManager for testing."""
    db = Mock()
    db.list_vaults = Mock(return_value=[])
    db.get_vault = Mock(return_value=None)
    db.get_vault_by_path = Mock(return_value=None)
    db.list_notes = Mock(return_value=[])
    db.get_note = Mock(return_value=None)
    db.get_vault_stats = Mock(return_value=None)
    db.get_note_metrics = Mock(return_value=None)
    db.get_hub_notes = Mock(return_value=[])
    db.get_orphaned_notes = Mock(return_value=[])
    db.get_broken_links = Mock(return_value=[])
    db.delete_vault = Mock()
    return db


@pytest.fixture
def mock_scanner():
    """Mock VaultScanner for testing."""
    scanner = Mock()
    scanner.discover_vaults = Mock(return_value=[])
    scanner.scan_vault = Mock(return_value={})
    return scanner


@pytest.fixture
def mock_graph_builder():
    """Mock GraphBuilder for testing."""
    builder = Mock()
    builder.build_graph = Mock(return_value=nx.DiGraph())
    builder.calculate_metrics = Mock(return_value={})
    builder.find_clusters = Mock(return_value=[])
    return builder


@pytest.fixture
def mock_link_resolver():
    """Mock LinkResolver for testing."""
    resolver = Mock()
    resolver.resolve_all_links = Mock(return_value={'resolved': 0, 'broken': 0})
    return resolver


@pytest.fixture
def sample_vault():
    """Sample Vault object for testing."""
    return Vault(
        id='vault-123',
        name='Test Vault',
        path='/path/to/vault',
        note_count=100,
        link_count=250,
        tag_count=50,
        orphan_count=5,
        hub_count=3,
        last_scanned=datetime(2025, 1, 15, 10, 30, 0),
        created_at=datetime(2025, 1, 1, 0, 0, 0),
    )


@pytest.fixture
def sample_vault_row():
    """Sample database row for a vault."""
    return {
        'id': 'vault-123',
        'name': 'Test Vault',
        'path': '/path/to/vault',
        'note_count': 100,
        'link_count': 250,
        'tag_count': 50,
        'orphan_count': 5,
        'hub_count': 3,
        'last_scanned': datetime(2025, 1, 15, 10, 30, 0),
        'created_at': datetime(2025, 1, 1, 0, 0, 0),
    }


@pytest.fixture
def sample_note():
    """Sample Note object for testing."""
    return Note(
        id='note-456',
        vault_id='vault-123',
        title='Test Note',
        path='/path/to/vault/Test Note.md',
        content='# Test Note\n\nThis is test content.',
        word_count=5,
        tags=['test', 'sample'],
        outgoing_links=['note-789'],
        incoming_links=['note-111'],
        created_at=datetime(2025, 1, 10, 14, 20, 0),
        modified_at=datetime(2025, 1, 15, 16, 45, 0),
    )


@pytest.fixture
def sample_note_row():
    """Sample database row for a note."""
    return {
        'id': 'note-456',
        'vault_id': 'vault-123',
        'title': 'Test Note',
        'path': '/path/to/vault/Test Note.md',
        'content': '# Test Note\n\nThis is test content.',
        'word_count': 5,
        'tags': '["test", "sample"]',
        'outgoing_links': '["note-789"]',
        'incoming_links': '["note-111"]',
        'created_at': datetime(2025, 1, 10, 14, 20, 0),
        'modified_at': datetime(2025, 1, 15, 16, 45, 0),
    }


@pytest.fixture
def sample_scan_result():
    """Sample ScanResult object for testing."""
    return ScanResult(
        vault_id='vault-123',
        vault_name='Test Vault',
        vault_path='/path/to/vault',
        notes_scanned=100,
        links_found=250,
        tags_found=50,
        orphans_detected=5,
        hubs_detected=3,
        duration_seconds=2.5,
        errors=[],
        warnings=[],
    )


@pytest.fixture
def sample_graph_metrics():
    """Sample GraphMetrics object for testing."""
    return GraphMetrics(
        node_id='note-456',
        vault_id='vault-123',
        pagerank=0.05,
        in_degree=3,
        out_degree=5,
        betweenness_centrality=0.15,
        closeness_centrality=0.42,
        clustering_coefficient=0.33,
    )


@pytest.fixture
def sample_graph_metrics_row():
    """Sample database row for graph metrics."""
    return {
        'note_id': 'note-456',
        'vault_id': 'vault-123',
        'pagerank': 0.05,
        'in_degree': 3,
        'out_degree': 5,
        'betweenness_centrality': 0.15,
        'closeness_centrality': 0.42,
        'clustering_coefficient': 0.33,
    }


@pytest.fixture
def sample_vault_stats():
    """Sample VaultStats object for testing."""
    return VaultStats(
        vault_id='vault-123',
        vault_name='Test Vault',
        total_notes=100,
        total_links=250,
        total_tags=50,
        unique_tags=40,
        orphan_notes=5,
        hub_notes=3,
        broken_links=7,
        avg_links_per_note=2.5,
        avg_words_per_note=150.0,
        graph_density=0.025,
        largest_component_size=85,
    )


@pytest.fixture
def sample_vault_stats_row():
    """Sample database row for vault statistics."""
    return {
        'total_notes': 100,
        'total_links': 250,
        'total_tags': 50,
        'unique_tags': 40,
        'orphan_notes': 5,
        'hub_notes': 3,
        'broken_links': 7,
        'avg_links_per_note': 2.5,
        'avg_words_per_note': 150.0,
        'graph_density': 0.025,
        'largest_component_size': 85,
    }


@pytest.fixture
def sample_graph():
    """Sample NetworkX graph for testing."""
    G = nx.DiGraph()
    G.add_node('note-1', title='Note 1')
    G.add_node('note-2', title='Note 2')
    G.add_node('note-3', title='Note 3')
    G.add_edge('note-1', 'note-2')
    G.add_edge('note-2', 'note-3')
    G.add_edge('note-3', 'note-1')
    return G
