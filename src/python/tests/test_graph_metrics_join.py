
import pytest
from db_manager import DatabaseManager
import os

class TestGraphMetricsJoin:
    """Test metrics retrieval with join."""

    def test_get_graph_metrics_includes_vault_id(self):
        """Test that get_graph_metrics returns vault_id."""
        db_path = "/tmp/test_metrics_join_db.sqlite"
        if os.path.exists(db_path):
            os.remove(db_path)
            
        try:
            db = DatabaseManager(db_path)
            vault_id = db.add_vault("Test", "/tmp")
            note_id = db.add_note(vault_id, "note.md", "Note", "Content")
            
            # This should now include vault_id due to the JOIN
            metrics = db.get_graph_metrics(note_id)
            assert metrics is not None
            assert 'vault_id' in metrics
            assert metrics['vault_id'] == vault_id
            
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)
