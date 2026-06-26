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
        
        mock_db.return_value.get_vault_by_name_or_id.return_value = None

        cli = ObsCLI()
        with pytest.raises(SystemExit) as exc_info:
            cli.stats(vault_identifier="nonexistent123")
        
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


class TestVaultDeleteCommand:
    """Tests for `obs vault delete` (ObsCLI.delete_vault) against a real DB.

    A real in-memory DatabaseManager is injected at construction so the cascade
    behavior is genuinely exercised and the user's DB is never touched.
    """

    @staticmethod
    def _cli_with_real_db():
        from obs_cli import ObsCLI
        from db_manager import DatabaseManager
        from core.vault_manager import VaultManager
        db = DatabaseManager(db_path=":memory:")
        db.initialize_database()
        with patch('obs_cli.DatabaseManager', return_value=db), \
             patch('obs_cli.VaultManager', return_value=VaultManager(db)), \
             patch('obs_cli.GraphAnalyzer'):
            cli = ObsCLI()
        return cli, db

    @patch('obs_cli.console')
    def test_dry_run_does_not_delete(self, mock_console):
        cli, db = self._cli_with_real_db()
        vid = db.add_vault("DryRun", "/tmp/dryrun")
        db.add_note(vid, "n.md", "N", "body")

        cli.delete_vault("DryRun", force=False)

        # Vault still present and a preview Panel (titled "DRY RUN") was rendered.
        assert db.get_vault(vid) is not None
        from rich.panel import Panel
        panels = [
            a
            for call in mock_console.print.call_args_list
            for a in call.args
            if isinstance(a, Panel)
        ]
        assert panels, "expected a dry-run Panel to be printed"
        assert "DRY RUN" in str(panels[0].title)

    @patch('obs_cli.console')
    def test_force_deletes_and_cascades(self, mock_console):
        cli, db = self._cli_with_real_db()
        vid = db.add_vault("KillMe", "/tmp/killme")
        note_id = db.add_note(vid, "n.md", "N", "body")

        cli.delete_vault("KillMe", force=True)

        assert db.get_vault(vid) is None
        with db.get_connection() as conn:
            assert conn.execute(
                "SELECT 1 FROM notes WHERE id = ?", (note_id,)
            ).fetchone() is None

    @patch('obs_cli.console')
    def test_not_found_exits_nonzero(self, mock_console):
        cli, _ = self._cli_with_real_db()
        with pytest.raises(SystemExit) as exc:
            cli.delete_vault("does-not-exist", force=True)
        assert exc.value.code == 1

    def test_json_force_output(self, capsys):
        cli, db = self._cli_with_real_db()
        vid = db.add_vault("JsonVault", "/tmp/jsonvault")
        db.add_note(vid, "n.md", "N", "body")

        cli.delete_vault("JsonVault", force=True, as_json=True)

        import json as _json
        # The DB-init banner precedes our JSON; the result is the last stdout line.
        last_line = capsys.readouterr().out.strip().splitlines()[-1]
        out = _json.loads(last_line)
        assert out["deleted"] is True
        assert out["vault_id"] == vid
        assert out["notes_removed"] == 1


class TestVaultRenameInfoCommands:
    """Tests for `obs vault rename` and `obs vault info` against a real DB."""

    @staticmethod
    def _cli_with_real_db():
        from obs_cli import ObsCLI
        from db_manager import DatabaseManager
        from core.vault_manager import VaultManager
        db = DatabaseManager(db_path=":memory:")
        db.initialize_database()
        with patch('obs_cli.DatabaseManager', return_value=db), \
             patch('obs_cli.VaultManager', return_value=VaultManager(db)), \
             patch('obs_cli.GraphAnalyzer'):
            cli = ObsCLI()
        return cli, db

    @patch('obs_cli.console')
    def test_rename_updates_name(self, mock_console):
        cli, db = self._cli_with_real_db()
        vid = db.add_vault("OldName", "/tmp/old")

        cli.rename_vault("OldName", "FreshName")

        assert db.get_vault(vid)["name"] == "FreshName"

    @patch('obs_cli.console')
    def test_rename_rejects_name_collision(self, mock_console):
        cli, db = self._cli_with_real_db()
        db.add_vault("Existing", "/tmp/existing")
        db.add_vault("Mover", "/tmp/mover")

        with pytest.raises(SystemExit) as exc:
            cli.rename_vault("Mover", "Existing")
        assert exc.value.code == 1
        # Collision was blocked — Mover keeps its name.
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "already uses the name" in printed

    @patch('obs_cli.console')
    def test_rename_not_found_exits_nonzero(self, mock_console):
        cli, _ = self._cli_with_real_db()
        with pytest.raises(SystemExit) as exc:
            cli.rename_vault("ghost", "whatever")
        assert exc.value.code == 1

    def test_info_json(self, capsys):
        cli, db = self._cli_with_real_db()
        vid = db.add_vault("InfoVault", "/tmp/info")
        db.add_note(vid, "n.md", "N", "body")

        cli.info_vault("InfoVault", as_json=True)

        import json as _json
        out = _json.loads(capsys.readouterr().out.strip().splitlines()[-1])
        assert out["id"] == vid
        assert out["name"] == "InfoVault"
        assert out["notes"] == 1

    @patch('obs_cli.console')
    def test_info_not_found_exits_nonzero(self, mock_console):
        cli, _ = self._cli_with_real_db()
        with pytest.raises(SystemExit) as exc:
            cli.info_vault("ghost")
        assert exc.value.code == 1
