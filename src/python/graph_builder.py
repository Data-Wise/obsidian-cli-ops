#!/usr/bin/env python3
"""
Graph Builder for Obsidian CLI Ops v2.0

Builds and analyzes the knowledge graph from vault data.
Calculates graph metrics (PageRank, centrality) and resolves wikilinks.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import networkx as nx

from db_manager import DatabaseManager


class LinkResolver:
    """Resolves wikilinks to actual note IDs."""

    def __init__(self, db: DatabaseManager):
        """
        Initialize link resolver.

        Args:
            db: Database manager instance
        """
        self.db = db
        self._note_cache = {}  # Cache for fast lookups

    def build_note_cache(self, vault_id: str):
        """
        Build cache of note paths and aliases for quick resolution.

        Args:
            vault_id: Vault to cache
        """
        notes = self.db.list_notes(vault_id)
        self._note_cache = {}

        for note in notes:
            note_id = note['id']
            path = note['path']
            title = note['title']

            # Cache by path (without .md extension)
            path_key = path.replace('.md', '')
            self._note_cache[path_key] = note_id

            # Cache by title
            self._note_cache[title] = note_id

            # Cache by filename only (for [[Filename]] links)
            filename = Path(path).stem
            if filename not in self._note_cache:
                self._note_cache[filename] = note_id

            # TODO: Add alias support from metadata

    def resolve_link(self, target_path: str, source_note: Dict) -> Optional[str]:
        """
        Resolve a wikilink target to a note ID.

        Args:
            target_path: Link target (as written in markdown)
            source_note: Source note containing the link

        Returns:
            Note ID if found, None if broken link
        """
        # Remove heading/block references (#, ^)
        target_path = re.sub(r'[#^].*$', '', target_path)
        target_path = target_path.strip()

        # Try exact match first
        if target_path in self._note_cache:
            return self._note_cache[target_path]

        # Try without .md extension
        if target_path.endswith('.md'):
            target_path = target_path[:-3]
            if target_path in self._note_cache:
                return self._note_cache[target_path]

        # Try as relative path from source note
        source_dir = str(Path(source_note['path']).parent)
        relative_path = str(Path(source_dir) / target_path)
        if relative_path in self._note_cache:
            return self._note_cache[relative_path]

        # Not found - broken link
        return None

    def resolve_all_links(self, vault_id: str, verbose: bool = False) -> Dict:
        """
        Resolve all links in a vault and update database.

        Args:
            vault_id: Vault to process
            verbose: Print progress

        Returns:
            Dictionary with resolution statistics
        """
        if verbose:
            print(f"🔗 Resolving links for vault...")

        # Build note cache
        self.build_note_cache(vault_id)

        notes = self.db.list_notes(vault_id)
        stats = {
            'total_links': 0,
            'resolved': 0,
            'broken': 0
        }

        for note in notes:
            note_id = note['id']
            links = self.db.get_outgoing_links(note_id)

            for link in links:
                stats['total_links'] += 1
                target_path = link['target_path']

                # Resolve link
                resolved_id = self.resolve_link(target_path, note)

                # Update link in database
                with self.db.get_connection() as conn:
                    if resolved_id:
                        conn.execute("""
                            UPDATE links
                            SET target_note_id = ?,
                                link_type = 'internal'
                            WHERE id = ?
                        """, (resolved_id, link['id']))
                        stats['resolved'] += 1
                    else:
                        conn.execute("""
                            UPDATE links
                            SET link_type = 'broken'
                            WHERE id = ?
                        """, (link['id'],))
                        stats['broken'] += 1

        if verbose:
            print(f"   Total links: {stats['total_links']}")
            print(f"   Resolved: {stats['resolved']}")
            print(f"   Broken: {stats['broken']}")

        return stats


class GraphBuilder:
    """Builds and analyzes knowledge graph using NetworkX."""

    def __init__(self, db: DatabaseManager):
        """
        Initialize graph builder.

        Args:
            db: Database manager instance
        """
        self.db = db
        self.resolver = LinkResolver(db)

    def build_graph(self, vault_id: str) -> nx.DiGraph:
        """
        Build NetworkX directed graph from database.

        Args:
            vault_id: Vault to build graph for

        Returns:
            NetworkX DiGraph
        """
        graph = nx.DiGraph()

        # Add nodes (notes)
        notes = self.db.list_notes(vault_id)
        for note in notes:
            graph.add_node(note['id'], **note)

        # Add edges (links)
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT source_note_id, target_note_id
                FROM links
                WHERE link_type = 'internal'
                AND target_note_id IS NOT NULL
            """)
            for row in cursor.fetchall():
                graph.add_edge(row[0], row[1])

        return graph

    def calculate_metrics(self, vault_id: str, verbose: bool = False) -> Dict:
        """
        Calculate graph metrics for all notes.

        Args:
            vault_id: Vault to analyze
            verbose: Print progress

        Returns:
            Dictionary with calculation statistics
        """
        if verbose:
            print(f"📊 Calculating graph metrics...")

        # Build graph
        graph = self.build_graph(vault_id)

        if len(graph) == 0:
            if verbose:
                print("   ⚠️  No notes in graph")
            return {'notes': 0}

        stats = {
            'notes': len(graph),
            'edges': graph.number_of_edges(),
            'density': nx.density(graph)
        }

        # Calculate PageRank
        try:
            pagerank = nx.pagerank(graph)
        except:
            pagerank = {node: 0.0 for node in graph.nodes()}

        # Calculate centrality metrics
        try:
            betweenness = nx.betweenness_centrality(graph)
        except:
            betweenness = {node: 0.0 for node in graph.nodes()}

        try:
            closeness = nx.closeness_centrality(graph)
        except:
            closeness = {node: 0.0 for node in graph.nodes()}

        # Calculate clustering coefficient (undirected)
        try:
            undirected = graph.to_undirected()
            clustering = nx.clustering(undirected)
        except:
            clustering = {node: 0.0 for node in graph.nodes()}

        # Update database
        with self.db.get_connection() as conn:
            for node in graph.nodes():
                in_deg = graph.in_degree(node)
                out_deg = graph.out_degree(node)

                conn.execute("""
                    UPDATE graph_metrics
                    SET pagerank = ?,
                        in_degree = ?,
                        out_degree = ?,
                        betweenness = ?,
                        closeness = ?,
                        clustering_coefficient = ?,
                        computed_at = CURRENT_TIMESTAMP
                    WHERE note_id = ?
                """, (
                    pagerank.get(node, 0.0),
                    in_deg,
                    out_deg,
                    betweenness.get(node, 0.0),
                    closeness.get(node, 0.0),
                    clustering.get(node, 0.0),
                    node
                ))

        if verbose:
            print(f"   Notes: {stats['notes']}")
            print(f"   Links: {stats['edges']}")
            print(f"   Density: {stats['density']:.4f}")
            print(f"   ✓ Metrics updated")

        return stats

    def find_clusters(self, vault_id: str, min_size: int = 3) -> List[Set[str]]:
        """
        Find clusters (communities) in the knowledge graph.

        Args:
            vault_id: Vault to analyze
            min_size: Minimum cluster size

        Returns:
            List of clusters (sets of note IDs)
        """
        graph = self.build_graph(vault_id)
        undirected = graph.to_undirected()

        # Find weakly connected components
        components = list(nx.connected_components(undirected))

        # Filter by minimum size
        clusters = [c for c in components if len(c) >= min_size]

        return clusters

    def get_note_neighborhood(self, note_id: str, depth: int = 1) -> nx.DiGraph:
        """
        Get subgraph of notes within N links of target note.

        Args:
            note_id: Center note
            depth: Number of link hops

        Returns:
            Subgraph centered on note
        """
        # Get note's vault
        note = self.db.get_note(note_id)
        if not note:
            return nx.DiGraph()

        vault_id = note['vault_id']
        graph = self.build_graph(vault_id)

        if note_id not in graph:
            return nx.DiGraph()

        # Get neighborhood
        nodes = {note_id}
        for _ in range(depth):
            new_nodes = set()
            for node in nodes:
                # Add predecessors and successors
                new_nodes.update(graph.predecessors(node))
                new_nodes.update(graph.successors(node))
            nodes.update(new_nodes)

        # Return subgraph
        return graph.subgraph(nodes).copy()

    def analyze_vault(self, vault_id: str, verbose: bool = False) -> Dict:
        """
        Complete vault analysis: resolve links + calculate metrics.

        Args:
            vault_id: Vault to analyze
            verbose: Print progress

        Returns:
            Combined statistics
        """
        if verbose:
            print(f"\n🔍 Analyzing vault graph...")

        # Resolve links
        link_stats = self.resolver.resolve_all_links(vault_id, verbose)

        # Calculate metrics
        graph_stats = self.calculate_metrics(vault_id, verbose)

        return {
            **link_stats,
            **graph_stats
        }


def main():
    """CLI interface for graph builder."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python graph_builder.py <vault_id>")
        sys.exit(1)

    vault_id = sys.argv[1]

    # Initialize
    db = DatabaseManager()
    builder = GraphBuilder(db)

    # Analyze
    try:
        stats = builder.analyze_vault(vault_id, verbose=True)
        print("\n✓ Analysis complete!")

        # Show interesting findings
        print("\n📈 Insights:")

        # Top hubs
        hubs = db.get_hub_notes(vault_id, limit=5)
        if hubs:
            print("\n  Top Hub Notes:")
            for hub in hubs:
                print(f"    • {hub['title']} ({hub['total_degree']} connections)")

        # Orphans
        orphans = db.get_orphaned_notes(vault_id)
        if orphans:
            print(f"\n  Orphaned Notes: {len(orphans)}")

        # Broken links
        broken = db.get_broken_links(vault_id)
        if broken:
            print(f"\n  Broken Links: {sum(b['broken_count'] for b in broken)}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
