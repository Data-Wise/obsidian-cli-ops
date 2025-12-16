"""Statistics Dashboard Screen for TUI."""

import json
from datetime import datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding

from core.vault_manager import VaultManager
from core.graph_analyzer import GraphAnalyzer
from db_manager import DatabaseManager  # Still needed for some specific queries


class StatisticsDashboardScreen(Screen):
    """Statistics dashboard screen showing vault analytics."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("tab", "cycle_view", "Next View", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("e", "export", "Export", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    CSS = """
    StatisticsDashboardScreen {
        background: $surface;
    }

    #stats-container {
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
        width: 35%;
        height: 1fr;
        border: solid $primary;
        background: $panel;
        padding: 1 2;
        overflow-y: auto;
    }

    #right-panel {
        width: 65%;
        height: 1fr;
        padding-left: 1;
    }

    #view-title {
        width: 100%;
        padding: 1 2;
        border: solid $primary;
        background: $panel;
        margin-bottom: 1;
    }

    #view-content {
        width: 100%;
        height: 1fr;
        border: solid $accent;
        background: $panel;
        padding: 1 2;
        overflow-y: auto;
    }
    """

    def __init__(self, vault_id: str, vault_name: str):
        """Initialize statistics dashboard.

        Args:
            vault_id: Vault ID
            vault_name: Vault name for display
        """
        super().__init__()
        self.vault_id = vault_id
        self.vault_name = vault_name
        self.vault_manager = VaultManager()
        self.graph_analyzer = GraphAnalyzer()
        self.db = DatabaseManager()  # Still needed for some specific queries
        self.current_view = "tags"  # tags, distribution, history

    def compose(self) -> ComposeResult:
        """Create dashboard layout."""
        yield Header()
        yield Container(
            Static(f"[bold cyan]📊  {self.vault_name} - Statistics Dashboard[/]", id="title"),
            Horizontal(
                Static("", id="left-panel"),
                Vertical(
                    Static("", id="view-title"),
                    Static("", id="view-content"),
                    id="right-panel"
                ),
                id="main-area"
            ),
            id="stats-container"
        )
        yield Footer()

    def on_mount(self) -> None:
        """Load data when screen mounts."""
        vault = self.vault_manager.get_vault(self.vault_id)
        if not vault:
            self.notify("Vault not found", severity="error")
            self.app.pop_screen()
            return

        self.update_overview()
        self.update_view()

    def action_back(self) -> None:
        """Return to previous screen."""
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Exit application."""
        self.app.exit()

    def action_refresh(self) -> None:
        """Refresh all data."""
        self.update_overview()
        self.update_view()
        self.notify("Dashboard refreshed", severity="information")

    def action_cycle_view(self) -> None:
        """Cycle through views."""
        views = ["tags", "distribution", "history"]
        current_idx = views.index(self.current_view)
        self.current_view = views[(current_idx + 1) % len(views)]
        self.update_view()

        view_names = {"tags": "Tag Analytics", "distribution": "Link Distribution", "history": "Scan History"}
        self.notify(f"View: {view_names[self.current_view]}", severity="information")

    def action_export(self) -> None:
        """Export statistics to JSON file."""
        try:
            # Collect all data
            vault = self.vault_manager.get_vault(self.vault_id)
            tags = self.db.get_vault_tag_stats(self.vault_id, limit=100)  # More than display
            distribution = self.db.get_link_distribution(self.vault_id)
            history = self.db.get_scan_history(self.vault_id, limit=50)  # More history
            orphans = self.graph_analyzer.get_orphan_notes(self.vault_id)
            hubs = self.graph_analyzer.get_hub_notes(self.vault_id, limit=100)
            broken = self.graph_analyzer.get_broken_links(self.vault_id)

            note_count = vault.note_count

            # Build export data structure
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "vault": {
                    "id": self.vault_id,
                    "name": self.vault_name,
                    "path": vault.path,
                    "note_count": note_count,
                    "link_count": vault.link_count,
                    "last_scanned": vault.last_scanned.isoformat() if vault.last_scanned else '',
                },
                "statistics": {
                    "orphans": {
                        "count": len(orphans),
                        "percentage": len(orphans) / note_count * 100 if note_count > 0 else 0
                    },
                    "hubs": {
                        "count": len(hubs),
                        "percentage": len(hubs) / note_count * 100 if note_count > 0 else 0
                    },
                    "broken_links": {
                        "count": len(broken)
                    },
                },
                "tags": tags,
                "link_distribution": distribution,
                "scan_history": history,
            }

            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            vault_slug = self.vault_name.lower().replace(' ', '_')
            filename = f"stats_{vault_slug}_{timestamp}.json"

            # Default export location (user's Downloads or current directory)
            export_dir = Path.home() / "Downloads"
            if not export_dir.exists():
                export_dir = Path.cwd()

            export_path = export_dir / filename

            # Write JSON file
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self.notify(f"Exported to: {export_path}", severity="information", timeout=5)

        except Exception as e:
            self.notify(f"Export failed: {str(e)}", severity="error")

    def update_overview(self) -> None:
        """Update left panel with vault overview."""
        panel = self.query_one("#left-panel", Static)

        # Get vault data
        vault = self.vault_manager.get_vault(self.vault_id)
        if not vault:
            panel.update("[red]Vault not found[/]")
            return

        # Get statistics using GraphAnalyzer
        orphans = self.graph_analyzer.get_orphan_notes(self.vault_id)
        hubs = self.graph_analyzer.get_hub_notes(self.vault_id, limit=100)
        broken = self.graph_analyzer.get_broken_links(self.vault_id)
        tags = self.db.get_vault_tag_stats(self.vault_id, limit=1)

        note_count = vault.note_count
        link_count = vault.link_count
        tag_count = len(tags) if tags else 0
        orphan_count = len(orphans)
        hub_count = len(hubs)
        broken_count = len(broken)

        # Calculate percentages
        orphan_pct = (orphan_count / note_count * 100) if note_count > 0 else 0
        hub_pct = (hub_count / note_count * 100) if note_count > 0 else 0

        # Last scanned (human-readable relative time)
        from utils import format_relative_time
        last_scan = format_relative_time(vault.last_scanned)

        # Build overview
        content = f"""[bold cyan]╭─ Vault Overview ─────────────────╮[/]
[bold cyan]│[/]
[bold cyan]│[/] [bold]📊 Statistics[/]
[bold cyan]│[/] ────────────────────────────────
[bold cyan]│[/]
[bold cyan]│[/] 📝 Notes:        {note_count:>8,}
[bold cyan]│[/] 🔗 Links:        {link_count:>8,}
[bold cyan]│[/] 🏷️  Tags:         {tag_count:>8}
[bold cyan]│[/]
[bold cyan]│[/] [bold]🔍 Analysis[/]
[bold cyan]│[/] ────────────────────────────────
[bold cyan]│[/]
[bold cyan]│[/] 🔴 Orphans:      {orphan_count:>8} ({orphan_pct:>5.1f}%)
[bold cyan]│[/] 🌟 Hubs:         {hub_count:>8} ({hub_pct:>5.1f}%)
[bold cyan]│[/] ❌ Broken:       {broken_count:>8}
[bold cyan]│[/]
[bold cyan]│[/] [bold]⏰ Last Scanned[/]
[bold cyan]│[/] {last_scan}
[bold cyan]│[/]
[bold cyan]╰────────────────────────────────────╯[/]

[dim]Views:[/]
• [cyan]Tab[/]: Tag Analytics
• [cyan]Tab[/]: Link Distribution
• [cyan]Tab[/]: Scan History

[dim]Actions:[/]
• [cyan]r[/]: Refresh data
• [cyan]Esc[/]: Back to vaults
"""

        panel.update(content)

    def update_tag_view(self) -> None:
        """Update right panel with tag analytics."""
        title_panel = self.query_one("#view-title", Static)
        content_panel = self.query_one("#view-content", Static)

        title_panel.update("[bold cyan]📊 Tag Analytics - Top 20 Tags[/]")

        # Get tag data
        tags = self.db.get_vault_tag_stats(self.vault_id, limit=20)
        vault = self.vault_manager.get_vault(self.vault_id)
        total_notes = vault.note_count

        if not tags or total_notes == 0:
            content_panel.update("[dim]No tags found in this vault[/]")
            return

        # Find max count for scaling bars
        max_count = max(tag['note_count'] for tag in tags)

        # Build content
        lines = []
        lines.append("[bold]Tag                          Notes    %      Distribution[/]")
        lines.append("─" * 70)

        for tag in tags:
            tag_name = tag['tag']
            count = tag['note_count']
            pct = (count / total_notes * 100)

            # Truncate long tag names
            display_name = tag_name if len(tag_name) <= 24 else tag_name[:21] + "..."

            # Create progress bar (scale to max_count)
            bar_width = 20
            filled = int((count / max_count) * bar_width) if max_count > 0 else 0
            bar = "▓" * filled + "░" * (bar_width - filled)

            # Color code by frequency
            if pct >= 10:
                color = "red"
            elif pct >= 5:
                color = "yellow"
            else:
                color = "dim"

            lines.append(f"[{color}]#{display_name:<24}[/] {count:>6,}  {pct:>5.1f}%  [{bar}]")

        lines.append("")
        lines.append(f"[dim]Total tags in vault: {len(tags)}[/]")
        lines.append(f"[dim]Total notes: {total_notes:,}[/]")

        content_panel.update("\n".join(lines))

    def update_distribution_view(self) -> None:
        """Update right panel with link distribution."""
        title_panel = self.query_one("#view-title", Static)
        content_panel = self.query_one("#view-content", Static)

        title_panel.update("[bold cyan]📊 Link Distribution - Degree Analysis[/]")

        # Get distribution
        dist = self.db.get_link_distribution(self.vault_id)
        total = sum(dist.values())

        if total == 0:
            content_panel.update("[dim]No notes in this vault[/]")
            return

        # Calculate stats
        vault = self.vault_manager.get_vault(self.vault_id)
        link_count = vault.link_count
        avg_links = link_count / total if total > 0 else 0

        # Build content
        lines = []
        lines.append("[bold]Degree Range    Notes     %       Distribution[/]")
        lines.append("─" * 70)

        buckets = [
            ("0-2 links", "0-2", "🔴"),
            ("3-5 links", "3-5", "🟡"),
            ("6-10 links", "6-10", "🟢"),
            ("11+ links", "11+", "🔵"),
        ]

        for label, key, emoji in buckets:
            count = dist[key]
            pct = (count / total * 100)

            # Create progress bar
            bar_width = 25
            filled = int((count / total) * bar_width) if total > 0 else 0
            bar = "█" * filled + "░" * (bar_width - filled)

            lines.append(f"{emoji} {label:<12} {count:>6,}  {pct:>5.1f}%  [{bar}]")

        lines.append("")
        lines.append("[bold]Summary[/]")
        lines.append("─" * 70)
        lines.append(f"Total notes:       {total:>8,}")
        lines.append(f"Total links:       {link_count:>8,}")
        lines.append(f"Average links:     {avg_links:>8.1f}")
        lines.append("")
        lines.append("[dim]Legend:[/]")
        lines.append("[dim]  🔴 Low connectivity (0-2)    🟡 Medium (3-5)[/]")
        lines.append("[dim]  🟢 Good connectivity (6-10)  🔵 Highly connected (11+)[/]")

        content_panel.update("\n".join(lines))

    def update_history_view(self) -> None:
        """Update right panel with scan history."""
        title_panel = self.query_one("#view-title", Static)
        content_panel = self.query_one("#view-content", Static)

        title_panel.update("[bold cyan]📊 Scan History - Last 10 Scans[/]")

        # Get history
        history = self.db.get_scan_history(self.vault_id, limit=10)

        if not history:
            content_panel.update("[dim]No scan history available[/]")
            return

        # Build content
        lines = []

        for i, scan in enumerate(history):
            started = scan.get('started_at', '')
            completed = scan.get('completed_at', '')
            status = scan.get('status', 'unknown')
            notes_added = scan.get('notes_added', 0)
            notes_updated = scan.get('notes_updated', 0)
            notes_deleted = scan.get('notes_deleted', 0)
            duration = scan.get('duration_seconds', 0)

            # Format timestamp (human-readable relative time)
            from utils import format_relative_time
            timestamp = format_relative_time(started)

            # Status icon
            status_icon = "✅" if status == "completed" else "❌"

            # Header
            lines.append(f"[bold]{status_icon} Scan #{i+1}[/]  {timestamp}")
            lines.append("─" * 70)

            # Stats
            if notes_added > 0:
                lines.append(f"  ➕ Added:    {notes_added:>6} notes")
            if notes_updated > 0:
                lines.append(f"  ✏️  Updated:  {notes_updated:>6} notes")
            if notes_deleted > 0:
                lines.append(f"  ➖ Deleted:  {notes_deleted:>6} notes")

            lines.append(f"  ⏱️  Duration: {duration:>6.1f}s")
            lines.append("")

        content_panel.update("\n".join(lines))

    def update_view(self) -> None:
        """Update right panel based on current view."""
        if self.current_view == "tags":
            self.update_tag_view()
        elif self.current_view == "distribution":
            self.update_distribution_view()
        elif self.current_view == "history":
            self.update_history_view()
