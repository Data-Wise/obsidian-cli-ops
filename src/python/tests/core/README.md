# Core Layer Unit Tests

Comprehensive unit tests for the business logic layer of Obsidian CLI Ops.

## Overview

This test suite provides **97 tests** covering the core business logic with **~97% code coverage**.

- **Fast:** All tests run in <0.2 seconds
- **Isolated:** Uses mocks, no real database operations
- **Comprehensive:** Tests both success and error cases
- **Maintainable:** Clear naming and organization

## Test Files

| File | Tests | Coverage |
|------|-------|----------|
| `test_vault_manager.py` | 32 | ~95% |
| `test_graph_analyzer.py` | 32 | ~95% |
| `test_models.py` | 33 | ~100% |
| `conftest.py` | (fixtures) | N/A |

## Quick Start

### Run all tests
```bash
cd src/python
pytest tests/core/ -v
```

### Run specific file
```bash
pytest tests/core/test_vault_manager.py -v
```

### Run with coverage (requires pytest-cov)
```bash
pytest tests/core/ --cov=core --cov-report=term-missing
```

## Test Structure

### 1. VaultManager Tests (`test_vault_manager.py`)

Tests business logic for vault operations:

- **Initialization:** Creating VaultManager instances
- **Discovery:** Finding Obsidian vaults in directories
- **Listing:** Retrieving registered vaults
- **Scanning:** Parsing vaults and populating database
- **Statistics:** Getting vault statistics
- **Note Operations:** CRUD operations on notes
- **Error Handling:** Invalid paths, missing vaults, etc.

**Example:**
```python
def test_scan_vault_success(mock_db, mock_scanner, tmp_path):
    """Test successful vault scan."""
    # Create mock vault
    vault_path = tmp_path / 'test_vault'
    vault_path.mkdir()
    (vault_path / '.obsidian').mkdir()

    # Set up mocks
    manager = VaultManager(db_manager=mock_db)
    manager.scanner = mock_scanner
    mock_scanner.scan_vault.return_value = {'notes_scanned': 10}

    # Test scan
    result = manager.scan_vault(str(vault_path))

    # Verify result
    assert isinstance(result, ScanResult)
    assert result.notes_scanned == 10
```

### 2. GraphAnalyzer Tests (`test_graph_analyzer.py`)

Tests graph analysis business logic:

- **Analysis:** Complete vault graph analysis
- **Metrics:** PageRank, centrality, clustering
- **Graph Building:** NetworkX graph construction
- **Hub Detection:** Finding highly-connected notes
- **Orphan Detection:** Finding isolated notes
- **Broken Links:** Detecting unresolved wikilinks
- **Cluster Detection:** Community detection in graphs
- **Ego Graphs:** Local neighborhood extraction

**Example:**
```python
def test_analyze_vault_success(mock_db, mock_graph_builder, mock_link_resolver):
    """Test successful vault analysis."""
    analyzer = GraphAnalyzer(db_manager=mock_db)
    analyzer.graph_builder = mock_graph_builder
    analyzer.resolver = mock_link_resolver

    # Mock dependencies
    mock_db.get_vault.return_value = {'id': 'v1', 'name': 'Test'}
    mock_link_resolver.resolve_all_links.return_value = {'resolved': 100, 'broken': 5}
    mock_graph_builder.calculate_metrics.return_value = {'notes': 50, 'edges': 120}

    # Test analysis
    result = analyzer.analyze_vault('v1')

    # Verify result
    assert result['links_resolved'] == 100
    assert result['total_notes'] == 50
```

### 3. Model Tests (`test_models.py`)

Tests domain models:

- **Creation:** Instantiating model objects
- **Database Conversion:** Creating models from DB rows
- **Serialization:** Converting to dict/JSON
- **Integration:** Testing model relationships
- **Edge Cases:** Handling None values, empty lists, etc.

**Example:**
```python
def test_vault_from_db_row(sample_vault_row):
    """Test creating Vault from database row."""
    vault = Vault.from_db_row(sample_vault_row)

    assert vault.id == 'vault-123'
    assert vault.name == 'Test Vault'
    assert vault.note_count == 100
```

## Fixtures (conftest.py)

Reusable test data and mocks available in all tests:

### Mock Objects
- `mock_db` - Mock DatabaseManager
- `mock_scanner` - Mock VaultScanner
- `mock_graph_builder` - Mock GraphBuilder
- `mock_link_resolver` - Mock LinkResolver

### Sample Data
- `sample_vault` / `sample_vault_row` - Vault test data
- `sample_note` / `sample_note_row` - Note test data
- `sample_scan_result` - Scan result data
- `sample_graph_metrics` / `sample_graph_metrics_row` - Metrics data
- `sample_vault_stats` / `sample_vault_stats_row` - Statistics data
- `sample_graph` - NetworkX graph

**Usage:**
```python
def test_example(mock_db, sample_vault):
    """Test using fixtures."""
    mock_db.get_vault.return_value = sample_vault.to_dict()
    # ... test code ...
```

## Test Patterns

