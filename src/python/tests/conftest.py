"""
Pytest configuration and shared fixtures for TUI tests.

This conftest.py ensures the src/python directory is on the Python path
so that imports like `from db_manager import DatabaseManager` work correctly.
"""
import sys
from pathlib import Path
import pytest

# Add src/python to path for imports - MUST happen before any other imports
_python_src = Path(__file__).parent.parent.resolve()
if str(_python_src) not in sys.path:
    sys.path.insert(0, str(_python_src))

# Now we can import from the project
# DO NOT import from src.python package here - it will fail due to relative imports
# Tests should import directly: from db_manager import DatabaseManager

@pytest.fixture
def db_manager():
    """
    Shared fixture for an in-memory database with schema initialized.

    This fixture creates a properly initialized DatabaseManager that can be
    used across all test files without duplicating the initialization logic.
    """
    from db_manager import DatabaseManager

    db = DatabaseManager(db_path=":memory:")
    db.initialize_database()
    return db
