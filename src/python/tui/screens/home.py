"""
Home and Help screens for the TUI.
"""
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static
from textual.binding import Binding
from textual.screen import Screen

from .notes import NoteExplorerScreen
from .graph import GraphVisualizerScreen
from .stats import StatisticsDashboardScreen

class HomeScreen(Screen):
    """Home screen with main menu."""
    CSS_PATH = "../styles/home.css"

    BINDINGS = [
        Binding("v", "show_vaults", "Vaults"),
        Binding("n", "open_last_vault('notes')", "Notes"),
    ]

    def compose(self) -> ComposeResult:
        yield Container(
            Static("Welcome to Obsidian CLI Ops", id="welcome"),
            Vertical(
                Static("v - Vaults", classes="menu-item"),
                Static("n - Last Vault Notes", classes="menu-item"),
                id="menu",
            ),
            id="home-container",
        )
        
    def action_show_vaults(self) -> None:
        """Switch to the vault browser screen."""
        self.app.push_screen('vaults')

    def action_open_last_vault(self, screen_name: str) -> None:
        """Open a screen for the last used vault."""
        if self.app.last_vault_id:
            if screen_name == "notes":
                self.app.push_screen(NoteExplorerScreen(self.app.last_vault_id, self.app.last_vault_name))
        else:
            self.app.notify("No vault used recently. Please select one.", severity="warning")
            self.app.push_screen('vaults')

class HelpScreen(Screen):
    """A simple help screen."""
    CSS_PATH = "../styles/home.css"
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]
    def compose(self) -> ComposeResult:
        yield Container(Static("This is the help screen."), id="help-content")