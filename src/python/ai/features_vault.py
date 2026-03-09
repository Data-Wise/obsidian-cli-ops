"""Vault-level AI features: merge-suggest, tag-suggest, quality scoring.

New in v3.2.0. These features operate across entire vaults and are
optimized for batch processing (500-2000 notes).

- merge_suggest_vault: Find note pairs with high cosine similarity
- tag_suggest_vault: Suggest tags for untagged notes
- note_quality_vault: Score every note across 4 quality dimensions
"""

import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from .models import MergeCandidate, NoteQuality, TagSuggestion
from .router import AIRouter, get_ai_client
from .features import _cosine_similarity, _get_note_content, _get_cached_embedding


# ── merge-suggest ──────────────────────────────────────────────────


def _batch_load_embeddings(
    vault_id: str, db_manager
) -> Dict[str, np.ndarray]:
    """Load all cached embeddings for a vault in one query.

    Returns dict mapping note_id → numpy vector.
    """
    result = {}
    try:
        with db_manager.get_connection() as conn:
            # Check table exists
            table_check = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='note_embeddings'"
            ).fetchone()
            if not table_check:
                return result
            cursor = conn.execute("""
                SELECT e.note_id, e.vector
                FROM note_embeddings e
                JOIN notes n ON e.note_id = n.id
                WHERE n.vault_id = ?
            """, (vault_id,))
            for row in cursor:
                vec = np.frombuffer(bytes(row['vector']), dtype=np.float32)
                if np.linalg.norm(vec) > 0:
                    result[row['note_id']] = vec / np.linalg.norm(vec)
    except (sqlite3.OperationalError, KeyError):
        pass
    return result


def _get_shared_links(
    note_a_id: str, note_b_id: str, db_manager
) -> List[str]:
    """Find link targets shared by two notes."""
    try:
        links_a = {l['target_note_id'] for l in db_manager.get_outgoing_links(note_a_id)}
        links_b = {l['target_note_id'] for l in db_manager.get_outgoing_links(note_b_id)}
        shared_ids = links_a & links_b
        # Resolve IDs to titles
        titles = []
        for nid in shared_ids:
            note = db_manager.get_note(nid)
            if note:
                titles.append(note['title'])
        return titles
    except (sqlite3.OperationalError, KeyError):
        return []


def _get_shared_tags(
    note_a_id: str, note_b_id: str, db_manager
) -> List[str]:
    """Find tags shared by two notes."""
    try:
        tags_a = set(db_manager.get_note_tags(note_a_id))
        tags_b = set(db_manager.get_note_tags(note_b_id))
        return sorted(tags_a & tags_b)
    except (sqlite3.OperationalError, KeyError):
        return []


