"""AI-powered vault refactoring — reorganization suggestions.

Extracted from features.py (v3.2.0) to keep module sizes manageable.
Three-phase analysis:
  Phase 1 (graph-only): orphan placement, stale folder archival, small folder merging
  Phase 2 (AI-enhanced): tag-folder mismatch, semantic clustering for orphan placement
  Phase 3: prioritization with confidence scores
"""

import os
import sqlite3
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path

from .router import get_ai_client
from .features import _cosine_similarity, _get_note_content, _get_cached_embedding


@dataclass
class RefactorSuggestion:
    """A single vault reorganization suggestion."""
    category: str          # "move", "merge-folder", "create-folder", "connect", "archive"
    priority: str          # "high", "medium", "low"
    description: str
    affected_notes: List[str] = field(default_factory=list)
    affected_paths: List[str] = field(default_factory=list)
    suggested_path: str = ""
    reason: str = ""
    confidence: float = 0.0   # 0.0-1.0

    def to_dict(self) -> dict:
        return {
            'category': self.category,
            'priority': self.priority,
            'description': self.description,
            'affected_notes': self.affected_notes,
            'affected_paths': self.affected_paths,
            'suggested_path': self.suggested_path,
            'reason': self.reason,
            'confidence': self.confidence,
        }


@dataclass
class RefactorPlan:
    """Complete vault refactor analysis result."""
    vault_name: str
    note_count: int
    folder_count: int
    suggestions: List[RefactorSuggestion] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            'vault_name': self.vault_name,
            'note_count': self.note_count,
            'folder_count': self.folder_count,
            'suggestions': [s.to_dict() for s in self.suggestions],
            'summary': self.summary,
        }

    def to_json(self) -> str:
        import json as json_mod
        return json_mod.dumps(self.to_dict(), indent=2, default=str)

    @property
    def high_priority(self) -> List[RefactorSuggestion]:
        return [s for s in self.suggestions if s.priority == 'high']

    @property
    def medium_priority(self) -> List[RefactorSuggestion]:
        return [s for s in self.suggestions if s.priority == 'medium']

    @property
    def low_priority(self) -> List[RefactorSuggestion]:
        return [s for s in self.suggestions if s.priority == 'low']


