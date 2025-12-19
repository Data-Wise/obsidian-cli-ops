"""
Tests for TUI Application (Phase 4.1)

Tests for the main TUI app, HomeScreen, HelpScreen, and PlaceholderScreen.
"""

import pytest
from unittest.mock import Mock, patch, PropertyMock
from tui.app import ObsidianTUI, HomeScreen, HelpScreen, PlaceholderScreen
from tui.screens.notes import NoteExplorerScreen
from tui.screens.graph import GraphVisualizerScreen
from tui.screens.stats import StatisticsDashboardScreen


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def mock_app():
    """Create a mock TUI app."""
    app = Mock()
    app.push_screen = Mock()
    app.pop_screen = Mock()
    app.exit = Mock()
    app.notify = Mock()
    app.last_vault_id = None
    app.last_vault_name = None
    return app


# ==============================================================================
# HomeScreen Tests
# ==============================================================================

class TestHomeScreen:
    """Tests for HomeScreen."""

    def test_home_screen_initialization(self):
        """Test that HomeScreen can be initialized."""
        screen = HomeScreen()
        assert screen is not None

    def test_home_screen_bindings(self):
        """Test that HomeScreen has correct key bindings."""
        bindings = {b.key: b.action for b in HomeScreen.BINDINGS}

        assert "v" in bindings
        assert bindings["v"] == "vaults"

        assert "n" in bindings
        assert bindings["n"] == "notes"

        assert "g" in bindings
        assert bindings["g"] == "graph"

        assert "s" in bindings
        assert bindings["s"] == "stats"

        assert "q" in bindings
        assert bindings["q"] == "quit"

        assert "?" in bindings
        assert bindings["?"] == "help"

    def test_home_screen_welcome_text(self):
        """Test that welcome text is generated."""
        screen = HomeScreen()
        text = screen._get_welcome_text()

        assert "Obsidian CLI Ops" in text
        assert "2.1.0" in text
        assert "Interactive Vault Explorer" in text

    def test_action_vaults(self, mock_app):
        """Test action_vaults pushes vaults screen."""
        screen = HomeScreen()
        type(screen).app = PropertyMock(return_value=mock_app)

        screen.action_vaults()

        mock_app.push_screen.assert_called_once_with("vaults")

    def test_action_notes_no_vault(self, mock_app):
        """Test action_notes when no vault is selected."""
        screen = HomeScreen()
        type(screen).app = PropertyMock(return_value=mock_app)
        mock_app.last_vault_id = None

        screen.action_notes()

        mock_app.notify.assert_called_once()
        mock_app.push_screen.assert_called_once_with("vaults")

    def test_action_notes_with_vault(self, mock_app):
        """Test action_notes when a vault is selected."""
        screen = HomeScreen()
        type(screen).app = PropertyMock(return_value=mock_app)
        mock_app.last_vault_id = "v1"
        mock_app.last_vault_name = "V1"

        screen.action_notes()

        assert mock_app.push_screen.called
        args = mock_app.push_screen.call_args[0]
        assert isinstance(args[0], NoteExplorerScreen)

    def test_action_graph_no_vault(self, mock_app):
        """Test action_graph when no vault is selected."""
        screen = HomeScreen()
        type(screen).app = PropertyMock(return_value=mock_app)
        mock_app.last_vault_id = None

        screen.action_graph()

        mock_app.notify.assert_called_once()
        mock_app.push_screen.assert_called_once_with("vaults")

    def test_action_graph_with_vault(self, mock_app):
        """Test action_graph when a vault is selected."""
        screen = HomeScreen()
        type(screen).app = PropertyMock(return_value=mock_app)
        mock_app.last_vault_id = "v1"
        mock_app.last_vault_name = "V1"

        screen.action_graph()

        assert mock_app.push_screen.called
        args = mock_app.push_screen.call_args[0]
        assert isinstance(args[0], GraphVisualizerScreen)

    def test_action_stats_no_vault(self, mock_app):
        """Test action_stats when no vault is selected."""
        screen = HomeScreen()
        type(screen).app = PropertyMock(return_value=mock_app)
        mock_app.last_vault_id = None

        screen.action_stats()

        mock_app.notify.assert_called_once()
        mock_app.push_screen.assert_called_once_with("vaults")

    def test_action_stats_with_vault(self, mock_app):
        """Test action_stats when a vault is selected."""
        screen = HomeScreen()
        type(screen).app = PropertyMock(return_value=mock_app)
        mock_app.last_vault_id = "v1"
        mock_app.last_vault_name = "V1"

        screen.action_stats()

        assert mock_app.push_screen.called
        args = mock_app.push_screen.call_args[0]
        assert isinstance(args[0], StatisticsDashboardScreen)

    def test_action_help(self, mock_app):
        """Test action_help pushes help screen."""
        screen = HomeScreen()
        type(screen).app = PropertyMock(return_value=mock_app)

        screen.action_help()

        # Should push a HelpScreen instance
        assert mock_app.push_screen.called
        args = mock_app.push_screen.call_args[0]
        assert isinstance(args[0], HelpScreen)

    def test_action_quit(self, mock_app):
        """Test action_quit exits the application."""
        screen = HomeScreen()
        type(screen).app = PropertyMock(return_value=mock_app)

        screen.action_quit()

        mock_app.exit.assert_called_once()


# ==============================================================================
# HelpScreen Tests
# ==============================================================================

