import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import asyncio

from core.vault_manager import VaultManager
from core.exceptions import VaultNotFoundError, ScanError
from db_manager import DatabaseManager

# Remove the pytest.mark.asyncio marker as we will run async manually
# pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_db():
    """Fixture for a mocked DatabaseManager."""
    db = Mock(spec=DatabaseManager)
    # Ensure get_vault_by_path returns None by default for edge cases
    db.get_vault_by_path.return_value = None 
    db.add_vault.return_value = "vault_id_123"
    return db

@pytest.fixture
def mock_scanner():
    """Fixture for a mocked, awaitable VaultScanner."""
    scanner = Mock()
    scanner.scan_vault = AsyncMock(return_value={'notes_scanned': 10})
    return scanner

class TestVaultManagerEdgeCases:
    """Tests for edge cases and error handling in VaultManager."""

    def test_init_with_no_db_manager(self):
        """Test that VaultManager creates its own DB manager if none is provided."""
        with patch('core.vault_manager.DatabaseManager') as MockDB:
            vm = VaultManager()
            MockDB.assert_called_once()

    def test_scan_vault_with_invalid_path(self):
        """Test scan_vault with a path that doesn't exist."""
        vm = VaultManager()
        
        async def run_test():
            with pytest.raises(VaultNotFoundError):
                await vm.scan_vault("/path/that/does/not/exist")
        
        asyncio.run(run_test())

    def test_scan_vault_that_is_not_a_vault(self, tmp_path):
        """Test scan_vault on a directory that is not a valid vault."""
        vm = VaultManager()
        # A directory without a .obsidian folder
        not_a_vault_path = tmp_path / "not_a_vault"
        not_a_vault_path.mkdir()
        
        async def run_test():
            with pytest.raises(VaultNotFoundError):
                await vm.scan_vault(str(not_a_vault_path))
        
        asyncio.run(run_test())
            
    def test_scan_vault_handles_scanner_exception(self, mock_db, tmp_path):
        """Test that scan_vault properly handles exceptions from the scanner."""
        # Setup a valid vault path
        vault_path = tmp_path / "TestVault"
        vault_path.mkdir()
        (vault_path / ".obsidian").mkdir()
        
        # Configure scanner mock to raise an error
        mock_failing_scanner = Mock()
        mock_failing_scanner.scan_vault = AsyncMock(side_effect=Exception("Scanner Failed!"))

        vm = VaultManager(db_manager=mock_db)
        vm.scanner = mock_failing_scanner
        
        async def run_test():
            with pytest.raises(ScanError, match="Scan failed: Scanner Failed!"):
                await vm.scan_vault(str(vault_path))
        
        asyncio.run(run_test())

    def test_register_vault_with_null_path(self, mock_db):
        """Test registering a vault with a null or empty path."""
        vm = VaultManager(db_manager=mock_db)
        # Assuming register_vault uses pathlib which will raise TypeError on None
        with pytest.raises(TypeError):
            vm.register_vault(None)
        
        # Path("") resolves to current directory, so might pass unless specific check exists
        # Let's check for empty string if your code handles it, otherwise remove this assertion
        # based on typical Path behavior

    def test_get_vault_with_empty_or_null_id(self, mock_db):
        """Test getting a vault with an empty or null ID."""
        vm = VaultManager(db_manager=mock_db)
        # Mock the DB call to return None if called
        mock_db.get_vault.return_value = None
        
        assert vm.get_vault(None) is None
        assert vm.get_vault("") is None