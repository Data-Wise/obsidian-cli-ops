#!/usr/bin/env python3
"""
Database Manager for Obsidian CLI Ops v2.0

Handles all database operations including initialization, queries,
and maintenance for the vault knowledge base.
"""

import sqlite3
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from contextlib import contextmanager


class DatabaseManager:
    """Manages SQLite database for vault analysis and knowledge management."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file.
                    Defaults to ~/.config/obs/vault_db.sqlite
        """
        if db_path is None:
            db_path = Path.home() / '.config' / 'obs' / 'vault_db.sqlite'
        else:
            db_path = Path(db_path)

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database if it doesn't exist
        if not self.db_path.exists():
            self.initialize_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def initialize_database(self):
        """Initialize database with schema."""
        schema_path = Path(__file__).parent.parent.parent / 'schema' / 'vault_db.sql'

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        with self.get_connection() as conn:
            conn.executescript(schema_sql)

        print(f"✓ Database initialized at: {self.db_path}")

    def rebuild_database(self):
        """Drop and recreate database (destructive!)."""
        if self.db_path.exists():
            backup_path = self.db_path.with_suffix('.backup')
            self.db_path.rename(backup_path)
            print(f"✓ Backed up existing database to: {backup_path}")

        self.initialize_database()

    # ========================================================================
    # VAULT OPERATIONS
    # ========================================================================

    def add_vault(self, name: str, path: str, metadata: Optional[Dict] = None) -> str:
        """
        Add a new vault to the database.

        Args:
            name: Vault display name
            path: Absolute path to vault
            metadata: Optional metadata dictionary

        Returns:
            Vault ID (hash of path)
        """
        vault_id = self._generate_id(path)

        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO vaults (id, name, path, metadata)
                VALUES (?, ?, ?, ?)
            """, (vault_id, name, path, json.dumps(metadata or {})))

        return vault_id

    def get_vault(self, vault_id: str) -> Optional[Dict]:
        """Get vault information by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM vaults WHERE id = ?
            """, (vault_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_vault_by_path(self, path: str) -> Optional[Dict]:
        """Get vault information by path."""
        vault_id = self._generate_id(path)
        return self.get_vault(vault_id)

    def list_vaults(self) -> List[Dict]:
        """List all vaults."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM vaults ORDER BY name
            """)
            return [dict(row) for row in cursor.fetchall()]

    def update_vault_scan_time(self, vault_id: str):
        """Update last_scanned timestamp for vault."""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE vaults
                SET last_scanned = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (vault_id,))

    # ========================================================================
    # NOTE OPERATIONS
    # ========================================================================

    def add_note(self, vault_id: str, path: str, title: str,
                 content: str, metadata: Optional[Dict] = None) -> str:
        """
        Add or update a note in the database.

        Args:
            vault_id: Parent vault ID
            path: Relative path within vault
            title: Note title
            content: Note content (for hashing)
            metadata: Note metadata including frontmatter

        Returns:
            Note ID
        """
        note_id = self._generate_id(f"{vault_id}:{path}")
        content_hash = self._hash_content(content)

        meta = metadata or {}
        word_count = len(content.split())
        char_count = len(content)

        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO notes
                (id, vault_id, path, title, content_hash, word_count, char_count,
                 created_at, modified_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                note_id,
                vault_id,
                path,
                title,
                content_hash,
                word_count,
                char_count,
                meta.get('created_at', datetime.now().isoformat()),
                meta.get('modified_at', datetime.now().isoformat()),
                json.dumps(meta)
            ))

            # Initialize graph metrics
            conn.execute("""
                INSERT OR IGNORE INTO graph_metrics (note_id)
                VALUES (?)
            """, (note_id,))

        return note_id

    def get_note(self, note_id: str) -> Optional[Dict]:
        """Get note information by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM notes WHERE id = ?
            """, (note_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_note_by_path(self, vault_id: str, path: str) -> Optional[Dict]:
        """Get note by vault and path."""
        note_id = self._generate_id(f"{vault_id}:{path}")
        return self.get_note(note_id)

    def list_notes(self, vault_id: Optional[str] = None) -> List[Dict]:
        """List all notes, optionally filtered by vault."""
        with self.get_connection() as conn:
            if vault_id:
                cursor = conn.execute("""
                    SELECT * FROM notes WHERE vault_id = ? ORDER BY title
                """, (vault_id,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM notes ORDER BY title
                """)
            return [dict(row) for row in cursor.fetchall()]

    def note_exists(self, vault_id: str, path: str) -> bool:
        """Check if note exists."""
        note_id = self._generate_id(f"{vault_id}:{path}")
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 1 FROM notes WHERE id = ? LIMIT 1
            """, (note_id,))
            return cursor.fetchone() is not None

    # ========================================================================
    # LINK OPERATIONS
    # ========================================================================

    def add_link(self, source_note_id: str, target_path: str,
                 link_text: Optional[str] = None) -> int:
        """
        Add a link between notes.

        Args:
            source_note_id: ID of note containing the link
            target_path: Path of target note (as written in link)
            link_text: Display text if different from target

        Returns:
            Link ID
        """
        # Try to resolve target note (might be broken link)
        # This will be improved in vault scanner with proper resolution
        target_note_id = None
        link_type = 'internal'  # Will be determined during resolution

        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO links (source_note_id, target_note_id, target_path,
                                 link_type, link_text)
                VALUES (?, ?, ?, ?, ?)
            """, (source_note_id, target_note_id, target_path, link_type, link_text))
            return cursor.lastrowid

    def get_outgoing_links(self, note_id: str) -> List[Dict]:
        """Get all links from this note."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM links WHERE source_note_id = ?
            """, (note_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_incoming_links(self, note_id: str) -> List[Dict]:
        """Get all links to this note (backlinks)."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM links WHERE target_note_id = ?
            """, (note_id,))
            return [dict(row) for row in cursor.fetchall()]

    # ========================================================================
    # TAG OPERATIONS
    # ========================================================================

    def add_tag(self, tag: str) -> int:
        """Add a tag to the tags table."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO tags (tag) VALUES (?)
            """, (tag,))
            if cursor.rowcount == 0:
                # Tag already exists, get its ID
                cursor = conn.execute("""
                    SELECT id FROM tags WHERE tag = ?
                """, (tag,))
            return cursor.lastrowid or cursor.fetchone()[0]

    def add_note_tag(self, note_id: str, tag: str):
        """Associate a tag with a note."""
        tag_id = self.add_tag(tag)
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO note_tags (note_id, tag_id)
                VALUES (?, ?)
            """, (note_id, tag_id))

    def get_note_tags(self, note_id: str) -> List[str]:
        """Get all tags for a note."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT t.tag
                FROM tags t
                JOIN note_tags nt ON t.id = nt.tag_id
                WHERE nt.note_id = ?
            """, (note_id,))
            return [row[0] for row in cursor.fetchall()]

    def get_tag_stats(self) -> List[Dict]:
        """Get tag usage statistics."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT tag, note_count
                FROM tags
                WHERE note_count > 0
                ORDER BY note_count DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_vault_tag_stats(self, vault_id: str, limit: int = 20) -> List[Dict]:
        """Get top tags for specific vault with note counts.

        Args:
            vault_id: Vault ID
            limit: Max tags to return (default: 20)

        Returns:
            List of {tag, note_count} dicts sorted by count desc
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.tag, COUNT(DISTINCT nt.note_id) as note_count
                FROM tags t
                JOIN note_tags nt ON t.id = nt.tag_id
                JOIN notes n ON nt.note_id = n.id
                WHERE n.vault_id = ?
                GROUP BY t.tag
                ORDER BY note_count DESC, t.tag ASC
                LIMIT ?
            """, (vault_id, limit))

            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_link_distribution(self, vault_id: str) -> Dict[str, int]:
        """Get distribution of link degrees in buckets.

        Args:
            vault_id: Vault ID

        Returns:
            Dict with buckets: {"0-2": count, "3-5": count, "6-10": count, "11+": count}
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    n.id,
                    COALESCE(gm.in_degree, 0) + COALESCE(gm.out_degree, 0) as total_degree
                FROM notes n
                LEFT JOIN graph_metrics gm ON n.id = gm.note_id
                WHERE n.vault_id = ?
            """, (vault_id,))

            degrees = [row[1] for row in cursor.fetchall()]

            distribution = {"0-2": 0, "3-5": 0, "6-10": 0, "11+": 0}
            for deg in degrees:
                if deg <= 2:
                    distribution["0-2"] += 1
                elif deg <= 5:
                    distribution["3-5"] += 1
                elif deg <= 10:
                    distribution["6-10"] += 1
                else:
                    distribution["11+"] += 1

            return distribution

    # ========================================================================
    # GRAPH METRICS
    # ========================================================================

    def get_graph_metrics(self, note_id: str) -> Optional[Dict]:
        """Get graph metrics for a note."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM graph_metrics WHERE note_id = ?
            """, (note_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_orphaned_notes(self, vault_id: Optional[str] = None) -> List[Dict]:
        """Get notes with no links."""
        with self.get_connection() as conn:
            if vault_id:
                cursor = conn.execute("""
                    SELECT * FROM orphaned_notes WHERE vault_id = ?
                """, (vault_id,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM orphaned_notes
                """)
            return [dict(row) for row in cursor.fetchall()]

    def get_hub_notes(self, vault_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Get highly connected notes."""
        with self.get_connection() as conn:
            if vault_id:
                cursor = conn.execute("""
                    SELECT * FROM hub_notes WHERE vault_id = ? LIMIT ?
                """, (vault_id, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM hub_notes LIMIT ?
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_broken_links(self, vault_id: Optional[str] = None) -> List[Dict]:
        """Get all broken links."""
        with self.get_connection() as conn:
            if vault_id:
                cursor = conn.execute("""
                    SELECT bl.*
                    FROM broken_links bl
                    JOIN notes n ON bl.source_path = n.path
                    WHERE n.vault_id = ?
                """, (vault_id,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM broken_links
                """)
            return [dict(row) for row in cursor.fetchall()]

    # ========================================================================
    # SCAN HISTORY
    # ========================================================================

    def start_scan(self, vault_id: str) -> int:
        """Record the start of a vault scan."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO scan_history (vault_id, status)
                VALUES (?, 'running')
            """, (vault_id,))
            return cursor.lastrowid

    def complete_scan(self, scan_id: int, notes_scanned: int,
                     notes_added: int = 0, notes_updated: int = 0,
                     notes_deleted: int = 0):
        """Mark scan as completed."""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE scan_history
                SET completed_at = CURRENT_TIMESTAMP,
                    notes_scanned = ?,
                    notes_added = ?,
                    notes_updated = ?,
                    notes_deleted = ?,
                    duration_seconds = (julianday(CURRENT_TIMESTAMP) - julianday(started_at)) * 86400,
                    status = 'completed'
                WHERE id = ?
            """, (notes_scanned, notes_added, notes_updated, notes_deleted, scan_id))

    def fail_scan(self, scan_id: int, error_message: str):
        """Mark scan as failed."""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE scan_history
                SET completed_at = CURRENT_TIMESTAMP,
                    status = 'failed',
                    error_message = ?
                WHERE id = ?
            """, (error_message, scan_id))

    def get_scan_history(self, vault_id: str, limit: int = 10) -> List[Dict]:
        """Get recent scan history for vault.

        Args:
            vault_id: Vault ID
            limit: Max records to return (default: 10)

        Returns:
            List of scan record dicts sorted by started_at desc
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT *
                FROM scan_history
                WHERE vault_id = ?
                ORDER BY started_at DESC
                LIMIT ?
            """, (vault_id, limit))

            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    # ========================================================================
    # UTILITY FUNCTIONS
    # ========================================================================

    @staticmethod
    def _generate_id(text: str) -> str:
        """Generate a unique ID from text using SHA256."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    @staticmethod
    def _hash_content(content: str) -> str:
        """Generate content hash for change detection."""
        return hashlib.sha256(content.encode()).hexdigest()

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self.get_connection() as conn:
            stats = {}

            # Vault stats
            cursor = conn.execute("SELECT COUNT(*) FROM vaults")
            stats['vaults'] = cursor.fetchone()[0]

            # Note stats
            cursor = conn.execute("SELECT COUNT(*) FROM notes")
            stats['notes'] = cursor.fetchone()[0]

            # Link stats
            cursor = conn.execute("SELECT COUNT(*) FROM links")
            stats['links'] = cursor.fetchone()[0]

            # Tag stats
            cursor = conn.execute("SELECT COUNT(*) FROM tags WHERE note_count > 0")
            stats['tags'] = cursor.fetchone()[0]

            # Orphan count
            cursor = conn.execute("SELECT COUNT(*) FROM orphaned_notes")
            stats['orphaned_notes'] = cursor.fetchone()[0]

            # Broken link count
            cursor = conn.execute("SELECT SUM(broken_count) FROM broken_links")
            result = cursor.fetchone()[0]
            stats['broken_links'] = result if result else 0

            return stats


if __name__ == '__main__':
    # Quick test
    db = DatabaseManager()
    print("Database initialized successfully!")
    print(f"Location: {db.db_path}")
    print(f"Stats: {db.get_stats()}")