def refactor_vault(
    vault_id: str,
    db_manager,
    provider: Optional[str] = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> RefactorPlan:
    """Analyze vault structure and generate reorganization suggestions.

    Phase 1 (graph-only): orphan placement, stale folder archival, small folder merging.
    Phase 2 (AI-enhanced): semantic clustering, tag-folder mismatch, orphan placement.
    Phase 3: prioritization with confidence scores.

    Args:
        vault_id: Vault name or ID
        db_manager: DatabaseManager instance
        provider: Preferred AI provider (optional)
        dry_run: If True, return scope info only (no AI calls)
        verbose: Print progress to stderr

    Returns:
        RefactorPlan with prioritized suggestions

    Raises:
        ValueError: If vault not found
    """
    import sys
    from collections import defaultdict
    from datetime import datetime, timezone

    # Resolve vault
    try:
        vault = db_manager.get_vault_by_name_or_id(vault_id)
    except ValueError:
        raise
    if not vault:
        raise ValueError(f"Vault not found: {vault_id}")

    actual_vault_id = vault['id']
    vault_name = vault['name']
    vault_path = vault['path']

    if verbose:
        print(f"  [verbose] Resolving vault: {vault_name} ({actual_vault_id[:8]})", file=sys.stderr)

    # Get all notes and group by folder
    all_notes = db_manager.list_notes(vault_id=actual_vault_id)
    folders: Dict[str, List[Dict]] = defaultdict(list)
    for note in all_notes:
        folder = str(Path(note['path']).parent)
        folders[folder].append(note)

    folder_count = len(folders)
    note_count = len(all_notes)

    if verbose:
        print(f"  [verbose] Found {note_count} notes across {folder_count} folders", file=sys.stderr)

    suggestions: List[RefactorSuggestion] = []

    # ── Phase 1: Graph-only analysis (runs even in dry-run) ──────

    # 1a. Root-level orphans → "move" suggestion
    orphans = db_manager.get_orphaned_notes(vault_id=actual_vault_id)
    root_orphans = [o for o in orphans if '/' not in o.get('path', '')]
    if root_orphans:
        for orphan in root_orphans:
            suggestions.append(RefactorSuggestion(
                category='move',
                priority='high',
                description=f"Move \"{orphan['title']}\" to inbox/",
                affected_notes=[orphan['title']],
                affected_paths=[orphan.get('path', '')],
                suggested_path='inbox/',
                reason='Root-level note with no links, likely unsorted',
                confidence=0.85,
            ))

    # 1b. Stale folders → "archive" suggestion
    freshness = db_manager.get_note_freshness(actual_vault_id, days_threshold=90)
    # Check each folder for staleness
    for folder_path, folder_notes in folders.items():
        if folder_path == '.':
            continue  # Skip root
        if len(folder_notes) == 0:
            continue

        # Check if all notes in folder are stale (modified_at > 90 days ago)
        all_stale = True
        for note in folder_notes:
            modified = note.get('modified_at', '')
            if modified:
                try:
                    # Parse ISO format timestamp
                    if isinstance(modified, str):
                        mod_dt = datetime.fromisoformat(modified.replace('Z', '+00:00'))
                    else:
                        mod_dt = modified
                    now = datetime.now(timezone.utc)
                    if hasattr(mod_dt, 'tzinfo') and mod_dt.tzinfo is None:
                        mod_dt = mod_dt.replace(tzinfo=timezone.utc)
                    days_old = (now - mod_dt).days
                    if days_old <= 90:
                        all_stale = False
                        break
                except (ValueError, TypeError):
                    pass  # Can't parse date — treat as stale

        # Check connectivity: are these notes orphans or low-connectivity?
        folder_orphan_ids = {o['id'] for o in orphans}
        low_connectivity = sum(1 for n in folder_notes if n['id'] in folder_orphan_ids)
        high_orphan_ratio = low_connectivity >= len(folder_notes) * 0.5

        if all_stale and high_orphan_ratio and len(folder_notes) <= 10:
            suggestions.append(RefactorSuggestion(
                category='archive',
                priority='high',
                description=f"Archive folder \"{folder_path}/\" → archive/",
                affected_notes=[n['title'] for n in folder_notes],
                affected_paths=[n['path'] for n in folder_notes],
                suggested_path='archive/',
                reason=f"{len(folder_notes)} notes, all >90 days stale, low connectivity",
                confidence=0.8,
            ))

    # 1c. Small scattered folders → "merge-folder" suggestion
    # Only flag shallow folders (depth ≤ 2) to avoid noise in deep academic hierarchies
    small_folders = [(fp, fn) for fp, fn in folders.items()
                     if fp != '.' and len(fn) < 3 and len(fn) > 0
                     and fp.count('/') <= 2]
    if len(small_folders) >= 2:
        for folder_path, folder_notes in small_folders:
            suggestions.append(RefactorSuggestion(
                category='merge-folder',
                priority='medium',
                description=f"Consider merging small folder \"{folder_path}/\" ({len(folder_notes)} notes)",
                affected_notes=[n['title'] for n in folder_notes],
                affected_paths=[n['path'] for n in folder_notes],
                reason=f"Folder has only {len(folder_notes)} {'note' if len(folder_notes) == 1 else 'notes'}, consider consolidating",
                confidence=0.5,
            ))

    # Dry run: return Phase 1 results only (no AI calls)
    if dry_run:
        high = sum(1 for s in suggestions if s.priority == 'high')
        medium = sum(1 for s in suggestions if s.priority == 'medium')
        low = sum(1 for s in suggestions if s.priority == 'low')
        summary = f"Dry run: {len(suggestions)} suggestions ({high} high, {medium} medium, {low} low) — graph-only, no AI calls"
        return RefactorPlan(
            vault_name=vault_name,
            note_count=note_count,
            folder_count=folder_count,
            suggestions=suggestions,
            summary=summary,
        )

    # ── Phase 2: AI-enhanced analysis ─────────────────────────────

    if verbose:
        print(f"  [verbose] Starting AI-enhanced analysis", file=sys.stderr)

    # 2a. Tag-folder mismatch detection
    try:
        tag_stats = db_manager.get_vault_tag_stats(actual_vault_id)
    except Exception:
        tag_stats = []

    if tag_stats:
        # Tags with 5+ notes may warrant their own folder
        for tag_info in tag_stats:
            tag_name = tag_info['tag']
            count = tag_info['note_count']
            if count >= 5:
                suggestions.append(RefactorSuggestion(
                    category='create-folder',
                    priority='medium',
                    description=f"Create \"{tag_name}/\" folder for {count} notes with #{tag_name} tag",
                    affected_notes=[],
                    reason=f"{count} notes share #{tag_name} tag but may span multiple folders",
                    confidence=0.6,
                ))

    # 2b. AI clustering for orphan placement (requires embeddings)
    non_root_orphans = [o for o in orphans if '/' in o.get('path', '')]
    if non_root_orphans and len(all_notes) > 5:
        try:
            router = get_ai_client(provider=provider)

            if verbose:
                print(f"  [verbose] Computing embeddings for orphan placement", file=sys.stderr)

            # Get embeddings for orphans and a random sample of connected notes
            import random
            connected_notes = [n for n in all_notes if n['id'] not in {o['id'] for o in orphans}]
            sample_size = min(20, len(connected_notes))
            sample_notes = random.sample(connected_notes, sample_size) if connected_notes else []

            orphan_embeddings = []
            for orphan in non_root_orphans[:10]:  # Limit to 10 orphans
                content = _get_note_content(orphan, vault_path)
                if content and len(content.strip()) > 50:
                    note_path = Path(vault_path) / orphan['path']
                    mtime = os.path.getmtime(note_path) if note_path.exists() else 0
                    emb = _get_cached_embedding(
                        orphan['id'], content, mtime,
                        db_manager, router,
                    )
                    orphan_embeddings.append((orphan, emb))

            sample_embeddings = []
            for note in sample_notes:
                content = _get_note_content(note, vault_path)
                if content and len(content.strip()) > 50:
                    note_path = Path(vault_path) / note['path']
                    mtime = os.path.getmtime(note_path) if note_path.exists() else 0
                    emb = _get_cached_embedding(
                        note['id'], content, mtime,
                        db_manager, router,
                    )
                    sample_embeddings.append((note, emb))

            # Find best folder match for each orphan
            for orphan, orphan_emb in orphan_embeddings:
                best_sim = 0.0
                best_folder = ""
                best_note_title = ""
                for note, note_emb in sample_embeddings:
                    sim = _cosine_similarity(orphan_emb, note_emb)
                    if sim > best_sim:
                        best_sim = sim
                        best_folder = str(Path(note['path']).parent)
                        best_note_title = note['title']

                if best_sim > 0.5 and best_folder and best_folder != '.':
                    suggestions.append(RefactorSuggestion(
                        category='connect',
                        priority='high' if best_sim > 0.8 else 'medium',
                        description=f"Move orphan \"{orphan['title']}\" → {best_folder}/",
                        affected_notes=[orphan['title']],
                        affected_paths=[orphan.get('path', '')],
                        suggested_path=best_folder + '/',
                        reason=f"Similar to \"{best_note_title}\" ({best_sim:.0%} match)",
                        confidence=best_sim,
                    ))
        except Exception:
            # AI not available — skip semantic analysis
            if verbose:
                print(f"  [verbose] AI provider unavailable, skipping semantic analysis", file=sys.stderr)

    # ── Phase 3: Sort by priority ─────────────────────────────────
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    suggestions.sort(key=lambda s: (priority_order.get(s.priority, 3), -s.confidence))

    # Build summary
    high = sum(1 for s in suggestions if s.priority == 'high')
    medium = sum(1 for s in suggestions if s.priority == 'medium')
    low = sum(1 for s in suggestions if s.priority == 'low')
    summary = f"{len(suggestions)} suggestions ({high} high, {medium} medium, {low} low)"

    return RefactorPlan(
        vault_name=vault_name,
        note_count=note_count,
        folder_count=folder_count,
        suggestions=suggestions,
        summary=summary,
    )
