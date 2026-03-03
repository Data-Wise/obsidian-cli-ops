"""
AI-powered features for note analysis and similarity detection.

Features:
- find_similar_notes: Find notes similar to a given note
- analyze_note: Deep analysis of a single note
- find_duplicates: Detect potential duplicate notes
- suggest_links: Suggest new links based on embedding similarity
- find_gaps: Identify knowledge gaps in the vault
- summarize_vault: Generate vault-wide summary with themes
"""

import os
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import numpy as np

from .router import get_ai_client, AIRouter
from .models import AnalysisResult, ComparisonResult, SimilarNote


@dataclass
class SimilarityMatch:
    """A note found to be similar to the query note."""
    note_id: str
    title: str
    path: str
    similarity: float  # 0.0 to 1.0
    reason: str = ""


@dataclass
class DuplicateGroup:
    """A group of potentially duplicate notes."""
    notes: List[Dict]  # List of note info dicts
    similarity: float  # Average similarity in group
    reason: str = ""


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a = np.array(vec1)
    b = np.array(vec2)

    # Handle zero vectors
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))


def _get_note_content(note: Dict, vault_path: str) -> Optional[str]:
    """Read note content from file.

    Args:
        note: Note dict from database
        vault_path: Path to the vault

    Returns:
        Note content or None if file not found
    """
    try:
        note_path = Path(vault_path) / note['path']
        if note_path.exists():
            return note_path.read_text(encoding='utf-8')
    except Exception:
        pass
    return None


def find_similar_notes(
    note_id: str,
    db_manager,
    limit: int = 10,
    min_similarity: float = 0.3,
    provider: Optional[str] = None
) -> List[SimilarityMatch]:
    """Find notes similar to the given note.

    Uses embeddings to find semantically similar notes within the same vault.

    Args:
        note_id: ID of the note to find similar notes for
        db_manager: DatabaseManager instance
        limit: Maximum number of similar notes to return
        min_similarity: Minimum similarity threshold (0.0-1.0)
        provider: Preferred AI provider (optional)

    Returns:
        List of SimilarityMatch objects sorted by similarity (highest first)

    Raises:
        ValueError: If note not found
        RuntimeError: If no AI provider available
    """
    # Get the source note
    source_note = db_manager.get_note(note_id)
    if not source_note:
        raise ValueError(f"Note not found: {note_id}")

    # Get vault info
    vault = db_manager.get_vault(source_note['vault_id'])
    if not vault:
        raise ValueError(f"Vault not found for note: {note_id}")

    # Get source note content
    source_content = _get_note_content(source_note, vault['path'])
    if not source_content:
        raise ValueError(f"Could not read note content: {source_note['path']}")

    # Get AI client
    router = get_ai_client(provider=provider)

    # Get embedding for source note
    source_embedding = router.get_embedding(source_content)

    # Get all other notes in the vault
    all_notes = db_manager.list_notes(vault_id=source_note['vault_id'])
    other_notes = [n for n in all_notes if n['id'] != note_id]

    if not other_notes:
        return []

    # Batch get contents and embeddings
    note_contents = []
    valid_notes = []

    for note in other_notes:
        content = _get_note_content(note, vault['path'])
        if content and len(content.strip()) > 50:  # Skip very short notes
            note_contents.append(content)
            valid_notes.append(note)

    if not note_contents:
        return []

    # Get embeddings (batch if possible)
    try:
        embeddings = router.get_embeddings_batch(note_contents)
    except Exception:
        # Fallback to sequential
        embeddings = [router.get_embedding(c) for c in note_contents]

    # Calculate similarities
    matches = []
    for note, embedding in zip(valid_notes, embeddings):
        similarity = _cosine_similarity(source_embedding, embedding)

        if similarity >= min_similarity:
            matches.append(SimilarityMatch(
                note_id=note['id'],
                title=note['title'],
                path=note['path'],
                similarity=similarity,
                reason=f"Semantic similarity: {similarity:.1%}"
            ))

    # Sort by similarity and limit
    matches.sort(key=lambda m: m.similarity, reverse=True)
    return matches[:limit]


