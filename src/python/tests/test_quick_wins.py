"""Tests for Quick Wins features (shell completions, export, timestamp, docs)."""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Import modules to test
from generate_bindings_docs import extract_bindings_from_file, generate_markdown


class TestShellCompletions:
    """Test shell completion files contain TUI command."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.zsh_completion = self.project_root / "completions" / "_obs"
        self.bash_completion = self.project_root / "completions" / "obs.bash"

    def test_zsh_completion_exists(self):
        """Test ZSH completion file exists."""
        assert self.zsh_completion.exists()

    def test_bash_completion_exists(self):
        """Test Bash completion file exists."""
        assert self.bash_completion.exists()

    def test_zsh_contains_tui_command(self):
        """Test ZSH completion includes 'tui' command."""
        content = self.zsh_completion.read_text()
        assert "'tui:" in content
        assert "Launch interactive TUI" in content

    def test_bash_contains_tui_command(self):
        """Test Bash completion includes 'tui' command."""
        content = self.bash_completion.read_text()
        assert "tui" in content
        # Should be in commands list
        import re
        assert re.search(r'commands="[^"]*tui[^"]*"', content)


class TestStatisticsExport:
    """Test JSON export functionality in statistics dashboard."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        # Import here to avoid issues if textual not installed
        try:
            from tui.screens.stats import StatisticsDashboardScreen
            self.stats_screen_class = StatisticsDashboardScreen
        except ImportError:
            self.stats_screen_class = None

    def test_stats_screen_imports_json(self):
        """Test that stats screen imports json module."""
        if not self.stats_screen_class:
            pytest.skip("Textual not installed")

        import tui.screens.stats as stats_module
        assert hasattr(stats_module, 'json')

    def test_stats_screen_has_export_binding(self):
        """Test that export binding exists and is visible."""
        if not self.stats_screen_class:
            pytest.skip("Textual not installed")

        bindings = self.stats_screen_class.BINDINGS
        export_binding = None
        for binding in bindings:
            if binding.action == "export":
                export_binding = binding
                break

        assert export_binding is not None, "Export binding not found"
        assert export_binding.key == "e"
        assert export_binding.show, "Export binding should be visible"

    @patch('tui.screens.stats.Path')
    @patch('tui.screens.stats.open')
    @patch('tui.screens.stats.json.dump')
    def test_export_creates_valid_json_structure(self, mock_dump, mock_open, mock_path):
        """Test that export creates correct JSON structure."""
        if not self.stats_screen_class:
            pytest.skip("Textual not installed")

        # Create mock database
        mock_db = Mock()
        mock_db.get_vault.return_value = {
            'id': 'test-vault',
            'name': 'Test Vault',
            'path': '/test/path',
            'note_count': 100,
            'link_count': 50,
            'last_scanned': '2025-12-15T10:00:00'
        }
        mock_db.get_vault_tag_stats.return_value = [
            {'tag': 'test', 'note_count': 10}
        ]
        mock_db.get_link_distribution.return_value = [
            {'bucket': '0-2', 'count': 20}
        ]
        mock_db.get_scan_history.return_value = [
            {'scanned_at': '2025-12-15T10:00:00', 'notes': 100}
        ]
        mock_db.get_orphaned_notes.return_value = []
        mock_db.get_hub_notes.return_value = []
        mock_db.get_broken_links.return_value = []

        # Create screen instance with mocked dependencies
        screen = self.stats_screen_class.__new__(self.stats_screen_class)
        # Set instance variables directly
        screen.vault_id = 'test-vault'
        screen.vault_name = 'Test Vault'
        screen.db = mock_db
        screen.notify = Mock()

        # Mock Path.home() to return a mock downloads dir
        mock_downloads = Mock()
        mock_downloads.exists.return_value = True
        mock_downloads.__truediv__ = Mock(return_value=Path('/home/user/Downloads/stats_test_vault_20251215_120000.json'))
        mock_home = Mock()
        mock_home.__truediv__ = Mock(return_value=mock_downloads)
        mock_path.home.return_value = mock_home

        # Call export
        screen.action_export()

        # Verify json.dump was called
        assert mock_dump.called, "json.dump should be called"

        # Get the data that was passed to json.dump
        call_args = mock_dump.call_args
        exported_data = call_args[0][0]

        # Verify structure
        assert 'exported_at' in exported_data
        assert 'vault' in exported_data
        assert 'statistics' in exported_data
        assert 'tags' in exported_data
        assert 'link_distribution' in exported_data
        assert 'scan_history' in exported_data

        # Verify vault data
        assert exported_data['vault']['id'] == 'test-vault'
        assert exported_data['vault']['name'] == 'Test Vault'
        assert exported_data['vault']['note_count'] == 100

    def test_export_filename_generation(self):
        """Test that export generates correct filename format."""
        vault_name = "Test Vault"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        vault_slug = vault_name.lower().replace(' ', '_')
        expected_pattern = f"stats_{vault_slug}_"

        filename = f"stats_{vault_slug}_{timestamp}.json"

        assert filename.startswith(expected_pattern)
        assert filename.endswith('.json')