class TestHelpScreen:
    """Tests for HelpScreen."""

    def test_help_screen_initialization(self):
        """Test that HelpScreen can be initialized."""
        screen = HelpScreen()
        assert screen is not None

    def test_help_screen_bindings(self):
        """Test that HelpScreen has correct key bindings."""
        bindings = {b.key: b.action for b in HelpScreen.BINDINGS}

        assert "escape" in bindings
        assert bindings["escape"] == "dismiss"

        assert "q" in bindings
        assert bindings["q"] == "dismiss"

    def test_help_screen_help_text(self):
        """Test that help text is generated."""
        screen = HelpScreen()
        text = screen._get_help_text()

        assert "Keyboard Shortcuts" in text
        assert "Navigation" in text
        assert "Global Actions" in text
        assert "Main Menu" in text
        assert "Features" in text

    def test_help_text_includes_navigation_shortcuts(self):
        """Test that help text includes navigation shortcuts."""
        screen = HelpScreen()
        text = screen._get_help_text()

        assert "↑↓" in text or "k/j" in text
        assert "Enter" in text
        assert "Esc" in text

    def test_help_text_includes_menu_shortcuts(self):
        """Test that help text includes main menu shortcuts."""
        screen = HelpScreen()
        text = screen._get_help_text()

        assert "v" in text.lower()  # vaults
        assert "n" in text.lower()  # notes
        assert "g" in text.lower()  # graph
        assert "s" in text.lower()  # stats

    def test_action_dismiss(self, mock_app):
        """Test action_dismiss pops the screen."""
        screen = HelpScreen()
        type(screen).app = PropertyMock(return_value=mock_app)

        screen.action_dismiss()

        mock_app.pop_screen.assert_called_once()


# ==============================================================================
# PlaceholderScreen Tests
# ==============================================================================

class TestPlaceholderScreen:
    """Tests for PlaceholderScreen."""

    def test_placeholder_screen_initialization(self):
        """Test that PlaceholderScreen can be initialized."""
        screen = PlaceholderScreen("Test Feature")
        assert screen is not None
        assert screen.screen_title == "Test Feature"

    def test_placeholder_screen_with_name(self):
        """Test PlaceholderScreen with custom name."""
        screen = PlaceholderScreen("Test Feature", name="test")
        assert screen.screen_title == "Test Feature"
        # Note: screen.name is set by Textual, not directly accessible

    def test_placeholder_screen_bindings(self):
        """Test that PlaceholderScreen has correct key bindings."""
        bindings = {b.key: b.action for b in PlaceholderScreen.BINDINGS}

        assert "escape" in bindings
        assert bindings["escape"] == "back"

        assert "q" in bindings
        assert bindings["q"] == "quit"

    def test_action_back(self, mock_app):
        """Test action_back pops the screen."""
        screen = PlaceholderScreen("Test")
        type(screen).app = PropertyMock(return_value=mock_app)

        screen.action_back()

        mock_app.pop_screen.assert_called_once()

    def test_action_quit(self, mock_app):
        """Test action_quit exits the application."""
        screen = PlaceholderScreen("Test")
        type(screen).app = PropertyMock(return_value=mock_app)

        screen.action_quit()

        mock_app.exit.assert_called_once()


# ==============================================================================
# ObsidianTUI Tests
# ==============================================================================

class TestObsidianTUI:
    """Tests for main ObsidianTUI application."""

    def test_tui_app_initialization(self):
        """Test that ObsidianTUI can be initialized."""
        app = ObsidianTUI()
        assert app is not None

    def test_tui_app_title(self):
        """Test that TUI has correct title."""
        assert ObsidianTUI.TITLE == "Obsidian CLI Ops"

    def test_tui_app_screens(self):
        """Test that TUI has correct screens registered."""
        screens = ObsidianTUI.SCREENS

        assert "home" in screens
        assert screens["home"] == HomeScreen

        assert "vaults" in screens
        # Note: VaultBrowserScreen is imported in the SCREENS dict

    def test_tui_app_has_css(self):
        """Test that TUI has CSS defined."""
        assert hasattr(ObsidianTUI, 'CSS')
        assert len(ObsidianTUI.CSS) > 0

    def test_tui_css_includes_screen_styles(self):
        """Test that CSS includes screen styles."""
        css = ObsidianTUI.CSS

        assert "Screen" in css
        assert "Header" in css
        assert "Footer" in css

    def test_tui_css_includes_home_styles(self):
        """Test that CSS includes home screen styles."""
        css = ObsidianTUI.CSS

        assert "#home-container" in css
        assert "#welcome" in css
        assert "#menu" in css

    def test_tui_css_includes_help_styles(self):
        """Test that CSS includes help screen styles."""
        css = ObsidianTUI.CSS

        assert "#help-container" in css
        assert "#help-content" in css

    def test_tui_css_includes_placeholder_styles(self):
        """Test that CSS includes placeholder screen styles."""
        css = ObsidianTUI.CSS

        assert "#placeholder-container" in css
        assert "#placeholder-content" in css


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestIntegration:
    """Integration tests for TUI app navigation."""

    def test_all_screens_are_importable(self):
        """Test that all screen classes can be imported."""
        from tui.app import HomeScreen, HelpScreen, PlaceholderScreen
        from tui.screens.vaults import VaultBrowserScreen
        from tui.screens.notes import NoteExplorerScreen
        from tui.screens.graph import GraphVisualizerScreen

        assert HomeScreen is not None
        assert HelpScreen is not None
        assert PlaceholderScreen is not None
        assert VaultBrowserScreen is not None
        assert NoteExplorerScreen is not None
        assert GraphVisualizerScreen is not None

    def test_placeholder_screen_factory(self):
        """Test that placeholder screen can be created via lambda."""
        factory = lambda: PlaceholderScreen("Statistics Dashboard", name="stats")
        screen = factory()

        assert isinstance(screen, PlaceholderScreen)
        assert screen.screen_title == "Statistics Dashboard"