"""
Unit tests for VaultManager (core business logic).

Tests vault operations without presentation layer dependencies.
Uses mocks to isolate business logic from database and scanner.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.vault_manager import VaultManager
from core.models import Vault, Note, ScanResult, VaultStats
from core.exceptions import VaultNotFoundError, ScanError


class TestVaultManagerInit:
    """Test VaultManager initialization."""

    def test_init_with_db_manager(self, mock_db):
        """Test initialization with provided DatabaseManager."""
        manager = VaultManager(db_manager=mock_db)
        assert manager.db == mock_db
        assert manager.scanner is not None

    def test_init_without_db_manager(self):
        """Test initialization creates DatabaseManager if not provided."""
        with patch('core.vault_manager.DatabaseManager') as mock_db_class:
            manager = VaultManager()
            mock_db_class.assert_called_once()


class TestDiscoverVaults:
    """Test vault discovery functionality."""

    def test_discover_vaults_success(self, mock_db, mock_scanner, tmp_path):
        """Test successful vault discovery."""
        manager = VaultManager(db_manager=mock_db)
        manager.scanner = mock_scanner

        # Mock scanner to return vault paths
        mock_scanner.discover_vaults.return_value = [
            str(tmp_path / 'vault1'),
            str(tmp_path / 'vault2'),
        ]

        result = manager.discover_vaults(str(tmp_path))

        assert len(result) == 2
        assert str(tmp_path / 'vault1') in result
        assert str(tmp_path / 'vault2') in result
        mock_scanner.discover_vaults.assert_called_once_with(str(tmp_path.resolve()), verbose=False)

    def test_discover_vaults_path_not_exists(self, mock_db):
        """Test discovery with non-existent path raises error."""
        manager = VaultManager(db_manager=mock_db)

        with pytest.raises(VaultNotFoundError, match="Path does not exist"):
            manager.discover_vaults('/nonexistent/path')

    def test_discover_vaults_path_is_file(self, mock_db, tmp_path):
        """Test discovery with file path (not directory) raises error."""
        manager = VaultManager(db_manager=mock_db)

        # Create a file
        test_file = tmp_path / 'test.txt'
        test_file.write_text('test')

        with pytest.raises(VaultNotFoundError, match="Path is not a directory"):
            manager.discover_vaults(str(test_file))

    def test_discover_vaults_empty_directory(self, mock_db, mock_scanner, tmp_path):
        """Test discovery in directory with no vaults."""
        manager = VaultManager(db_manager=mock_db)
        manager.scanner = mock_scanner
        mock_scanner.discover_vaults.return_value = []

        result = manager.discover_vaults(str(tmp_path))

        assert result == []
        mock_scanner.discover_vaults.assert_called_once()


class TestListVaults:
    """Test vault listing functionality."""

    def test_list_vaults_success(self, mock_db, sample_vault_row):
        """Test successful vault listing."""
        manager = VaultManager(db_manager=mock_db)
        mock_db.list_vaults.return_value = [sample_vault_row]

        result = manager.list_vaults()

        assert len(result) == 1
        assert isinstance(result[0], Vault)
        assert result[0].id == 'vault-123'
        assert result[0].name == 'Test Vault'
        mock_db.list_vaults.assert_called_once()

    def test_list_vaults_empty(self, mock_db):
        """Test listing when no vaults registered."""
        manager = VaultManager(db_manager=mock_db)
        mock_db.list_vaults.return_value = []

        result = manager.list_vaults()

        assert result == []
        mock_db.list_vaults.assert_called_once()

    def test_list_vaults_multiple(self, mock_db):
        """Test listing multiple vaults."""
        manager = VaultManager(db_manager=mock_db)
        mock_db.list_vaults.return_value = [
            {'id': 'v1', 'name': 'Vault 1', 'path': '/v1', 'note_count': 10},
            {'id': 'v2', 'name': 'Vault 2', 'path': '/v2', 'note_count': 20},
            {'id': 'v3', 'name': 'Vault 3', 'path': '/v3', 'note_count': 30},
        ]

        result = manager.list_vaults()

        assert len(result) == 3
        assert all(isinstance(v, Vault) for v in result)
        assert [v.id for v in result] == ['v1', 'v2', 'v3']


class TestGetVault:
    """Test vault retrieval by ID."""

    def test_get_vault_success(self, mock_db, sample_vault_row):
        """Test successful vault retrieval."""
        manager = VaultManager(db_manager=mock_db)
        mock_db.get_vault.return_value = sample_vault_row

        result = manager.get_vault('vault-123')

        assert result is not None
        assert isinstance(result, Vault)
        assert result.id == 'vault-123'
        mock_db.get_vault.assert_called_once_with('vault-123')

    def test_get_vault_not_found(self, mock_db):
        """Test retrieval when vault doesn't exist."""
        manager = VaultManager(db_manager=mock_db)
        mock_db.get_vault.return_value = None

        result = manager.get_vault('nonexistent')

        assert result is None
        mock_db.get_vault.assert_called_once_with('nonexistent')


