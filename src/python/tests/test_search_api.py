
import pytest
from db_manager import DatabaseManager
from core.vault_manager import VaultManager
import os

class TestSearchAPI:
    """Test search functionality."""

    def test_search_notes(self):
        """Test search query, filtering, and snippet generation."""
        db_path = "/tmp/test_search_db.sqlite"
        if os.path.exists(db_path):
            os.remove(db_path)
            
        try:
            db = DatabaseManager(db_path)
            vm = VaultManager(db)
            
            # Setup Data
            v1 = db.add_vault("Personal", "/tmp/v1")
            v2 = db.add_vault("Work", "/tmp/v2")

            # Note 1: In Personal, title contains "Project"
            db.add_note(v1, "n1.md", "Important Project Diary", "Today I worked on the important project for client X.")

            # Note 2: In Work, title contains "Project"
            db.add_note(v2, "n2.md", "Project Meeting Notes", "The project deadline is tomorrow.")

            # Note 3: In Personal, tagged #idea, no "project" in title
            n3 = db.add_note(v1, "n3.md", "New Idea", "Some random text.")
            db.add_note_tag(n3, "idea")

            # 1. Global Search "project" (searches titles only)
            # Should find n1 and n2
            results = vm.search_notes("project")
            assert len(results) == 2
            titles = [r['title'] for r in results]
            assert "Important Project Diary" in titles
            assert "Project Meeting Notes" in titles

            # 2. Vault Scoped Search
            # Search "project" in Work vault (v2) only
            results = vm.search_notes("project", vault_id=v2)
            assert len(results) == 1
            assert results[0]['title'] == "Project Meeting Notes"
            
            # 3. Tag Filter
            # Search for tag "idea"
            results = vm.search_notes("", tags=["idea"])
            assert len(results) == 1
            assert results[0]['title'] == "New Idea"
            
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)
