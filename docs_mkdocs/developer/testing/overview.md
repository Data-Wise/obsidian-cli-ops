# Testing Overview

**Version:** 3.2.1
**Total Tests:** 294 (235 pytest + 59 Jest)

## Test Coverage

| Component | Tests | Framework | File |
|-----------|-------|-----------|------|
| AI Providers | 26 | pytest | `test_ai_providers.py` |
| Vault Health | 21 | pytest | `test_vault_health.py` |
| AI Refactor | 20 | pytest | `test_ai_refactor.py` |
| AI Models | 33 | pytest | `test_ai_models.py` |
| Obsidian Bridge | 17 | pytest | `test_obsidian_bridge.py` |
| Vault Fixtures | 15 | pytest | `test_vault_fixtures.py` |
| AI Features | 15 | pytest | `test_ai_features.py` |
| JSON Output | 13 | pytest | `test_json_output.py` |
| CLI Edge Cases | 11 | pytest | `test_cli_edge_cases.py` |
| Vault Scanner | 8 | pytest | `test_vault_scanner.py` |
| Vault Lookup | 7 | pytest | `test_vault_lookup.py` |
| Version Consistency | 6 | pytest | `test_version_consistency.py` |
| Vault Manager | 6 | pytest | `test_vault_manager.py` |
| Embedding Cache | 6 | pytest | `test_embedding_cache.py` |
| CLI Rich Output | 6 | pytest | `test_cli_rich.py` |
| CLI Polish | 6 | pytest | `test_cli_polish.py` |
| Search API | 1 | pytest | `test_search_api.py` |
| Graph Metrics Join | 1 | pytest | `test_graph_metrics_join.py` |
| DB Pagination | 1 | pytest | `test_db_pagination.py` |
| DB Metrics | 1 | pytest | `test_db_metrics.py` |
| Vault Features | 16 | pytest | `test_features_vault.py` |
| **Python Subtotal** | **235** | **pytest** | |
| ZSH CLI Wrapper | 30 | Jest | `obs.test.js`, `cli.test.js` |
| Dependency Bootstrapping | 29 | Jest | `dep_bootstrap.test.js` (2 network-gated, run in CI) |
| **Jest Subtotal** | **59** | **Jest** | |
| **Total** | **294** | | |

---

## Running Tests

```bash
# Python tests (run from src/python/)
cd src/python && python3 -m pytest tests/ -q

# Jest tests
npx jest

# All tests
npm test
```

### Selective Testing

```bash
# Run a specific test file
python3 -m pytest tests/test_ai_refactor.py -v

# Run tests matching a pattern
python3 -m pytest tests/ -k "test_refactor"

# Run with coverage
python3 -m pytest tests/ --cov=. --cov-report=term-missing
```

---

## Test Architecture

### Three-Layer Testing

Tests mirror the application architecture:

| Layer | What's Tested | Key Files |
|-------|--------------|-----------|
| **Data** | DB operations, scanner, embeddings | `test_vault_scanner.py`, `test_embedding_cache.py` |
| **Core** | Vault manager, graph analysis, health | `test_vault_manager.py`, `test_vault_health.py` |
| **AI** | Providers, features, models, bridge | `test_ai_*.py`, `test_obsidian_bridge.py` |
| **CLI** | Output formatting, JSON, edge cases | `test_cli_*.py`, `test_json_output.py` |

### Mocking Strategy

- **AI providers**: Mocked with `MagicMock()` — no real API calls in tests
- **Database**: Temporary SQLite files per test (auto-cleaned)
- **Obsidian Bridge**: Mocked subprocess calls
- **Embeddings**: Pre-computed mock vectors

### Test Fixtures

Vault fixtures in `tests/fixtures/test_vault/`:

```
test_vault/
  .obsidian/.gitkeep    # Marks as Obsidian vault
  note-a.md             # Has links to note-b
  note-b.md             # Has links to note-c
  note-c.md             # Leaf node
  hub-note.md           # Links to all notes
  broken-link-note.md   # Links to non-existent note
```

Note: `.obsidian/` is gitignored — fixtures use `git add -f` to track the `.gitkeep`.

---

## Best Practices

1. **Test isolation**: Each test gets a fresh temp database
2. **Descriptive names**: `test_refactor_vault_dry_run_skips_ai_calls`
3. **Arrange-Act-Assert**: Consistent test structure
4. **Mock at boundaries**: Mock external APIs, not internal logic
5. **Run from correct directory**: `cd src/python` before pytest (avoids import errors)

---

## CI/CD

Tests run on GitHub Actions for both `dev` and `main` branches:

```yaml
# .github/workflows/ci.yml
- Python 3.9+ on ubuntu-latest
- pytest with coverage reporting
- Jest for ZSH wrapper validation
```

See [CI workflow](https://github.com/Data-Wise/obsidian-cli-ops/actions) for latest results.
