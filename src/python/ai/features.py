"""
AI-powered features for note analysis and similarity detection.

Phase 5B features:
- find_similar_notes: Find notes similar to a given note
- analyze_note: Deep analysis of a single note
- find_duplicates: Detect potential duplicate notes
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import numpy as np

from .router import get_ai_client, AIRouter
from .providers.base import AnalysisResult, ComparisonResult, SimilarNote


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
