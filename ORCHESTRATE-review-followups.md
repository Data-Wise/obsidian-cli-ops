# ORCHESTRATE: PR #4 Review Follow-ups

## Overview

Apply the three "Could" enhancements identified during PR #4 code review: verbose plumbing for new commands, narrower exception handling, and test coverage.

**Branch**: `feature/review-followups`
**Base**: `dev`
**Scope**: `src/python/` (features, bridge, CLI, tests)
**Estimated**: ~45 min total

---

## Increment 1: Wire `--verbose` to New Commands + ObsidianBridge

**Goal**: The 3 new AI commands (`suggest-links`, `gaps`, `summarize`) don't pass `--verbose` through. ObsidianBridge was designed for verbose-conditional logging but never receives the flag.

### Files to modify

#### `src/python/ai/obsidian_bridge.py`
- Add `verbose: bool = False` parameter to `__init__`
- When `verbose=True` and Obsidian CLI is unavailable, print a notice (via stderr or logging)
- When `verbose=True`, log each CLI call being made

```python
class ObsidianBridge:
    def __init__(self, verbose: bool = False):
        self._available: Optional[bool] = None
        self._verbose = verbose

    def is_available(self) -> bool:
        # ... existing logic ...
        if self._available is False and self._verbose:
            import sys
            print("  [verbose] Obsidian CLI not available, using file scanning fallback", file=sys.stderr)
        return self._available
```

#### `src/python/ai/features.py`
- Add `verbose: bool = False` parameter to `suggest_links()`, `find_gaps()`, `summarize_vault()`
- Pass `verbose` to `ObsidianBridge(verbose=verbose)`
- When `verbose=True`, log cache hits/misses in `_get_cached_embedding()`

```python
def suggest_links(note_id, db_manager, limit=5, provider=None, verbose=False):
    # ... existing logic ...
    # When computing embeddings, log cache status
    if verbose:
        print(f"  [verbose] Computing embedding for {note_id}", file=sys.stderr)

def find_gaps(vault_id, db_manager, provider=None, verbose=False):
    # ... existing logic ...
    bridge = ObsidianBridge(verbose=verbose)

def summarize_vault(vault_id, db_manager, folder=None, tag=None, provider=None,
                    batch_size=10, batch_delay=4.0, progress_callback=None, verbose=False):
    # ... existing logic ...
```

#### `src/python/obs_cli.py`
- Pass `verbose=args.verbose` to the 3 new command calls

```python
elif args.ai_command == 'suggest-links':
    suggestions = suggest_links(
        args.note_id, cli.db, limit=args.limit,
        provider=args.provider, verbose=args.verbose,
    )

elif args.ai_command == 'gaps':
    gaps = find_gaps(
        args.vault_id, cli.db,
        provider=args.provider, verbose=args.verbose,
    )

elif args.ai_command == 'summarize':
    summary = summarize_vault(
        args.vault_id, cli.db,
        folder=args.folder, tag=args.tag,
        provider=args.provider, verbose=args.verbose,
        progress_callback=progress,
    )
```

### Tests
- Test ObsidianBridge with `verbose=True` captures expected stderr output
- Test that features pass verbose through to bridge

---

## Increment 2: Narrow Remaining Broad Exceptions

**Goal**: Two `except Exception: pass` blocks remain in `features.py` that should be narrowed.

### Files to modify

#### `src/python/ai/features.py`

**Location 1** — `suggest_links()` line ~505:
```python
# Current:
except Exception:
    pass

# Fix: This catches SQL errors when the links table doesn't exist
except (sqlite3.OperationalError, KeyError):
    pass
```

**Location 2** — `find_gaps()` line ~598:
```python
# Current:
except Exception:
    pass

# Fix: This catches SQL errors when graph_metrics table doesn't exist or has no data
except sqlite3.OperationalError:
    pass
```

Note: `sqlite3` is already imported in features.py (added during PR #4 fix commit).

### Tests
- Verify existing `test_ai_features.py` tests still pass
- No new tests needed — these are narrower catches of the same cases

---

## Increment 3: Verify + Commit

1. Run full test suite: `python3 -m pytest tests/ -q`
2. Confirm 120+ tests passing
3. Commit with conventional message: `fix: wire --verbose to new commands, narrow exception handling`
4. Push and create PR to dev

---

## Test Strategy

| Test | What |
|------|------|
| Existing 120 | Must continue passing |
| ObsidianBridge verbose | Test stderr output when verbose=True and CLI unavailable |
| Features verbose passthrough | Test that verbose param reaches ObsidianBridge |
| **Total new** | ~3-4 tests |

---

## PR Target

`feature/review-followups` → `dev`
