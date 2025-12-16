# Graph Builder Test Fixes

## Issue
All 12 tests in `test_graph_builder.py` were failing with:
```
AttributeError: 'str' object has no attribute 'get'
```

## Root Causes

### 1. Incorrect `add_note()` calls
**Issue:** Tests were passing 5 arguments but the 5th was a string `'h1'` instead of a dict.

**Actual signature:**
```python
def add_note(self, vault_id: str, path: str, title: str,
             content: str, metadata: Optional[Dict] = None) -> str:
```

**Fix:** Removed the invalid 5th string argument, allowing metadata to default to None.

### 2. Incorrect `add_link()` calls
**Issue:** Tests were passing note IDs as the second argument instead of target paths.

**Actual signature:**
```python
def add_link(self, source_note_id: str, target_path: str,
             link_text: Optional[str] = None) -> int:
```

**Fix:** Changed from `db.add_link(note1, note2, ...)` to `db.add_link(note1, 'note2.md', ...)`.

### 3. Missing link resolution
**Issue:** Links need to be resolved before the graph can be built. The `build_graph()` method only includes edges where `link_type = 'internal'` AND `target_note_id IS NOT NULL`.

**Fix:** Added link resolution step to `populated_db` fixture:
```python
resolver = LinkResolver(db)
resolver.resolve_all_links(vault_id)
```

### 4. Incorrect LinkResolver API usage
**Issue:** Tests used wrong constructor signature and method names.

**Actual API:**
- Constructor: `LinkResolver(db)` (not `LinkResolver(db, vault_id)`)
- Methods: `build_note_cache(vault_id)` and `resolve_link(target, source)`
- Cache attribute: `_note_cache` (not `cache`)

**Fix:** Updated all LinkResolver test calls to match actual API.

### 5. Incorrect `calculate_metrics()` API
**Issue:** Tests called `calculate_metrics(graph)` expecting per-note metrics dict.

**Actual API:**
- Signature: `calculate_metrics(vault_id)` (not `calculate_metrics(graph)`)
- Returns: Overall stats dict `{'notes': N, 'edges': M, 'density': D}`
- Per-note metrics stored in database, retrieved via `db.get_graph_metrics(note_id)`

**Fix:** Updated all metric tests to:
1. Call `calculate_metrics(vault_id)`
2. Retrieve metrics from database using `db.get_graph_metrics(note_id)`

### 6. Incorrect `analyze_vault()` return value expectations
**Issue:** Tests expected keys `'total_nodes'` and `'total_edges'`.

**Actual return value:** Combined dict with:
- Link stats: `'total_links'`, `'resolved'`, `'broken'`
- Graph stats: `'notes'`, `'edges'`, `'density'`

**Fix:** Updated assertions to check correct keys.

### 7. Database schema initialization issue
**Issue:** `temp_db` fixture created an empty file, causing DatabaseManager to skip auto-initialization.

**Fix:** Changed `temp_db` fixture to delete the temp file immediately after getting the path, allowing DatabaseManager to auto-initialize.

## Files Modified

### `/Users/dt/projects/dev-tools/obsidian-cli-ops/src/python/tests/test_graph_builder.py`

**Changed lines:**
- Line 20-28: Fixed `temp_db` fixture to allow auto-initialization
- Line 31-35: Simplified `populated_db` fixture (removed manual schema init)
- Line 51-54: Fixed `add_note()` calls (removed invalid 5th argument)
- Line 57-59: Fixed `add_link()` calls (use paths instead of note IDs)
- Line 61-63: Added link resolution step
- Line 99-116: Fixed `test_calculate_metrics` (use vault_id, get from DB)
- Line 118-134: Fixed `test_pagerank_calculation` (use vault_id, get from DB)
- Line 136-155: Fixed `test_degree_calculation` (use vault_id, get from DB)
- Line 157-172: Fixed `test_analyze_vault` (check correct return keys)
- Line 167-180: Fixed `test_resolve_exact_path` (correct API, get note dict)
- Line 182-193: Fixed `test_resolve_by_title` (correct API, get note dict)
- Line 195-206: Fixed `test_resolve_nonexistent` (correct API, get note dict)
- Line 208-216: Fixed `test_cache_building` (correct API, cache attribute)
- Line 234-246: Fixed `test_centrality_on_hub_note` (use vault_id, get from DB)
- Line 248-258: Fixed `test_clustering_coefficient` (use vault_id, get from DB)
- Line 264-265: Fixed `test_graph_with_no_links` (removed invalid argument)
- Line 278: Fixed `test_self_referencing_link` (removed invalid argument, use path)

## Summary

All 12 test failures were caused by the tests being written for an older API that no longer exists. The fixes align the tests with the current `GraphBuilder`, `LinkResolver`, and `DatabaseManager` implementations.

**Key API changes the tests missed:**
1. `add_note()` takes 4 required args + optional metadata dict
2. `add_link()` takes target_path (str), not target_note_id
3. Links must be resolved before graph building
4. `LinkResolver` constructor takes only `db`, not `vault_id`
5. `calculate_metrics()` takes `vault_id`, returns stats, stores per-note metrics in DB
6. Metrics retrieved via `db.get_graph_metrics(note_id)`, not from return value

## Testing

Run the tests with:
```bash
cd /Users/dt/projects/dev-tools/obsidian-cli-ops
PYTHONPATH=src/python pytest src/python/tests/test_graph_builder.py -v
```

Expected: All 12 tests should now pass.
