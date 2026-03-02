"""Tests for vault lookup by name or ID prefix."""
import pytest


class TestGetVaultByNameOrId:
    """Tests for db_manager.get_vault_by_name_or_id()."""

    def _add_vault(self, db, vault_id, name, path):
        """Helper to insert a vault directly."""
        with db.get_connection() as conn:
            conn.execute(
                "INSERT INTO vaults (id, name, path) VALUES (?, ?, ?)",
                (vault_id, name, path),
            )

    def test_exact_name_match(self, db_manager):
        self._add_vault(db_manager, "abc123def456", "Knowledge_Base", "/vaults/kb")
        result = db_manager.get_vault_by_name_or_id("Knowledge_Base")
        assert result is not None
        assert result["name"] == "Knowledge_Base"
        assert result["id"] == "abc123def456"

    def test_name_match_case_insensitive(self, db_manager):
        self._add_vault(db_manager, "abc123def456", "Knowledge_Base", "/vaults/kb")
        result = db_manager.get_vault_by_name_or_id("knowledge_base")
        assert result is not None
        assert result["name"] == "Knowledge_Base"

    def test_exact_id_match(self, db_manager):
        self._add_vault(db_manager, "abc123def456", "MyVault", "/vaults/mv")
        result = db_manager.get_vault_by_name_or_id("abc123def456")
        assert result is not None
        assert result["id"] == "abc123def456"

    def test_id_prefix_unique(self, db_manager):
        self._add_vault(db_manager, "abc123def456", "VaultA", "/vaults/a")
        self._add_vault(db_manager, "xyz789ghi012", "VaultB", "/vaults/b")
        result = db_manager.get_vault_by_name_or_id("abc1")
        assert result is not None
        assert result["name"] == "VaultA"

    def test_id_prefix_ambiguous_raises(self, db_manager):
        self._add_vault(db_manager, "abc123000000", "VaultA", "/vaults/a")
        self._add_vault(db_manager, "abc123999999", "VaultB", "/vaults/b")
        with pytest.raises(ValueError, match="Ambiguous ID prefix"):
            db_manager.get_vault_by_name_or_id("abc123")

    def test_no_match_returns_none(self, db_manager):
        self._add_vault(db_manager, "abc123def456", "MyVault", "/vaults/mv")
        result = db_manager.get_vault_by_name_or_id("nonexistent")
        assert result is None

    def test_name_takes_priority_over_id_prefix(self, db_manager):
        """If a vault name happens to look like an ID prefix, name wins."""
        self._add_vault(db_manager, "abc123def456", "abc1", "/vaults/tricky")
        self._add_vault(db_manager, "abc199900000", "Other", "/vaults/other")
        result = db_manager.get_vault_by_name_or_id("abc1")
        # Should match by name, not by ambiguous prefix
        assert result is not None
        assert result["name"] == "abc1"