def merge_suggest_vault(
    vault_id: str,
    db_manager,
    threshold: float = 0.8,
    provider: Optional[str] = None,
    verbose: bool = False,
) -> List[MergeCandidate]:
    """Find note pairs with high embedding similarity that may be merge candidates.

    Args:
        vault_id: Vault name or ID
        db_manager: DatabaseManager instance
        threshold: Minimum cosine similarity (default 0.8)
        provider: AI provider for computing missing embeddings (optional)
        verbose: Print progress to stderr

    Returns:
        List of MergeCandidate sorted by similarity (highest first)

    Raises:
        ValueError: If vault not found
    """
    # Resolve vault
    try:
        vault = db_manager.get_vault_by_name_or_id(vault_id)
    except ValueError:
        raise
    if not vault:
        raise ValueError(f"Vault not found: {vault_id}")

    actual_vault_id = vault['id']
    vault_path = vault['path']

    if verbose:
        print(f"  [verbose] Loading embeddings for vault: {vault['name']}", file=sys.stderr)

    # Batch-load all cached embeddings
    embeddings = _batch_load_embeddings(actual_vault_id, db_manager)

    if len(embeddings) < 2:
        if verbose:
            print(f"  [verbose] Only {len(embeddings)} embeddings cached — need at least 2", file=sys.stderr)
        return []

    if verbose:
        print(f"  [verbose] {len(embeddings)} embeddings loaded, computing pairwise similarity", file=sys.stderr)

    # Build note lookup for titles
    all_notes = db_manager.list_notes(vault_id=actual_vault_id)
    note_lookup = {n['id']: n for n in all_notes}

    # Vectorized pairwise cosine similarity
    note_ids = list(embeddings.keys())
    matrix = np.stack([embeddings[nid] for nid in note_ids])
    # matrix is already L2-normalized from _batch_load_embeddings
    sim_matrix = np.dot(matrix, matrix.T)

    # Extract pairs above threshold (upper triangle only)
    candidates = []
    n = len(note_ids)
    for i in range(n):
        for j in range(i + 1, n):
            sim = float(sim_matrix[i, j])
            if sim >= threshold:
                nid_a = note_ids[i]
                nid_b = note_ids[j]
                note_a = note_lookup.get(nid_a, {})
                note_b = note_lookup.get(nid_b, {})

                shared_links = _get_shared_links(nid_a, nid_b, db_manager)
                shared_tags = _get_shared_tags(nid_a, nid_b, db_manager)

                # Suggest keeping the note with more incoming links
                incoming_a = len(db_manager.get_incoming_links(nid_a))
                incoming_b = len(db_manager.get_incoming_links(nid_b))
                suggested_target = note_a.get('title', '') if incoming_a >= incoming_b else note_b.get('title', '')

                # Confidence based on similarity + shared context
                confidence = min(1.0, sim * 0.7 + (len(shared_links) + len(shared_tags)) * 0.05 + 0.1)

                candidates.append(MergeCandidate(
                    note_a_id=nid_a,
                    note_b_id=nid_b,
                    note_a_title=note_a.get('title', ''),
                    note_b_title=note_b.get('title', ''),
                    similarity=sim,
                    shared_links=shared_links,
                    shared_tags=shared_tags,
                    suggested_target=suggested_target,
                    confidence=confidence,
                ))

    # Sort by similarity descending
    candidates.sort(key=lambda c: -c.similarity)

    if verbose:
        print(f"  [verbose] Found {len(candidates)} merge candidates above {threshold:.0%} threshold", file=sys.stderr)

    return candidates


# ── tag-suggest ────────────────────────────────────────────────────


def _get_neighbor_tags(note_id: str, db_manager) -> List[str]:
    """Get tags from linked notes (neighbors in the graph)."""
    neighbor_tags = set()
    try:
        for link in db_manager.get_outgoing_links(note_id):
            tags = db_manager.get_note_tags(link['target_note_id'])
            neighbor_tags.update(tags)
        for link in db_manager.get_incoming_links(note_id):
            tags = db_manager.get_note_tags(link['source_note_id'])
            neighbor_tags.update(tags)
    except (sqlite3.OperationalError, KeyError):
        pass
    return sorted(neighbor_tags)


def _get_vault_tag_frequency(vault_id: str, db_manager) -> Dict[str, int]:
    """Get tag → usage count mapping for a vault."""
    try:
        stats = db_manager.get_vault_tag_stats(vault_id, limit=100)
        return {s['tag']: s['note_count'] for s in stats}
    except (sqlite3.OperationalError, KeyError):
        return {}