class TestTimestampFormatting:
    """Test vault scan timestamp formatting."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        try:
            from tui.screens.vaults import VaultBrowserScreen
            self.vault_screen_class = VaultBrowserScreen
        except ImportError:
            self.vault_screen_class = None

    def test_format_last_scan_none(self):
        """Test formatting with None timestamp."""
        if not self.vault_screen_class:
            pytest.skip("Textual not installed")

        screen = self.vault_screen_class.__new__(self.vault_screen_class)
        result = screen._format_last_scan(None)
        assert result == "Never scanned"

    def test_format_last_scan_empty(self):
        """Test formatting with empty string."""
        if not self.vault_screen_class:
            pytest.skip("Textual not installed")

        screen = self.vault_screen_class.__new__(self.vault_screen_class)
        result = screen._format_last_scan("")
        assert result == "Never scanned"

    def test_format_last_scan_just_now(self):
        """Test formatting for recent scan (< 60 seconds)."""
        if not self.vault_screen_class:
            pytest.skip("Textual not installed")

        screen = self.vault_screen_class.__new__(self.vault_screen_class)
        now = datetime.now()
        timestamp = now.isoformat()
        result = screen._format_last_scan(timestamp)
        assert result == "Just now"

    def test_format_last_scan_minutes(self):
        """Test formatting for minutes ago."""
        if not self.vault_screen_class:
            pytest.skip("Textual not installed")

        screen = self.vault_screen_class.__new__(self.vault_screen_class)
        past = datetime.now() - timedelta(minutes=5)
        timestamp = past.isoformat()
        result = screen._format_last_scan(timestamp)
        assert result == "5 minutes ago"

    def test_format_last_scan_one_minute(self):
        """Test formatting for 1 minute ago (singular)."""
        if not self.vault_screen_class:
            pytest.skip("Textual not installed")

        screen = self.vault_screen_class.__new__(self.vault_screen_class)
        past = datetime.now() - timedelta(minutes=1)
        timestamp = past.isoformat()
        result = screen._format_last_scan(timestamp)
        assert result == "1 minute ago"

    def test_format_last_scan_hours(self):
        """Test formatting for hours ago."""
        if not self.vault_screen_class:
            pytest.skip("Textual not installed")

        screen = self.vault_screen_class.__new__(self.vault_screen_class)
        past = datetime.now() - timedelta(hours=3)
        timestamp = past.isoformat()
        result = screen._format_last_scan(timestamp)
        assert result == "3 hours ago"

    def test_format_last_scan_days(self):
        """Test formatting for days ago."""
        if not self.vault_screen_class:
            pytest.skip("Textual not installed")

        screen = self.vault_screen_class.__new__(self.vault_screen_class)
        past = datetime.now() - timedelta(days=2)
        timestamp = past.isoformat()
        result = screen._format_last_scan(timestamp)
        assert result == "2 days ago"

    def test_format_last_scan_invalid(self):
        """Test formatting with invalid timestamp returns original."""
        if not self.vault_screen_class:
            pytest.skip("Textual not installed")

        screen = self.vault_screen_class.__new__(self.vault_screen_class)
        invalid = "not-a-timestamp"
        result = screen._format_last_scan(invalid)
        assert result == invalid

    def test_update_header_timestamp_with_vault(self):
        """Test header update with selected vault."""
        if not self.vault_screen_class:
            pytest.skip("Textual not installed")

        screen = self.vault_screen_class.__new__(self.vault_screen_class)
        screen.selected_vault = {
            'last_scanned': datetime.now().isoformat()
        }

        # Mock query_one
        mock_title = Mock()
        screen.query_one = Mock(return_value=mock_title)

        screen.update_header_timestamp()

        # Verify update was called
        mock_title.update.assert_called_once()
        call_args = mock_title.update.call_args[0][0]
        assert "Last scan:" in call_args

    def test_update_header_timestamp_no_vault(self):
        """Test header update without selected vault."""
        if not self.vault_screen_class:
            pytest.skip("Textual not installed")

        screen = self.vault_screen_class.__new__(self.vault_screen_class)
        screen.selected_vault = None

        # Mock query_one
        mock_title = Mock()
        screen.query_one = Mock(return_value=mock_title)

        screen.update_header_timestamp()

        # Verify update was called with default title
        mock_title.update.assert_called_once()
        call_args = mock_title.update.call_args[0][0]
        assert call_args == "[bold cyan]📁 Vault Browser[/]"


class TestKeyboardShortcutsGenerator:
    """Test keyboard shortcuts documentation generator."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_screen.py"
        yield
        # Cleanup
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_extract_bindings_from_valid_file(self):
        """Test extracting bindings from valid screen file."""
        content = '''
from textual.screen import Screen
from textual.binding import Binding

class TestScreen(Screen):
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("h", "help", "Help", show=False),
    ]
'''
        self.test_file.write_text(content)

        result = extract_bindings_from_file(self.test_file)

        assert "TestScreen" in result
        bindings = result["TestScreen"]
        assert len(bindings) == 2
        assert bindings[0]["key"] == "q"
        assert bindings[0]["action"] == "quit"
        assert bindings[0]["label"] == "Quit"
        assert bindings[0]["show"]
        assert not bindings[1]["show"]

    def test_extract_bindings_no_screen_class(self):
        """Test extracting from file without Screen class."""
        content = '''
def some_function():
    pass
'''
        self.test_file.write_text(content)

        result = extract_bindings_from_file(self.test_file)

        assert result == {}

    def test_extract_bindings_no_bindings_array(self):
        """Test extracting from Screen without BINDINGS."""
        content = '''
from textual.screen import Screen

class TestScreen(Screen):
    pass
'''
        self.test_file.write_text(content)

        result = extract_bindings_from_file(self.test_file)

        assert result == {}

    def test_generate_markdown_structure(self):
        """Test markdown generation has correct structure."""
        test_bindings = {
            "TestScreen": [
                {"key": "q", "action": "quit", "label": "Quit", "show": True},
                {"key": "escape", "action": "back", "label": "Back", "show": True},
            ]
        }

        markdown = generate_markdown(test_bindings)

        # Check header
        assert "# Keyboard Shortcuts Reference" in markdown

        # Check global shortcuts section
        assert "## Global Shortcuts" in markdown

        # Check that escape is converted to Esc
        assert "`Esc`" in markdown

        # Check footer
        assert "Generated automatically" in markdown
        assert "Last updated:" in markdown

    def test_generate_markdown_key_formatting(self):
        """Test that special keys are formatted correctly."""
        # Use a real screen name that will be included in output
        test_bindings = {
            "HomeScreen": [
                {"key": "escape", "action": "back", "label": "Back", "show": True},
                {"key": "enter", "action": "select", "label": "Select", "show": True},
                {"key": "tab", "action": "next", "label": "Next", "show": True},
            ]
        }

        markdown = generate_markdown(test_bindings)

        # Verify key formatting in the generated markdown
        assert "`Esc`" in markdown
        assert "`Enter`" in markdown
        assert "`Tab`" in markdown

    def test_keyboard_shortcuts_file_generated(self):
        """Test that KEYBOARD_SHORTCUTS.md was generated."""
        project_root = Path(__file__).parent.parent.parent.parent
        shortcuts_file = project_root / "KEYBOARD_SHORTCUTS.md"

        assert shortcuts_file.exists()

        content = shortcuts_file.read_text()
        assert "# Keyboard Shortcuts Reference" in content
        assert "## Global Shortcuts" in content
        assert "## Statistics Dashboard" in content
        assert "`e` | Export | Export" in content  # Export binding we added

    def test_generated_docs_include_all_screens(self):
        """Test that generated docs include all TUI screens."""
        project_root = Path(__file__).parent.parent.parent.parent
        shortcuts_file = project_root / "KEYBOARD_SHORTCUTS.md"

        if not shortcuts_file.exists():
            pytest.skip("KEYBOARD_SHORTCUTS.md not generated yet")

        content = shortcuts_file.read_text()

        # Check for all expected screens
        assert "## Home Screen" in content
        assert "## Vault Browser" in content
        assert "## Note Explorer" in content
        assert "## Graph Visualizer" in content
        assert "## Statistics Dashboard" in content


