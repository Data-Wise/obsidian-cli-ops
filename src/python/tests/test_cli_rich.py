"""
Unit tests for Rich CLI output commands.

Tests the enhanced CLI with Rich tables and panels.
"""
import pytest
from unittest.mock import MagicMock, patch
from io import StringIO
from datetime import datetime

# Import the CLI class
from obs_cli import ObsCLI


class TestRichCLIOutput:
    """Tests for Rich-enhanced CLI output."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock DatabaseManager."""
        db = MagicMock()
        db.get_stats.return_value = {
            'vaults': 2,
            'notes': 100,
            'links': 50,
            'tags': 25,
            'orphaned_notes': 5,
            'broken_links': 2,
        }
        return db

    @pytest.fixture
    def mock_vault(self):
        """Create a mock Vault object."""
        vault = MagicMock()
        vault.id = "abc12345"
        vault.name = "Test Vault"
        vault.path = "/path/to/vault"
        vault.note_count = 100
        vault.link_count = 50
        vault.last_scanned = datetime(2025, 12, 19, 10, 0, 0)
        return vault

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    def test_cli_initialization(self, mock_ga, mock_vm, mock_db):
        """Test CLI initializes without errors."""
        cli = ObsCLI()
        assert cli.db is not None
        assert cli.vault_manager is not None
        assert cli.graph_analyzer is not None

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    @patch('obs_cli.console')
    def test_list_vaults_empty(self, mock_console, mock_ga, mock_vm, mock_db):
        """Test list_vaults with no vaults."""
        mock_vm.return_value.list_vaults.return_value = []
        
        cli = ObsCLI()
        cli.list_vaults()
        
        # Should print "No vaults" message
        assert mock_console.print.called

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    @patch('obs_cli.console')
    def test_list_vaults_with_data(self, mock_console, mock_ga, mock_vm, mock_db, mock_vault):
        """Test list_vaults with vault data."""
        mock_vm.return_value.list_vaults.return_value = [mock_vault]
        
        cli = ObsCLI()
        cli.list_vaults()
        
        # Should print table
        assert mock_console.print.called
        # At least 3 calls: newline, table, newline
        assert mock_console.print.call_count >= 2

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    @patch('obs_cli.console')
    def test_stats_global(self, mock_console, mock_ga, mock_vm, mock_db_class):
        """Test stats command with no vault specified."""
        mock_db_class.return_value.get_stats.return_value = {
            'vaults': 2,
            'notes': 100,
            'links': 50,
            'tags': 25,
            'orphaned_notes': 5,
            'broken_links': 2,
        }
        
        cli = ObsCLI()
        cli.stats()
        
        # Should print panel
        assert mock_console.print.called

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager') 
    @patch('obs_cli.GraphAnalyzer')
    @patch('obs_cli.console')
    def test_stats_vault_not_found(self, mock_console, mock_ga, mock_vm, mock_db_class):
        """Test stats command with non-existent vault."""
        mock_db_class.return_value.get_vault.return_value = None
        
        cli = ObsCLI()
        with pytest.raises(SystemExit):
            cli.stats(vault_id="nonexistent")


class TestCLICommands:
    """Test CLI command handlers."""

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    def test_db_init(self, mock_ga, mock_vm, mock_db):
        """Test db init command."""
        cli = ObsCLI()
        cli.db_init()
        
        # Should call rebuild_database
        cli.db.rebuild_database.assert_called_once()
