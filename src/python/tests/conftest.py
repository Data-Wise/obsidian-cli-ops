"""
Pytest configuration and fixtures for all tests.

Provides shared fixtures including test database initialization.
"""

import pytest
import sqlite3
import os
from pathlib import Path


@pytest.fixture
def test_db(tmp_path):
    """
    Create a test database with schema initialized.

    This fixture:
    - Creates a temporary SQLite database
    - Loads and executes the schema from schema/vault_db.sql
    - Returns a DatabaseManager instance
    - Cleans up automatically after the test

    Args:
        tmp_path: pytest's temporary directory fixture

    Returns:
        DatabaseManager: Configured database manager with initialized schema
    """
    # Create temp database file
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))

    # Load schema from project root
    schema_path = Path(__file__).parent.parent.parent.parent / "schema" / "vault_db.sql"

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    # Read and execute schema
    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    conn.executescript(schema_sql)
    conn.commit()
    conn.close()

    # Import and return DatabaseManager
    from db_manager import DatabaseManager
    db_manager = DatabaseManager(str(db_path))

    yield db_manager

    # Cleanup is automatic with tmp_path
    # DatabaseManager will close connections when garbage collected