def tag_suggest_vault(
    vault_id: str,
    db_manager,
    provider: Optional[str] = None,
    min_confidence: float = 0.0,
    apply: bool = False,
    verbose: bool = False,
) -> List[TagSuggestion]:
    """Suggest tags for untagged notes using AI and vault context.

    Args:
        vault_id: Vault name or ID
        db_manager: DatabaseManager instance
        provider: AI provider for tag suggestions
        min_confidence: Only return suggestions above this confidence (0.0-1.0)
        apply: If True, auto-apply tags with >80% confidence to frontmatter
        verbose: Print progress to stderr

    Returns:
        List of TagSuggestion

    Raises:
        ValueError: If vault not found
    """
    # Resolve vault
    try:
        vault = db_manager.get_vault_by_name_or_id(vault_id)
    except ValueError:
        raise
    if not vault:
        raise ValueError(f"Vault not found: {vault_id}")

    actual_vault_id = vault['id']
    vault_path = vault['path']

    # Find untagged notes
    all_notes = db_manager.list_notes(vault_id=actual_vault_id)
    untagged = []
    for note in all_notes:
        tags = db_manager.get_note_tags(note['id'])
        if not tags:
            untagged.append(note)

    if verbose:
        print(f"  [verbose] Found {len(untagged)} untagged notes out of {len(all_notes)}", file=sys.stderr)

    if not untagged:
        return []

    # Get vault-wide tag frequency for context
    tag_freq = _get_vault_tag_frequency(actual_vault_id, db_manager)

    # Get AI provider
    try:
        router = get_ai_client(provider=provider)
    except Exception:
        if verbose:
            print("  [verbose] AI provider unavailable, cannot suggest tags", file=sys.stderr)
        return []

    suggestions = []
    for note in untagged:
        content = _get_note_content(note, vault_path)
        if not content or len(content.strip()) < 20:
            continue

        neighbor_tags = _get_neighbor_tags(note['id'], db_manager)

        # Build prompt for AI
        top_vault_tags = sorted(tag_freq.keys(), key=lambda t: -tag_freq[t])[:20]
        prompt = (
            f"Suggest tags for this Obsidian note. "
            f"Existing vault tags (most used): {', '.join(top_vault_tags[:10])}. "
            f"Tags from linked notes: {', '.join(neighbor_tags[:10]) if neighbor_tags else 'none'}. "
            f"Return JSON: {{\"tags\": [{{\"tag\": \"name\", \"confidence\": 0.0-1.0}}]}}\n\n"
            f"Note title: {note['title']}\n"
            f"Content (first 500 chars):\n{content[:500]}"
        )

        try:
            response = router.generate(prompt)
            # Parse AI response
            import json
            # Try to extract JSON from response
            text = response if isinstance(response, str) else str(response)
            # Find JSON in response
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
                ai_tags = data.get('tags', [])
            else:
                ai_tags = []

            # Build suggestion with vault usage counts
            suggested_tags = []
            for tag_entry in ai_tags:
                if isinstance(tag_entry, dict) and 'tag' in tag_entry:
                    tag_name = str(tag_entry['tag']).strip('#').strip()
                    conf = float(tag_entry.get('confidence', 0.5))
                    conf = max(0.0, min(1.0, conf))
                    if conf >= min_confidence:
                        suggested_tags.append({
                            'tag': tag_name,
                            'confidence': conf,
                            'vault_usage_count': tag_freq.get(tag_name, 0),
                        })

            if suggested_tags:
                suggestions.append(TagSuggestion(
                    note_id=note['id'],
                    note_title=note['title'],
                    suggested_tags=suggested_tags,
                    existing_tags=[],
                    neighbor_tags=neighbor_tags,
                ))
        except Exception:
            if verbose:
                print(f"  [verbose] Failed to get suggestions for: {note['title']}", file=sys.stderr)

    # Apply high-confidence tags if requested
    if apply:
        for suggestion in suggestions:
            for tag_entry in suggestion.suggested_tags:
                if tag_entry['confidence'] > 0.8:
                    _apply_tag_to_frontmatter(
                        suggestion.note_id, tag_entry['tag'],
                        vault_path, db_manager, verbose,
                    )

    if verbose:
        total_tags = sum(len(s.suggested_tags) for s in suggestions)
        print(f"  [verbose] Generated {total_tags} tag suggestions for {len(suggestions)} notes", file=sys.stderr)

    return suggestions


def tag_suggest_note(
    note_id: str,
    db_manager,
    provider: Optional[str] = None,
    verbose: bool = False,
) -> Optional[TagSuggestion]:
    """Suggest tags for a single note. Thin wrapper around tag_suggest_vault logic."""
    note = db_manager.get_note(note_id)
    if not note:
        raise ValueError(f"Note not found: {note_id}")

    vault = db_manager.get_vault(note['vault_id'])
    if not vault:
        raise ValueError(f"Vault not found for note: {note_id}")

    vault_path = vault['path']
    existing_tags = db_manager.get_note_tags(note_id)

    tag_freq = _get_vault_tag_frequency(note['vault_id'], db_manager)
    neighbor_tags = _get_neighbor_tags(note_id, db_manager)

    content = _get_note_content(note, vault_path)
    if not content or len(content.strip()) < 20:
        return None

    try:
        router = get_ai_client(provider=provider)
    except Exception:
        return None

    top_vault_tags = sorted(tag_freq.keys(), key=lambda t: -tag_freq[t])[:20]
    prompt = (
        f"Suggest tags for this Obsidian note. "
        f"Existing tags on note: {', '.join(existing_tags) if existing_tags else 'none'}. "
        f"Existing vault tags (most used): {', '.join(top_vault_tags[:10])}. "
        f"Tags from linked notes: {', '.join(neighbor_tags[:10]) if neighbor_tags else 'none'}. "
        f"Return JSON: {{\"tags\": [{{\"tag\": \"name\", \"confidence\": 0.0-1.0}}]}}\n\n"
        f"Note title: {note['title']}\n"
        f"Content (first 500 chars):\n{content[:500]}"
    )

    try:
        import json
        response = router.generate(prompt)
        text = response if isinstance(response, str) else str(response)
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
            ai_tags = data.get('tags', [])
        else:
            return None

        suggested_tags = []
        for tag_entry in ai_tags:
            if isinstance(tag_entry, dict) and 'tag' in tag_entry:
                tag_name = str(tag_entry['tag']).strip('#').strip()
                conf = max(0.0, min(1.0, float(tag_entry.get('confidence', 0.5))))
                suggested_tags.append({
                    'tag': tag_name,
                    'confidence': conf,
                    'vault_usage_count': tag_freq.get(tag_name, 0),
                })

        if suggested_tags:
            return TagSuggestion(
                note_id=note_id,
                note_title=note['title'],
                suggested_tags=suggested_tags,
                existing_tags=existing_tags,
                neighbor_tags=neighbor_tags,
            )
    except Exception:
        pass
    return None


