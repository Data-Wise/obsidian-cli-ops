# ORCHESTRATE: `obs ai refactor <vault>`

## Status: Implementation Complete — Ready for Testing & PR

## What's Done

### Increment 1+2 (Combined): Full Implementation ✅

**Files changed (4):**

| File | Change |
|------|--------|
| `src/python/ai/features.py` | `RefactorSuggestion`, `RefactorPlan` dataclasses + `refactor_vault()` with 3-phase pipeline |
| `src/python/obs_cli.py` | `refactor` argparse subparser + dispatch + `_print_refactor_plan()` Rich output |
| `src/obs.zsh` | `refactor)` case + fixed missing `suggest-links)`, `gaps)`, `summarize)` cases + updated help |
| `src/python/tests/test_ai_refactor.py` | **NEW** — 16 tests |

**Tests:** 202 passing (was 186, +16 new)

## Architecture

### 3-Phase Pipeline in `refactor_vault()`

```
Phase 1 (graph-only, no AI)        Phase 2 (AI-enhanced)           Phase 3
─────────────────────────────    ─────────────────────────────    ──────────
• Root orphans → "move"          • Tag-folder mismatch →         • Sort by
• Stale folders → "archive"        "create-folder"                 priority
• Small folders → "merge"        • Semantic orphan placement →   • Confidence
                                   "connect" (via embeddings)      scoring
```

- `--dry-run` returns after Phase 1 scope info (no AI calls)
- Phase 2 gracefully degrades if no AI provider available

### Dataclasses

- `RefactorSuggestion`: category, priority, description, affected_notes/paths, confidence
- `RefactorPlan`: vault_name, note/folder counts, suggestions list, summary
  - Properties: `high_priority`, `medium_priority`, `low_priority`
  - Methods: `to_dict()`, `to_json()`

## Remaining Work (In This Worktree Session)

### 1. Manual Testing
```bash
# Test with real vault
obs ai refactor <vault>
obs ai refactor <vault> --dry-run
obs ai refactor <vault> --json | python3 -m json.tool
obs ai refactor <vault> --verbose

# Verify ZSH wiring fixes
obs ai suggest-links <note_id>
obs ai gaps <vault>
obs ai summarize <vault>
```

### 2. Pre-PR Checklist
- [ ] Run full test suite: `cd src/python && python3 -m pytest tests/ -q`
- [ ] Verify no lint issues
- [ ] Update test count in docs if needed (186 → 202)
- [ ] Check `.STATUS` file

### 3. Create PR
```bash
gh pr create --base dev --title "feat: add obs ai refactor command"
```

## Key Decisions

- **No Pydantic**: Dataclasses with manual `to_dict()`/`to_json()` — consistent with existing `AnalysisResult`, `SimilarNote` pattern
- **Phase 2 try/except**: AI clustering wrapped in broad `except Exception` — graceful degradation when no provider configured (consistent with project's exception narrowing strategy)
- **Tag-folder heuristic**: Tags with 5+ notes suggest folder creation — simple threshold, avoids over-suggesting
- **Stale threshold**: 90 days + 50%+ orphan ratio — matches `get_note_freshness()` default
