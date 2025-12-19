"""
Vault Browser Screen

Features on--demand, non-blocking scanning of vaults with real-time progress.
"""
import asyncio
from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, DataTable, Static, ProgressBar
from textual.containers import Container, Vertical
from textual.binding import Binding
from datetime import datetime
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.vault_manager import VaultManager
from core.graph_analyzer import GraphAnalyzer
from core.models import Vault


class VaultBrowserScreen(Screen):
    """A screen for browsing and managing Obsidian vaults."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", show=True),
        Binding("d", "discover_vaults", "Discover", show=True),
        Binding("r", "refresh_vaults", "Refresh", show=True),
    ]

    CSS_PATH = "../styles/vault_browser.css"

    def __init__(self):
        super().__init__()
        self.vault_manager = VaultManager() # Ensures production DB is used
        self.graph_analyzer = GraphAnalyzer()
        self.vaults: List[Vault] = []
        self.scanning_vault_id: Optional[str] = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("[bold cyan]📁 Vault Browser[/]", id="title"),
            DataTable(id="vault-table"),
            id="vault-container"
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_column("Status", width=12)
        table.add_column("Name", width=30)
        table.add_column("Path", width=60)
        table.add_column("Notes", width=10)
        self.refresh_vaults()

    def action_refresh_vaults(self) -> None:
        self.refresh_vaults()
        self.notify("Vault list refreshed.")

    @work(exclusive=True, group="discovery")
    async def action_discover_vaults(self) -> None:
        self.notify("Starting vault discovery...")
        try:
            default_path = Path.home() / "Library" / "Mobile Documents" / "iCloud~md~obsidian" / "Documents"
            if not default_path.exists():
                default_path = Path.home() / "Documents"

            discovered = self.vault_manager.discover_vaults(str(default_path))
            new_vaults = 0
            for path in discovered:
                if not self.vault_manager.get_vault_by_path(path):
                    self.vault_manager.register_vault(path)
                    new_vaults += 1
            
            if new_vaults > 0:
                self.notify(f"Discovered {new_vaults} new vault(s).")
                self.refresh_vaults()
            else:
                self.notify("No new vaults found.")
        except Exception as e:
            self.notify(f"Discovery failed: {e}", severity="error")

    def refresh_vaults(self) -> None:
        table = self.query_one(DataTable)
        current_cursor = table.cursor_row
        table.clear()
        self.vaults = self.vault_manager.list_vaults()

        if not self.vaults:
            table.add_row("[dim]No vaults found. Press 'd' to discover.[/]")
            return

        for vault in self.vaults:
            status = "[green]✓ Scanned[/]" if vault.last_scanned else "[yellow]⊘ Unscanned[/]"
            if self.scanning_vault_id == vault.id:
                status = "[cyan]◉ Scanning...[/]"
            
            table.add_row(status, vault.name, vault.path, str(vault.note_count), key=vault.id)
        
        if current_cursor < len(self.vaults):
            table.cursor_row = current_cursor

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        vault_id = event.row_key.value
        selected_vault = self.vault_manager.get_vault(vault_id)

        if not selected_vault:
            return

        if self.scanning_vault_id:
            self.notify("A scan is already in progress.", severity="warning")
            return

        if not selected_vault.last_scanned:
            self.scan_vault(selected_vault)
        else:
            self.app.last_vault_id = selected_vault.id
            self.app.last_vault_name = selected_vault.name
            from .notes import NoteExplorerScreen
            self.app.push_screen(NoteExplorerScreen(vault_id=selected_vault.id, vault_name=selected_vault.name))

    @work(exclusive=True, group="scanning")
    async def scan_vault(self, vault: Vault) -> None:
        self.scanning_vault_id = vault.id
        self.refresh_vaults()

        progress_bar = self.app.query_one("#scan-progress", expect_type=ProgressBar)
        progress_bar.display = True

        async def progress_callback(current, total):
            if total > 0:
                progress_bar.update(progress=current, total=total)

        try:
            await self.vault_manager.scan_vault(vault.path, progress_callback=progress_callback)
            self.notify(f"Scan complete for '{vault.name}'.")
        except Exception as e:
            self.notify(f"Scan failed: {e}", severity="error")
        finally:
            self.scanning_vault_id = None
            progress_bar.display = False
            self.refresh_vaults()

    def action_quit(self) -> None:
        self.app.exit()

class VaultContainer(Container):
    def compose(self) -> ComposeResult:
        yield VaultBrowserScreen()
        yield ProgressBar(id="scan-progress", total=100, show_eta=False)