def _apply_tag_to_frontmatter(
    note_id: str, tag: str, vault_path: str,
    db_manager, verbose: bool = False,
):
    """Apply a tag to a note's YAML frontmatter."""
    note = db_manager.get_note(note_id)
    if not note:
        return

    note_path = Path(vault_path) / note['path']
    if not note_path.exists():
        return

    try:
        content = note_path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return

    # Parse or create frontmatter
    if content.startswith('---\n'):
        end = content.find('\n---\n', 4)
        if end > 0:
            frontmatter = content[4:end]
            body = content[end + 5:]
            # Append tag to tags list
            if 'tags:' in frontmatter:
                frontmatter = frontmatter.rstrip() + f'\n  - {tag}'
            else:
                frontmatter = frontmatter.rstrip() + f'\ntags:\n  - {tag}'
            new_content = f'---\n{frontmatter}\n---\n{body}'
        else:
            return  # Malformed frontmatter
    else:
        # No frontmatter — create one
        new_content = f'---\ntags:\n  - {tag}\n---\n{content}'

    try:
        note_path.write_text(new_content, encoding='utf-8')
        # Also update DB
        db_manager.add_note_tag(note_id, tag)
        if verbose:
            print(f"  [verbose] Applied tag #{tag} to: {note['title']}", file=sys.stderr)
    except (OSError, sqlite3.OperationalError):
        pass


# ── quality scoring ────────────────────────────────────────────────