class TestGetVaultByPath:
    """Test vault retrieval by filesystem path."""

    def test_get_vault_by_path_success(self, mock_db, sample_vault_row):
        """Test successful vault retrieval by path."""
        manager = VaultManager(db_manager=mock_db)
        mock_db.get_vault_by_path.return_value = sample_vault_row

        result = manager.get_vault_by_path('/path/to/vault')

        assert result is not None
        assert isinstance(result, Vault)
        assert result.path == '/path/to/vault'
        mock_db.get_vault_by_path.assert_called_once_with('/path/to/vault')

    def test_get_vault_by_path_not_found(self, mock_db):
        """Test retrieval when vault path doesn't exist in database."""
        manager = VaultManager(db_manager=mock_db)
        mock_db.get_vault_by_path.return_value = None

        result = manager.get_vault_by_path('/nonexistent/path')

        assert result is None


class TestScanVault:
    """Test vault scanning functionality."""

    def test_scan_vault_success(self, mock_db, mock_scanner, tmp_path):
        """Test successful vault scan."""
        # Create a mock Obsidian vault
        vault_path = tmp_path / 'test_vault'
        vault_path.mkdir()
        obsidian_dir = vault_path / '.obsidian'
        obsidian_dir.mkdir()

        manager = VaultManager(db_manager=mock_db)
        manager.scanner = mock_scanner

        # Mock scanner response
        mock_scanner.scan_vault.return_value = {
            'notes_scanned': 10,
            'links_found': 25,
            'tags_found': 15,
            'orphan_count': 2,
            'hub_count': 1,
        }

        # Mock database response
        mock_db.get_vault_by_path.return_value = {
            'id': 'vault-123',
            'name': 'test_vault',
            'path': str(vault_path),
        }

        result = manager.scan_vault(str(vault_path))

        assert isinstance(result, ScanResult)
        assert result.vault_id == 'vault-123'
        assert result.vault_name == 'test_vault'
        assert result.notes_scanned == 10
        assert result.links_found == 25
        assert result.tags_found == 15
        assert result.orphans_detected == 2
        assert result.hubs_detected == 1
        assert result.duration_seconds > 0
        assert result.success is True

        mock_scanner.scan_vault.assert_called_once()

    def test_scan_vault_with_custom_name(self, mock_db, mock_scanner, tmp_path):
        """Test vault scan with custom name."""
        vault_path = tmp_path / 'test_vault'
        vault_path.mkdir()
        obsidian_dir = vault_path / '.obsidian'
        obsidian_dir.mkdir()

        manager = VaultManager(db_manager=mock_db)
        manager.scanner = mock_scanner

        mock_scanner.scan_vault.return_value = {'notes_scanned': 5}
        mock_db.get_vault_by_path.return_value = {
            'id': 'vault-456',
            'name': 'Custom Name',
            'path': str(vault_path),
        }

        result = manager.scan_vault(str(vault_path), vault_name='Custom Name')

        assert result.vault_name == 'Custom Name'

    def test_scan_vault_path_not_exists(self, mock_db):
        """Test scan with non-existent path raises error."""
        manager = VaultManager(db_manager=mock_db)

        with pytest.raises(VaultNotFoundError, match="Path does not exist"):
            manager.scan_vault('/nonexistent/path')

    def test_scan_vault_path_is_file(self, mock_db, tmp_path):
        """Test scan with file path (not directory) raises error."""
        manager = VaultManager(db_manager=mock_db)
        test_file = tmp_path / 'test.txt'
        test_file.write_text('test')

        with pytest.raises(VaultNotFoundError, match="Path is not a directory"):
            manager.scan_vault(str(test_file))

    def test_scan_vault_no_obsidian_dir(self, mock_db, tmp_path):
        """Test scan with directory that's not a vault raises error."""
        manager = VaultManager(db_manager=mock_db)
        vault_path = tmp_path / 'not_a_vault'
        vault_path.mkdir()

        with pytest.raises(VaultNotFoundError, match="Not a valid Obsidian vault"):
            manager.scan_vault(str(vault_path))

    def test_scan_vault_scanner_error(self, mock_db, mock_scanner, tmp_path):
        """Test scan when scanner raises exception."""
        vault_path = tmp_path / 'test_vault'
        vault_path.mkdir()
        obsidian_dir = vault_path / '.obsidian'
        obsidian_dir.mkdir()

        manager = VaultManager(db_manager=mock_db)
        manager.scanner = mock_scanner

        mock_scanner.scan_vault.side_effect = Exception("Scanner failed")

        with pytest.raises(ScanError, match="Scan failed"):
            manager.scan_vault(str(vault_path))

    def test_scan_vault_not_in_db_after_scan(self, mock_db, mock_scanner, tmp_path):
        """Test scan when vault not found in database after scanning."""
        vault_path = tmp_path / 'test_vault'
        vault_path.mkdir()
        obsidian_dir = vault_path / '.obsidian'
        obsidian_dir.mkdir()

        manager = VaultManager(db_manager=mock_db)
        manager.scanner = mock_scanner

        mock_scanner.scan_vault.return_value = {'notes_scanned': 5}
        mock_db.get_vault_by_path.return_value = None  # Not found after scan

        with pytest.raises(ScanError, match="Vault not found in database after scan"):
            manager.scan_vault(str(vault_path))


