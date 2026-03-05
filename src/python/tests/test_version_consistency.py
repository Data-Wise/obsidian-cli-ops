"""
Test version consistency across project files.

Ensures VERSION in obs.zsh matches references in tests/obs.test.js and CLAUDE.md.
"""

import re
from pathlib import Path

import pytest

# Project root is 3 levels up from this test file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class TestVersionConsistency:
    """Verify version strings are consistent across the project."""

    @pytest.fixture(autouse=True)
    def _load_version(self):
        """Extract VERSION from obs.zsh for all tests."""
        obs_zsh = PROJECT_ROOT / "src" / "obs.zsh"
        assert obs_zsh.exists(), f"obs.zsh not found at {obs_zsh}"
        content = obs_zsh.read_text()
        match = re.search(r'^VERSION="([^"]+)"', content, re.MULTILINE)
        assert match, "VERSION= line not found in obs.zsh"
        self.version = match.group(1)

    def test_version_format(self):
        """VERSION should follow semver with optional pre-release suffix."""
        assert re.match(
            r"^\d+\.\d+\.\d+(-[\w.]+)?$", self.version
        ), f"VERSION '{self.version}' does not match expected semver format"

    def test_obs_test_js_matches(self):
        """tests/obs.test.js should reference the same version."""
        obs_test_js = PROJECT_ROOT / "tests" / "obs.test.js"
        assert obs_test_js.exists(), f"obs.test.js not found at {obs_test_js}"
        content = obs_test_js.read_text()
        expected = f'VERSION="{self.version}"'
        assert expected in content, (
            f"obs.test.js does not contain {expected!r}"
        )

    def test_claude_md_matches(self):
        """CLAUDE.md should reference the same version."""
        claude_md = PROJECT_ROOT / "CLAUDE.md"
        assert claude_md.exists(), f"CLAUDE.md not found at {claude_md}"
        content = claude_md.read_text()
        expected = f"**Current Version**: {self.version}"
        assert expected in content, (
            f"CLAUDE.md does not contain {expected!r}"
        )
