"""
Note Explorer Screen

Interactive note browser for exploring notes within a vault with search,
filtering, preview, and metadata display.
"""

from pathlib import Path
from datetime import datetime
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, DataTable, Static, Input
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.vault_manager import VaultManager
from core.graph_analyzer import GraphAnalyzer


class NoteExplorerScreen(Screen):
    """Note explorer screen with searchable note list and preview pane."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("enter", "view_note", "View", show=True),
        Binding("/", "focus_search", "Search", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("s", "toggle_sort", "Sort", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    CSS = """
    NoteExplorerScreen {
        background: $surface;
    }

    #note-container {
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

    #search-bar {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    #search-box {
        width: 1fr;
        margin-right: 2;
    }

    #result-count {
        width: auto;
        color: $accent;
    }

    #main-area {
        width: 100%;
        height: 1fr;
    }

    #note-table {
        width: 50%;
        height: 1fr;
        border: solid $primary;
    }

    #detail-area {
        width: 50%;
        height: 1fr;
        padding: 0 2;
    }

    #preview-pane {
        width: 100%;
        height: 70%;
        padding: 1 2;
        border: solid $accent;
        background: $panel;
        overflow-y: auto;
    }

    #metadata-pane {
        width: 100%;
        height: 30%;
        padding: 1 2;
        margin-top: 1;
        border: solid $primary;
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

    def __init__(self, vault_id: str, vault_name: str):
        """Initialize note explorer with vault context."""
        super().__init__()
        self.vault_id = vault_id
        self.vault_name = vault_name
        self.vault_manager = VaultManager()
        self.graph_analyzer = GraphAnalyzer()
        self.all_notes = []          # Full dataset
        self.filtered_notes = []     # Search results
        self.selected_note = None
        self.current_sort = "title"  # Default sort

    def compose(self) -> ComposeResult:
        """Create child widgets for the note explorer screen."""
        yield Header()
        yield Container(
            Static(f"[bold cyan]📝 {self.vault_name} - Notes[/]", id="title"),
            Horizontal(
                Input(placeholder="Search notes...", id="search-box"),
                Static("0 notes", id="result-count"),
                id="search-bar"
            ),
            Horizontal(
                # Left: Note list
                DataTable(id="note-table"),
                # Right: Preview + metadata
                Vertical(
                    Static("", id="preview-pane"),
                    Static("", id="metadata-pane"),
                    id="detail-area"
                ),
                id="main-area"
            ),
            id="note-container"
        )
        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted to the app."""
        # Verify vault exists
        vault = self.vault_manager.get_vault(self.vault_id)
        if not vault:
            self.notify(
                "Vault not found in database",
                severity="error",
                timeout=5
            )
            self.app.pop_screen()
            return

        # Configure DataTable
        table = self.query_one("#note-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_column("Title", width=40)
        table.add_column("Words", width=8)
        table.add_column("Links", width=8)
        table.add_column("Tags", width=12)
        table.add_column("Modified", width=20)

        # Load data
        self.refresh_data()

    def refresh_data(self) -> None:
        """Load notes from database and populate table."""
        try:
            # Load all notes using VaultManager
            self.all_notes = self.vault_manager.get_notes(vault_id=self.vault_id)

            # Apply current sort (in-memory)
            self.all_notes = self._sort_notes(self.all_notes, self.current_sort)

            # Initially, show all notes
            self.filtered_notes = self.all_notes

            # Show warning for large vaults
            if len(self.all_notes) > 1000:
                self.notify(
                    f"Large vault ({len(self.all_notes)} notes). This may take a moment.",
                    severity="information",
                    timeout=3
                )

            self.update_table()
            self.update_result_count()

        except Exception as e:
            self.notify(f"Database error: {e}", severity="error")
            self.all_notes = []
            self.filtered_notes = []

    def _sort_notes(self, notes: list, sort_by: str) -> list:
        """Sort notes in-memory by specified field."""
        if sort_by == "title":
            return sorted(notes, key=lambda n: n.title.lower())
        elif sort_by == "word_count":
            return sorted(notes, key=lambda n: n.word_count, reverse=True)
        elif sort_by == "modified_at":
            return sorted(notes, key=lambda n: n.modified_at or '', reverse=True)
        else:
            return notes

    def update_table(self) -> None:
        """Update the note list table."""
        table = self.query_one("#note-table", DataTable)
        table.clear()

        # Empty state handling
        if not self.filtered_notes:
            table.add_row(
                "[dim]No notes found[/]",
                "",
                "",
                "",
                "",
                key="empty"
            )
            return

        for note in self.filtered_notes:
            # Get graph metrics using GraphAnalyzer
            metrics = self.graph_analyzer.get_note_metrics(note.id)
            if metrics:
                out_links = metrics.out_degree
                in_links = metrics.in_degree
            else:
                out_links = in_links = 0

            # Get tags from note object (note: tags may not be populated from DB)
            # For now, we'll use the database directly for tags
            # TODO: Add tags to VaultManager.get_notes()
            from db_manager import DatabaseManager
            db = DatabaseManager()
            tags = db.get_note_tags(note.id)

            # Truncate long titles
            title = note.title
            if len(title) > 40:
                title = title[:37] + "..."

            # Format timestamp
            modified = self._format_datetime(note.modified_at)

            table.add_row(
                title,
                str(note.word_count),
                f"{out_links}→ {in_links}←",
                ", ".join(tags[:2]) + ("..." if len(tags) > 2 else "") if tags else "-",
                modified,
                key=str(note.id)
            )

    def update_result_count(self) -> None:
        """Update the search result count display."""
        count_widget = self.query_one("#result-count", Static)
        count = len(self.filtered_notes)
        total = len(self.all_notes)
        count_widget.update(f"[cyan]{count}[/] / {total} notes")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle real-time search filtering."""
        if event.input.id == "search-box":
            query = event.value.strip().lower()

            if not query:
                # No search - show all
                self.filtered_notes = self.all_notes
            else:
                # Filter by title (case-insensitive)
                self.filtered_notes = [
                    note for note in self.all_notes
                    if query in note.title.lower()
                ]

            self.update_table()
            self.update_result_count()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection from DataTable."""
        # Get row key (unique identifier)
        note_id = event.row_key.value

        # Handle empty state
        if note_id == "empty":
            return

        # Find corresponding note
        self.selected_note = None
        for note in self.filtered_notes:
            if str(note.id) == note_id:
                self.selected_note = note
                break

        # Update dependent widgets
        if self.selected_note:
            self.show_preview()
            self.show_metadata()

    def show_preview(self) -> None:
        """Display note content preview."""
        preview_pane = self.query_one("#preview-pane", Static)

        if not self.selected_note:
            preview_pane.update("[dim]No note selected[/]")
            return

        # Get vault using VaultManager
        vault = self.vault_manager.get_vault(self.vault_id)
        if not vault:
            preview_pane.update("[red]Error: Vault not found[/]")
            return

        # Construct full path to note
        note_path = Path(vault.path) / self.selected_note.path

        try:
            # Read markdown file from disk
            with open(note_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Empty file handling
            if len(content.strip()) == 0:
                preview_pane.update("[dim]📄 Empty note[/]")
                return

            # Show first 20 lines
            lines = content.split('\n')[:20]
            preview_text = '\n'.join(lines)

            # Add truncation indicator if needed
            if len(content.split('\n')) > 20:
                preview_text += "\n\n[dim]...[/]"

            preview_pane.update(
                f"[bold cyan]╭─ Preview ──────────────────────────────╮[/]\n"
                f"{preview_text}\n"
                f"[bold cyan]╰────────────────────────────────────────╯[/]"
            )

        except FileNotFoundError:
            preview_pane.update(
                "[yellow]⚠️  File not found[/]\n"
                "[dim]This note may have been moved or deleted.\n"
                "Try refreshing the vault scan.[/]"
            )
        except PermissionError:
            preview_pane.update("[red]❌ Permission denied[/]")
        except UnicodeDecodeError:
            preview_pane.update("[red]❌ Unable to read file (encoding issue)[/]")
        except Exception as e:
            preview_pane.update(f"[red]Error reading file: {e}[/]")

    def show_metadata(self) -> None:
        """Display note metadata."""
        metadata_pane = self.query_one("#metadata-pane", Static)

        if not self.selected_note:
            metadata_pane.update("")
            return

        # Get detailed info using database (for links and tags not in core layer yet)
        note = self.selected_note
        from db_manager import DatabaseManager
        db = DatabaseManager()
        out_links = db.get_outgoing_links(note.id)
        in_links = db.get_incoming_links(note.id)
        tags = db.get_note_tags(note.id)

        # Get metrics using GraphAnalyzer
        metrics = self.graph_analyzer.get_note_metrics(note.id)

        # Build metadata display
        metadata_text = f"""[bold cyan]╭─ Metadata ─────────────────────────────╮[/]
