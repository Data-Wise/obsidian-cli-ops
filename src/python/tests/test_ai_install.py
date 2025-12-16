"""Tests for AI install module."""

import pytest
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from ai.install import (
    is_package_installed,
    get_missing_deps,
    install_packages,
    PROVIDER_DEPS,
    IMPORT_NAMES,
    InstallMode,
)


class TestIsPackageInstalled:
    """Tests for is_package_installed function."""

    def test_installed_package(self):
        """Test detection of installed package."""
        # requests should be installed
        assert is_package_installed("requests") is True

    def test_not_installed_package(self):
        """Test detection of missing package."""
        assert is_package_installed("nonexistent-fake-package-xyz") is False

    def test_package_with_import_mapping(self):
        """Test package with different import name."""
        # PyYAML imports as yaml
        result = is_package_installed("PyYAML")
        # Result depends on whether yaml is installed
        assert isinstance(result, bool)

    def test_nested_import_name(self):
        """Test package with nested import (google.generativeai)."""
        # Should handle google.generativeai -> google
        result = is_package_installed("google-generativeai")
        assert isinstance(result, bool)


class TestGetMissingDeps:
    """Tests for get_missing_deps function."""

    def test_provider_with_no_deps(self):
        """Test provider with no Python dependencies."""
        # gemini-cli and claude-cli have no pip deps
        assert get_missing_deps("gemini-cli") == []
        assert get_missing_deps("claude-cli") == []

    def test_unknown_provider(self):
        """Test unknown provider returns empty list."""
        assert get_missing_deps("unknown-provider") == []

    def test_provider_deps_structure(self):
        """Test PROVIDER_DEPS has expected structure."""
        assert "gemini-api" in PROVIDER_DEPS
        assert "ollama" in PROVIDER_DEPS
        assert isinstance(PROVIDER_DEPS["gemini-api"], list)


class TestInstallPackages:
    """Tests for install_packages function."""

    def test_empty_package_list(self):
        """Test installing empty list succeeds."""
        success, msg = install_packages([])
        assert success is True
        assert "No packages" in msg

    @patch('subprocess.run')
    def test_successful_install(self, mock_run):
        """Test successful package installation."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        success, msg = install_packages(["test-package"])

        assert success is True
        assert "Installed" in msg
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_failed_install(self, mock_run):
        """Test failed package installation."""
        mock_run.return_value = MagicMock(returncode=1, stderr="Error message")

        success, msg = install_packages(["test-package"])

        assert success is False
        assert "pip error" in msg

    @patch('subprocess.run')
    def test_timeout_install(self, mock_run):
        """Test installation timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="pip", timeout=120)

        success, msg = install_packages(["test-package"])

        assert success is False
        assert "timed out" in msg


class TestInstallMode:
    """Tests for InstallMode enum."""

    def test_install_modes(self):
        """Test all install modes exist."""
        assert InstallMode.ALWAYS == "always"
        assert InstallMode.PROMPT == "prompt"
        assert InstallMode.NEVER == "never"

    def test_mode_from_string(self):
        """Test creating mode from string."""
        assert InstallMode("always") == InstallMode.ALWAYS
        assert InstallMode("prompt") == InstallMode.PROMPT
        assert InstallMode("never") == InstallMode.NEVER


class TestImportNames:
    """Tests for IMPORT_NAMES mapping."""

    def test_known_mappings(self):
        """Test known package to import mappings."""
        assert IMPORT_NAMES.get("google-generativeai") == "google.generativeai"
        assert IMPORT_NAMES.get("python-frontmatter") == "frontmatter"
        assert IMPORT_NAMES.get("PyYAML") == "yaml"
        assert IMPORT_NAMES.get("scikit-learn") == "sklearn"

    def test_unmapped_package(self):
        """Test unmapped package returns None."""
        assert IMPORT_NAMES.get("requests") is None