def note_quality_vault(
    vault_id: str,
    db_manager,
    verbose: bool = False,
) -> List[NoteQuality]:
    """Score every note in a vault across 4 quality dimensions (graph-only, no AI).

    Dimensions (weighted):
    - Completeness (30%): word count vs vault avg, has headings
    - Connectivity (30%): outgoing/incoming links, not orphan
    - Metadata (20%): has tags, has frontmatter
    - Freshness (20%): modified within 90 days

    Args:
        vault_id: Vault name or ID
        db_manager: DatabaseManager instance
        verbose: Print progress to stderr

    Returns:
        List of NoteQuality sorted by overall_score ascending (worst first)

    Raises:
        ValueError: If vault not found
    """
    # Resolve vault
    try:
        vault = db_manager.get_vault_by_name_or_id(vault_id)
    except ValueError:
        raise
    if not vault:
        raise ValueError(f"Vault not found: {vault_id}")

    actual_vault_id = vault['id']
    vault_path = vault['path']

    all_notes = db_manager.list_notes(vault_id=actual_vault_id)
    if not all_notes:
        return []

    if verbose:
        print(f"  [verbose] Scoring {len(all_notes)} notes in vault: {vault['name']}", file=sys.stderr)

    # Pre-compute orphan set for connectivity scoring
    orphan_ids = {o['id'] for o in db_manager.get_orphaned_notes(vault_id=actual_vault_id)}

    # Pre-compute vault average word count for completeness scoring
    word_counts = []
    for note in all_notes:
        content = _get_note_content(note, vault_path)
        if content:
            word_counts.append(len(content.split()))
        else:
            word_counts.append(0)
    avg_words = sum(word_counts) / len(word_counts) if word_counts else 100

    now = datetime.now(timezone.utc)
    results = []

    for idx, note in enumerate(all_notes):
        content = _get_note_content(note, vault_path)
        wc = word_counts[idx]

        # ── Completeness (30%) ──
        # Word count score: 0 if empty, 100 if >= vault average
        if avg_words > 0 and wc > 0:
            word_score = min(100.0, (wc / avg_words) * 100)
        else:
            word_score = 0.0
        # Has headings bonus
        has_headings = bool(content and ('\n#' in content or content.startswith('#')))
        heading_bonus = 20.0 if has_headings else 0.0
        completeness = min(100.0, word_score * 0.8 + heading_bonus)

        # ── Connectivity (30%) ──
        outgoing = len(db_manager.get_outgoing_links(note['id']))
        incoming = len(db_manager.get_incoming_links(note['id']))
        is_orphan = note['id'] in orphan_ids

        if is_orphan:
            connectivity = 0.0
        else:
            # Score based on link count (max out at 10 links total)
            link_score = min(100.0, (outgoing + incoming) / 10 * 100)
            connectivity = link_score

        # ── Metadata (20%) ──
        tags = db_manager.get_note_tags(note['id'])
        has_tags = len(tags) > 0
        has_frontmatter = bool(content and content.startswith('---\n'))
        metadata = 0.0
        if has_frontmatter:
            metadata += 50.0
        if has_tags:
            metadata += 50.0

        # ── Freshness (20%) ──
        modified = note.get('modified_at', '')
        freshness = 0.0
        if modified:
            try:
                if isinstance(modified, str):
                    mod_dt = datetime.fromisoformat(modified.replace('Z', '+00:00'))
                else:
                    mod_dt = modified
                if hasattr(mod_dt, 'tzinfo') and mod_dt.tzinfo is None:
                    mod_dt = mod_dt.replace(tzinfo=timezone.utc)
                days_old = (now - mod_dt).days
                if days_old <= 30:
                    freshness = 100.0
                elif days_old <= 90:
                    freshness = 70.0
                elif days_old <= 180:
                    freshness = 40.0
                elif days_old <= 365:
                    freshness = 20.0
                else:
                    freshness = 5.0
            except (ValueError, TypeError):
                freshness = 0.0

        # ── Overall score ──
        overall = (
            completeness * 0.30
            + connectivity * 0.30
            + metadata * 0.20
            + freshness * 0.20
        )

        dimensions = {
            'completeness': round(completeness, 1),
            'connectivity': round(connectivity, 1),
            'metadata': round(metadata, 1),
            'freshness': round(freshness, 1),
        }

        # Generate issues and suggestions
        issues = []
        suggestions_list = []

        if is_orphan:
            issues.append({'severity': 'high', 'description': 'Note has no links (orphan)'})
            suggestions_list.append('Add links to related notes')
        if wc < 50:
            issues.append({'severity': 'medium', 'description': f'Very short ({wc} words)'})
            suggestions_list.append('Expand note content')
        if not has_tags:
            issues.append({'severity': 'low', 'description': 'No tags assigned'})
            suggestions_list.append('Add relevant tags')
        if not has_frontmatter:
            issues.append({'severity': 'low', 'description': 'Missing YAML frontmatter'})
            suggestions_list.append('Add frontmatter with metadata')
        if freshness <= 20.0 and modified:
            issues.append({'severity': 'low', 'description': 'Note is stale (>6 months old)'})
            suggestions_list.append('Review and update content')

        results.append(NoteQuality(
            note_id=note['id'],
            note_title=note['title'],
            overall_score=round(overall, 1),
            dimensions=dimensions,
            issues=issues,
            suggestions=suggestions_list,
        ))

    # Sort worst first
    results.sort(key=lambda r: r.overall_score)

    if verbose:
        avg_score = sum(r.overall_score for r in results) / len(results) if results else 0
        print(f"  [verbose] Average quality score: {avg_score:.1f}/100", file=sys.stderr)

    return results


def note_quality_note(
    note_id: str,
    db_manager,
    verbose: bool = False,
) -> Optional[NoteQuality]:
    """Score a single note. Returns the NoteQuality or None if not found."""
    note = db_manager.get_note(note_id)
    if not note:
        raise ValueError(f"Note not found: {note_id}")

    vault = db_manager.get_vault(note['vault_id'])
    if not vault:
        raise ValueError(f"Vault not found for note: {note_id}")

    # Use the vault-level function and filter
    results = note_quality_vault(note['vault_id'], db_manager, verbose=verbose)
    for r in results:
        if r.note_id == note_id:
            return r
    return None