def analyze_note(
    note_id: str,
    db_manager,
    provider: Optional[str] = None
) -> AnalysisResult:
    """Perform deep analysis of a single note.

    Analyzes the note's content for topics, themes, quality, and suggestions.

    Args:
        note_id: ID of the note to analyze
        db_manager: DatabaseManager instance
        provider: Preferred AI provider (optional)

    Returns:
        AnalysisResult with topics, themes, quality scores, and suggestions

    Raises:
        ValueError: If note not found
        RuntimeError: If no AI provider available
    """
    # Get the note
    note = db_manager.get_note(note_id)
    if not note:
        raise ValueError(f"Note not found: {note_id}")

    # Get vault info
    vault = db_manager.get_vault(note['vault_id'])
    if not vault:
        raise ValueError(f"Vault not found for note: {note_id}")

    # Get note content
    content = _get_note_content(note, vault['path'])
    if not content:
        raise ValueError(f"Could not read note content: {note['path']}")

    # Get AI client and analyze
    router = get_ai_client(provider=provider)
    return router.analyze_note(content, note['title'])


def find_duplicates(
    vault_id: str,
    db_manager,
    threshold: float = 0.85,
    limit: int = 50,
    provider: Optional[str] = None
) -> List[DuplicateGroup]:
    """Find potential duplicate notes in a vault.

    Uses embeddings to find notes with very high similarity that may be duplicates.

    Args:
        vault_id: ID of the vault to scan
        db_manager: DatabaseManager instance
        threshold: Similarity threshold for duplicate detection (default 0.85)
        limit: Maximum number of duplicate groups to return
        provider: Preferred AI provider (optional)

    Returns:
        List of DuplicateGroup objects

    Raises:
        ValueError: If vault not found
        RuntimeError: If no AI provider available
    """
    # Get vault info
    vault = db_manager.get_vault(vault_id)
    if not vault:
        raise ValueError(f"Vault not found: {vault_id}")

    # Get all notes
    notes = db_manager.list_notes(vault_id=vault_id)

    if len(notes) < 2:
        return []

    # Get AI client
    router = get_ai_client(provider=provider)

    # Get contents and embeddings
    note_contents = []
    valid_notes = []

    for note in notes:
        content = _get_note_content(note, vault['path'])
        if content and len(content.strip()) > 50:
            note_contents.append(content)
            valid_notes.append(note)

    if len(valid_notes) < 2:
        return []

    # Get embeddings
    print(f"  Computing embeddings for {len(valid_notes)} notes...")
    try:
        embeddings = router.get_embeddings_batch(note_contents)
    except Exception:
        embeddings = [router.get_embedding(c) for c in note_contents]

    # Find duplicate pairs
    duplicates: List[Tuple[int, int, float]] = []

    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            similarity = _cosine_similarity(embeddings[i], embeddings[j])
            if similarity >= threshold:
                duplicates.append((i, j, similarity))

    # Group duplicates (simple clustering)
    # Use Union-Find to group connected duplicates
    parent = list(range(len(valid_notes)))

    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for i, j, _ in duplicates:
        union(i, j)

    # Collect groups
    groups: Dict[int, List[Tuple[int, float]]] = {}
    for idx in range(len(valid_notes)):
        root = find(idx)
        if root not in groups:
            groups[root] = []
        groups[root].append(idx)

    # Convert to DuplicateGroup objects
    result = []
    for indices in groups.values():
        if len(indices) < 2:
            continue

        # Calculate average similarity within group
        sims = []
        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                sim = _cosine_similarity(embeddings[indices[i]], embeddings[indices[j]])
                sims.append(sim)
        avg_sim = sum(sims) / len(sims) if sims else 0

        group_notes = [
            {
                'id': valid_notes[idx]['id'],
                'title': valid_notes[idx]['title'],
                'path': valid_notes[idx]['path'],
            }
            for idx in indices
        ]

        result.append(DuplicateGroup(
            notes=group_notes,
            similarity=avg_sim,
            reason=f"Average similarity: {avg_sim:.1%}"
        ))

    # Sort by similarity and limit
    result.sort(key=lambda g: g.similarity, reverse=True)
    return result[:limit]


