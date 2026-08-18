"""Tests for Obsidian CLI bridge."""

import json
import subprocess
import pytest
from unittest.mock import patch, MagicMock

from ai.obsidian_bridge import ObsidianBridge


class TestObsidianBridgeAvailability:
    """Tests for availability detection and caching."""

    @patch("ai.obsidian_bridge.subprocess.run")
    def test_available_with_native_cli_version_command(self, mock_run):
        def run_cli(args, **kwargs):
            if args == ["obsidian", "version"]:
                return MagicMock(returncode=0, stdout="1.12.7 (installer 1.12.7)")
            return MagicMock(returncode=1, stdout="", stderr="unknown command")

        mock_run.side_effect = run_cli
        bridge = ObsidianBridge()

        assert bridge.is_available() is True

    @patch("ai.obsidian_bridge.subprocess.run")
    def test_available_when_cli_works(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        bridge = ObsidianBridge()
        assert bridge.is_available() is True

    @patch("ai.obsidian_bridge.subprocess.run")
    def test_not_available_when_cli_fails(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        bridge = ObsidianBridge()
        assert bridge.is_available() is False

    @patch("ai.obsidian_bridge.subprocess.run")
    def test_not_available_when_not_installed(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        bridge = ObsidianBridge()
        assert bridge.is_available() is False

    @patch("ai.obsidian_bridge.subprocess.run")
    def test_not_available_on_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired("obsidian", 5)
        bridge = ObsidianBridge()
        assert bridge.is_available() is False

    @patch("ai.obsidian_bridge.subprocess.run")
    def test_availability_is_cached(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        bridge = ObsidianBridge()
        bridge.is_available()
        bridge.is_available()
        # Only called once because result is cached
        assert mock_run.call_count == 1

    @patch("ai.obsidian_bridge.subprocess.run")
    def test_reset_clears_cache(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        bridge = ObsidianBridge()
        bridge.is_available()
        bridge.reset()
        bridge.is_available()
        assert mock_run.call_count == 2

    @patch("ai.obsidian_bridge.subprocess.run")
    def test_status_reports_native_cli_version(self, mock_run):
        def run_cli(args, **kwargs):
            if args == ["obsidian", "version"]:
                return MagicMock(returncode=0, stdout="1.12.7 (installer 1.12.7)")
            if args == ["obsidian", "vaults"]:
                return MagicMock(returncode=0, stdout="Research")
            return MagicMock(returncode=1, stdout="", stderr="unknown command")

        mock_run.side_effect = run_cli
        bridge = ObsidianBridge()

        status = bridge.get_status()

        assert status.cli_installed is True
        assert status.cli_version == "1.12.7 (installer 1.12.7)"
        assert status.app_running is True


class TestObsidianBridgeGracefulDegradation:
    """Tests that all methods return empty results when unavailable."""

    def setup_method(self):
        self.bridge = ObsidianBridge()
        self.bridge._available = False  # Force unavailable

    def test_backlinks_empty_when_unavailable(self):
        assert self.bridge.get_backlinks("note.md") == []

    def test_orphans_empty_when_unavailable(self):
        assert self.bridge.get_orphans() == []

    def test_tags_empty_when_unavailable(self):
        assert self.bridge.get_tags() == {}

    def test_read_note_none_when_unavailable(self):
        assert self.bridge.read_note("note.md") is None


class TestObsidianBridgeDataParsing:
    """Tests for JSON parsing from Obsidian CLI output."""

    def setup_method(self):
        self.bridge = ObsidianBridge()
        self.bridge._available = True

    @patch("ai.obsidian_bridge.subprocess.run")
    def test_get_backlinks_parses_json(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(["note-a.md", "note-b.md"]),
        )
        result = self.bridge.get_backlinks("target.md")
        assert result == ["note-a.md", "note-b.md"]

    @patch("ai.obsidian_bridge.subprocess.run")
    def test_get_orphans_parses_json(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(["orphan-1.md", "orphan-2.md"]),
        )
        result = self.bridge.get_orphans()
        assert result == ["orphan-1.md", "orphan-2.md"]

    @patch("ai.obsidian_bridge.subprocess.run")
    def test_get_tags_parses_json(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"python": 15, "testing": 8}),
        )
        result = self.bridge.get_tags()
        assert result == {"python": 15, "testing": 8}

    @patch("ai.obsidian_bridge.subprocess.run")
    def test_read_note_returns_content(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="# My Note\n\nContent here.",
        )
        result = self.bridge.read_note("my-note.md")
        assert result == "# My Note\n\nContent here."

    @patch("ai.obsidian_bridge.subprocess.run")
    def test_invalid_json_returns_empty(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="not valid json",
        )
        assert self.bridge.get_backlinks("note.md") == []

    @patch("ai.obsidian_bridge.subprocess.run")
    def test_cli_error_returns_empty(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        assert self.bridge.get_backlinks("note.md") == []

    @patch("ai.obsidian_bridge.subprocess.run")
    def test_timeout_returns_empty(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired("obsidian", 10)
        assert self.bridge.get_orphans() == []
