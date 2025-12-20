
import pytest
from db_manager import DatabaseManager
import os

class TestDBMetrics:
    """Test metrics retrieval."""

    def test_get_note_metrics_alias(self):
        """Test that get_note_metrics works as an alias."""
        db_path = "/tmp/test_metrics_db.sqlite"
        if os.path.exists(db_path):
            os.remove(db_path)
            
        try:
            db = DatabaseManager(db_path)
            vault_id = db.add_vault("Test", "/tmp")
            note_id = db.add_note(vault_id, "note.md", "Note", "Content")
            
            # Should not crash and return a dict (initialized empty in add_note)
            metrics = db.get_note_metrics(note_id)
            assert metrics is not None
            assert 'pagerank' in metrics # Assuming schema has columns, rows return keys
            
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)
