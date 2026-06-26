"""Tests for embedding cache in DatabaseManager."""

import pytest
np = pytest.importorskip("numpy", reason="numpy not installed in this Python env")
from db_manager import DatabaseManager


@pytest.fixture
def db():
    """Create an in-memory database for testing."""
    manager = DatabaseManager(db_path=":memory:")
    manager.initialize_database()
    manager.ensure_embeddings_table()

    # Insert a test vault and note
    with manager.get_connection() as conn:
        conn.execute(
            "INSERT INTO vaults (id, name, path) VALUES (?, ?, ?)",
            ("v1", "Test Vault", "/test"),
        )
        conn.execute(
            "INSERT INTO notes (id, vault_id, path, title, content_hash) VALUES (?, ?, ?, ?, ?)",
            ("n1", "v1", "note1.md", "Note 1", "abc123"),
        )
    return manager


class TestEmbeddingCacheCRUD:
    """Tests for embedding cache CRUD operations."""

    def test_save_and_get_embedding(self, db):
        vector = np.array([0.1, 0.2, 0.3], dtype=np.float32).tobytes()
        db.save_embedding("n1", "gemini-api", "text-embedding-004", vector, 1234.5)

        result = db.get_embedding("n1", "gemini-api", "text-embedding-004")
        assert result is not None
        arr = np.frombuffer(result, dtype=np.float32)
        np.testing.assert_array_almost_equal(arr, [0.1, 0.2, 0.3])

    def test_get_embedding_returns_none_on_miss(self, db):
        result = db.get_embedding("n1", "gemini-api", "text-embedding-004")
        assert result is None

    def test_get_embedding_with_mtime(self, db):
        vector = np.array([0.4, 0.5], dtype=np.float32).tobytes()
        db.save_embedding("n1", "ollama", "nomic", vector, 5678.0)

        result = db.get_embedding_with_mtime("n1", "ollama", "nomic")
        assert result is not None
        assert result['file_mtime'] == 5678.0
        assert result['updated_at'] is not None

    def test_save_embedding_updates_on_conflict(self, db):
        v1 = np.array([1.0, 2.0], dtype=np.float32).tobytes()
        v2 = np.array([3.0, 4.0], dtype=np.float32).tobytes()

        db.save_embedding("n1", "test", "model", v1, 100.0)
        db.save_embedding("n1", "test", "model", v2, 200.0)

        result = db.get_embedding_with_mtime("n1", "test", "model")
        assert result['file_mtime'] == 200.0
        arr = np.frombuffer(bytes(result['vector']), dtype=np.float32)
        np.testing.assert_array_almost_equal(arr, [3.0, 4.0])

    def test_delete_embeddings(self, db):
        vector = np.array([1.0], dtype=np.float32).tobytes()
        db.save_embedding("n1", "a", "m1", vector, 1.0)
        db.save_embedding("n1", "b", "m2", vector, 1.0)

        db.delete_embeddings("n1")
        assert db.get_embedding("n1", "a", "m1") is None
        assert db.get_embedding("n1", "b", "m2") is None

    def test_count_embeddings(self, db):
        vector = np.array([1.0], dtype=np.float32).tobytes()
        assert db.count_embeddings() == 0

        db.save_embedding("n1", "gemini", "model-a", vector, 1.0)
        assert db.count_embeddings() == 1
        assert db.count_embeddings(provider="gemini") == 1
        assert db.count_embeddings(provider="gemini", model="model-a") == 1
        assert db.count_embeddings(provider="ollama") == 0


class TestEmbeddingCascadeOnReplace:
    """N1 mechanism: INSERT OR REPLACE in add_note cascades and wipes embeddings.

    This documents WHY the scanner must short-circuit unchanged notes — a bare
    re-add_note() of an already-indexed note destroys its cached embedding.
    """

    def test_add_note_replace_cascades_embedding(self, db):
        # add_note derives the id from vault_id:path; cache against that id.
        note_id = db.add_note(
            vault_id="v1", path="cascade.md", title="Cascade",
            content="first content", metadata={},
        )
        vector = np.array([0.1, 0.2], dtype=np.float32).tobytes()
        db.save_embedding(note_id, "gemini-api", "text-embedding-004", vector, 1.0)
        assert db.get_embedding(note_id, "gemini-api", "text-embedding-004") is not None

        # Re-add the SAME note (same vault_id:path -> same id) — REPLACE fires
        # ON DELETE CASCADE, which removes the note_embeddings row.
        db.add_note(
            vault_id="v1", path="cascade.md", title="Cascade",
            content="second content", metadata={},
        )
        assert db.get_embedding(note_id, "gemini-api", "text-embedding-004") is None

    def test_re_add_vault_does_not_cascade_notes_or_embeddings(self, db):
        """add_vault must upsert in place — re-adding a vault (which every
        rescan does at line ~220, BEFORE the note loop) must NOT cascade-wipe
        its notes or their embeddings. This is the earlier, more total trigger
        of N1; the content-hash short-circuit is moot if the vault REPLACE has
        already deleted everything."""
        vault_id = db.add_vault("Re Vault", "/tmp/re-vault")
        note_id = db.add_note(
            vault_id=vault_id, path="keep.md", title="Keep",
            content="body", metadata={},
        )
        vector = np.array([0.9, 0.8], dtype=np.float32).tobytes()
        db.save_embedding(note_id, "gemini-api", "text-embedding-004", vector, 1.0)

        # Re-add the SAME vault (same path -> same id), as scan_vault does.
        db.add_vault("Re Vault", "/tmp/re-vault")

        # Both the note and its embedding must survive.
        assert db.get_note(note_id) is not None
        assert db.get_embedding(note_id, "gemini-api", "text-embedding-004") is not None
