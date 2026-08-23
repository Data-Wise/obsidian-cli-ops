"""Unit tests for DatabaseManager."""

import pytest

from db_manager import DatabaseManager


@pytest.fixture
def db():
    """In-memory DatabaseManager with the full schema applied."""
    manager = DatabaseManager(db_path=":memory:")
    manager.initialize_database()
    return manager


class TestSearchNotesVaultScope:
    """db.search_notes() must accept a vault NAME, not only an exact ID.

    The WHERE clause compares against `notes.vault_id` (an ID hash), so before
    the resolver was added here a caller passing a name matched zero rows --
    an empty result indistinguishable from "no such note", against a perfectly
    healthy index. Resolution lives at this layer because it is the choke point
    every caller reaches (obs_cli resolved first, the MCP path did not).
    """

    @pytest.fixture
    def seeded(self, db):
        vault_id = db.add_vault(name="NamedVault", path="/tmp/named-vault")
        db.add_note(vault_id=vault_id, path="a.md", title="Alpha Note",
                    content="alpha body")
        return db, vault_id

    def test_scope_by_name(self, seeded):
        db, vault_id = seeded
        assert "NamedVault" != vault_id          # else this proves nothing
        rows = db.search_notes("Alpha", vault_id="NamedVault")
        assert len(rows) == 1

    def test_scope_by_id_and_prefix(self, seeded):
        db, vault_id = seeded
        assert len(db.search_notes("Alpha", vault_id=vault_id)) == 1
        assert len(db.search_notes("Alpha", vault_id=vault_id[:8])) == 1

    def test_scoped_matches_unscoped(self, seeded):
        db, _ = seeded
        assert len(db.search_notes("Alpha")) == 1
        assert len(db.search_notes("Alpha", vault_id="NamedVault")) == 1

    def test_unknown_vault_raises_rather_than_returning_empty(self, seeded):
        db, _ = seeded
        with pytest.raises(ValueError, match="Vault not found"):
            db.search_notes("Alpha", vault_id="no-such-vault")

    def test_empty_string_does_not_silently_search_globally(self, seeded):
        """vault_id="" must not skip resolution AND scoping.

        `if vault_id:` is falsy for "", so the query ran unscoped and returned
        cross-vault results labelled as scoped -- worse than an error, because
        a client passing "" instead of None cannot tell.
        """
        db, _ = seeded
        db2 = db.add_vault(name="OtherVault", path="/tmp/other-vault")
        db.add_note(vault_id=db2, path="b.md", title="Alpha Elsewhere",
                    content="elsewhere")
        assert len(db.search_notes("Alpha")) == 2          # genuinely global
        with pytest.raises(ValueError, match="empty vault identifier"):
            db.search_notes("Alpha", vault_id="")

    def test_empty_string_is_rejected_even_with_one_vault(self, seeded):
        """With a single vault, "" used to resolve to it via the prefix branch.

        Same call, different meaning depending on how many vaults exist.
        """
        db, _ = seeded
        with pytest.raises(ValueError, match="empty vault identifier"):
            db.search_notes("Alpha", vault_id="")

    def test_ambiguous_vault_name_raises_rather_than_picking_one(self, db):
        """Duplicate vault NAMES must raise, as duplicate ID prefixes already do.

        `vaults.name` has no UNIQUE constraint, and two vaults called
        "Documents" (a local one and an iCloud one) is realistic. fetchone()
        picked one arbitrarily and silently dropped the other's notes.
        """
        a = db.add_vault(name="Documents", path="/tmp/one/Documents")
        b = db.add_vault(name="Documents", path="/tmp/two/Documents")
        db.add_note(vault_id=a, path="m1.md", title="Meeting A", content="x")
        db.add_note(vault_id=b, path="m2.md", title="Meeting B", content="y")
        with pytest.raises(ValueError, match="Ambiguous vault name"):
            db.search_notes("Meeting", vault_id="Documents")

    def test_limit_is_honored(self, db):
        """db's default of 50 must not cap a caller asking for more."""
        vault_id = db.add_vault(name="BigVault", path="/tmp/big-vault")
        for i in range(60):
            db.add_note(vault_id=vault_id, path=f"n{i}.md",
                        title=f"Note {i:03d}", content="body")
        assert len(db.search_notes("Note", vault_id="BigVault")) == 50   # default
        assert len(db.search_notes("Note", vault_id="BigVault", limit=60)) == 60


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

