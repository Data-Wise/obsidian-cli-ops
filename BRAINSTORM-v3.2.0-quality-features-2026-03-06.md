# BRAINSTORM: v3.2.0 Quality Features

> **Mode:** feature | **Depth:** max (2 agents) | **Duration:** ~12 min
> **Date:** 2026-03-06

---

## Context

v3.1.0 is stable (236 tests, 15 commands, 5 AI providers). Phase 8 added `obs ai refactor`. Now planning v3.2.0 — the "Quality Features" release — completing the remaining Phase 8 items from IDEAS.md.

**User Pain Point:** Notes pile up untagged and unlinked. Large vaults (500-2000 notes) accumulate organizational debt silently.

**Top Priority Feature:** `merge-suggest` — detect near-duplicate notes for consolidation.

**Interaction Model:** Interactive approve/reject dashboard (Rich), not batch auto-apply.

---

## Quick Wins (< 2 hours each)

1. **`obs ai quality <note_id>`** — Single-note quality score (0-100) with issue breakdown (orphan, no tags, short, no headings). Reuses existing embedding + graph data. Minimal new code.

2. **`obs ai tag-suggest <note_id>`** — Suggest tags for one note based on content + neighbor tags. Auto-apply with `--apply` flag when confidence >80%. Modifies YAML frontmatter.

3. **Split `features.py`** — Extract `refactor_vault()` (265 lines) into `features_refactor.py`. Reduces main file from 1068 → ~800 lines. Zero behavior change.

---

## Medium Effort (4-8 hours each)

4. **`obs ai merge-suggest <vault>`** — Scan vault for near-duplicate notes using pairwise cosine similarity. Group candidates by similarity threshold (default 0.8). Show overlapping sections, shared links/tags, and recommended merge target.

5. **`obs ai tag-suggest <vault>`** — Vault-wide tag suggestion scan. Batch process all untagged notes. Group by confidence tier (>80% auto-apply, 60-80% review, <60% skip). Uses neighbor tag propagation + AI content analysis.

6. **`obs ai quality <vault>`** — Vault-wide quality scan. Score every note, surface worst offenders. Dimensions: completeness (word count vs avg), connectivity (links), metadata (tags, headings), freshness (last modified).

---

## Long-Term (Future sessions — v3.3.0+)

7. **`obs ai review <vault>`** — Interactive Rich dashboard for batch review of all AI suggestions (merge, tag, quality). One-card-at-a-time UX. SQLite persistence for exit/resume. Apply approved changes on confirmation.

8. **`obs ai apply <vault>`** — Execute previously approved suggestions from a saved review session. Separate review (thinking) from execution (doing).

9. **Cross-vault analysis** — Find duplicate content across multiple vaults. Suggest consolidation or linking.

---

## Architecture (from Code Architect Agent)

### Module Split Plan

```
ai/features.py (1068 lines)
  ├── ai/features.py (~740 lines)          ← base functions (similarity, gaps, summarize)
  ├── ai/features_refactor.py (~265 lines) ← extract existing refactor_vault()
  ├── ai/features_vault.py (~400 lines)    ← NEW: merge_suggest, tag_suggest, note_quality
  └── ai/features_review.py (~300 lines)   ← NEW: batch_review + Rich dashboard
```

### New Data Models (in `ai/models.py`)

```python
@dataclass
class MergeCandidate:
    note_a_id: str
    note_b_id: str
    note_a_title: str
    note_b_title: str
    similarity: float           # 0.0-1.0
    shared_links: List[str]
    shared_tags: List[str]
    overlapping_sections: List[str]
    suggested_target: str       # which note to keep
    confidence: float

@dataclass
class TagSuggestion:
    note_id: str
    note_title: str
    suggested_tags: List[Dict[str, Any]]  # [{tag, confidence, vault_usage_count}]
    existing_tags: List[str]
    neighbor_tags: List[str]    # tags from linked notes

@dataclass
class NoteQuality:
    note_id: str
    note_title: str
    overall_score: float        # 0-100
    dimensions: Dict[str, float]  # completeness, connectivity, metadata, freshness
    issues: List[Dict[str, str]]  # [{severity, description}]
    suggestions: List[str]
```

### Performance Strategy (500-2000 notes)

| Technique | Where | Impact |
|-----------|-------|--------|
| Batch cache loading | `SELECT * FROM note_embeddings WHERE vault_id = ?` | Eliminates N+1 queries |
| Vectorized pairwise similarity | `np.dot(matrix, matrix.T)` | O(n^2) but fast with numpy |
| Batch API calls | Groups of 100 notes per prompt | Reduces API round-trips |
| Lazy detail loading | Diff computation on `d` keypress only | Keeps card rendering instant |

### Implementation Sequence (7 phases)

| Phase | Deliverable | Depends On |
|-------|-------------|------------|
| 1 | Data models in `ai/models.py` | — |
| 2 | Extract `features_refactor.py` | Phase 1 |
| 3 | `features_vault.py` (merge, tag, quality) | Phase 1 |
| 4 | CLI wiring in `obs_cli.py` + ZSH | Phase 3 |
| 5 | `features_review.py` (batch review) | Phase 3 |
| 6 | Interactive Rich dashboard | Phase 5 |
| 7 | ZSH integration + docs + tests | Phase 6 |

---

## UX Design (from UX Designer Agent)

### One-Card-at-a-Time Dashboard

**Why:** ADHD users freeze when shown a list of 50 items. One card at a time forces a decision and provides clear progress.

**Three card types:**
- **MERGE** — side-by-side note comparison, similarity bar, overlapping sections
- **TAGS** — note preview, suggested tags with confidence bars, neighbor context
- **QUALITY** — quality score bar, issue list, suggested improvements

**Keybinds:** `[y]` approve `[n]` reject `[s]` skip `[d]` details `[q]` quit

**Session persistence:** SQLite tables (`ai_review_sessions`, `ai_suggestions`) for exit/resume.

**Apply later:** Approved changes saved but NOT applied until explicit confirmation or `obs ai apply`.

**Full UX spec:** `docs/specs/UX-SPEC-ai-review-dashboard.md`

---

## Recommended Path

Start with **Phase 1-4** (data models + module split + vault features + CLI wiring) as v3.2.0. This delivers the three new AI commands (`merge-suggest`, `tag-suggest`, `quality`) without the interactive dashboard complexity.

The interactive dashboard (Phases 5-7) becomes v3.3.0 — it's a larger UX effort that benefits from having the underlying features stable first.

**Estimated scope:**
- v3.2.0: ~600 new lines, ~12 new tests, 3 new commands
- v3.3.0: ~500 new lines, ~15 new tests, 2 new commands (`review`, `apply`)

---

## Files

- `BRAINSTORM-v3.2.0-quality-features-2026-03-06.md` — this file
- `docs/specs/UX-SPEC-ai-review-dashboard.md` — interactive dashboard UX spec
- `docs/specs/SPEC-v3.2.0-quality-features-2026-03-06.md` — implementation spec

---

## Completed in ~12 min (within max budget of 30 min)
