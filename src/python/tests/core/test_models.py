"""
Unit tests for domain models.

Tests model creation, serialization, and database row conversion.
"""

import pytest
from datetime import datetime
import json

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.models import Vault, Note, ScanResult, GraphMetrics, VaultStats


class TestVaultModel:
    """Test Vault domain model."""

    def test_vault_creation(self):
        """Test creating a Vault instance."""
        vault = Vault(
            id='vault-123',
            name='Test Vault',
            path='/path/to/vault',
            note_count=50,
            link_count=100,
        )

        assert vault.id == 'vault-123'
        assert vault.name == 'Test Vault'
        assert vault.path == '/path/to/vault'
        assert vault.note_count == 50
        assert vault.link_count == 100

    def test_vault_from_db_row(self, sample_vault_row):
        """Test creating Vault from database row."""
        vault = Vault.from_db_row(sample_vault_row)

        assert vault.id == 'vault-123'
        assert vault.name == 'Test Vault'
        assert vault.path == '/path/to/vault'
        assert vault.note_count == 100
        assert vault.link_count == 250
        assert vault.tag_count == 50
        assert vault.orphan_count == 5
        assert vault.hub_count == 3
        assert vault.last_scanned == datetime(2025, 1, 15, 10, 30, 0)
        assert vault.created_at == datetime(2025, 1, 1, 0, 0, 0)

    def test_vault_from_db_row_minimal(self):
        """Test creating Vault with minimal database row."""
        row = {
            'id': 'vault-456',
            'name': 'Minimal',
            'path': '/minimal',
        }

        vault = Vault.from_db_row(row)

        assert vault.id == 'vault-456'
        assert vault.name == 'Minimal'
        assert vault.note_count == 0  # Default value
        assert vault.link_count == 0

    def test_vault_to_dict(self, sample_vault):
        """Test converting Vault to dictionary."""
        result = sample_vault.to_dict()

        assert isinstance(result, dict)
        assert result['id'] == 'vault-123'
        assert result['name'] == 'Test Vault'
        assert result['note_count'] == 100
        assert result['last_scanned'] == '2025-01-15T10:30:00'

    def test_vault_to_dict_with_none_dates(self):
        """Test converting Vault with None dates to dictionary."""
        vault = Vault(
            id='vault-789',
            name='No Dates',
            path='/path',
        )

        result = vault.to_dict()

        assert result['last_scanned'] is None
        assert result['created_at'] is None

    def test_vault_to_json(self, sample_vault):
        """Test converting Vault to JSON string."""
        result = sample_vault.to_json()

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed['id'] == 'vault-123'
        assert parsed['name'] == 'Test Vault'


class TestNoteModel:
    """Test Note domain model."""

    def test_note_creation(self):
        """Test creating a Note instance."""
        note = Note(
            id='note-123',
            vault_id='vault-456',
            title='Test Note',
            path='/vault/Test Note.md',
            content='# Test\n\nContent here.',
            word_count=10,
        )

        assert note.id == 'note-123'
        assert note.vault_id == 'vault-456'
        assert note.title == 'Test Note'
        assert note.word_count == 10

    def test_note_from_db_row(self, sample_note_row):
        """Test creating Note from database row."""
        note = Note.from_db_row(sample_note_row)

        assert note.id == 'note-456'
        assert note.vault_id == 'vault-123'
        assert note.title == 'Test Note'
        assert note.content == '# Test Note\n\nThis is test content.'
        assert note.word_count == 5
        assert note.tags == ['test', 'sample']
        assert note.outgoing_links == ['note-789']
        assert note.incoming_links == ['note-111']

    def test_note_from_db_row_with_list_tags(self):
        """Test creating Note when tags are already a list (not JSON string)."""
        row = {
            'id': 'note-999',
            'vault_id': 'vault-123',
            'title': 'Test',
            'path': '/test.md',
            'tags': ['tag1', 'tag2'],  # Already a list
            'outgoing_links': ['link1'],  # Already a list
            'incoming_links': [],
        }

        note = Note.from_db_row(row)

        assert note.tags == ['tag1', 'tag2']
        assert note.outgoing_links == ['link1']

    def test_note_to_dict(self, sample_note):
        """Test converting Note to dictionary."""
        result = sample_note.to_dict()

        assert isinstance(result, dict)
        assert result['id'] == 'note-456'
        assert result['title'] == 'Test Note'
        assert result['tags'] == ['test', 'sample']
        assert result['word_count'] == 5
        assert result['created_at'] == '2025-01-10T14:20:00'

    def test_note_to_dict_excludes_content(self, sample_note):
        """Test that to_dict doesn't include content (too large)."""
        result = sample_note.to_dict()

        assert 'content' not in result

    def test_note_with_default_fields(self):
        """Test Note with default field values."""
        note = Note(
            id='note-min',
            vault_id='vault-min',
            title='Minimal',
            path='/minimal.md',
        )

        assert note.content == ""
        assert note.word_count == 0
        assert note.tags == []
        assert note.outgoing_links == []
        assert note.incoming_links == []


