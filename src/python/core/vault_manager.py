"""
Vault Manager - Core business logic for vault operations.

This module contains interface-agnostic business logic for discovering,
scanning, and managing Obsidian vaults. Can be used by CLI, TUI, GUI, or any
other presentation layer.
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Callable, Coroutine, Dict
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db_manager import DatabaseManager
from vault_scanner import VaultScanner
from core.models import Vault, Note, ScanResult, VaultStats, HealthScore, VaultHealth
from core.exceptions import VaultNotFoundError, ScanError


@dataclass
class StalenessResult:
    """Result of a vault index staleness check."""
    is_stale: bool
    age_hours: float
    last_scanned: Optional[str]


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
        progress_callback: Optional[Callable[[int, int], Coroutine]] = None,
        prune: bool = False
    ) -> ScanResult:
        """
        Asynchronously scan a vault and populate database.

        Args:
            vault_path: Path to vault
            vault_name: Optional vault name (defaults to directory name)
            force: Force rescan even if vault hasn't changed
            progress_callback: Async function to call with (current, total) progress.
            prune: Opt-in mark-and-sweep of deleted/renamed notes (S1/S2).
                Default False keeps the scan additive.

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
                str(vault_path_obj), name,
                progress_callback=progress_callback, prune=prune
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
                notes_pruned=stats.get('notes_pruned', 0),
                notes_unchanged=stats.get('notes_unchanged', 0),
                notes_failed=stats.get('notes_failed', 0),
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

    def get_vault_health(self, vault_identifier: str) -> VaultHealth:
        """
        Compute health scores for a vault.

        Args:
            vault_identifier: Vault name or ID

        Returns:
            VaultHealth with 4 sub-scores and overall

        Raises:
            VaultNotFoundError: If vault not found
            ValueError: If ambiguous prefix
        """
        # Resolve vault — may raise ValueError for ambiguous prefix
        vault = self.db.get_vault_by_name_or_id(vault_identifier)
        if not vault:
            raise VaultNotFoundError(f"Vault not found: {vault_identifier}")

        vault_id = vault['id']
        vault_name = vault['name']

        # --- Shared data ---
        notes = self.db.list_notes(vault_id)
        total_notes = len(notes)

        # --- Connectivity (weight: 30%) ---
        orphans = self.db.get_orphaned_notes(vault_id)
        orphan_pct = len(orphans) / max(total_notes, 1) * 100
        conn_score = max(0, int(100 - orphan_pct * 2))
        conn_details = [
            f"{total_notes} notes",
            f"{len(orphans)} orphans ({orphan_pct:.1f}%)",
        ]
        conn_recs = []
        if len(orphans) > 0:
            conn_recs.append(f"Link or archive {len(orphans)} orphaned notes")
        connectivity = HealthScore(
            name="Connectivity",
            score=conn_score,
            details=conn_details,
            recommendations=conn_recs,
        )

        # --- Link Integrity (weight: 25%) ---
        broken_links = self.db.get_broken_links(vault_id)
        broken_count = sum(b.get('broken_count', 0) for b in broken_links)

        # Count total links from links table
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM links l JOIN notes n ON l.source_note_id = n.id WHERE n.vault_id = ?",
                    (vault_id,),
                )
                total_links = cursor.fetchone()[0]
        except Exception:
            total_links = 0

        broken_pct = broken_count / max(total_links, 1) * 100
        integrity_score = max(0, int(100 - broken_pct * 5))
        integrity_details = [
            f"{broken_count} broken links across {len(broken_links)} notes",
        ]
        integrity_recs = []
        if broken_count > 0:
            integrity_recs.append(f"Fix {broken_count} broken links in {len(broken_links)} notes")
        link_integrity = HealthScore(
            name="Link Integrity",
            score=integrity_score,
            details=integrity_details,
            recommendations=integrity_recs,
        )

        # --- Structure (weight: 25%) ---
        # Tag coverage
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT nt.note_id)
                    FROM note_tags nt
                    JOIN notes n ON nt.note_id = n.id
                    WHERE n.vault_id = ?
                """, (vault_id,))
                tagged_count = cursor.fetchone()[0]
        except Exception:
            tagged_count = 0

        tag_coverage = tagged_count / max(total_notes, 1) * 100

        # Hub balance
        hubs = self.db.get_hub_notes(vault_id, limit=3)
        hub_link_sum = sum(h.get('in_degree', 0) + h.get('out_degree', 0) for h in hubs)
        hub_concentration = hub_link_sum / max(total_links * 2, 1) * 100
        balance_score = 100 - min(hub_concentration, 100)

        structure_score = int(tag_coverage * 0.6 + balance_score * 0.4)
        structure_details = [
            f"Tag coverage: {tag_coverage:.0f}% of notes tagged",
            f"Hub balance: top 3 hubs hold {hub_concentration:.0f}% of links",
        ]
        structure_recs = []
        if tag_coverage < 50:
            structure_recs.append(f"Add tags to untagged notes ({100 - tag_coverage:.0f}% untagged)")
        structure = HealthScore(
            name="Structure",
            score=structure_score,
            details=structure_details,
            recommendations=structure_recs,
        )

        # --- Freshness (weight: 20%) ---
        freshness_data = self.db.get_note_freshness(vault_id)
        total_fresh = freshness_data['total']
        recent = freshness_data['recent']
        stale = freshness_data['stale']
        freshness_score = int(recent / max(total_fresh, 1) * 100)
        freshness_details = [
            f"{stale} notes not modified in 90+ days",
        ]
        freshness_recs = []
        if stale > 0:
            freshness_recs.append(f"Review {stale} stale notes (>90 days old)")
        freshness = HealthScore(
            name="Freshness",
            score=freshness_score,
            details=freshness_details,
            recommendations=freshness_recs,
        )

        # --- Overall ---
        overall = int(
            connectivity.score * 0.30
            + link_integrity.score * 0.25
            + structure.score * 0.25
            + freshness.score * 0.20
        )

        return VaultHealth(
            vault_name=vault_name,
            overall=overall,
            connectivity=connectivity,
            link_integrity=link_integrity,
            structure=structure,
            freshness=freshness,
        )

    def get_notes(self, vault_id: str, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Note]:
        """
        Get all notes in a vault.

        Args:
            vault_id: Vault ID
            limit: Max results
            offset: Pagination offset

        Returns:
            List of Note objects
        """
        rows = self.db.list_notes(vault_id, limit=limit, offset=offset)
        return [Note.from_db_row(dict(row)) for row in rows]

    def search_notes(self, query: str, vault_id: Optional[str] = None, tags: List[str] = None) -> List[Dict]:
        """
        Search notes and generate context snippets.

        Args:
            query: Search term
            vault_id: Optional vault ID
            tags: Optional tags

        Returns:
            List of dicts with note info and 'snippet' field
        """
        results = self.db.search_notes(query, vault_id, tags)
        processed = []
        
        lower_query = query.lower()
        
        for row in results:
            content = row.get('content', '')
            snippet = ""
            
            if content:
                # Find query position (simple case-insensitive find)
                idx = content.lower().find(lower_query)
                if idx != -1:
                    # Capture context around match
                    start = max(0, idx - 40)
                    end = min(len(content), idx + len(query) + 40)
                    snippet = "..." + content[start:end].replace('\n', ' ') + "..."
                else:
                    # If match was in title, just show start of content
                    snippet = content[:80].replace('\n', ' ') + "..."
            
            row['snippet'] = snippet
            # Don't send full content to UI to save memory
            if len(content) > 1000: 
                row['content'] = content[:100] + "..." 
            
            processed.append(row)
            
        return processed

    def get_note(self, note_id: str) -> Optional[Note]:
        """
        Get note by ID.

        Args:
            note_id: Note ID

        Returns:
            Note object or None
        """
        row = self.db.get_note(note_id)
        if not row:
            return None
        return Note.from_db_row(dict(row))

    def get_bridge_status(self):
        """Return BridgeStatus for the Obsidian CLI bridge."""
        from ai.obsidian_bridge import ObsidianBridge
        return ObsidianBridge(verbose=False).get_status()

    def get_trends(self, vault_identifier: str, lookback_days: int = 90):
        """Return TrendReport of weekly activity for a vault.

        Raises:
            VaultNotFoundError: If vault not found.
            ValueError: If vault_identifier is ambiguous.
        """
        from core.temporal import compute_trends
        vault = self.db.get_vault_by_name_or_id(vault_identifier)
        if not vault:
            raise VaultNotFoundError(f"Vault not found: {vault_identifier}")
        return compute_trends(vault['id'], self.db, lookback_days)

    def get_stale_notes(self, vault_identifier: str, limit: int = 50):
        """Return StaleReport of importance-weighted stale notes.

        Raises:
            VaultNotFoundError: If vault not found.
            ValueError: If vault_identifier is ambiguous.
        """
        from core.temporal import compute_stale
        vault = self.db.get_vault_by_name_or_id(vault_identifier)
        if not vault:
            raise VaultNotFoundError(f"Vault not found: {vault_identifier}")
        return compute_stale(vault['id'], self.db, limit)

    def get_daily_digest(self, vault_identifier: str, lookback_days: int = 90, stale_limit: int = 5):
        """Return DigestReport combining bridge status, weekly trends, and top stale notes.

        Raises:
            VaultNotFoundError: If vault not found.
            ValueError: If vault_identifier is ambiguous.
        """
        from ai.models import DigestReport
        vault = self.db.get_vault_by_name_or_id(vault_identifier)
        if not vault:
            raise VaultNotFoundError(f"Vault not found: {vault_identifier}")
        bridge = self.get_bridge_status()
        trends = self.get_trends(vault_identifier, lookback_days)
        stale = self.get_stale_notes(vault_identifier, limit=stale_limit)
        return DigestReport(vault_id=vault['id'], stale_limit=stale_limit,
                            bridge=bridge, trends=trends, stale=stale)

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

    def check_index_staleness(self, vault_id: str, threshold_hours: float = 24.0) -> StalenessResult:
        """
        Check whether a vault's index is stale relative to a threshold.

        Args:
            vault_id: Exact vault ID
            threshold_hours: Hours after which the index is considered stale (default: 24)

        Returns:
            StalenessResult with is_stale, age_hours, and last_scanned timestamp
        """
        try:
            vault = self.db.get_vault_by_name_or_id(vault_id)
        except ValueError:
            vault = None
        if not vault or not vault.get("last_scanned"):
            return StalenessResult(is_stale=True, age_hours=float("inf"), last_scanned=None)

        last = datetime.fromisoformat(vault["last_scanned"])
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - last).total_seconds() / 3600
        return StalenessResult(
            is_stale=age > threshold_hours,
            age_hours=age,
            last_scanned=vault["last_scanned"],
        )
