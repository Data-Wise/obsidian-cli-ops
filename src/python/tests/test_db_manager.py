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


class TestRenameVault:
    """Tests for DatabaseManager.rename_vault."""

    def test_rename_changes_name_only(self, db):
        """Renaming updates the name but leaves id and path intact."""
        vault_id = db.add_vault(name="OldName", path="/tmp/rename-vault")

        renamed = db.rename_vault(vault_id, "NewName")

        assert renamed is True
        row = db.get_vault(vault_id)
        assert row["name"] == "NewName"
        assert row["id"] == vault_id
        assert row["path"] == "/tmp/rename-vault"

    def test_rename_returns_false_when_missing(self, db):
        """Renaming an unknown vault id reports no row updated."""
        assert db.rename_vault("does-not-exist", "Whatever") is False


class TestVaultNestingGuard:
    """Tests for preventing parent-child vault nesting/overlap."""

    def test_add_vault_nesting_exact_match(self, db):
        """Registering the same vault path under a different name is allowed (upsert)."""
        db.add_vault("Vault1", "/tmp/vault1")
        # Upserting the same path is allowed (updates name/metadata)
        db.add_vault("Vault1-Rename", "/tmp/vault1")

    def test_add_vault_nesting_child(self, db):
        """Registering a child directory of an existing vault raises ValueError."""
        db.add_vault("Parent", "/tmp/parent")
        with pytest.raises(ValueError) as excinfo:
            db.add_vault("Child", "/tmp/parent/child")
        assert "Vault nesting detected" in str(excinfo.value)
        assert "child" in str(excinfo.value)

    def test_add_vault_nesting_parent(self, db):
        """Registering a parent directory of an existing vault raises ValueError."""
        db.add_vault("Child", "/tmp/parent/child")
        with pytest.raises(ValueError) as excinfo:
            db.add_vault("Parent", "/tmp/parent")
        assert "Vault nesting detected" in str(excinfo.value)
        assert "parent" in str(excinfo.value)


class TestScanHistoryFailedPaths:
    """Tests for scan history failed_paths serialization."""

    def test_complete_scan_saves_failed_paths(self, db):
        """complete_scan saves failed paths as serialized JSON."""
        vault_id = db.add_vault("Test", "/tmp/test")
        scan_id = db.start_scan(vault_id)
        
        failed = ["path1.md", "path2.md"]
        db.complete_scan(scan_id, notes_scanned=5, notes_failed=2, failed_paths=failed)
        
        history = db.get_scan_history(vault_id, limit=1)
        assert len(history) == 1
        assert history[0]["notes_failed"] == 2
        
        # Verify JSON decoding
        import json
        saved_paths = json.loads(history[0]["failed_paths"])
        assert saved_paths == failed