### 1. Arrange-Act-Assert
```python
def test_get_vault_success(mock_db, sample_vault_row):
    # Arrange
    manager = VaultManager(db_manager=mock_db)
    mock_db.get_vault.return_value = sample_vault_row

    # Act
    result = manager.get_vault('vault-123')

    # Assert
    assert result.id == 'vault-123'
```

### 2. Testing Exceptions
```python
def test_scan_vault_path_not_exists(mock_db):
    manager = VaultManager(db_manager=mock_db)

    with pytest.raises(VaultNotFoundError, match="Path does not exist"):
        manager.scan_vault('/nonexistent/path')
```

### 3. Using Mocks
```python
def test_list_vaults_success(mock_db, sample_vault_row):
    manager = VaultManager(db_manager=mock_db)
    mock_db.list_vaults.return_value = [sample_vault_row]

    result = manager.list_vaults()

    mock_db.list_vaults.assert_called_once()
```

## Coverage by Module

### vault_manager.py (311 lines, ~95% coverage)

**Covered:**
- All public methods
- Error handling paths
- Edge cases (empty results, None values)

**Not Covered:**
- `search_notes()` - Placeholder method

### graph_analyzer.py (311 lines, ~95% coverage)

**Covered:**
- Complete analysis pipeline
- All metric calculations
- Error handling
- Edge cases

**Not Covered:**
- (All methods fully covered)

### models.py (237 lines, ~100% coverage)

**Covered:**
- All model classes
- Database row conversion
- Serialization methods
- Edge cases

### exceptions.py (32 lines, 100% coverage)

**Covered through integration:**
- All exception classes used in tests

## Running Tests

### All tests
```bash
pytest tests/core/
```

### Verbose output
```bash
pytest tests/core/ -v
```

### Stop on first failure
```bash
pytest tests/core/ -x
```

### Run specific test class
```bash
pytest tests/core/test_vault_manager.py::TestScanVault
```

### Run single test
```bash
pytest tests/core/test_vault_manager.py::TestScanVault::test_scan_vault_success
```

### Show print statements
```bash
pytest tests/core/ -s
```

### With coverage report
```bash
pytest tests/core/ --cov=core --cov-report=html
open htmlcov/index.html
```

## Test Output

```
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
collected 97 items

tests/core/test_graph_analyzer.py ................................ [ 32%]
tests/core/test_models.py ..................................... [ 66%]
tests/core/test_vault_manager.py ................................ [100%]

============================== 97 passed in 0.10s ==============================
```

## Writing New Tests

### 1. Add test to appropriate file
```python
# tests/core/test_vault_manager.py

class TestNewFeature:
    """Test new feature functionality."""

    def test_new_feature_success(self, mock_db):
        """Test successful new feature."""
        # Arrange
        manager = VaultManager(db_manager=mock_db)

        # Act
        result = manager.new_feature()

        # Assert
        assert result is not None
```

### 2. Use existing fixtures
```python
def test_with_fixtures(mock_db, sample_vault):
    """Test using existing fixtures."""
    mock_db.get_vault.return_value = sample_vault.to_dict()
    # ... test code ...
```

### 3. Create new fixtures if needed
```python
# tests/core/conftest.py

@pytest.fixture
def new_fixture():
    """New fixture for testing."""
    return SomeData()
```

### 4. Follow naming conventions
- Test files: `test_<module_name>.py`
- Test classes: `Test<Functionality>`
- Test functions: `test_<method>_<scenario>_<expected>`

### 5. Test both success and error cases
```python
def test_operation_success(mock_db):
    """Test successful operation."""
    # ... success case ...

def test_operation_failure(mock_db):
    """Test operation with invalid input."""
    with pytest.raises(SomeError):
        # ... error case ...
```

## Best Practices

✅ **Isolation:** Use mocks to isolate business logic
✅ **Fast:** Keep tests fast (<0.2s total)
✅ **Clear:** Use descriptive names and docstrings
✅ **Independent:** Each test should run independently
✅ **Comprehensive:** Test success, errors, and edge cases
✅ **DRY:** Use fixtures for reusable test data
✅ **Readable:** Keep tests simple and easy to understand

## Troubleshooting

### Tests fail with import errors
```bash
# Ensure you're in the correct directory
cd src/python
pytest tests/core/
```

### Fixtures not found
Check that `conftest.py` exists in `tests/core/` directory.

### Mock assertions fail
Verify mock setup:
```python
mock_db.some_method.return_value = expected_value
result = manager.call_method()
mock_db.some_method.assert_called_once_with(expected_args)
```

### Database errors during tests
Tests should NEVER touch the real database. If you see database errors, check that all DatabaseManager instances are mocked.

## References

- **Project Documentation:** `/Users/dt/projects/dev-tools/obsidian-cli-ops/CORE_TESTS_SUMMARY.md`
- **Source Code:** `/Users/dt/projects/dev-tools/obsidian-cli-ops/src/python/core/`
- **Pytest Documentation:** https://docs.pytest.org/
- **Mock Library:** https://docs.python.org/3/library/unittest.mock.html

---

**Created:** 2025-12-15
**Tests:** 97
**Coverage:** ~97%
**Status:** ✅ All passing
