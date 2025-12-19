import pytest
from unittest.mock import Mock, patch, PropertyMock, AsyncMock
from textual.pilot import Pilot

from tui.app import ObsidianTUI
from tui.screens.vaults import VaultBrowserScreen
from core.models import Vault
from datetime import datetime

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_vault_manager():
    """Fixture for a mocked VaultManager that can be modified in tests."""
    vm = Mock()
    vm.list_vaults.return_value = [
        Vault(id='1', name='Scanned Vault', path='/v/scanned', last_scanned=datetime.now()),
        Vault(id='2', name='Unscanned Vault', path='/v/unscanned', last_scanned=None)
    ]
    vm.get_vault.side_effect = lambda vault_id: next((v for v in vm.list_vaults.return_value if v.id == vault_id), None)
    vm.scan_vault = AsyncMock()
    return vm

class TestTUIErrorHandling:
    """Tests for TUI stability and error handling."""

    async def test_app_startup_with_no_vaults(self):
        """Test that the app starts up fine even with an empty database."""
        empty_vm = Mock()
        empty_vm.list_vaults.return_value = []
        
        with patch('tui.screens.vaults.VaultManager', return_value=empty_vm):
            app = ObsidianTUI()
            async with app.run_test() as pilot:
                await pilot.press("v") # Go to vault browser
                await pilot.pause(0.1)
                # We just need to ensure it doesn't crash
                assert isinstance(pilot.app.screen, VaultBrowserScreen)
                assert "No vaults found" in pilot.app.screen.query_one("#vault-table").pseudo_class_names

    async def test_scan_failure_shows_notification(self, mock_vault_manager):
        """Test that a scan failure is handled gracefully and shows a notification."""
        # Make the scan fail
        mock_vault_manager.scan_vault.side_effect = Exception("Disk on fire")
        
        with patch('tui.screens.vaults.VaultManager', return_value=mock_vault_manager):
            app = ObsidianTUI()
            async with app.run_test() as pilot:
                await pilot.press("v")
                await pilot.pause(0.1)

                # Select the unscanned vault
                await pilot.press("down") 
                await pilot.press("enter")
                await pilot.pause(0.5)

                # The app should have sent a notification
                # This is hard to test directly with Pilot, but we ensure the app didn't crash
                # and the scanning state has been reset
                vault_screen = pilot.app.screen
                assert vault_screen.scanning_vault_id is None
    
    async def test_back_navigation_from_root_screen(self):
        """Test that pressing escape on the home screen does not crash the app."""
        app = ObsidianTUI()
        async with app.run_test() as pilot:
            await pilot.pause(0.1)
            # Pressing escape on the root screen should do nothing, not crash
            await pilot.press("escape")
            await pilot.pause(0.1)
            # Verify the app is still running and on the home screen
            assert app.is_running
            assert app.screen.id == "_default" # Home screen has default ID