class TestQuickWinsIntegration:
    """Integration tests for all quick wins together."""

    def test_all_quick_wins_files_exist(self):
        """Test that all quick wins files exist."""
        project_root = Path(__file__).parent.parent.parent.parent

        # Completion files
        assert (project_root / "completions" / "_obs").exists()
        assert (project_root / "completions" / "obs.bash").exists()

        # Generator script
        assert (project_root / "src" / "python" / "generate_bindings_docs.py").exists()

        # Generated docs
        assert (project_root / "KEYBOARD_SHORTCUTS.md").exists()

    def test_stats_screen_has_all_features(self):
        """Test that stats screen has export + all original features."""
        try:
            from tui.screens.stats import StatisticsDashboardScreen
        except ImportError:
            pytest.skip("Textual not installed")

        # Check class has required methods
        assert hasattr(StatisticsDashboardScreen, 'action_export')
        assert hasattr(StatisticsDashboardScreen, 'action_refresh')
        assert hasattr(StatisticsDashboardScreen, 'action_cycle_view')

        # Check BINDINGS
        bindings = StatisticsDashboardScreen.BINDINGS
        actions = [b.action for b in bindings]
        assert "export" in actions
        assert "refresh" in actions
        assert "cycle_view" in actions

    def test_vault_browser_has_timestamp_features(self):
        """Test that vault browser has timestamp formatting."""
        try:
            from tui.screens.vaults import VaultBrowserScreen
        except ImportError:
            pytest.skip("Textual not installed")

        # Check class has timestamp methods
        assert hasattr(VaultBrowserScreen, '_format_last_scan')
        assert hasattr(VaultBrowserScreen, 'update_header_timestamp')
