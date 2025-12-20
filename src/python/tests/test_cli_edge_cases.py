"""
Edge case unit tests for CLI commands.

Tests error handling, empty states, and boundary conditions.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


class TestVaultListEdgeCases:
    """Edge case tests for obs vaults command."""

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    @patch('obs_cli.console')
    def test_empty_vault_list(self, mock_console, mock_ga, mock_vm, mock_db):
        """Test listing when no vaults exist."""
        from obs_cli import ObsCLI
        mock_vm.return_value.list_vaults.return_value = []
        
        cli = ObsCLI()
        cli.list_vaults()
        
        # Should print empty message
        assert mock_console.print.called
        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any('No vaults' in str(c) for c in calls)

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    @patch('obs_cli.console')
    def test_vault_with_zero_notes(self, mock_console, mock_ga, mock_vm, mock_db):
        """Test vault with no notes."""
        from obs_cli import ObsCLI
        
        mock_vault = MagicMock()
        mock_vault.id = "abc12345"
        mock_vault.name = "Empty Vault"
        mock_vault.path = "/path/to/empty"
        mock_vault.note_count = 0
        mock_vault.link_count = 0
        mock_vault.last_scanned = None
        
        mock_vm.return_value.list_vaults.return_value = [mock_vault]
        
        cli = ObsCLI()
        cli.list_vaults()
        
        # Should still display table
        assert mock_console.print.called

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    @patch('obs_cli.console')
    def test_vault_never_scanned(self, mock_console, mock_ga, mock_vm, mock_db):
        """Test vault that was never scanned."""
        from obs_cli import ObsCLI
        
        mock_vault = MagicMock()
        mock_vault.id = "abc12345"
        mock_vault.name = "New Vault"
        mock_vault.path = "/path/to/new"
        mock_vault.note_count = 0
        mock_vault.link_count = 0
        mock_vault.last_scanned = None  # Never scanned
        
        mock_vm.return_value.list_vaults.return_value = [mock_vault]
        
        cli = ObsCLI()
        cli.list_vaults()
        
        # Should show pending status
        assert mock_console.print.called


class TestStatsEdgeCases:
    """Edge case tests for obs stats command."""

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    @patch('obs_cli.console')
    def test_stats_empty_database(self, mock_console, mock_ga, mock_vm, mock_db):
        """Test stats with empty database."""
        from obs_cli import ObsCLI
        
        mock_db.return_value.get_stats.return_value = {
            'vaults': 0,
            'notes': 0,
            'links': 0,
            'tags': 0,
            'orphaned_notes': 0,
            'broken_links': 0,
        }
        
        cli = ObsCLI()
        cli.stats()
        
        # Should display panel with zero counts
        assert mock_console.print.called

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    @patch('obs_cli.console')
    def test_stats_nonexistent_vault(self, mock_console, mock_ga, mock_vm, mock_db):
        """Test stats for vault that doesn't exist."""
        from obs_cli import ObsCLI
        
        mock_db.return_value.get_vault.return_value = None
        
        cli = ObsCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.stats(vault_id="nonexistent123")
        
        assert exc_info.value.code == 1

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    @patch('obs_cli.console')
    def test_stats_with_many_orphans(self, mock_console, mock_ga, mock_vm, mock_db):
        """Test stats with high orphan count (warning indicator)."""
        from obs_cli import ObsCLI
        
        mock_db.return_value.get_stats.return_value = {
            'vaults': 1,
            'notes': 100,
            'links': 10,
            'tags': 5,
            'orphaned_notes': 90,  # High orphan ratio
            'broken_links': 0,
        }
        
        cli = ObsCLI()
        cli.stats()
        
        # Should display with yellow warning color for orphans
        assert mock_console.print.called


class TestDiscoverEdgeCases:
    """Edge case tests for obs discover command."""

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    def test_discover_nonexistent_path(self, mock_ga, mock_vm, mock_db):
        """Test discovering in path that doesn't exist."""
        from obs_cli import ObsCLI
        from core.exceptions import VaultNotFoundError
        
        mock_vm.return_value.discover_vaults.side_effect = VaultNotFoundError("Path not found")
        
        cli = ObsCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.discover("/nonexistent/path")
        
        assert exc_info.value.code == 1

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    def test_discover_no_vaults_found(self, mock_ga, mock_vm, mock_db):
        """Test discovering when no vaults exist."""
        from obs_cli import ObsCLI
        
        mock_vm.return_value.discover_vaults.return_value = []
        
        cli = ObsCLI()
        # Should not raise, just print message
        cli.discover("/some/path")


class TestScanEdgeCases:
    """Edge case tests for obs scan command."""

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    def test_scan_nonexistent_vault(self, mock_ga, mock_vm, mock_db):
        """Test scanning path that doesn't exist."""
        from obs_cli import ObsCLI
        from core.exceptions import VaultNotFoundError
        
        mock_vm.return_value.scan_vault.side_effect = VaultNotFoundError("Vault not found")
        
        cli = ObsCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.scan("/nonexistent/path")
        
        assert exc_info.value.code == 1


class TestAnalyzeEdgeCases:
    """Edge case tests for obs analyze command."""

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    def test_analyze_nonexistent_vault(self, mock_ga, mock_vm, mock_db):
        """Test analyzing vault that doesn't exist."""
        from obs_cli import ObsCLI
        from core.exceptions import VaultNotFoundError
        
        mock_ga.return_value.analyze_vault.side_effect = VaultNotFoundError("Vault not found")
        
        cli = ObsCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.analyze("nonexistent123")
        
        assert exc_info.value.code == 1

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    def test_analyze_empty_vault(self, mock_ga, mock_vm, mock_db):
        """Test analyzing vault with no notes."""
        from obs_cli import ObsCLI
        
        mock_ga.return_value.analyze_vault.return_value = {
            'vault_name': 'Empty',
            'total_notes': 0,
            'total_edges': 0,
            'graph_density': 0.0,
            'clusters_found': 0,
        }
        mock_ga.return_value.get_hub_notes.return_value = []
        mock_ga.return_value.get_orphan_notes.return_value = []
        mock_ga.return_value.get_broken_links.return_value = []
        
        cli = ObsCLI()
        # Should complete without error
        cli.analyze("empty123", verbose=True)
