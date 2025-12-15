"""
Graph Visualizer Screen

Interactive knowledge graph visualization with statistics and ego graph views.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, DataTable, Static
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from db_manager import DatabaseManager
from graph_builder import GraphBuilder


class GraphVisualizerScreen(Screen):
    """Graph visualizer screen with statistics and interactive exploration."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("enter", "view_neighborhood", "Neighborhood", show=True),
        Binding("h", "toggle_hubs", "Hubs", show=True),
        Binding("o", "toggle_orphans", "Orphans", show=True),
        Binding("c", "toggle_clusters", "Clusters", show=True),
        Binding("n", "view_note", "View Note", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    CSS = """
    GraphVisualizerScreen {
        background: $surface;
    }

    #graph-container {
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

    #main-area {
        width: 100%;
        height: 1fr;
    }

    #left-panel {
        width: 40%;
        height: 1fr;
    }

    #stats-panel {
        width: 100%;
        height: auto;
        padding: 1 2;
        margin-bottom: 1;
        border: solid $primary;
        background: $panel;
    }

    #node-table {
        width: 100%;
        height: 1fr;
        border: solid $accent;
    }

    #viz-panel {
        width: 60%;
        height: 1fr;
        padding: 1 2;
        border: solid $primary;
        background: $panel;
        overflow-y: auto;
    }
    """

    def __init__(self, vault_id: str, vault_name: str):
        """Initialize graph visualizer screen.

        Args:
            vault_id: Vault ID to visualize
            vault_name: Vault name for display
        """
        super().__init__()
        self.vault_id = vault_id
        self.vault_name = vault_name
        self.db = DatabaseManager()
        self.builder = GraphBuilder(self.db)
        self.graph = None
        self.current_view = "hubs"
        self.selected_note = None

    def compose(self) -> ComposeResult:
        """Create graph visualizer widgets."""
        yield Header()
        yield Container(
            Static(f"[bold cyan]🕸️  {self.vault_name} - Knowledge Graph[/]", id="title"),
            Horizontal(
                Vertical(
                    Static("", id="stats-panel"),
                    DataTable(id="node-table"),
                    id="left-panel"
                ),
                Static("", id="viz-panel"),
                id="main-area"
            ),
            id="graph-container"
        )
        yield Footer()

    def on_mount(self) -> None:
        """Set up the graph visualizer when screen is mounted."""
        vault = self.db.get_vault(self.vault_id)
        if not vault:
            self.notify("Vault not found", severity="error")
            self.app.pop_screen()
            return

        # Configure node table
        table = self.query_one("#node-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_column("Title", width=30)
        table.add_column("Degree", width=10)
        table.add_column("PageRank", width=12)

        # Load graph and update displays
        self.load_graph()
        self.update_stats()
        self.update_node_list()

    def load_graph(self) -> None:
        """Load graph from database."""
        try:
            self.graph = self.builder.build_graph(self.vault_id)
            if not self.graph or len(self.graph) == 0:
                self.notify("No graph data available", severity="warning")
        except Exception as e:
            self.notify(f"Error loading graph: {e}", severity="error")
            self.graph = None

    def update_stats(self) -> None:
        """Update statistics panel with graph metrics."""
        stats_panel = self.query_one("#stats-panel", Static)

        if not self.graph or len(self.graph) == 0:
            stats_panel.update("[dim]No graph data available[/]")
            return

        import networkx as nx

        num_nodes = len(self.graph)
        num_edges = self.graph.number_of_edges()
        density = nx.density(self.graph)
        degrees = [d for n, d in self.graph.degree()]
        avg_degree = sum(degrees) / len(degrees) if degrees else 0

        # Distribution buckets
        dist = {"0-2": 0, "3-5": 0, "6-10": 0, "11+": 0}
        for d in degrees:
            if d <= 2:
                dist["0-2"] += 1
            elif d <= 5:
                dist["3-5"] += 1
            elif d <= 10:
                dist["6-10"] += 1
            else:
                dist["11+"] += 1

        # Get top hub and orphan count
        hubs = self.db.get_hub_notes(self.vault_id, limit=1)
        orphans = self.db.get_orphaned_notes(self.vault_id)

        # ASCII bar chart function
        def bar(count, total, width=10):
            filled = int(count / total * width) if total > 0 else 0
            return "█" * filled + "░" * (width - filled)

        stats_text = f"""[bold cyan]╭─ Graph Statistics ──────────────╮[/]
[bold cyan]│[/] Notes: {num_nodes:,}
[bold cyan]│[/] Links: {num_edges:,}
[bold cyan]│[/] Density: {density:.4f}
[bold cyan]│[/] Avg Degree: {avg_degree:.1f}
[bold cyan]│[/]
[bold cyan]│[/] [bold]📈 Degree Distribution:[/]
[bold cyan]│[/] 0-2:  {bar(dist["0-2"], num_nodes)} {dist["0-2"] / num_nodes * 100:.0f}%
[bold cyan]│[/] 3-5:  {bar(dist["3-5"], num_nodes)} {dist["3-5"] / num_nodes * 100:.0f}%
[bold cyan]│[/] 6-10: {bar(dist["6-10"], num_nodes)} {dist["6-10"] / num_nodes * 100:.0f}%
[bold cyan]│[/] 11+:  {bar(dist["11+"], num_nodes)} {dist["11+"] / num_nodes * 100:.0f}%
[bold cyan]│[/]
[bold cyan]│[/] [bold]🌟 Top Hub:[/] {hubs[0]['title'][:20] if hubs else 'N/A'}
[bold cyan]│[/] [bold]🔴 Orphans:[/] {len(orphans)} ({len(orphans) / num_nodes * 100:.1f}%)
[bold cyan]╰──────────────────────────────────╯[/]"""

        stats_panel.update(stats_text)

    def update_node_list(self) -> None:
        """Update node list DataTable based on current view."""
        table = self.query_one("#node-table", DataTable)
        table.clear()

        if self.current_view == "hubs":
            nodes = self.db.get_hub_notes(self.vault_id, limit=20)
            for node in nodes:
                table.add_row(
                    node['title'][:30],
                    str(node.get('total_degree', 0)),
                    f"{node.get('pagerank', 0):.4f}",
                    key=str(node['id'])
                )

        elif self.current_view == "orphans":
            nodes = self.db.get_orphaned_notes(self.vault_id)
            for node in nodes:
                metrics = self.db.get_graph_metrics(node['id'])
                table.add_row(
                    node['title'][:30],
                    "0",
                    f"{metrics.get('pagerank', 0):.4f}" if metrics else "0.0000",
                    key=str(node['id'])
                )

        elif self.current_view == "clusters":
            # Future: implement cluster view
            table.add_row("Coming soon", "", "", key="empty")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle node selection from table."""
        node_id = event.row_key.value
        if node_id != "empty":
            self.selected_note = node_id
            self.show_ego_graph()

    def render_ascii_graph_simple(self, graph) -> str:
        """Simple indented list representation of graph.

        Args:
            graph: NetworkX graph to render

        Returns:
            ASCII art string representation
        """
        if not graph or len(graph) == 0:
            return "[dim]No nodes to display[/]"

        if len(graph) > 30:
            return "[yellow]Graph too large (>30 nodes).\nSelect a node to view neighborhood.[/]"

        lines = []
        for node in list(graph.nodes())[:20]:  # Limit display
            title = graph.nodes[node].get('title', str(node))[:30]
            successors = list(graph.successors(node))

            if successors:
                lines.append(f"[bold]● {title}[/]")
                for succ in successors[:5]:
                    succ_title = graph.nodes[succ].get('title', str(succ))[:25]
                    lines.append(f"  └─→ {succ_title}")
                if len(successors) > 5:
                    lines.append(f"  [dim]... +{len(successors) - 5} more[/]")
            else:
                lines.append(f"● {title}")

        return "\n".join(lines)

    def show_ego_graph(self) -> None:
        """Display ego graph for selected note."""
        if not self.selected_note:
            return

        viz_panel = self.query_one("#viz-panel", Static)
        note = self.db.get_note(self.selected_note)

        if not note:
            viz_panel.update("[red]Note not found[/]")
            return

        # Get 1-hop neighborhood
        ego_graph = self.builder.get_note_neighborhood(self.selected_note, depth=1)

        if not ego_graph or len(ego_graph) == 0:
            viz_panel.update(
                f"[bold cyan]╭─ {note['title'][:30]} ──────────────╮[/]\n"
                f"[dim]No connected notes (orphan)[/]\n"
                f"[bold cyan]╰────────────────────────────────╯[/]"
            )
            return

        # Render ASCII graph
        ascii_graph = self.render_ascii_graph_simple(ego_graph)

        # Get metrics
        metrics = self.db.get_graph_metrics(self.selected_note)

        in_degree = metrics.get('in_degree', 0) if metrics else 0
        out_degree = metrics.get('out_degree', 0) if metrics else 0
        pagerank = metrics.get('pagerank', 0) if metrics else 0

        viz_text = f"""[bold cyan]╭─ Neighborhood: {note['title'][:30]} ──╮[/]

{ascii_graph}

[bold]Metrics:[/]
• In-degree: {in_degree}
• Out-degree: {out_degree}
• PageRank: {pagerank:.4f}

[dim]Press [/][cyan]n[/][dim] to view full note[/]
[bold cyan]╰────────────────────────────────────╯[/]"""

        viz_panel.update(viz_text)

    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def action_refresh(self) -> None:
        """Refresh graph data."""
        self.load_graph()
        self.update_stats()
        self.update_node_list()
        self.notify("Graph refreshed", severity="information")

    def action_toggle_hubs(self) -> None:
        """Toggle to hub notes view."""
        self.current_view = "hubs"
        self.update_node_list()
        self.notify("Viewing: Hub Notes", severity="information")

    def action_toggle_orphans(self) -> None:
        """Toggle to orphan notes view."""
        self.current_view = "orphans"
        self.update_node_list()
        self.notify("Viewing: Orphaned Notes", severity="information")

    def action_toggle_clusters(self) -> None:
        """Toggle to cluster view."""
        self.current_view = "clusters"
        self.update_node_list()
        self.notify("Viewing: Clusters (coming soon)", severity="information")

    def action_view_neighborhood(self) -> None:
        """View neighborhood for selected note."""
        if self.selected_note:
            self.show_ego_graph()
        else:
            self.notify("No note selected", severity="warning")

    def action_view_note(self) -> None:
        """Navigate to note explorer for selected note."""
        if not self.selected_note:
            self.notify("No note selected", severity="warning")
            return

        from tui.screens.notes import NoteExplorerScreen
        vault = self.db.get_vault(self.vault_id)
        self.app.push_screen(
            NoteExplorerScreen(vault_id=self.vault_id, vault_name=vault['name'])
        )
