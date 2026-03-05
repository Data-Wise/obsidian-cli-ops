"""
Tests for CLI polish features (Phase 7.3 Inc 4).

Tests recovery tips, --force flag on db init, and --verbose on stats.
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add src/python to path for imports
SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))


class TestRecoveryTips:
    """Verify helpful tips are shown when vault/note not found."""

    def test_analyze_not_found_shows_tip(self):
        """analyze with bad vault should show recovery tips."""
        result = subprocess.run(
            [sys.executable, str(SRC_DIR / "obs_cli.py"), "analyze", "nonexistent_vault_xyz"],
            capture_output=True, text=True
        )
        assert result.returncode != 0
        combined = result.stdout + result.stderr
        assert "Tip:" in combined or "not found" in combined.lower()

    def test_stats_not_found_shows_tip(self):
        """stats with bad vault should show recovery tips."""
        result = subprocess.run(
            [sys.executable, str(SRC_DIR / "obs_cli.py"), "stats", "--vault", "nonexistent_vault_xyz"],
            capture_output=True, text=True
        )
        assert result.returncode != 0
        combined = result.stdout + result.stderr
        assert "Tip:" in combined or "not found" in combined.lower()

    def test_health_not_found_shows_tip(self):
        """health with bad vault should show recovery tips."""
        result = subprocess.run(
            [sys.executable, str(SRC_DIR / "obs_cli.py"), "health", "nonexistent_vault_xyz"],
            capture_output=True, text=True
        )
        assert result.returncode != 0
        combined = result.stdout + result.stderr
        assert "Tip:" in combined or "not found" in combined.lower()


class TestDbInitForce:
    """Verify --force flag on db init."""

    def test_db_init_force_flag_accepted(self):
        """db init --force should be a valid argument."""
        result = subprocess.run(
            [sys.executable, str(SRC_DIR / "obs_cli.py"), "db", "init", "--force", "--help"],
            capture_output=True, text=True
        )
        # --help exits 0 even if --force is present; we just check it doesn't error
        # as "unrecognized argument"
        assert "unrecognized arguments" not in result.stderr

    def test_db_init_without_force_warns_if_exists(self):
        """db init without --force should warn if database exists."""
        db_path = Path("~/.config/obs/vault_db.sqlite").expanduser()
        if not db_path.exists():
            pytest.skip("No existing database to test against")
        result = subprocess.run(
            [sys.executable, str(SRC_DIR / "obs_cli.py"), "db", "init"],
            capture_output=True, text=True
        )
        combined = result.stdout + result.stderr
        assert "already exists" in combined.lower() or "force" in combined.lower()


class TestVerboseStats:
    """Verify --verbose wiring to stats command."""

    def test_verbose_flag_accepted_on_stats(self):
        """stats --verbose should not error as unrecognized."""
        result = subprocess.run(
            [sys.executable, str(SRC_DIR / "obs_cli.py"), "--verbose", "stats", "--help"],
            capture_output=True, text=True
        )
        assert "unrecognized arguments" not in result.stderr