class TestGetVaultStats:
    """Test vault statistics retrieval."""

    def test_get_vault_stats_success(self, mock_db, sample_vault_row, sample_vault_stats_row):
        """Test successful vault statistics retrieval."""
        manager = VaultManager(db_manager=mock_db)
        mock_db.get_vault.return_value = sample_vault_row
        mock_db.get_vault_stats.return_value = sample_vault_stats_row

        result = manager.get_vault_stats('vault-123')

        assert isinstance(result, VaultStats)
        assert result.vault_id == 'vault-123'
        assert result.vault_name == 'Test Vault'
        assert result.total_notes == 100
        assert result.total_links == 250
        assert result.orphan_notes == 5
        mock_db.get_vault_stats.assert_called_once_with('vault-123')

    def test_get_vault_stats_vault_not_found(self, mock_db):
        """Test statistics retrieval when vault doesn't exist."""
        manager = VaultManager(db_manager=mock_db)
        mock_db.get_vault.return_value = None

        with pytest.raises(VaultNotFoundError, match="Vault not found"):
            manager.get_vault_stats('nonexistent')

    def test_get_vault_stats_no_stats_data(self, mock_db, sample_vault_row):
        """Test statistics retrieval when no stats available (returns empty)."""
        manager = VaultManager(db_manager=mock_db)
        mock_db.get_vault.return_value = sample_vault_row
        mock_db.get_vault_stats.return_value = None

        result = manager.get_vault_stats('vault-123')

        assert isinstance(result, VaultStats)
        assert result.vault_id == 'vault-123'
        assert result.total_notes == 0  # Empty stats


class TestGetNotes:
    """Test note retrieval functionality."""

    def test_get_notes_success(self, mock_db, sample_note_row):
        """Test successful note retrieval."""
        manager = VaultManager(db_manager=mock_db)
        mock_db.list_notes.return_value = [sample_note_row]

        result = manager.get_notes('vault-123')

        assert len(result) == 1
        assert isinstance(result[0], Note)
        assert result[0].id == 'note-456'
        mock_db.list_notes.assert_called_once_with('vault-123', limit=None, offset=0)

    def test_get_notes_with_limit_offset(self, mock_db):
        """Test note retrieval with pagination."""
        manager = VaultManager(db_manager=mock_db)
        mock_db.list_notes.return_value = []

        manager.get_notes('vault-123', limit=10, offset=20)

        mock_db.list_notes.assert_called_once_with('vault-123', limit=10, offset=20)

    def test_get_notes_empty(self, mock_db):
        """Test note retrieval when vault has no notes."""
        manager = VaultManager(db_manager=mock_db)
        mock_db.list_notes.return_value = []

        result = manager.get_notes('vault-123')

        assert result == []


class TestGetNote:
    """Test single note retrieval."""

    def test_get_note_success(self, mock_db, sample_note_row):
        """Test successful note retrieval."""
        manager = VaultManager(db_manager=mock_db)
        mock_db.get_note.return_value = sample_note_row

        result = manager.get_note('note-456')

        assert result is not None
        assert isinstance(result, Note)
        assert result.id == 'note-456'
        mock_db.get_note.assert_called_once_with('note-456')

    def test_get_note_not_found(self, mock_db):
        """Test note retrieval when note doesn't exist."""
        manager = VaultManager(db_manager=mock_db)
        mock_db.get_note.return_value = None

        result = manager.get_note('nonexistent')

        assert result is None


class TestSearchNotes:
    """Test note search functionality."""

    def test_search_notes_returns_empty_for_now(self, mock_db):
        """Test search notes returns empty list (to be implemented)."""
        manager = VaultManager(db_manager=mock_db)

        result = manager.search_notes('vault-123', 'test query')

        assert result == []


class TestDeleteVault:
    """Test vault deletion functionality."""

    def test_delete_vault_success(self, mock_db, sample_vault_row):
        """Test successful vault deletion."""
        manager = VaultManager(db_manager=mock_db)
        mock_db.get_vault.return_value = sample_vault_row

        result = manager.delete_vault('vault-123')

        assert result is True
        mock_db.delete_vault.assert_called_once_with('vault-123')

    def test_delete_vault_not_found(self, mock_db):
        """Test deletion when vault doesn't exist."""
        manager = VaultManager(db_manager=mock_db)
        mock_db.get_vault.return_value = None

        result = manager.delete_vault('nonexistent')

        assert result is False
        mock_db.delete_vault.assert_not_called()
