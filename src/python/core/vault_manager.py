"""
Vault Manager - Core business logic for vault operations.

This module contains interface-agnostic business logic for discovering,
scanning, and managing Obsidian vaults. Can be used by CLI, TUI, GUI, or any
other presentation layer.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db_manager import DatabaseManager
from vault_scanner import VaultScanner
from core.models import Vault, Note, ScanResult, VaultStats
from core.exceptions import VaultNotFoundError, ScanError


class VaultManager:
    """
    Manages vault operations (interface-agnostic business logic).

    This class orchestrates vault discovery, scanning, and management
    without any presentation logic. All methods return structured data
    that can be formatted by presentation layers.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize VaultManager.

        Args:
            db_manager: Optional DatabaseManager instance.
                       If not provided, creates a new one.
        """
        self.db = db_manager if db_manager else DatabaseManager()
        self.scanner = VaultScanner(self.db)

    def discover_vaults(self, root_path: str) -> List[str]:
        """
        Discover Obsidian vaults in a directory tree.

        Args:
            root_path: Root directory to search

        Returns:
            List of vault paths found

        Raises:
            VaultNotFoundError: If root_path doesn't exist
        """
        root = Path(root_path).resolve()

        if not root.exists():
            raise VaultNotFoundError(f"Path does not exist: {root_path}")

        if not root.is_dir():
            raise VaultNotFoundError(f"Path is not a directory: {root_path}")

        # Use scanner's discover method (it doesn't print, just returns paths)
        vaults = self.scanner.discover_vaults(str(root), verbose=False)

        return vaults

    def register_vault(self, vault_path: str, vault_name: Optional[str] = None) -> str:
        """
        Register a vault in the database without scanning it.

        Args:
            vault_path: Absolute path to the vault.
            vault_name: Optional vault name (defaults to directory name).

        Returns:
            The ID of the registered vault.
        """
        vault_path_obj = Path(vault_path).resolve()
        name = vault_name or vault_path_obj.name
        vault_id = self.db.add_vault(name, str(vault_path_obj))
        return vault_id

    def list_vaults(self) -> List[Vault]:
        """
        List all registered vaults from database.

        Returns:
            List of Vault objects
        """
        rows = self.db.list_vaults()
        return [Vault.from_db_row(dict(row)) for row in rows]

    def get_vault(self, vault_id: str) -> Optional[Vault]:
        """
        Get vault by ID.

        Args:
            vault_id: Vault ID

        Returns:
            Vault object or None if not found
        """
        row = self.db.get_vault(vault_id)
        if not row:
            return None
        return Vault.from_db_row(dict(row))

    def get_vault_by_path(self, vault_path: str) -> Optional[Vault]:
        """
        Get vault by filesystem path.

        Args:
            vault_path: Path to vault

        Returns:
            Vault object or None if not found
        """
        row = self.db.get_vault_by_path(vault_path)
        if not row:
            return None
        return Vault.from_db_row(dict(row))

    async def scan_vault(
        self,
        vault_path: str,
        vault_name: Optional[str] = None,
        force: bool = False,
        progress_callback: Optional[Callable[[int, int], Coroutine]] = None
    ) -> ScanResult:
        """
        Asynchronously scan a vault and populate database.

        Args:
            vault_path: Path to vault
            vault_name: Optional vault name (defaults to directory name)
            force: Force rescan even if vault hasn't changed
            progress_callback: Async function to call with (current, total) progress.

        Returns:
            ScanResult with scan statistics
        """
        vault_path_obj = Path(vault_path).resolve()

        if not vault_path_obj.exists() or not vault_path_obj.is_dir():
            raise VaultNotFoundError(f"Invalid vault path: {vault_path}")

        obsidian_dir = vault_path_obj / '.obsidian'
        if not obsidian_dir.exists():
            raise VaultNotFoundError(f"Not a valid Obsidian vault: {vault_path}")

        name = vault_name or vault_path_obj.name
        start_time = time.time()

        try:
            stats = await self.scanner.scan_vault(
                str(vault_path_obj), name, progress_callback=progress_callback
            )
            
            vault = self.db.get_vault_by_path(str(vault_path_obj))
            if not vault:
                raise ScanError("Vault not found in database after scan")

            return ScanResult(
                vault_id=vault['id'],
                vault_name=name,
                vault_path=str(vault_path_obj),
                notes_scanned=stats.get('notes_scanned', 0),
                links_found=stats.get('links_added', 0),
                duration_seconds=time.time() - start_time
            )

        except Exception as e:
            raise ScanError(f"Scan failed: {e}")

    def get_vault_stats(self, vault_id: str) -> VaultStats:
        """
        Get statistical summary for a vault.

        Args:
            vault_id: Vault ID

        Returns:
            VaultStats object

        Raises:
            VaultNotFoundError: If vault not found
        """
        vault = self.get_vault(vault_id)
        if not vault:
            raise VaultNotFoundError(f"Vault not found: {vault_id}")

        # Get stats from database
        stats_row = self.db.get_vault_stats(vault_id)

        if not stats_row:
            # Return empty stats if no data
            return VaultStats(
                vault_id=vault_id,
                vault_name=vault.name,
            )

        # Build VaultStats from database row
        return VaultStats(
            vault_id=vault_id,
            vault_name=vault.name,
            total_notes=stats_row.get('total_notes', 0),
            total_links=stats_row.get('total_links', 0),
            total_tags=stats_row.get('total_tags', 0),
            unique_tags=stats_row.get('unique_tags', 0),
            orphan_notes=stats_row.get('orphan_notes', 0),
            hub_notes=stats_row.get('hub_notes', 0),
            broken_links=stats_row.get('broken_links', 0),
            avg_links_per_note=stats_row.get('avg_links_per_note', 0.0),
            avg_words_per_note=stats_row.get('avg_words_per_note', 0.0),
            graph_density=stats_row.get('graph_density', 0.0),
            largest_component_size=stats_row.get('largest_component_size', 0),
        )

    def get_notes(
        self,
        vault_id: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Note]:
        """
        Get notes from a vault.

        Args:
            vault_id: Vault ID
            limit: Maximum number of notes to return
            offset: Number of notes to skip

        Returns:
            List of Note objects
        """
        rows = self.db.list_notes(vault_id, limit=limit, offset=offset)
        return [Note.from_db_row(dict(row)) for row in rows]

    def get_note(self, note_id: str) -> Optional[Note]:
        """
        Get a specific note by ID.

        Args:
            note_id: Note ID

        Returns:
            Note object or None if not found
        """
        row = self.db.get_note(note_id)
        if not row:
            return None
        return Note.from_db_row(dict(row))

    def search_notes(
        self,
        vault_id: str,
        query: str,
        limit: Optional[int] = None
    ) -> List[Note]:
        """
        Search notes by title or content.

        Args:
            vault_id: Vault ID
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching Note objects
        """
        # This would use a search method in DatabaseManager
        # For now, return empty list (to be implemented)
        return []

    def delete_vault(self, vault_id: str) -> bool:
        """
        Delete vault from database (not from filesystem).

        Args:
            vault_id: Vault ID

        Returns:
            True if deleted, False if not found
        """
        vault = self.get_vault(vault_id)
        if not vault:
            return False

        self.db.delete_vault(vault_id)
        return True
