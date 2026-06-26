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
        mock_db_class.return_value.get_vault_by_name_or_id.return_value = None

        cli = ObsCLI()
        with pytest.raises(SystemExit):
            cli.stats(vault_identifier="nonexistent")


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


class TestScanSummaryVisibility:
    """P1: the scan summary must surface failed/unchanged/pruned counts so the S4
    error tally + the N2 short-circuit are visible where users actually look —
    not just in logs / scan_history."""

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    def test_failed_and_unchanged_are_printed(self, mock_ga, mock_vm, mock_db, capsys):
        from core.models import ScanResult
        cli = ObsCLI()
        result = ScanResult(
            vault_id="v1", vault_name="V", vault_path="/tmp/v",
            notes_scanned=10, links_found=4, tags_found=2,
            notes_pruned=3, notes_unchanged=5, notes_failed=2,
            duration_seconds=1.0,
        )
        cli._print_scan_result(result)
        out = capsys.readouterr().out
        assert "Failed: 2" in out
        assert "Unchanged: 5" in out
        assert "Pruned: 3" in out

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    def test_zero_failed_unchanged_are_not_noise(self, mock_ga, mock_vm, mock_db, capsys):
        """Clean scan stays terse — no Failed:/Unchanged: lines when both are 0."""
        from core.models import ScanResult
        cli = ObsCLI()
        result = ScanResult(vault_id="v1", vault_name="V", vault_path="/tmp/v",
                            notes_scanned=10, notes_failed=0, notes_unchanged=0)
        cli._print_scan_result(result)
        out = capsys.readouterr().out
        assert "Failed:" not in out
        assert "Unchanged:" not in out