[cyan]Path:[/] {note.path}
[cyan]Words:[/] {note.word_count} | [cyan]Chars:[/] {len(note.content) if note.content else 0}
[cyan]Modified:[/] {self._format_datetime(note.modified_at)}

[bold]🔗 Links:[/]
  → Outgoing: {len(out_links)}
  ← Incoming: {len(in_links)}

[bold]🏷️ Tags:[/]
  {', '.join(tags) if tags else '[dim]No tags[/]'}
"""

        # Add graph metrics if available
        if metrics:
            metadata_text += f"""
[bold]📊 Graph Metrics:[/]
  PageRank: {metrics.pagerank:.4f}
  Centrality: {metrics.betweenness_centrality:.4f}
"""

        metadata_text += "[bold cyan]╰────────────────────────────────────────╯[/]"
        metadata_pane.update(metadata_text)

    # Action methods (bound to keyboard shortcuts)

    def action_back(self) -> None:
        """Go back to vault browser."""
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def action_refresh(self) -> None:
        """Refresh note list."""
        self.refresh_data()
        self.notify("Notes refreshed", severity="information")

    def action_focus_search(self) -> None:
        """Focus the search input box."""
        search_box = self.query_one("#search-box", Input)
        search_box.focus()

    def action_toggle_sort(self) -> None:
        """Cycle through sort options."""
        sort_options = ["title", "word_count", "modified_at"]
        current_idx = sort_options.index(self.current_sort)
        self.current_sort = sort_options[(current_idx + 1) % len(sort_options)]
        self.refresh_data()
        self.notify(f"Sorted by: {self.current_sort}", severity="information")

    def action_view_note(self) -> None:
        """View full note details (future feature)."""
        if self.selected_note:
            self.notify("Full note view: Coming in future phase", severity="information")

    # Helper methods

    def _format_datetime(self, dt) -> str:
        """Format datetime for display as relative time."""
        from utils import format_relative_time
        result = format_relative_time(dt)
        if result == "Never":
            return "[dim]Unknown[/]"
        return result
