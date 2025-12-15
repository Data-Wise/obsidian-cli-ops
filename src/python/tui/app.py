#!/usr/bin/env python3
"""
Obsidian CLI Ops - TUI Application

Main TUI application for interactive vault exploration and analysis.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static
from textual.binding import Binding
from textual.screen import Screen

# Import custom screens
from tui.screens.vaults import VaultBrowserScreen


class HomeScreen(Screen):
    """Home screen with main menu."""

    BINDINGS = [
        Binding("v", "vaults", "Vaults", show=True),
        Binding("n", "notes", "Notes", show=True),
        Binding("g", "graph", "Graph", show=True),
        Binding("s", "stats", "Stats", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("?", "help", "Help", show=True),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the home screen."""
        yield Header()
        yield Container(
            Static(self._get_welcome_text(), id="welcome"),
            Vertical(
                Static("📁  [bold cyan]V[/]aults    - Browse all vaults", classes="menu-item"),
                Static("📝  [bold cyan]N[/]otes     - Explore notes", classes="menu-item"),
                Static("🕸️  [bold cyan]G[/]raph     - Visualize knowledge graph", classes="menu-item"),
                Static("📊  [bold cyan]S[/]tats     - View statistics", classes="menu-item"),
                Static("❓  [bold cyan]?[/]         - Show help", classes="menu-item"),
                Static("🚪  [bold cyan]Q[/]uit      - Exit application", classes="menu-item"),
                id="menu",
            ),
            id="home-container",
        )
        yield Footer()

    def _get_welcome_text(self) -> str:
        """Get welcome message."""
        return """[bold cyan]╭─ Obsidian CLI Ops ─────────────────────────────╮[/]
[bold cyan]│[/]  [bold]Interactive Vault Explorer & Analyzer[/]        [bold cyan]│[/]
[bold cyan]│[/]  Version 2.0.0-beta                          [bold cyan]│[/]
[bold cyan]╰─────────────────────────────────────────────────╯[/]

[dim]Select an option below to get started:[/]
"""

    def action_vaults(self) -> None:
        """Navigate to vaults screen."""
        self.app.push_screen("vaults")

    def action_notes(self) -> None:
        """Navigate to notes screen."""
        self.app.push_screen("notes")

    def action_graph(self) -> None:
        """Navigate to graph screen."""
        self.app.push_screen("graph")

    def action_stats(self) -> None:
        """Navigate to stats screen."""
        self.app.push_screen("stats")

    def action_help(self) -> None:
        """Show help modal."""
        self.app.push_screen(HelpScreen())

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()


class HelpScreen(Screen):
    """Help screen showing keyboard shortcuts and usage."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close", show=True),
        Binding("q", "dismiss", "Close", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Create help screen widgets."""
        yield Header()
        yield Container(
            Static(self._get_help_text(), id="help-content"),
            id="help-container",
        )
        yield Footer()

    def _get_help_text(self) -> str:
        """Get help text with keyboard shortcuts."""
        return """[bold cyan]╭─ Help ──────────────────────────────────────────╮[/]
[bold cyan]│[/]  [bold]Keyboard Shortcuts[/]                          [bold cyan]│[/]
[bold cyan]╰─────────────────────────────────────────────────╯[/]

[bold]Navigation:[/]
  [cyan]↑↓[/] or [cyan]k/j[/]      Move up/down
  [cyan]←→[/] or [cyan]h/l[/]      Move left/right
  [cyan]Enter[/]          Select/Open
  [cyan]Esc[/]            Go back

[bold]Global Actions:[/]
  [cyan]?[/]              Show this help
  [cyan]q[/]              Quit application
  [cyan]Ctrl+C[/]         Force quit

[bold]Main Menu:[/]
  [cyan]v[/]              Browse vaults
  [cyan]n[/]              Explore notes
  [cyan]g[/]              View knowledge graph
  [cyan]s[/]              View statistics

[bold]Features:[/]
  • Interactive vault browser
  • Note search and preview
  • Knowledge graph visualization
  • Statistics dashboard
  • ADHD-friendly design

[dim]Press [/][cyan]Esc[/][dim] or [/][cyan]q[/][dim] to close this help screen[/]
"""

    def action_dismiss(self) -> None:
        """Close the help screen."""
        self.app.pop_screen()


class PlaceholderScreen(Screen):
    """Placeholder screen for features under development."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self, title: str, name: str | None = None):
        """Initialize placeholder screen.

        Args:
            title: Screen title to display
            name: Screen name for routing
        """
        super().__init__(name=name)
        self.screen_title = title

    def compose(self) -> ComposeResult:
        """Create placeholder widgets."""
        yield Header()
        yield Container(
            Static(
                f"""[bold cyan]╭─ {self.screen_title} ──────────────────────────────────────╮[/]
[bold cyan]│[/]  [bold yellow]⚠️  Under Construction[/]                     [bold cyan]│[/]
[bold cyan]╰─────────────────────────────────────────────────╯[/]

[dim]This feature is currently being implemented.[/]

[bold]Coming soon:[/]
  • {self.screen_title} functionality
  • Interactive exploration
  • Real-time analysis

[dim]Press [/][cyan]Esc[/][dim] to go back or [/][cyan]q[/][dim] to quit[/]
""",
                id="placeholder-content",
            ),
            id="placeholder-container",
        )
        yield Footer()

    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()


class ObsidianTUI(App):
    """Obsidian CLI Ops TUI Application."""

    CSS = """
    Screen {
        background: $surface;
    }

    Header {
        background: $primary;
        color: $text;
    }

    Footer {
        background: $primary;
    }

    #home-container {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    #welcome {
        width: 100%;
        text-align: center;
        padding: 1 2;
    }

    #menu {
        width: auto;
        height: auto;
        padding: 1 4;
        border: solid $primary;
        background: $panel;
    }

    .menu-item {
        padding: 0 2;
        margin: 0 0 1 0;
    }

    #help-container {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    #help-content {
        width: auto;
        height: auto;
        padding: 2 4;
        border: solid $primary;
        background: $panel;
    }

    #placeholder-container {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    #placeholder-content {
        width: auto;
        height: auto;
        padding: 2 4;
        border: solid $warning;
        background: $panel;
    }
    """

    TITLE = "Obsidian CLI Ops"

    SCREENS = {
        "home": HomeScreen,
        "vaults": VaultBrowserScreen,
        # Note: "notes", "graph", and "stats" screens use direct instantiation (see vaults.py)
    }

    def on_mount(self) -> None:
        """Mount the home screen on startup."""
        self.push_screen("home")


def main():
    """Run the TUI application."""
    app = ObsidianTUI()
    app.run()


if __name__ == "__main__":
    main()
