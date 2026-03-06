# v3.2.0 Quality Features — Orchestration Plan

> **Branch:** `feature/v3.2.0-quality`
> **Base:** `dev`
> **Worktree:** `~/.git-worktrees/obsidian-cli-ops/feature-v3.2.0-quality`
> **Spec:** `docs/specs/SPEC-v3.2.0-quality-features-2026-03-06.md`
> **UX Spec:** `docs/specs/UX-SPEC-ai-review-dashboard.md` (v3.3.0 scope)

## Objective

Add three new AI commands (`merge-suggest`, `tag-suggest`, `quality`) and refactor the growing `features.py` into focused modules. Targets large vaults (500-2000 notes) with batch-optimized processing.

**Scope:** v3.2.0 delivers Phases 1-4 (data models, module split, vault features, CLI wiring). The interactive dashboard (Phases 5-7) is deferred to v3.3.0.

## Phase Overview

| Phase | Task | Priority | Status |
| ----- | ---- | -------- | ------ |
| 1 | Data models (`MergeCandidate`, `TagSuggestion`, `NoteQuality`) in `ai/models.py` | High | |
| 2 | Extract `refactor_vault()` into `ai/features_refactor.py` (~265 lines) | High | |
| 3 | New `ai/features_vault.py` — `merge_suggest_vault()`, `tag_suggest_vault()`, `note_quality_vault()` + single-note variants | High | |
| 4 | CLI wiring — argparse subcommands in `obs_cli.py` + ZSH cases in `obs.zsh` | High | |
| 5 | Tests — ~16 new tests across models, features, CLI | High | |
| 6 | Docs update — usage.md, cookbook.md, refcard.md, cli-reference.md, testing overview | Medium | |
| 7 | Version bump + release prep | Medium | |

## Implementation Details

### Phase 1: Data Models

Add to `src/python/ai/models.py`:

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
    neighbor_tags: List[str]

@dataclass
class NoteQuality:
    note_id: str
    note_title: str
    overall_score: float        # 0-100
    dimensions: Dict[str, float]  # completeness, connectivity, metadata, freshness
    issues: List[Dict[str, str]]  # [{severity, description}]
    suggestions: List[str]
```

Each needs `to_dict()` and `from_dict()` classmethod (same pattern as existing `AnalysisResult`).

### Phase 2: Module Extraction

Extract from `ai/features.py` (line ~803 onwards):
- `refactor_vault()` and its helper functions
- Move to `ai/features_refactor.py`
- Update imports in `obs_cli.py`
- Zero behavior change — pure refactor

### Phase 3: New Features (`ai/features_vault.py`)

**`merge_suggest_vault()`:**
1. Batch-load all embeddings (`SELECT * FROM note_embeddings WHERE vault_id = ?`)
2. Vectorized pairwise cosine similarity (`np.dot(normalized, normalized.T)`)
3. Extract pairs above threshold (default 0.8)
4. Enrich with shared links/tags from DB
5. AI: name overlapping sections (single batch prompt)
6. Return sorted `List[MergeCandidate]`

**`tag_suggest_vault()`:**
1. Find all untagged notes (`WHERE tags IS NULL OR tags = ''`)
2. For each: get content, neighbor tags (linked notes), vault tag frequency
3. AI: suggest tags with confidence scores
4. If `--apply` and confidence >80%: modify YAML frontmatter
5. Return `List[TagSuggestion]`

**`note_quality_vault()`:**
1. Score every note across 4 dimensions (graph-only, no AI):
   - Completeness (30%): word count vs vault avg, has headings
   - Connectivity (30%): outgoing/incoming links, not orphan
   - Metadata (20%): has tags, has frontmatter
   - Freshness (20%): modified within 90 days
2. Return sorted `List[NoteQuality]` (worst first)

### Phase 4: CLI Wiring

**`obs_cli.py`:** Add 5 argparse subcommands (merge-suggest, tag-suggest vault/note, quality vault/note). Add `_print_merge_candidates()`, `_print_tag_suggestions()`, `_print_quality_scores()` Rich formatters. Support `--json`, `--verbose`, `--threshold`, `--apply`, `--min-confidence`.

**`obs.zsh`:** Add cases in `obs_ai()`: `merge-suggest)`, `tag-suggest)`, `quality)`.

### Phase 5: Tests

| Test File | Tests | Covers |
|-----------|-------|--------|
| `test_ai_models.py` | +4 | `MergeCandidate`, `TagSuggestion`, `NoteQuality` serialization |
| `test_features_vault.py` (NEW) | +8 | merge-suggest, tag-suggest, quality (basic, empty, threshold, JSON) |
| `test_cli_quality.py` (NEW) | +4 | CLI output formatting, --json, --verbose |

Target: 236 + 16 = 252+ tests passing.

### Phase 6: Docs

Update these files:
- `docs_mkdocs/usage.md` — add 3 commands to AI Features table
- `docs_mkdocs/cookbook.md` — add recipes for merge/tag/quality
- `docs_mkdocs/refcard.md` — add to AI Commands table
- `docs_mkdocs/cli-reference.md` — full command docs
- `docs_mkdocs/developer/testing/overview.md` — update test counts
- `.STATUS` — update for v3.2.0

### Phase 7: Release

- Version bump across 11 files (use `grep -rn "3.1.0"` to find all)
- CHANGELOG.md update
- PR to dev, then release PR to main
- GitHub release + tag
- Homebrew formula update
- Docs deploy

## Acceptance Criteria

- [ ] `obs ai merge-suggest <vault>` identifies note pairs with >80% cosine similarity
- [ ] `obs ai tag-suggest <vault>` suggests tags for untagged notes with confidence scores
- [ ] `obs ai quality <vault>` scores every note 0-100 across 4 dimensions
- [ ] Single-note variants: `obs ai tag-suggest <note_id>`, `obs ai quality <note_id>`
- [ ] `--apply` flag on `tag-suggest` auto-applies tags with >80% confidence
- [ ] All commands support `--json` and `--verbose`
- [ ] Performance: <30s for 1000-note vault (embedding cache warm)
- [ ] 252+ tests passing (236 existing + 16 new)
- [ ] All docs updated

## How to Start

```bash
cd ~/.git-worktrees/obsidian-cli-ops/feature-v3.2.0-quality
claude
```

Start with Phase 1 (data models) — it's the foundation everything else depends on.
