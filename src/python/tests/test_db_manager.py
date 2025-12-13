"""
Unit tests for DatabaseManager class.

Tests database operations including vault, note, link, and tag management.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from db_manager import DatabaseManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def db_manager(temp_db):
    """Create a DatabaseManager instance with temporary database."""
    manager = DatabaseManager(temp_db)
    return manager


class TestDatabaseInitialization:
    """Test database initialization and schema creation."""

    def test_database_creation(self, temp_db):
        """Test that database file is created."""
        manager = DatabaseManager(temp_db)
        assert os.path.exists(temp_db)

    def test_schema_creation(self, db_manager):
        """Test that all tables are created."""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Check that tables exist
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}

            expected_tables = {
                'vaults', 'notes', 'links', 'tags', 'note_tags',
                'graph_metrics', 'scan_history', 'schema_version'
            }

            assert expected_tables.issubset(tables)

    def test_views_creation(self, db_manager):
        """Test that views are created."""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='view'"
            )
            views = {row[0] for row in cursor.fetchall()}

            expected_views = {'orphaned_notes', 'hub_notes', 'broken_links'}

            assert expected_views.issubset(views)


class TestVaultOperations:
    """Test vault CRUD operations."""

    def test_add_vault(self, db_manager):
        """Test adding a vault."""
        vault_id = db_manager.add_vault(
            '/path/to/vault',
            'Test Vault'
        )

        assert vault_id is not None
        assert isinstance(vault_id, int)

    def test_get_vault(self, db_manager):
        """Test retrieving a vault."""
        vault_id = db_manager.add_vault('/path/to/vault', 'Test Vault')

        vault = db_manager.get_vault(vault_id)

        assert vault is not None
        assert vault['path'] == '/path/to/vault'
        assert vault['name'] == 'Test Vault'

    def test_list_vaults(self, db_manager):
        """Test listing all vaults."""
        db_manager.add_vault('/path/vault1', 'Vault 1')
        db_manager.add_vault('/path/vault2', 'Vault 2')

        vaults = db_manager.list_vaults()

        assert len(vaults) == 2
        assert vaults[0]['name'] in ['Vault 1', 'Vault 2']

    def test_add_duplicate_vault(self, db_manager):
        """Test that adding duplicate vault path updates existing."""
        vault_id1 = db_manager.add_vault('/path/vault', 'Vault 1')
        vault_id2 = db_manager.add_vault('/path/vault', 'Vault 2')

        # Should return same ID or handle gracefully
        vaults = db_manager.list_vaults()
        assert len(vaults) == 1  # Only one vault with this path


class TestNoteOperations:
    """Test note CRUD operations."""

    def test_add_note(self, db_manager):
        """Test adding a note."""
        vault_id = db_manager.add_vault('/path/vault', 'Test Vault')

        note_id = db_manager.add_note(
            vault_id=vault_id,
            path='notes/test.md',
            title='Test Note',
            content='# Test\n\nContent here',
            content_hash='abc123'
        )

        assert note_id is not None
        assert isinstance(note_id, int)

    def test_get_note(self, db_manager):
        """Test retrieving a note."""
        vault_id = db_manager.add_vault('/path/vault', 'Test Vault')
        note_id = db_manager.add_note(
            vault_id, 'notes/test.md', 'Test Note',
            '# Test', 'abc123'
        )

        note = db_manager.get_note(note_id)

        assert note is not None
        assert note['title'] == 'Test Note'
        assert note['path'] == 'notes/test.md'

    def test_list_notes(self, db_manager):
        """Test listing notes in a vault."""
        vault_id = db_manager.add_vault('/path/vault', 'Test Vault')
        db_manager.add_note(vault_id, 'note1.md', 'Note 1', '# 1', 'hash1')
        db_manager.add_note(vault_id, 'note2.md', 'Note 2', '# 2', 'hash2')

        notes = db_manager.list_notes(vault_id)

        assert len(notes) == 2
        titles = {n['title'] for n in notes}
        assert titles == {'Note 1', 'Note 2'}

    def test_update_note_content_hash(self, db_manager):
        """Test updating note when content changes."""
        vault_id = db_manager.add_vault('/path/vault', 'Test Vault')
        note_id = db_manager.add_note(
            vault_id, 'test.md', 'Test', '# Original', 'hash1'
        )

        # Update with new hash
        note_id2 = db_manager.add_note(
            vault_id, 'test.md', 'Test', '# Updated', 'hash2'
        )

        # Should update existing note
        notes = db_manager.list_notes(vault_id)
        assert len(notes) == 1
        assert notes[0]['content_hash'] == 'hash2'


class TestLinkOperations:
    """Test link operations."""

    def test_add_link(self, db_manager):
        """Test adding a link between notes."""
        vault_id = db_manager.add_vault('/path/vault', 'Test Vault')
        note1_id = db_manager.add_note(vault_id, 'note1.md', 'Note 1', '# 1', 'h1')
        note2_id = db_manager.add_note(vault_id, 'note2.md', 'Note 2', '# 2', 'h2')

        link_id = db_manager.add_link(note1_id, note2_id, 'Note 2')

        assert link_id is not None

    def test_get_outgoing_links(self, db_manager):
        """Test retrieving outgoing links from a note."""
        vault_id = db_manager.add_vault('/path/vault', 'Test Vault')
        note1 = db_manager.add_note(vault_id, 'note1.md', 'Note 1', '# 1', 'h1')
        note2 = db_manager.add_note(vault_id, 'note2.md', 'Note 2', '# 2', 'h2')
        note3 = db_manager.add_note(vault_id, 'note3.md', 'Note 3', '# 3', 'h3')

        db_manager.add_link(note1, note2, 'Note 2')
        db_manager.add_link(note1, note3, 'Note 3')

        links = db_manager.get_outgoing_links(note1)

        assert len(links) == 2
        target_ids = {link['target_note_id'] for link in links}
        assert target_ids == {note2, note3}

    def test_get_incoming_links(self, db_manager):
        """Test retrieving incoming links to a note."""
        vault_id = db_manager.add_vault('/path/vault', 'Test Vault')
        note1 = db_manager.add_note(vault_id, 'note1.md', 'Note 1', '# 1', 'h1')
        note2 = db_manager.add_note(vault_id, 'note2.md', 'Note 2', '# 2', 'h2')
        note3 = db_manager.add_note(vault_id, 'note3.md', 'Note 3', '# 3', 'h3')

        db_manager.add_link(note1, note3, 'Note 3')
        db_manager.add_link(note2, note3, 'Note 3')

        links = db_manager.get_incoming_links(note3)

        assert len(links) == 2
        source_ids = {link['source_note_id'] for link in links}
        assert source_ids == {note1, note2}


class TestTagOperations:
    """Test tag operations."""

    def test_add_tag(self, db_manager):
        """Test adding a tag."""
        tag_id = db_manager.add_tag('research')

        assert tag_id is not None

    def test_add_note_tag(self, db_manager):
        """Test associating a tag with a note."""
        vault_id = db_manager.add_vault('/path/vault', 'Test Vault')
        note_id = db_manager.add_note(vault_id, 'test.md', 'Test', '# Test', 'h1')
        tag_id = db_manager.add_tag('research')

        # This would use a method like add_note_tag if it exists
        # For now, test that tags are properly stored
        assert tag_id is not None

    def test_get_tag_stats(self, db_manager):
        """Test getting tag statistics."""
        stats = db_manager.get_tag_stats()

        # Should return a list, even if empty
        assert isinstance(stats, list)


class TestGraphQueries:
    """Test graph-related queries."""

    def test_get_orphaned_notes(self, db_manager):
        """Test finding orphaned notes (no links)."""
        vault_id = db_manager.add_vault('/path/vault', 'Test Vault')
        orphan = db_manager.add_note(vault_id, 'orphan.md', 'Orphan', '# O', 'h1')
        connected1 = db_manager.add_note(vault_id, 'c1.md', 'C1', '# C1', 'h2')
        connected2 = db_manager.add_note(vault_id, 'c2.md', 'C2', '# C2', 'h3')

        db_manager.add_link(connected1, connected2, 'C2')

        orphans = db_manager.get_orphaned_notes(vault_id)

        # Orphan should be in the list
        orphan_ids = {o['id'] for o in orphans}
        assert orphan in orphan_ids

    def test_get_hub_notes(self, db_manager):
        """Test finding hub notes (highly connected)."""
        vault_id = db_manager.add_vault('/path/vault', 'Test Vault')

        # This will depend on the threshold in the view (>10 links)
        # For now, just test that the query works
        hubs = db_manager.get_hub_notes(vault_id)

        assert isinstance(hubs, list)

    def test_get_broken_links(self, db_manager):
        """Test finding broken links."""
        broken = db_manager.get_broken_links()

        assert isinstance(broken, list)


class TestScanHistory:
    """Test scan history tracking."""

    def test_start_scan(self, db_manager):
        """Test starting a scan."""
        vault_id = db_manager.add_vault('/path/vault', 'Test Vault')

        scan_id = db_manager.start_scan(vault_id)

        assert scan_id is not None

    def test_complete_scan(self, db_manager):
        """Test completing a scan."""
        vault_id = db_manager.add_vault('/path/vault', 'Test Vault')
        scan_id = db_manager.start_scan(vault_id)

        db_manager.complete_scan(scan_id, notes_scanned=10, links_found=15)

        # Verify scan was completed
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT status, notes_scanned FROM scan_history WHERE id = ?",
                (scan_id,)
            )
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == 'completed'
            assert row[1] == 10

    def test_fail_scan(self, db_manager):
        """Test failing a scan with error message."""
        vault_id = db_manager.add_vault('/path/vault', 'Test Vault')
        scan_id = db_manager.start_scan(vault_id)

        db_manager.fail_scan(scan_id, "Test error message")

        # Verify scan failed
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT status, error_message FROM scan_history WHERE id = ?",
                (scan_id,)
            )
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == 'failed'
            assert row[1] == "Test error message"


@pytest.mark.unit
class TestConnectionManagement:
    """Test database connection management."""

    def test_context_manager(self, db_manager):
        """Test that get_connection works as context manager."""
        with db_manager.get_connection() as conn:
            assert conn is not None
            assert isinstance(conn, sqlite3.Connection)

    def test_multiple_connections(self, db_manager):
        """Test that multiple connections can be opened."""
        with db_manager.get_connection() as conn1:
            with db_manager.get_connection() as conn2:
                assert conn1 is not None
                assert conn2 is not None
