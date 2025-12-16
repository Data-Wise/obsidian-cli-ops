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
    # Initialize schema from schema file
    schema_path = Path(__file__).parent.parent.parent.parent / "schema" / "vault_db.sql"

    if schema_path.exists():
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        conn = sqlite3.connect(temp_db)
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()

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
            'Test Vault',
            '/path/to/vault'
        )

        assert vault_id is not None
        assert isinstance(vault_id, str)

    def test_get_vault(self, db_manager):
        """Test retrieving a vault."""
        vault_id = db_manager.add_vault('Test Vault', '/path/to/vault')

        vault = db_manager.get_vault(vault_id)

        assert vault is not None
        assert vault['name'] == 'Test Vault'
        assert vault['path'] == '/path/to/vault'

    def test_list_vaults(self, db_manager):
        """Test listing all vaults."""
        db_manager.add_vault('Vault 1', '/path/vault1')
        db_manager.add_vault('Vault 2', '/path/vault2')

        vaults = db_manager.list_vaults()

        assert len(vaults) == 2
        assert vaults[0]['name'] in ['Vault 1', 'Vault 2']

    def test_add_duplicate_vault(self, db_manager):
        """Test that adding duplicate vault path updates existing."""
        vault_id1 = db_manager.add_vault('Vault 1', '/path/vault')
        vault_id2 = db_manager.add_vault('Vault 2', '/path/vault')

        # Should return same ID since path is same (vault_id is hash of path)
        assert vault_id1 == vault_id2
        vaults = db_manager.list_vaults()
        assert len(vaults) == 1  # Only one vault with this path


class TestNoteOperations:
    """Test note CRUD operations."""

    def test_add_note(self, db_manager):
        """Test adding a note."""
        vault_id = db_manager.add_vault('Test Vault', '/path/vault')

        note_id = db_manager.add_note(
            vault_id=vault_id,
            path='notes/test.md',
            title='Test Note',
            content='# Test\n\nContent here'
        )

        assert note_id is not None
        assert isinstance(note_id, str)

    def test_get_note(self, db_manager):
        """Test retrieving a note."""
        vault_id = db_manager.add_vault('Test Vault', '/path/vault')
        note_id = db_manager.add_note(
            vault_id, 'notes/test.md', 'Test Note',
            '# Test'
        )

        note = db_manager.get_note(note_id)

        assert note is not None
        assert note['title'] == 'Test Note'
        assert note['path'] == 'notes/test.md'

    def test_list_notes(self, db_manager):
        """Test listing notes in a vault."""
        vault_id = db_manager.add_vault('Test Vault', '/path/vault')
        db_manager.add_note(vault_id, 'note1.md', 'Note 1', '# 1')
        db_manager.add_note(vault_id, 'note2.md', 'Note 2', '# 2')

        notes = db_manager.list_notes(vault_id)

        assert len(notes) == 2
        titles = {n['title'] for n in notes}
        assert titles == {'Note 1', 'Note 2'}

    def test_update_note_content_hash(self, db_manager):
        """Test updating note when content changes."""
        vault_id = db_manager.add_vault('Test Vault', '/path/vault')
        note_id = db_manager.add_note(
            vault_id, 'test.md', 'Test', '# Original'
        )

        # Get original hash
        note = db_manager.get_note(note_id)
        original_hash = note['content_hash']

        # Update with new content
        note_id2 = db_manager.add_note(
            vault_id, 'test.md', 'Test', '# Updated'
        )

        # Should update existing note with new hash
        notes = db_manager.list_notes(vault_id)
        assert len(notes) == 1
        assert notes[0]['content_hash'] != original_hash  # Hash should change


class TestLinkOperations:
    """Test link operations."""

    def test_add_link(self, db_manager):
        """Test adding a link between notes."""
        vault_id = db_manager.add_vault('Test Vault', '/path/vault')
        note1_id = db_manager.add_note(vault_id, 'note1.md', 'Note 1', '# 1')
        note2_id = db_manager.add_note(vault_id, 'note2.md', 'Note 2', '# 2')

        link_id = db_manager.add_link(note1_id, 'note2.md', 'Note 2')

        assert link_id is not None

    def test_get_outgoing_links(self, db_manager):
        """Test retrieving outgoing links from a note."""
        vault_id = db_manager.add_vault('Test Vault', '/path/vault')
        note1 = db_manager.add_note(vault_id, 'note1.md', 'Note 1', '# 1')
        note2 = db_manager.add_note(vault_id, 'note2.md', 'Note 2', '# 2')
        note3 = db_manager.add_note(vault_id, 'note3.md', 'Note 3', '# 3')

        db_manager.add_link(note1, 'note2.md', 'Note 2')
        db_manager.add_link(note1, 'note3.md', 'Note 3')

        links = db_manager.get_outgoing_links(note1)

        assert len(links) == 2
        target_paths = {link['target_path'] for link in links}
        assert target_paths == {'note2.md', 'note3.md'}

    def test_get_incoming_links(self, db_manager):
        """Test retrieving incoming links to a note."""
        vault_id = db_manager.add_vault('Test Vault', '/path/vault')
        note1 = db_manager.add_note(vault_id, 'note1.md', 'Note 1', '# 1')
        note2 = db_manager.add_note(vault_id, 'note2.md', 'Note 2', '# 2')
        note3 = db_manager.add_note(vault_id, 'note3.md', 'Note 3', '# 3')

        db_manager.add_link(note1, 'note3.md', 'Note 3')
        db_manager.add_link(note2, 'note3.md', 'Note 3')

        # Manually resolve links for testing
        with db_manager.get_connection() as conn:
            conn.execute("""
                UPDATE links SET target_note_id = ? WHERE target_path = 'note3.md'
            """, (note3,))

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
        vault_id = db_manager.add_vault('Test Vault', '/path/vault')
        note_id = db_manager.add_note(vault_id, 'test.md', 'Test', '# Test')
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
        vault_id = db_manager.add_vault('Test Vault', '/path/vault')
        orphan = db_manager.add_note(vault_id, 'orphan.md', 'Orphan', '# O')
        connected1 = db_manager.add_note(vault_id, 'c1.md', 'C1', '# C1')
        connected2 = db_manager.add_note(vault_id, 'c2.md', 'C2', '# C2')

        db_manager.add_link(connected1, 'c2.md', 'C2')

        orphans = db_manager.get_orphaned_notes(vault_id)

        # Orphan should be in the list
        orphan_ids = {o['id'] for o in orphans}
        assert orphan in orphan_ids

    def test_get_hub_notes(self, db_manager):
        """Test finding hub notes (highly connected)."""
        vault_id = db_manager.add_vault('Test Vault', '/path/vault')

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
        vault_id = db_manager.add_vault('Test Vault', '/path/vault')

        scan_id = db_manager.start_scan(vault_id)

        assert scan_id is not None

    def test_complete_scan(self, db_manager):
        """Test completing a scan."""
        vault_id = db_manager.add_vault('Test Vault', '/path/vault')
        scan_id = db_manager.start_scan(vault_id)

        db_manager.complete_scan(scan_id, notes_scanned=10, notes_added=8, notes_updated=2)

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
        vault_id = db_manager.add_vault('Test Vault', '/path/vault')
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
