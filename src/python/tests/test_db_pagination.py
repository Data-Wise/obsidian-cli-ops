
import pytest
from unittest.mock import Mock, patch
from db_manager import DatabaseManager
import sqlite3
import os

class TestDBPagination:
    """Test pagination support in DatabaseManager."""

    def test_list_notes_pagination(self):
        """Test that list_notes accepts limit and offset."""
        db_path = "/tmp/test_pagination_db.sqlite"
        if os.path.exists(db_path):
            os.remove(db_path)
            
        try:
            db = DatabaseManager(db_path)
            
            # Add a dummy vault
            vault_id = db.add_vault("Test Vault", "/tmp/test")
            
            # Add 5 dummy notes
            for i in range(5):
                db.add_note(vault_id, f"note_{i}.md", f"Note {i}", f"Content {i}")
                
            # Test Limit
            notes = db.list_notes(vault_id, limit=2)
            assert len(notes) == 2
            assert notes[0]['title'] == "Note 0"
            assert notes[1]['title'] == "Note 1"
            
            # Test Offset
            notes = db.list_notes(vault_id, limit=2, offset=2)
            assert len(notes) == 2
            assert notes[0]['title'] == "Note 2"
            assert notes[1]['title'] == "Note 3"
            
            # Test Remaining
            notes = db.list_notes(vault_id, limit=2, offset=4)
            assert len(notes) == 1
            assert notes[0]['title'] == "Note 4"

            # Test Offset Only (should imply no limit)
            notes = db.list_notes(vault_id, offset=3)
            assert len(notes) == 2
            assert notes[0]['title'] == "Note 3"
            assert notes[1]['title'] == "Note 4"
            
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)
