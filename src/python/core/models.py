"""
Domain models for Obsidian CLI Ops.

These dataclasses represent the core business entities and are
interface-agnostic (can be used by CLI, TUI, GUI, etc.).
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class Vault:
    """Represents an Obsidian vault."""

    id: str
    name: str
    path: str
    note_count: int = 0
    link_count: int = 0
    tag_count: int = 0
    orphan_count: int = 0
    hub_count: int = 0
    last_scanned: Optional[datetime] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'Vault':
        """Create Vault from database row."""
        return cls(
            id=row['id'],
            name=row['name'],
            path=row['path'],
            note_count=row.get('note_count', 0),
            link_count=row.get('link_count', 0),
            tag_count=row.get('tag_count', 0),
            orphan_count=row.get('orphan_count', 0),
            hub_count=row.get('hub_count', 0),
            last_scanned=row.get('last_scanned'),
            created_at=row.get('created_at'),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'path': self.path,
            'note_count': self.note_count,
            'link_count': self.link_count,
            'tag_count': self.tag_count,
            'orphan_count': self.orphan_count,
            'hub_count': self.hub_count,
            'last_scanned': self.last_scanned.isoformat() if self.last_scanned else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class Note:
    """Represents a note in a vault."""

    id: str
    vault_id: str
    title: str
    path: str
    content: str = ""
    word_count: int = 0
    tags: List[str] = field(default_factory=list)
    outgoing_links: List[str] = field(default_factory=list)
    incoming_links: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'Note':
        """Create Note from database row."""
        return cls(
            id=row['id'],
            vault_id=row['vault_id'],
            title=row['title'],
            path=row['path'],
            content=row.get('content', ''),
            word_count=row.get('word_count', 0),
            tags=json.loads(row['tags']) if isinstance(row.get('tags'), str) else row.get('tags', []),
            outgoing_links=json.loads(row['outgoing_links']) if isinstance(row.get('outgoing_links'), str) else row.get('outgoing_links', []),
            incoming_links=json.loads(row['incoming_links']) if isinstance(row.get('incoming_links'), str) else row.get('incoming_links', []),
            created_at=row.get('created_at'),
            modified_at=row.get('modified_at'),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'vault_id': self.vault_id,
            'title': self.title,
            'path': self.path,
            'word_count': self.word_count,
            'tags': self.tags,
            'outgoing_links': self.outgoing_links,
            'incoming_links': self.incoming_links,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
        }


@dataclass
class ScanResult:
    """Result of a vault scan operation."""

    vault_id: str
    vault_name: str
    vault_path: str
    notes_scanned: int = 0
    links_found: int = 0
    tags_found: int = 0
    orphans_detected: int = 0
    hubs_detected: int = 0
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Whether scan completed without errors."""
        return len(self.errors) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'vault_id': self.vault_id,
            'vault_name': self.vault_name,
            'vault_path': self.vault_path,
            'notes_scanned': self.notes_scanned,
            'links_found': self.links_found,
            'tags_found': self.tags_found,
            'orphans_detected': self.orphans_detected,
            'hubs_detected': self.hubs_detected,
            'duration_seconds': self.duration_seconds,
            'success': self.success,
            'errors': self.errors,
            'warnings': self.warnings,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class GraphMetrics:
    """Graph analysis metrics for a note or vault."""

    node_id: str
    vault_id: str
    pagerank: float = 0.0
    in_degree: int = 0
    out_degree: int = 0
    betweenness_centrality: float = 0.0
    closeness_centrality: float = 0.0
    clustering_coefficient: float = 0.0

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'GraphMetrics':
        """Create GraphMetrics from database row."""
        return cls(
            node_id=row['note_id'],
            vault_id=row['vault_id'],
            pagerank=row.get('pagerank', 0.0),
            in_degree=row.get('in_degree', 0),
            out_degree=row.get('out_degree', 0),
            betweenness_centrality=row.get('betweenness_centrality', 0.0),
            closeness_centrality=row.get('closeness_centrality', 0.0),
            clustering_coefficient=row.get('clustering_coefficient', 0.0),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'node_id': self.node_id,
            'vault_id': self.vault_id,
            'pagerank': self.pagerank,
            'in_degree': self.in_degree,
            'out_degree': self.out_degree,
            'betweenness_centrality': self.betweenness_centrality,
            'closeness_centrality': self.closeness_centrality,
            'clustering_coefficient': self.clustering_coefficient,
        }


@dataclass
class VaultStats:
    """Statistical summary for a vault."""

    vault_id: str
    vault_name: str
    total_notes: int = 0
    total_links: int = 0
    total_tags: int = 0
    unique_tags: int = 0
    orphan_notes: int = 0
    hub_notes: int = 0
    broken_links: int = 0
    avg_links_per_note: float = 0.0
    avg_words_per_note: float = 0.0
    graph_density: float = 0.0
    largest_component_size: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'vault_id': self.vault_id,
            'vault_name': self.vault_name,
            'total_notes': self.total_notes,
            'total_links': self.total_links,
            'total_tags': self.total_tags,
            'unique_tags': self.unique_tags,
            'orphan_notes': self.orphan_notes,
            'hub_notes': self.hub_notes,
            'broken_links': self.broken_links,
            'avg_links_per_note': self.avg_links_per_note,
            'avg_words_per_note': self.avg_words_per_note,
            'graph_density': self.graph_density,
            'largest_component_size': self.largest_component_size,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