def compare_notes(
    note1_id: str,
    note2_id: str,
    db_manager,
    provider: Optional[str] = None
) -> ComparisonResult:
    """Compare two notes for similarity and potential merge.

    Args:
        note1_id: First note ID
        note2_id: Second note ID
        db_manager: DatabaseManager instance
        provider: Preferred AI provider (optional)

    Returns:
        ComparisonResult with similarity score, reason, and merge suggestion

    Raises:
        ValueError: If either note not found
        RuntimeError: If no AI provider available
    """
    # Get notes
    note1 = db_manager.get_note(note1_id)
    note2 = db_manager.get_note(note2_id)

    if not note1:
        raise ValueError(f"Note not found: {note1_id}")
    if not note2:
        raise ValueError(f"Note not found: {note2_id}")

    # Get vault (both notes must be in same vault for now)
    vault = db_manager.get_vault(note1['vault_id'])
    if not vault:
        raise ValueError(f"Vault not found")

    # Get contents
    content1 = _get_note_content(note1, vault['path'])
    content2 = _get_note_content(note2, vault['path'])

    if not content1:
        raise ValueError(f"Could not read note: {note1['path']}")
    if not content2:
        raise ValueError(f"Could not read note: {note2['path']}")

    # Get AI client and compare
    router = get_ai_client(provider=provider)
    return router.compare_notes(
        content1, content2,
        note1['title'], note2['title']
    )


# ====================================================================
# New AI commands (Increment 5)
# ====================================================================

@dataclass
class LinkSuggestion:
    """A suggested link between notes."""
    source_title: str
    target_title: str
    target_path: str
    similarity: float
    reason: str = ""


@dataclass
class KnowledgeGap:
    """A gap in the knowledge graph."""
    description: str
    related_notes: List[str] = field(default_factory=list)
    suggested_action: str = ""


@dataclass
class VaultSummary:
    """Summary of a vault or subset."""
    note_count: int = 0
    themes: List[str] = field(default_factory=list)
    top_hubs: List[Dict] = field(default_factory=list)
    orphan_count: int = 0
    graph_stats: Dict = field(default_factory=dict)
    summary_text: str = ""


def _get_cached_embedding(
    note_id: str,
    content: str,
    file_mtime: float,
    db_manager,
    router: AIRouter,
    provider_name: str = "",
    model_name: str = "",
) -> List[float]:
    """Get embedding from cache or compute and cache it.

    Invalidates cache if file_mtime has changed.
    """
    if not provider_name:
        provider_name = "unknown"
    if not model_name:
        model_name = "default"

    # Try cache
    try:
        cached = db_manager.get_embedding_with_mtime(note_id, provider_name, model_name)
        if cached and cached['file_mtime'] == file_mtime:
            return list(np.frombuffer(cached['vector'], dtype=np.float32))
    except Exception:
        pass  # Table might not exist yet

    # Compute fresh
    embedding = router.get_embedding(content)

    # Cache it
    try:
        db_manager.ensure_embeddings_table()
        vector_bytes = np.array(embedding, dtype=np.float32).tobytes()
        db_manager.save_embedding(note_id, provider_name, model_name, vector_bytes, file_mtime)
    except Exception:
        pass  # Caching failure shouldn't block the operation

    return embedding


