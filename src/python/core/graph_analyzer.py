"""
Graph Analyzer - Core business logic for graph analysis operations.

This module contains interface-agnostic business logic for analyzing
vault knowledge graphs. Can be used by CLI, TUI, GUI, or any other
presentation layer.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import networkx as nx

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db_manager import DatabaseManager
from graph_builder import GraphBuilder, LinkResolver
from core.models import GraphMetrics, VaultStats
from core.exceptions import AnalysisError, VaultNotFoundError


class GraphAnalyzer:
    """
    Manages graph analysis operations (interface-agnostic business logic).

    This class orchestrates graph analysis, metrics calculation, and
    cluster detection without any presentation logic.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize GraphAnalyzer.

        Args:
            db_manager: Optional DatabaseManager instance.
                       If not provided, creates a new one.
        """
        self.db = db_manager if db_manager else DatabaseManager()
        self.graph_builder = GraphBuilder(self.db)
        self.resolver = LinkResolver(self.db)

    def analyze_vault(self, vault_id: str) -> Dict[str, Any]:
        """
        Complete graph analysis for a vault.

        Performs:
        1. Link resolution
        2. Graph metrics calculation
        3. Cluster detection

        Args:
            vault_id: Vault ID to analyze

        Returns:
            Dictionary with analysis statistics

        Raises:
            VaultNotFoundError: If vault not found
            AnalysisError: If analysis fails
        """
        # Verify vault exists
        vault = self.db.get_vault(vault_id)
        if not vault:
            raise VaultNotFoundError(f"Vault not found: {vault_id}")

        try:
            # Step 1: Resolve links
            link_stats = self.resolver.resolve_all_links(vault_id, verbose=False)

            # Step 2: Calculate metrics
            metric_stats = self.graph_builder.calculate_metrics(vault_id, verbose=False)

            # Step 3: Find clusters
            clusters = self.graph_builder.find_clusters(vault_id, min_size=3)

            # Combine results
            result = {
                'vault_id': vault_id,
                'vault_name': vault['name'],
                'links_resolved': link_stats.get('resolved', 0),
                'links_broken': link_stats.get('broken', 0),
                'total_notes': metric_stats.get('notes', 0),
                'total_edges': metric_stats.get('edges', 0),
                'graph_density': metric_stats.get('density', 0.0),
                'clusters_found': len(clusters),
                'largest_cluster_size': max((len(c) for c in clusters), default=0),
            }

            return result

        except Exception as e:
            raise AnalysisError(f"Graph analysis failed: {e}")

    def get_graph(self, vault_id: str) -> nx.DiGraph:
        """
        Build NetworkX graph for a vault.

        Args:
            vault_id: Vault ID

        Returns:
            NetworkX DiGraph

        Raises:
            VaultNotFoundError: If vault not found
        """
        # Verify vault exists
        vault = self.db.get_vault(vault_id)
        if not vault:
            raise VaultNotFoundError(f"Vault not found: {vault_id}")

        return self.graph_builder.build_graph(vault_id)

    def get_note_metrics(self, note_id: str) -> Optional[GraphMetrics]:
        """
        Get graph metrics for a specific note.

        Args:
            note_id: Note ID

        Returns:
            GraphMetrics object or None if not found
        """
        row = self.db.get_note_metrics(note_id)
        if not row:
            return None

        return GraphMetrics.from_db_row(dict(row))

    def get_hub_notes(
        self,
        vault_id: str,
        limit: int = 10,
        min_links: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get hub notes (highly connected notes).

        Args:
            vault_id: Vault ID
            limit: Maximum number of hubs to return
            min_links: Minimum number of links to qualify as hub

        Returns:
            List of hub note dictionaries with metrics
        """
        # Verify vault exists
        vault = self.db.get_vault(vault_id)
        if not vault:
            return []

        hubs = self.db.get_hub_notes(vault_id, limit=limit)

        # Filter by minimum links
        return [
            dict(hub) for hub in hubs
            if (hub.get('in_degree', 0) + hub.get('out_degree', 0)) >= min_links
        ]

    def get_orphan_notes(
        self,
        vault_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get orphan notes (notes with no connections).

        Args:
            vault_id: Vault ID
            limit: Maximum number of orphans to return

        Returns:
            List of orphan note dictionaries
        """
        # Verify vault exists
        vault = self.db.get_vault(vault_id)
        if not vault:
            return []

        orphans = self.db.get_orphaned_notes(vault_id, limit=limit)
        return [dict(orphan) for orphan in orphans]

    def get_broken_links(
        self,
        vault_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get broken wikilinks in vault.

        Args:
            vault_id: Vault ID
            limit: Maximum number to return

        Returns:
            List of broken link dictionaries
        """
        # Verify vault exists
        vault = self.db.get_vault(vault_id)
        if not vault:
            return []

        broken = self.db.get_broken_links(vault_id, limit=limit)
        return [dict(link) for link in broken]

    def calculate_metrics(self, vault_id: str) -> Dict[str, Any]:
        """
        Calculate and store graph metrics for a vault.

        Args:
            vault_id: Vault ID

        Returns:
            Dictionary with calculation statistics

        Raises:
            VaultNotFoundError: If vault not found
            AnalysisError: If calculation fails
        """
        # Verify vault exists
        vault = self.db.get_vault(vault_id)
        if not vault:
            raise VaultNotFoundError(f"Vault not found: {vault_id}")

        try:
            stats = self.graph_builder.calculate_metrics(vault_id, verbose=False)
            return stats
        except Exception as e:
            raise AnalysisError(f"Metric calculation failed: {e}")

    def resolve_links(self, vault_id: str) -> Dict[str, int]:
        """
        Resolve all wikilinks in a vault.

        Args:
            vault_id: Vault ID

        Returns:
            Dictionary with resolution statistics

        Raises:
            VaultNotFoundError: If vault not found
        """
        # Verify vault exists
        vault = self.db.get_vault(vault_id)
        if not vault:
            raise VaultNotFoundError(f"Vault not found: {vault_id}")

        return self.resolver.resolve_all_links(vault_id, verbose=False)

    def find_clusters(
        self,
        vault_id: str,
        min_size: int = 3
    ) -> List[Set[str]]:
        """
        Find clusters (communities) in knowledge graph.

        Args:
            vault_id: Vault ID
            min_size: Minimum cluster size

        Returns:
            List of clusters (sets of note IDs)

        Raises:
            VaultNotFoundError: If vault not found
        """
        # Verify vault exists
        vault = self.db.get_vault(vault_id)
        if not vault:
            raise VaultNotFoundError(f"Vault not found: {vault_id}")

        return self.graph_builder.find_clusters(vault_id, min_size=min_size)

    def get_ego_graph(
        self,
        note_id: str,
        radius: int = 1
    ) -> nx.DiGraph:
        """
        Get ego graph (local neighborhood) for a note.

        Args:
            note_id: Center note ID
            radius: Number of hops from center (default 1)

        Returns:
            NetworkX DiGraph containing ego network

        Raises:
            ValueError: If note not found
        """
        # Get note to find vault_id
        note = self.db.get_note(note_id)
        if not note:
            raise ValueError(f"Note not found: {note_id}")

        vault_id = note['vault_id']

        # Build full graph
        graph = self.graph_builder.build_graph(vault_id)

        # Extract ego graph
        if note_id not in graph:
            raise ValueError(f"Note not in graph: {note_id}")

        ego = nx.ego_graph(graph, note_id, radius=radius)
        return ego