class TestScanResultModel:
    """Test ScanResult domain model."""

    def test_scan_result_creation(self):
        """Test creating a ScanResult instance."""
        result = ScanResult(
            vault_id='vault-123',
            vault_name='Test Vault',
            vault_path='/test/vault',
            notes_scanned=50,
            links_found=120,
            duration_seconds=3.5,
        )

        assert result.vault_id == 'vault-123'
        assert result.notes_scanned == 50
        assert result.links_found == 120
        assert result.duration_seconds == 3.5

    def test_scan_result_success_property(self):
        """Test success property returns True when no errors."""
        result = ScanResult(
            vault_id='v1',
            vault_name='V1',
            vault_path='/v1',
            errors=[],
        )

        assert result.success is True

    def test_scan_result_success_property_with_errors(self):
        """Test success property returns False when errors exist."""
        result = ScanResult(
            vault_id='v1',
            vault_name='V1',
            vault_path='/v1',
            errors=['Error 1', 'Error 2'],
        )

        assert result.success is False

    def test_scan_result_to_dict(self, sample_scan_result):
        """Test converting ScanResult to dictionary."""
        result = sample_scan_result.to_dict()

        assert isinstance(result, dict)
        assert result['vault_id'] == 'vault-123'
        assert result['notes_scanned'] == 100
        assert result['duration_seconds'] == 2.5
        assert result['success'] is True
        assert result['errors'] == []

    def test_scan_result_to_json(self, sample_scan_result):
        """Test converting ScanResult to JSON string."""
        result = sample_scan_result.to_json()

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed['vault_name'] == 'Test Vault'
        assert parsed['notes_scanned'] == 100

    def test_scan_result_with_errors_and_warnings(self):
        """Test ScanResult with errors and warnings."""
        result = ScanResult(
            vault_id='v1',
            vault_name='V1',
            vault_path='/v1',
            errors=['Critical error'],
            warnings=['Warning 1', 'Warning 2'],
        )

        assert len(result.errors) == 1
        assert len(result.warnings) == 2
        assert result.success is False


class TestGraphMetricsModel:
    """Test GraphMetrics domain model."""

    def test_graph_metrics_creation(self):
        """Test creating a GraphMetrics instance."""
        metrics = GraphMetrics(
            node_id='note-123',
            vault_id='vault-456',
            pagerank=0.05,
            in_degree=10,
            out_degree=15,
            betweenness_centrality=0.25,
            closeness_centrality=0.5,
            clustering_coefficient=0.33,
        )

        assert metrics.node_id == 'note-123'
        assert metrics.vault_id == 'vault-456'
        assert metrics.pagerank == 0.05
        assert metrics.in_degree == 10
        assert metrics.out_degree == 15

    def test_graph_metrics_from_db_row(self, sample_graph_metrics_row):
        """Test creating GraphMetrics from database row."""
        metrics = GraphMetrics.from_db_row(sample_graph_metrics_row)

        assert metrics.node_id == 'note-456'
        assert metrics.vault_id == 'vault-123'
        assert metrics.pagerank == 0.05
        assert metrics.betweenness_centrality == 0.15
        assert metrics.closeness_centrality == 0.42

    def test_graph_metrics_from_db_row_minimal(self):
        """Test creating GraphMetrics with minimal database row."""
        row = {
            'note_id': 'note-999',
            'vault_id': 'vault-999',
        }

        metrics = GraphMetrics.from_db_row(row)

        assert metrics.node_id == 'note-999'
        assert metrics.pagerank == 0.0  # Default value
        assert metrics.in_degree == 0

    def test_graph_metrics_to_dict(self, sample_graph_metrics):
        """Test converting GraphMetrics to dictionary."""
        result = sample_graph_metrics.to_dict()

        assert isinstance(result, dict)
        assert result['node_id'] == 'note-456'
        assert result['pagerank'] == 0.05
        assert result['in_degree'] == 3
        assert result['out_degree'] == 5

    def test_graph_metrics_default_values(self):
        """Test GraphMetrics with default metric values."""
        metrics = GraphMetrics(
            node_id='note-min',
            vault_id='vault-min',
        )

        assert metrics.pagerank == 0.0
        assert metrics.in_degree == 0
        assert metrics.out_degree == 0
        assert metrics.betweenness_centrality == 0.0
        assert metrics.closeness_centrality == 0.0
        assert metrics.clustering_coefficient == 0.0


