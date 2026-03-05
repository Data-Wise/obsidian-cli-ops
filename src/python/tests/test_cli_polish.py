"""
Tests for CLI polish improvements (Phase 7.3 Increment 4).

- Recovery suggestions on vault not found
- --force flag on db init
- --verbose wiring for stats
"""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path


class TestVaultNotFoundRecovery:
    """Vault-not-found errors should include recovery tips."""

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    def test_analyze_vault_not_found_shows_tips(self, mock_ga, mock_vm, mock_db, capsys):
        """analyze() prints recovery tips when vault is not found."""
        from obs_cli import ObsCLI

        mock_db.return_value.get_vault_by_name_or_id.return_value = None

        cli = ObsCLI()
        with pytest.raises(SystemExit):
            cli.analyze("nonexistent")

        captured = capsys.readouterr()
        assert "Tip:" in captured.out
        assert "obs discover" in captured.out

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    @patch('obs_cli.console')
    def test_stats_vault_not_found_shows_tips(self, mock_console, mock_ga, mock_vm, mock_db):
        """stats() prints recovery tips when vault is not found."""
        from obs_cli import ObsCLI

        mock_db.return_value.get_vault_by_name_or_id.return_value = None

        cli = ObsCLI()
        with pytest.raises(SystemExit):
            cli.stats(vault_identifier="nonexistent")

        # Check that console.print was called with tip text
        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("Tip:" in c for c in calls)


class TestDbInitForceFlag:
    """db init --force flag guards against accidental reinit."""

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    @patch('obs_cli.console')
    def test_db_init_warns_existing(self, mock_console, mock_ga, mock_vm, mock_db):
        """db init warns when database already exists and --force not set."""
        from obs_cli import main
        import sys

        # Mock Path("~/.config/obs/vault_db.sqlite").expanduser().exists()
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True

        with patch.object(sys, 'argv', ['obs_cli', 'db', 'init']), \
             patch('obs_cli.Path') as mock_path_cls:
            mock_path_cls.return_value.expanduser.return_value = mock_path_instance
            main()

        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("already exists" in c for c in calls)

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    @patch('obs_cli.console')
    def test_db_init_force_proceeds(self, mock_console, mock_ga, mock_vm, mock_db):
        """db init --force proceeds even when database exists."""
        from obs_cli import main
        import sys

        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True

        with patch.object(sys, 'argv', ['obs_cli', 'db', 'init', '--force']), \
             patch('obs_cli.Path') as mock_path_cls:
            mock_path_cls.return_value.expanduser.return_value = mock_path_instance
            main()

        # Should have called rebuild_database (via db_init)
        mock_db.return_value.rebuild_database.assert_called_once()


class TestVerboseStats:
    """--verbose flag on stats shows extra detail."""

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    @patch('obs_cli.console')
    def test_verbose_stats_shows_top_notes(self, mock_console, mock_ga, mock_vm, mock_db):
        """stats with verbose shows top notes by link count."""
        from obs_cli import ObsCLI

        mock_vault = {'id': 'abc123', 'name': 'Test', 'path': '/tmp/test',
                       'last_scanned': '2026-01-01'}
        mock_db.return_value.get_vault_by_name_or_id.return_value = mock_vault
        mock_db.return_value.list_notes.return_value = [
            {'id': 'n1', 'title': 'Note1'},
            {'id': 'n2', 'title': 'Note2'},
        ]
        mock_db.return_value.get_outgoing_links.return_value = [{'id': 'l1'}]
        mock_db.return_value.get_tag_stats.return_value = []
        mock_db.return_value.get_orphaned_notes.return_value = []
        mock_db.return_value.get_hub_notes.return_value = []
        mock_db.return_value.get_broken_links.return_value = []

        cli = ObsCLI()
        cli.stats(vault_identifier="Test", verbose=True)

        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("Top notes" in c for c in calls)

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    @patch('obs_cli.console')
    def test_non_verbose_stats_no_top_notes(self, mock_console, mock_ga, mock_vm, mock_db):
        """stats without verbose does not show top notes."""
        from obs_cli import ObsCLI

        mock_vault = {'id': 'abc123', 'name': 'Test', 'path': '/tmp/test',
                       'last_scanned': '2026-01-01'}
        mock_db.return_value.get_vault_by_name_or_id.return_value = mock_vault
        mock_db.return_value.list_notes.return_value = [
            {'id': 'n1', 'title': 'Note1'},
        ]
        mock_db.return_value.get_outgoing_links.return_value = [{'id': 'l1'}]
        mock_db.return_value.get_tag_stats.return_value = []
        mock_db.return_value.get_orphaned_notes.return_value = []
        mock_db.return_value.get_hub_notes.return_value = []
        mock_db.return_value.get_broken_links.return_value = []

        cli = ObsCLI()
        cli.stats(vault_identifier="Test", verbose=False)

        calls = [str(c) for c in mock_console.print.call_args_list]
        assert not any("Top notes" in c for c in calls)
