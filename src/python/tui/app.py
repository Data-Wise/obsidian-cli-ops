#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ProgressBar
from textual.binding import Binding

from tui.screens.home import HomeScreen, HelpScreen
from tui.screens.vaults import VaultBrowserScreen

class ObsidianTUI(App):
    CSS_PATH = "styles/app.css"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True, priority=True),
        Binding("?", "push_screen('help')", "Help", show=True),
    ]

    SCREENS = {
        "vaults": VaultBrowserScreen,
        "help": HelpScreen,
    }

    def __init__(self):
        super().__init__()
        self.last_vault_id = None
        self.last_vault_name = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield ProgressBar(id="scan-progress", total=100, show_eta=False)

    def on_mount(self) -> None:
        self.query_one("#scan-progress").display = False
        self.push_screen(HomeScreen())

    def action_quit(self) -> None:
        self.exit()

if __name__ == "__main__":
    app = ObsidianTUI()
    app.run()