class TestVaultStatsModel:
    """Test VaultStats domain model."""

    def test_vault_stats_creation(self):
        """Test creating a VaultStats instance."""
        stats = VaultStats(
            vault_id='vault-123',
            vault_name='Test Vault',
            total_notes=100,
            total_links=250,
            orphan_notes=5,
            hub_notes=3,
        )

        assert stats.vault_id == 'vault-123'
        assert stats.vault_name == 'Test Vault'
        assert stats.total_notes == 100
        assert stats.total_links == 250

    def test_vault_stats_to_dict(self, sample_vault_stats):
        """Test converting VaultStats to dictionary."""
        result = sample_vault_stats.to_dict()

        assert isinstance(result, dict)
        assert result['vault_id'] == 'vault-123'
        assert result['total_notes'] == 100
        assert result['total_links'] == 250
        assert result['orphan_notes'] == 5
        assert result['avg_links_per_note'] == 2.5

    def test_vault_stats_to_json(self, sample_vault_stats):
        """Test converting VaultStats to JSON string."""
        result = sample_vault_stats.to_json()

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed['vault_name'] == 'Test Vault'
        assert parsed['graph_density'] == 0.025

    def test_vault_stats_default_values(self):
        """Test VaultStats with default values."""
        stats = VaultStats(
            vault_id='vault-min',
            vault_name='Minimal',
        )

        assert stats.total_notes == 0
        assert stats.total_links == 0
        assert stats.orphan_notes == 0
        assert stats.avg_links_per_note == 0.0
        assert stats.graph_density == 0.0

    def test_vault_stats_comprehensive(self, sample_vault_stats):
        """Test VaultStats with all fields populated."""
        assert sample_vault_stats.vault_id == 'vault-123'
        assert sample_vault_stats.total_notes == 100
        assert sample_vault_stats.total_links == 250
        assert sample_vault_stats.total_tags == 50
        assert sample_vault_stats.unique_tags == 40
        assert sample_vault_stats.orphan_notes == 5
        assert sample_vault_stats.hub_notes == 3
        assert sample_vault_stats.broken_links == 7
        assert sample_vault_stats.avg_links_per_note == 2.5
        assert sample_vault_stats.avg_words_per_note == 150.0
        assert sample_vault_stats.graph_density == 0.025
        assert sample_vault_stats.largest_component_size == 85


class TestModelIntegration:
    """Test interactions between models."""

    def test_vault_and_stats_consistency(self, sample_vault, sample_vault_stats):
        """Test that Vault and VaultStats have consistent data."""
        assert sample_vault.id == sample_vault_stats.vault_id
        assert sample_vault.name == sample_vault_stats.vault_name
        assert sample_vault.note_count == sample_vault_stats.total_notes

    def test_note_belongs_to_vault(self, sample_note, sample_vault):
        """Test that Note references correct Vault."""
        assert sample_note.vault_id == sample_vault.id

    def test_graph_metrics_belongs_to_vault(self, sample_graph_metrics, sample_vault):
        """Test that GraphMetrics references correct Vault."""
        assert sample_graph_metrics.vault_id == sample_vault.id


class TestModelSerialization:
    """Test JSON serialization for all models."""

    def test_vault_json_roundtrip(self, sample_vault):
        """Test Vault JSON serialization roundtrip."""
        json_str = sample_vault.to_json()
        parsed = json.loads(json_str)

        assert parsed['id'] == sample_vault.id
        assert parsed['name'] == sample_vault.name

    def test_scan_result_json_roundtrip(self, sample_scan_result):
        """Test ScanResult JSON serialization roundtrip."""
        json_str = sample_scan_result.to_json()
        parsed = json.loads(json_str)

        assert parsed['vault_id'] == sample_scan_result.vault_id
        assert parsed['notes_scanned'] == sample_scan_result.notes_scanned

    def test_vault_stats_json_roundtrip(self, sample_vault_stats):
        """Test VaultStats JSON serialization roundtrip."""
        json_str = sample_vault_stats.to_json()
        parsed = json.loads(json_str)

        assert parsed['vault_id'] == sample_vault_stats.vault_id
        assert parsed['total_notes'] == sample_vault_stats.total_notes
