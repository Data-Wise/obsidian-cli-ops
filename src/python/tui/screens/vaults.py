"""
Vault Browser Screen

Interactive vault browser showing all discovered vaults with statistics.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, DataTable, Static
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
from datetime import datetime
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.vault_manager import VaultManager
from core.graph_analyzer import GraphAnalyzer


class VaultBrowserScreen(Screen):
    """Vault browser screen with interactive vault list."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("enter", "select_vault", "Open", show=True),
        Binding("g", "view_graph", "Graph", show=True),
        Binding("s", "view_stats", "Stats", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    CSS = """
    VaultBrowserScreen {
        background: $surface;
    }

    #vault-container {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }

    #title {
        width: 100%;
        text-align: center;
        padding: 1 0;
        color: $primary;
    }

    #content {
        width: 100%;
        height: 1fr;
    }

    #vault-table {
        width: 100%;
        height: 1fr;
        border: solid $primary;
    }

    #details-panel {
        width: 100%;
        height: auto;
        padding: 1 2;
        margin-top: 1;
        border: solid $accent;
        background: $panel;
    }

    #empty-message {
        width: 100%;
        height: 100%;
        content-align: center middle;
        padding: 2;
        color: $warning;
    }
    """

    def __init__(self):
        """Initialize vault browser screen."""
        super().__init__()
        self.vault_manager = VaultManager()
        self.graph_analyzer = GraphAnalyzer()
        self.vaults = []
        self.selected_vault = None

    def compose(self) -> ComposeResult:
        """Create vault browser widgets."""
        yield Header()
        yield Container(
            Static("[bold cyan]📁 Vault Browser[/]", id="title"),
            Vertical(
                DataTable(id="vault-table"),
                Static("", id="details-panel"),
                id="content",
            ),
            id="vault-container",
        )
        yield Footer()

    def _format_last_scan(self, last_scanned) -> str:
        """Format last scan timestamp as relative time.

        Args:
            last_scanned: datetime object or ISO timestamp string

        Returns:
            Human-readable relative time (e.g., "5 minutes ago")
        """
        if not last_scanned:
            return "Never scanned"

        try:
            if isinstance(last_scanned, str):
                dt = datetime.fromisoformat(last_scanned.replace('Z', '+00:00'))
            else:
                dt = last_scanned

            now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
            delta = now - dt

            seconds = delta.total_seconds()
            if seconds < 60:
                return "Just now"
            elif seconds < 3600:
                minutes = int(seconds / 60)
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            elif seconds < 86400:
                hours = int(seconds / 3600)
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            else:
                days = int(seconds / 86400)
                return f"{days} day{'s' if days > 1 else ''} ago"
        except:
            return str(last_scanned)

    def update_header_timestamp(self):
        """Update header with latest scan timestamp."""
        if self.selected_vault:
            last_scan = self.selected_vault.last_scanned
            scan_text = self._format_last_scan(last_scan)
            title = f"[bold cyan]📁 Vault Browser[/]  [dim]Last scan: {scan_text}[/]"
        else:
            title = "[bold cyan]📁 Vault Browser[/]"

        title_widget = self.query_one("#title", Static)
        title_widget.update(title)

    def on_mount(self) -> None:
        """Set up the vault table when screen is mounted."""
        table = self.query_one("#vault-table", DataTable)

        # Configure table
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Add columns
        table.add_column("ID", width=6)
        table.add_column("Name", width=30)
        table.add_column("Path", width=50)
        table.add_column("Notes", width=10)
        table.add_column("Links", width=10)
        table.add_column("Last Scanned", width=20)

        # Load vaults
        self.refresh_vaults()

    def refresh_vaults(self) -> None:
        """Load vaults from database."""
        table = self.query_one("#vault-table", DataTable)

        # Clear existing rows
        table.clear()

        # Query vaults using VaultManager
        self.vaults = self.vault_manager.list_vaults()

        if not self.vaults:
            # Show empty message
            table.add_row("", "", "[dim]No vaults found. Run 'obs discover' to scan for vaults.[/]", "", "", "")
            return

        # Add vault rows
        for vault in self.vaults:
            vault_id = str(vault.id)
            name = vault.name or '[dim]Unnamed[/]'
            path = vault.path

            # Shorten path if too long
            if len(path) > 45:
                path = "..." + path[-42:]

            note_count = str(vault.note_count)
            link_count = str(vault.link_count)

            # Format last scanned time
            last_scanned = vault.last_scanned
            if last_scanned:
                try:
                    if isinstance(last_scanned, str):
                        dt = datetime.fromisoformat(last_scanned)
                    else:
                        dt = last_scanned
                    scanned_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    scanned_str = "[dim]Unknown[/]"
            else:
                scanned_str = "[dim]Never[/]"

            table.add_row(
                vault_id,
                name,
                f"[dim]{path}[/]",
                note_count,
                link_count,
                scanned_str,
                key=vault_id,
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle vault selection."""
        if not self.vaults:
            return

        # Get selected vault ID from row key
        vault_id = event.row_key.value

        # Find vault by ID
        self.selected_vault = None
        for vault in self.vaults:
            if str(vault.id) == vault_id:
                self.selected_vault = vault
                break

        if self.selected_vault:
            self.update_header_timestamp()
            self.show_vault_details()

    def show_vault_details(self) -> None:
        """Display details for selected vault."""
        if not self.selected_vault:
            return

        details_panel = self.query_one("#details-panel", Static)

        vault = self.selected_vault
        vault_id = str(vault.id)

        # Get additional statistics using GraphAnalyzer
        orphans = self.graph_analyzer.get_orphan_notes(vault_id)
        hubs = self.graph_analyzer.get_hub_notes(vault_id, limit=3)
        broken = self.graph_analyzer.get_broken_links(vault_id)

        orphan_count = len(orphans)
        hub_count = len(hubs)
        broken_count = len(broken)
        tag_count = vault.tag_count

        # Build details text
        details = f"""[bold]Vault Details:[/]

[cyan]Name:[/] {vault.name}
[cyan]Path:[/] {vault.path}
[cyan]ID:[/] {vault.id}

[bold]Statistics:[/]
  📝 Notes: {vault.note_count}
  🔗 Links: {vault.link_count}
  🏷️  Tags: {tag_count}
  🔴 Orphans: {orphan_count}
  🌟 Hubs: {hub_count}
  ❌ Broken Links: {broken_count}

[dim]Last Scanned: {vault.last_scanned or 'Never'}[/]

[dim italic]Press Enter to explore this vault's notes[/]
"""

        details_panel.update(details)

    def action_back(self) -> None:
        """Go back to home screen."""
        self.app.pop_screen()

    def action_select_vault(self) -> None:
        """Open selected vault in note explorer."""
        if self.selected_vault:
            # Import at call site to avoid circular imports
            from tui.screens.notes import NoteExplorerScreen

            # Push screen instance directly with parameters
            self.app.push_screen(
                NoteExplorerScreen(
                    vault_id=str(self.selected_vault.id),
                    vault_name=self.selected_vault.name
                )
            )
        else:
            # If no vault selected, show message
            self.notify("Please select a vault first", severity="warning")

    def action_view_graph(self) -> None:
        """Open graph visualizer for selected vault."""
        if self.selected_vault:
            # Import at call site to avoid circular imports
            from tui.screens.graph import GraphVisualizerScreen

            # Push screen instance directly with parameters
            self.app.push_screen(
                GraphVisualizerScreen(
                    vault_id=str(self.selected_vault.id),
                    vault_name=self.selected_vault.name
                )
            )
        else:
            self.notify("Please select a vault first", severity="warning")

    def action_view_stats(self) -> None:
        """Open statistics dashboard for selected vault."""
        if self.selected_vault:
            # Import at call site to avoid circular imports
            from tui.screens.stats import StatisticsDashboardScreen

            # Push screen instance directly with parameters
            self.app.push_screen(
                StatisticsDashboardScreen(
                    vault_id=str(self.selected_vault.id),
                    vault_name=self.selected_vault.name
                )
            )
        else:
            self.notify("Please select a vault first", severity="warning")

    def action_refresh(self) -> None:
        """Refresh vault list."""
        self.refresh_vaults()
        self.notify("Vault list refreshed", severity="information")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
