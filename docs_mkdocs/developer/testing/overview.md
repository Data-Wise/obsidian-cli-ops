# Testing Overview

**Version:** 4.3.0
**Total Tests:** 764 pytest + 69 Jest — includes the nexus-cli absorption (config + research) shipped in v4.0.0. The per-file table below is the exact inventory; the headline figures are gated as round-down floors (see `core/doc_counts.py`).

## Test Coverage

### Unit Tests (pytest)

| Component | Tests | Framework | File |
|-----------|-------|-----------|------|
| Doctor / Diagnostics | 35 | pytest | `test_doctor.py` |
| AI Models | 32 | pytest | `test_ai_models.py` |
| Config Loader | 27 | pytest | `test_config_loader.py` |
| AI Providers | 26 | pytest | `test_ai_providers.py` |
| Vault Health | 21 | pytest | `test_vault_health.py` |
| AI Refactor | 20 | pytest | `test_ai_refactor.py` |
| Note Inserter | 18 | pytest | `test_note_inserter.py` |
| Obsidian Bridge | 17 | pytest | `test_obsidian_bridge.py` |
| Temporal / Monitoring | 17 | pytest | `test_temporal.py` |
| Vault Features | 16 | pytest | `test_features_vault.py` |
| AI Features | 15 | pytest | `test_ai_features.py` |
| Vault Fixtures | 15 | pytest | `test_vault_fixtures.py` |
| JSON Output | 13 | pytest | `test_json_output.py` |
| Vault Scanner | 13 | pytest | `test_vault_scanner.py` |
| Flow Init (Core) | 36 | pytest | `test_flow_init.py` |
| CLI Edge Cases | 11 | pytest | `test_cli_edge_cases.py` |
| Board Engine | 28 | pytest | `test_board.py` |
| Flow Init (Dogfood) | 19 | pytest | `test_flow_dogfood.py` |
| Research Board | 8 | pytest | `test_research_board.py` |
| DB Manager | 8 | pytest | `test_db_manager.py` |
| Vault Lookup | 7 | pytest | `test_vault_lookup.py` |
| CLI Polish | 6 | pytest | `test_cli_polish.py` |
| CLI Rich Output | 6 | pytest | `test_cli_rich.py` |
| Embedding Cache | 6 | pytest | `test_embedding_cache.py` |
| Vault Manager | 6 | pytest | `test_vault_manager.py` |
| Version Consistency | 6 | pytest | `test_version_consistency.py` |
| Doc Count Gate | 5 | pytest | `test_doc_counts.py` |
| DB Metrics | 1 | pytest | `test_db_metrics.py` |
| DB Pagination | 1 | pytest | `test_db_pagination.py` |
| Graph Metrics Join | 1 | pytest | `test_graph_metrics_join.py` |
| Search API | 1 | pytest | `test_search_api.py` |
| **Unit Subtotal** | **413** | **pytest** | |

### MCP Unit Tests (pytest)

| Component | Tests | Framework | File |
|-----------|-------|-----------|------|
| MCP Server — all 42 tools + 4 resources | 113 | pytest | `test_mcp_server.py` |
| **MCP Subtotal** | **113** | **pytest** | |

Covers all 42 MCP tools and 4 resources with mock vault/DB fixtures. Includes edge cases: unicode inputs, empty queries, path traversal safety, and server stability under error conditions.

### E2E Tests (pytest, gated)

| Component | Tests | Framework | File |
|-----------|-------|-----------|------|
| MCP dogfood — real subprocess JSON-RPC | 71 | pytest | `tests/e2e/test_e2e_mcp.py` |
| **E2E Subtotal** | **71** | **pytest** | |

E2E tests spin up the real MCP server as a subprocess and exercise the JSON-RPC protocol end-to-end. **Gated behind `E2E=1`** — not run in standard CI to avoid environment dependencies.

### Jest Tests

| Component | Tests | Framework | File |
|-----------|-------|-----------|------|
| ZSH CLI Wrapper | 30 | Jest | `obs.test.js`, `cli.test.js` |
| Dependency Bootstrapping | 29 | Jest | `dep_bootstrap.test.js` (2 network-gated, run in CI) |
| Man-page version sync | 6 | Jest | `man-page-version-sync.test.js` |
| Flag-routing regression | 4 | Jest | *(in cli.test.js)* |
| **Jest Subtotal** | **70** | **Jest** | |

---

## Running Tests

```bash
# Python unit tests (run from src/python/)
cd src/python && python3 -m pytest tests/ -q

# MCP unit tests
cd src/python && python3 -m pytest tests/test_mcp_server.py -v

# E2E tests (requires E2E=1 env var)
E2E=1 pytest src/python/tests/e2e/ -v

# Jest tests
npx jest

# All tests (unit + Jest, no E2E)
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

!!! note "numpy-dependent tests"
    Tests that require numpy skip gracefully when running under system Python (no isolated venv). Use `./install.sh` to provision the venv so all tests run.

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
