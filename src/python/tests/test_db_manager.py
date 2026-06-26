"""Unit tests for DatabaseManager."""

import pytest

from db_manager import DatabaseManager


@pytest.fixture
def db():
    """In-memory DatabaseManager with the full schema applied."""
    manager = DatabaseManager(db_path=":memory:")
    manager.initialize_database()
    return manager


class TestDeleteVault:
    """Tests for DatabaseManager.delete_vault and its FK cascade."""

    def test_delete_vault_removes_vault_and_cascades_notes(self, db):
        """Deleting a vault removes its row and cascades to child notes."""
        vault_id = db.add_vault(name="TestVault", path="/tmp/test-vault")
        note_id = db.add_note(
            vault_id=vault_id,
            path="note.md",
            title="A Note",
            content="hello world",
        )

        # Preconditions: both rows exist.
        assert db.get_vault(vault_id) is not None
        with db.get_connection() as conn:
            assert conn.execute(
                "SELECT 1 FROM notes WHERE id = ?", (note_id,)
            ).fetchone() is not None

        deleted = db.delete_vault(vault_id)

        assert deleted is True
        # Vault row is gone.
        assert db.get_vault(vault_id) is None
        # Child note row was cascaded away (ON DELETE CASCADE + foreign_keys=ON).
        with db.get_connection() as conn:
            assert conn.execute(
                "SELECT COUNT(*) AS c FROM notes WHERE vault_id = ?", (vault_id,)
            ).fetchone()["c"] == 0
            assert conn.execute(
                "SELECT 1 FROM notes WHERE id = ?", (note_id,)
            ).fetchone() is None

    def test_delete_vault_returns_false_when_missing(self, db):
        """Deleting an unknown vault id reports no row removed."""
        assert db.delete_vault("does-not-exist") is False