def suggest_links(
    note_id: str,
    db_manager,
    limit: int = 5,
    provider: Optional[str] = None,
) -> List[LinkSuggestion]:
    """Suggest new links for a note based on embedding similarity.

    Finds the most similar notes that aren't already linked.

    Args:
        note_id: ID of the note to suggest links for
        db_manager: DatabaseManager instance
        limit: Number of suggestions to return
        provider: Preferred AI provider

    Returns:
        List of LinkSuggestion objects
    """
    # Get the source note
    source_note = db_manager.get_note(note_id)
    if not source_note:
        raise ValueError(f"Note not found: {note_id}")

    vault = db_manager.get_vault(source_note['vault_id'])
    if not vault:
        raise ValueError(f"Vault not found for note: {note_id}")

    source_content = _get_note_content(source_note, vault['path'])
    if not source_content:
        raise ValueError(f"Could not read note content: {source_note['path']}")

    router = get_ai_client(provider=provider)

    # Get existing links from this note (to exclude them)
    existing_links = set()
    try:
        from db_manager import DatabaseManager
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT target_note_id FROM links WHERE source_note_id = ? AND target_note_id IS NOT NULL",
                (note_id,),
            )
            existing_links = {row['target_note_id'] for row in cursor.fetchall()}
    except Exception:
        pass

    # Get all other notes
    all_notes = db_manager.list_notes(vault_id=source_note['vault_id'])
    candidates = [
        n for n in all_notes
        if n['id'] != note_id and n['id'] not in existing_links
    ]

    if not candidates:
        return []

    # Get source embedding
    source_mtime = os.path.getmtime(Path(vault['path']) / source_note['path']) if Path(vault['path']).joinpath(source_note['path']).exists() else 0
    source_embedding = _get_cached_embedding(
        note_id, source_content, source_mtime,
        db_manager, router,
    )

    # Get candidate embeddings and compute similarity
    suggestions = []
    for note in candidates:
        content = _get_note_content(note, vault['path'])
        if not content or len(content.strip()) < 50:
            continue

        note_path = Path(vault['path']) / note['path']
        mtime = os.path.getmtime(note_path) if note_path.exists() else 0
        embedding = _get_cached_embedding(
            note['id'], content, mtime,
            db_manager, router,
        )

        similarity = _cosine_similarity(source_embedding, embedding)
        if similarity > 0.3:
            suggestions.append(LinkSuggestion(
                source_title=source_note['title'],
                target_title=note['title'],
                target_path=note['path'],
                similarity=similarity,
                reason=f"Semantic similarity: {similarity:.0%}",
            ))

    suggestions.sort(key=lambda s: s.similarity, reverse=True)
    return suggestions[:limit]


def find_gaps(
    vault_id: str,
    db_manager,
    provider: Optional[str] = None,
) -> List[KnowledgeGap]:
    """Identify knowledge gaps in the vault.

    Finds:
    - Notes with high incoming references but low content (< 100 words)
    - Orphaned notes that should be connected
    - High-centrality areas with few notes

    Args:
        vault_id: Vault ID
        db_manager: DatabaseManager instance
        provider: Preferred AI provider

    Returns:
        List of KnowledgeGap objects
    """
    vault = db_manager.get_vault(vault_id)
    if not vault:
        raise ValueError(f"Vault not found: {vault_id}")

    gaps = []

    # 1. Find stub notes (high in-degree but low word count)
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT n.id, n.title, n.word_count, gm.in_degree, gm.pagerank
                FROM notes n
                JOIN graph_metrics gm ON n.id = gm.note_id
                WHERE n.vault_id = ? AND n.word_count < 100 AND gm.in_degree > 3
                ORDER BY gm.in_degree DESC
                LIMIT 10
            """, (vault_id,))
            stubs = [dict(row) for row in cursor.fetchall()]

            for stub in stubs:
                gaps.append(KnowledgeGap(
                    description=f"Stub note '{stub['title']}' has {stub['in_degree']} incoming links but only {stub['word_count']} words",
                    related_notes=[stub['title']],
                    suggested_action=f"Expand '{stub['title']}' — it's referenced by {stub['in_degree']} other notes",
                ))
    except Exception:
        pass

    # 2. Find orphaned notes
    orphans = db_manager.get_orphaned_notes(vault_id=vault_id, limit=10)
    if orphans:
        orphan_titles = [o['title'] for o in orphans]
        gaps.append(KnowledgeGap(
            description=f"{len(orphans)} orphaned notes with no connections",
            related_notes=orphan_titles,
            suggested_action="Add links to connect these notes to the knowledge graph",
        ))

    # 3. Use Obsidian bridge for additional data
    from .obsidian_bridge import ObsidianBridge
    bridge = ObsidianBridge()
    bridge_orphans = bridge.get_orphans()
    if bridge_orphans:
        bridge_only = [o for o in bridge_orphans if o not in [n['path'] for n in orphans]]
        if bridge_only:
            gaps.append(KnowledgeGap(
                description=f"{len(bridge_only)} additional orphans detected by Obsidian",
                related_notes=bridge_only[:5],
                suggested_action="Review and connect or archive these notes",
            ))

    return gaps


def summarize_vault(
    vault_id: str,
    db_manager,
    folder: Optional[str] = None,
    tag: Optional[str] = None,
    provider: Optional[str] = None,
    batch_size: int = 10,
    batch_delay: float = 4.0,
    progress_callback=None,
) -> VaultSummary:
    """Generate a summary of the vault or a subset.

    Args:
        vault_id: Vault ID
        db_manager: DatabaseManager instance
        folder: Optional folder path to scope
        tag: Optional tag to scope
        provider: Preferred AI provider
        batch_size: Notes per batch for AI processing
        batch_delay: Seconds between batches (rate limiting)
        progress_callback: Optional callable(current, total) for progress

    Returns:
        VaultSummary with themes, stats, and summary text
    """
    vault = db_manager.get_vault(vault_id)
    if not vault:
        raise ValueError(f"Vault not found: {vault_id}")

    # Get notes in scope
    all_notes = db_manager.list_notes(vault_id=vault_id)

    if folder:
        all_notes = [n for n in all_notes if n['path'].startswith(folder)]
    if tag:
        all_notes = [
            n for n in all_notes
            if n.get('tags') and tag in n['tags']
        ]

    if not all_notes:
        return VaultSummary(note_count=0, summary_text="No notes found in scope.")

    router = get_ai_client(provider=provider)

    # Batch process for theme extraction
    all_themes = []
    processed = 0

    for i in range(0, len(all_notes), batch_size):
        batch = all_notes[i:i + batch_size]

        for note in batch:
            content = _get_note_content(note, vault['path'])
            if not content or len(content.strip()) < 50:
                processed += 1
                continue

            try:
                result = router.analyze_note(content, note['title'])
                all_themes.extend(result.themes)
            except Exception:
                pass

            processed += 1
            if progress_callback:
                progress_callback(processed, len(all_notes))

        # Rate limiting between batches
        if i + batch_size < len(all_notes):
            time.sleep(batch_delay)

    # Aggregate themes (count occurrences)
    theme_counts: Dict[str, int] = {}
    for theme in all_themes:
        theme_lower = theme.lower().strip()
        theme_counts[theme_lower] = theme_counts.get(theme_lower, 0) + 1

    top_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # Get graph stats
    orphans = db_manager.get_orphaned_notes(vault_id=vault_id)
    hubs = db_manager.get_hub_notes(vault_id=vault_id, limit=5)

    return VaultSummary(
        note_count=len(all_notes),
        themes=[t[0] for t in top_themes],
        top_hubs=[{'title': h['title'], 'connections': h.get('total_degree', 0)} for h in hubs],
        orphan_count=len(orphans),
        graph_stats={
            'total_notes': len(all_notes),
            'themes_found': len(theme_counts),
            'hub_count': len(hubs),
        },
        summary_text=f"Vault contains {len(all_notes)} notes across {len(theme_counts)} themes. "
                     f"Top themes: {', '.join(t[0] for t in top_themes[:5])}. "
                     f"{len(orphans)} orphaned notes, {len(hubs)} hub notes.",
    )
