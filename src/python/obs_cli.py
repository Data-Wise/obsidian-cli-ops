#!/usr/bin/env python3
"""
Obsidian CLI Ops - Python CLI Entry Point

Main CLI for v2.0 Python functionality:
- Vault discovery and scanning
- Graph analysis and metrics
- Database management
"""

import sys
import asyncio
import argparse
import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from db_manager import DatabaseManager
from core.vault_manager import VaultManager, StalenessResult
from core.graph_analyzer import GraphAnalyzer
from core.exceptions import VaultNotFoundError, ScanError, AnalysisError
from utils import format_relative_time
import config_loader

# Rich console for formatted output
console = Console()


class ObsCLI:
    """Main CLI handler for obs Python commands (presentation layer only)."""

    def __init__(self):
        """Initialize CLI."""
        self.db = DatabaseManager()
        self.vault_manager = VaultManager(self.db)
        self.graph_analyzer = GraphAnalyzer(self.db)

    def _warn_if_stale(self, vault_id: str, threshold_hours: float = 24.0) -> None:
        """Print a warning to stderr if the vault index is older than threshold_hours."""
        try:
            result: StalenessResult = self.vault_manager.check_index_staleness(vault_id, threshold_hours)
            if result.is_stale:
                if result.last_scanned is None:
                    console.print("[yellow]⚠ Index not yet scanned. Run 'obs scan <path>' first.[/]", file=sys.stderr)
                else:
                    age = result.age_hours
                    unit = f"{age:.0f}h" if age < 48 else f"{age / 24:.0f}d"
                    console.print(
                        f"[yellow]⚠ Index is {unit} old — consider running 'obs scan' to refresh.[/]",
                        file=sys.stderr,
                    )
        except Exception:
            pass  # Never let a staleness check break the main command

    def discover(self, root_path: str, scan: bool = False, verbose: bool = False):
        """
        Discover Obsidian vaults in a directory.

        Args:
            root_path: Root directory to search
            scan: Whether to scan discovered vaults
            verbose: Print detailed output
        """
        try:
            vaults = self.vault_manager.discover_vaults(root_path)
        except VaultNotFoundError as e:
            print(f"❌ {e}")
            sys.exit(1)

        if not vaults:
            print("No vaults found.")
            return

        if verbose:
            print(f"\n✓ Found {len(vaults)} vault(s):")
            for vault_path in vaults:
                print(f"  • {vault_path}")

        if scan:
            print(f"\n📂 Scanning {len(vaults)} vault(s)...\n")
            for vault_path in vaults:
                vault_name = Path(vault_path).name
                try:
                    result = asyncio.run(self.vault_manager.scan_vault(vault_path, vault_name))
                    self._print_scan_result(result, verbose)
                    print("")
                except (VaultNotFoundError, ScanError) as e:
                    print(f"❌ Error scanning {vault_name}: {e}\n")

    def scan(self, vault_path: str, vault_name: Optional[str] = None,
             analyze: bool = False, verbose: bool = False):
        """
        Scan a vault and populate database.

        Args:
            vault_path: Path to vault
            vault_name: Optional vault name
            analyze: Whether to run graph analysis after scan
            verbose: Print detailed output
        """
        try:
            # Scan vault using core layer
            result = asyncio.run(self.vault_manager.scan_vault(vault_path, vault_name))

            # Print scan result
            self._print_scan_result(result, verbose)

            # Analyze graph if requested
            if analyze:
                print("")
                self.analyze(result.vault_id, verbose=verbose)

        except (VaultNotFoundError, ScanError) as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    def analyze(self, vault_identifier: str, verbose: bool = False):
        """
        Analyze vault graph and calculate metrics.

        Args:
            vault_identifier: Vault name or ID (full or prefix)
            verbose: Print detailed output
        """
        try:
            # Resolve vault name/prefix to actual ID
            try:
                vault = self.db.get_vault_by_name_or_id(vault_identifier)
            except ValueError as e:
                print(f"❌ {e}")
                sys.exit(1)
            if not vault:
                print(f"❌ Vault not found: {vault_identifier}")
                print(f"  Tip: Run 'obs' to list known vaults")
                print(f"  Tip: Run 'obs discover <path>' to find new vaults")
                sys.exit(1)
            vault_id = vault['id']

            # Run analysis using core layer
            with console.status("Analyzing vault graph..."):
                result = self.graph_analyzer.analyze_vault(vault_id)

            # Print results
            print(f"📊 Graph Analysis: {result['vault_name']}")
            print(f"   Notes: {result['total_notes']}")
            print(f"   Links: {result['total_edges']}")
            print(f"   Density: {result['graph_density']:.4f}")
            print(f"   Clusters: {result['clusters_found']}")

            if verbose:
                # Show additional insights
                print("\n📈 Insights:")

                # Top hubs
                hubs = self.graph_analyzer.get_hub_notes(vault_id, limit=5)
                if hubs:
                    print("\n  🌟 Top Hub Notes:")
                    for hub in hubs:
                        total_degree = hub.get('in_degree', 0) + hub.get('out_degree', 0)
                        print(f"    • {hub['title']} ({total_degree} connections)")

                # Orphans
                orphans = self.graph_analyzer.get_orphan_notes(vault_id)
                if orphans:
                    print(f"\n  🏝️  Orphaned Notes: {len(orphans)}")
                    if len(orphans) <= 10:
                        for orphan in orphans[:5]:
                            print(f"    • {orphan['title']}")

                # Broken links
                broken = self.graph_analyzer.get_broken_links(vault_id)
                if broken:
                    print(f"\n  🔗 Broken Links: {len(broken)}")
                    if len(broken) <= 5:
                        for link in broken[:5]:
                            print(f"    • {link.get('source_title', 'Unknown')} → {link.get('target_path', 'Unknown')}")

        except (VaultNotFoundError, AnalysisError) as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    def stats(self, vault_identifier: Optional[str] = None, verbose: bool = False):
        """
        Show database statistics with Rich panels.

        Args:
            vault_identifier: Optional vault name or ID (full or prefix)
            verbose: Print additional detail (top notes by link count)
        """
        if vault_identifier:
            try:
                vault = self.db.get_vault_by_name_or_id(vault_identifier)
            except ValueError as e:
                console.print(f"[red]❌ {e}[/]")
                sys.exit(1)
            if not vault:
                console.print(f"[red]❌ Vault not found: {vault_identifier}[/]")
                console.print(f"[dim]  Tip: Run 'obs' to list known vaults[/]")
                console.print(f"[dim]  Tip: Run 'obs discover <path>' to find new vaults[/]")
                sys.exit(1)
            vault_id = vault['id']

            notes = self.db.list_notes(vault_id)
            # Count only resolved internal links (excludes broken links)
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM links l
                    JOIN notes n ON l.source_note_id = n.id
                    WHERE l.link_type = 'internal'
                    AND n.vault_id = ?
                """, (vault_id,))
                internal_link_count = cursor.fetchone()[0]
            tag_stats = self.db.get_tag_stats()

            # Graph health
            orphans = self.db.get_orphaned_notes(vault_id)
            hubs = self.db.get_hub_notes(vault_id, limit=10)
            broken = self.db.get_broken_links(vault_id)
            broken_count = sum(b['broken_count'] for b in broken)

            # Build stats content
            links_display = f"{internal_link_count}"
            if broken_count > 0:
                links_display += f" ({broken_count} broken)"
            stats_content = f"""[bold]Path:[/] {vault['path']}
[bold]Last Scanned:[/] {format_relative_time(vault.get('last_scanned'))}

[cyan]Content[/]
  Notes: [bold]{len(notes)}[/]
  Links: [bold]{links_display}[/]
  Tags: [bold]{len(tag_stats)}[/]

[cyan]Graph Health[/]
  Orphaned: [{'yellow' if len(orphans) > 0 else 'green'}]{len(orphans)}[/]
  Hubs (>10 links): [green]{len(hubs)}[/]
  Broken Links: [{'red' if broken_count > 0 else 'green'}]{broken_count}[/]"""

            panel = Panel(
                stats_content,
                title=f"📊 {vault['name']}",
                border_style="cyan",
                box=box.ROUNDED,
            )
            console.print()
            console.print(panel)
            console.print()

            if verbose and notes:
                # Show top 5 notes by outgoing link count
                notes_with_links = []
                for note in notes:
                    out_links = self.db.get_outgoing_links(note['id'])
                    notes_with_links.append((note['title'], len(out_links)))
                notes_with_links.sort(key=lambda x: x[1], reverse=True)
                top = notes_with_links[:5]
                if top:
                    console.print("[bold]Top notes by link count:[/]")
                    for title, count in top:
                        console.print(f"  {title}: {count} links")
                    console.print()

        else:
            # Global stats
            db_stats = self.db.get_stats()

            stats_content = f"""[cyan]Overview[/]
  Vaults: [bold]{db_stats['vaults']}[/]
  Notes: [bold]{db_stats['notes']}[/]
  Links: [bold]{db_stats['links']}[/]
  Tags: [bold]{db_stats['tags']}[/]

[cyan]Graph Health[/]
  Orphaned Notes: [{'yellow' if db_stats['orphaned_notes'] > 0 else 'green'}]{db_stats['orphaned_notes']}[/]
  Broken Links: [{'red' if db_stats['broken_links'] > 0 else 'green'}]{db_stats['broken_links']}[/]"""

            panel = Panel(
                stats_content,
                title="📊 Database Statistics",
                border_style="cyan",
                box=box.ROUNDED,
            )
            console.print()
            console.print(panel)
            console.print()

    def list_vaults(self):
        """List all vaults in database with Rich table."""
        vaults = self.vault_manager.list_vaults()

        if not vaults:
            console.print("[dim]No vaults in database.[/]")
            console.print("\n[cyan]Use 'obs discover' to find and scan vaults.[/]")
            return

        table = Table(
            title="📚 Obsidian Vaults",
            box=box.ROUNDED,
            header_style="bold cyan",
            title_style="bold white",
        )
        table.add_column("Status", style="dim", width=10)
        table.add_column("Name", style="bold")
        table.add_column("Notes", justify="right")
        table.add_column("Links", justify="right")
        table.add_column("Last Scanned", style="dim")
        table.add_column("ID", style="dim")

        for vault in vaults:
            status = "[green]✓ Scanned[/]" if vault.last_scanned else "[yellow]⊘ Pending[/]"
            table.add_row(
                status,
                vault.name,
                str(vault.note_count),
                str(vault.link_count),
                format_relative_time(vault.last_scanned),
                vault.id[:8] if vault.id else "-"
            )

        console.print()
        console.print(table)
        console.print()

    def _print_scan_result(self, result, verbose: bool = False):
        """
        Print scan result (presentation layer helper).

        Args:
            result: ScanResult object from core layer
            verbose: Print detailed output
        """
        print(f"✓ Scanned: {result.vault_name}")
        print(f"  Notes: {result.notes_scanned}")
        print(f"  Links: {result.links_found}")
        print(f"  Tags: {result.tags_found}")
        print(f"  Duration: {result.duration_seconds:.2f}s")

        if verbose:
            if result.orphans_detected > 0:
                print(f"  Orphans: {result.orphans_detected}")
            if result.hubs_detected > 0:
                print(f"  Hubs: {result.hubs_detected}")

        if result.errors:
            print(f"  ⚠️  Errors: {len(result.errors)}")
            if verbose:
                for error in result.errors[:5]:
                    print(f"    • {error}")

        if result.warnings and verbose:
            print(f"  ⚠️  Warnings: {len(result.warnings)}")
            for warning in result.warnings[:5]:
                print(f"    • {warning}")

    def db_init(self):
        """Initialize or rebuild database."""
        try:
            self.db.rebuild_database()
            print("✓ Database initialized successfully!")
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


def _print_health_dashboard(health):
    """Print Rich health dashboard."""
    # Rating label
    if health.overall >= 80:
        rating = "[green]Excellent[/]"
    elif health.overall >= 60:
        rating = "[yellow]Good[/]"
    elif health.overall >= 40:
        rating = "[yellow]Fair[/]"
    else:
        rating = "[red]Poor[/]"

    console.print()
    console.print(f"  [bold]Vault Health: {health.vault_name}[/]")
    console.print(f"  Overall: [bold]{health.overall}/100[/] ({rating})")
    console.print()

    for sub in [health.connectivity, health.link_integrity, health.structure, health.freshness]:
        filled = sub.score // 10
        empty = 10 - filled
        bar = "\u2588" * filled + "\u2591" * empty

        if sub.score >= 80:
            color = "green"
        elif sub.score >= 60:
            color = "yellow"
        else:
            color = "red"

        console.print(f"  {sub.name:<18} [{color}]{bar}[/]  {sub.score}/100")
        for detail in sub.details:
            console.print(f"    {detail}")
        console.print()

    if health.recommendations:
        console.print("  [bold]Recommendations:[/]")
        for i, rec in enumerate(health.recommendations, 1):
            console.print(f"    {i}. {rec}")
        console.print()


def _print_refactor_plan(plan):
    """Print refactor plan with Rich formatting."""
    console.print()
    console.print(f"  [bold]🔄 Vault Refactor Analysis: {plan.vault_name}[/]")
    console.print(f"  [dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
    console.print(f"  📊 Analyzed {plan.note_count} notes across {plan.folder_count} folders")
    console.print()

    if not plan.suggestions:
        console.print("  [green]✓ No reorganization suggestions — vault looks well-organized![/]")
        console.print()
        return

    priority_icons = {'high': '🔴 HIGH', 'medium': '🟡 MEDIUM', 'low': '🟢 LOW'}
    priority_colors = {'high': 'red', 'medium': 'yellow', 'low': 'green'}

    idx = 1
    for priority_level in ['high', 'medium', 'low']:
        items = [s for s in plan.suggestions if s.priority == priority_level]
        if not items:
            continue
        icon = priority_icons[priority_level]
        color = priority_colors[priority_level]
        console.print(f"  [{color}]{icon} PRIORITY ({len(items)} items)[/]")
        for s in items:
            console.print(f"    {idx}. {s.description}")
            if s.reason:
                console.print(f"       [dim]{s.reason}[/]")
            idx += 1
        console.print()

    console.print(f"  📋 [bold]Summary:[/] {plan.summary}")
    console.print()


def _print_merge_candidates(candidates):
    """Print merge candidates with Rich formatting."""
    console.print()
    if not candidates:
        console.print("  [green]✓ No merge candidates found above threshold.[/]")
        console.print()
        return

    console.print(f"  [bold]🔗 Merge Candidates ({len(candidates)} found)[/]")
    console.print(f"  [dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
    console.print()

    for i, c in enumerate(candidates, 1):
        sim_pct = f"{c.similarity:.0%}"
        conf_pct = f"{c.confidence:.0%}"
        console.print(f"  {i}. [bold]{c.note_a_title}[/] ↔ [bold]{c.note_b_title}[/]")
        console.print(f"     Similarity: {sim_pct}  |  Confidence: {conf_pct}")
        if c.shared_tags:
            console.print(f"     Shared tags: {', '.join(c.shared_tags)}")
        if c.shared_links:
            console.print(f"     Shared links: {', '.join(c.shared_links[:5])}")
        if c.suggested_target:
            console.print(f"     [dim]Suggested keep: {c.suggested_target}[/]")
        console.print()


def _print_tag_suggestions(suggestions):
    """Print tag suggestions with Rich formatting."""
    console.print()
    if not suggestions:
        console.print("  [green]✓ No tag suggestions — all notes have tags or AI unavailable.[/]")
        console.print()
        return

    total_tags = sum(len(s.suggested_tags) for s in suggestions)
    console.print(f"  [bold]🏷️  Tag Suggestions ({total_tags} tags for {len(suggestions)} notes)[/]")
    console.print(f"  [dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
    console.print()

    for s in suggestions:
        console.print(f"  [bold]{s.note_title}[/]")
        if s.neighbor_tags:
            console.print(f"    [dim]Neighbor tags: {', '.join(s.neighbor_tags[:5])}[/]")
        for tag in s.suggested_tags:
            conf = tag.get('confidence', 0)
            usage = tag.get('vault_usage_count', 0)
            color = 'green' if conf >= 0.8 else 'yellow' if conf >= 0.5 else 'dim'
            console.print(f"    [{color}]#{tag['tag']}[/] ({conf:.0%} confidence, {usage} vault uses)")
        console.print()


def _print_quality_scores(scores):
    """Print quality scores with Rich formatting."""
    console.print()
    if not scores:
        console.print("  [green]✓ No notes to score.[/]")
        console.print()
        return

    avg_score = sum(s.overall_score for s in scores) / len(scores) if scores else 0
    console.print(f"  [bold]📊 Note Quality Scores ({len(scores)} notes, avg {avg_score:.0f}/100)[/]")
    console.print(f"  [dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
    console.print()

    table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
    table.add_column("Score", justify="right", style="bold", width=6)
    table.add_column("Note", width=35)
    table.add_column("Comp", justify="right", width=5)
    table.add_column("Conn", justify="right", width=5)
    table.add_column("Meta", justify="right", width=5)
    table.add_column("Fresh", justify="right", width=5)
    table.add_column("Issues", width=30)

    for s in scores[:50]:  # Show worst 50
        score_color = 'red' if s.overall_score < 30 else 'yellow' if s.overall_score < 60 else 'green'
        dims = s.dimensions
        issue_text = '; '.join(i['description'] for i in s.issues[:2]) if s.issues else ''
        table.add_row(
            f"[{score_color}]{s.overall_score:.0f}[/]",
            s.note_title[:35],
            f"{dims.get('completeness', 0):.0f}",
            f"{dims.get('connectivity', 0):.0f}",
            f"{dims.get('metadata', 0):.0f}",
            f"{dims.get('freshness', 0):.0f}",
            issue_text[:30],
        )

    console.print(table)
    console.print()


def _print_bridge_status(status):
    """Render BridgeStatus as a Rich panel."""
    from ai.models import BridgeStatus

    cli_icon = "✅" if status.cli_installed else "❌"
    app_icon = "✅" if status.app_running else "⚠️ "
    cli_label = f"CLI installed ({status.cli_version})" if status.cli_installed else "CLI not installed"
    app_label = "Obsidian app connected" if status.app_running else "Obsidian app not running"

    lines = [
        f"{cli_icon}  {cli_label}",
        f"{app_icon}  {app_label}",
    ]
    if status.capabilities:
        caps = ", ".join(status.capabilities)
        lines.append(f"\n[dim]Capabilities:[/] {caps}")
    if not status.cli_installed:
        lines.append("\n[dim]Install:[/] brew install obsidian-cli")
    elif not status.app_running:
        lines.append("\n[dim]Start Obsidian app to enable bridge commands.[/]")

    console.print(Panel("\n".join(lines), title="[bold]Obsidian CLI Bridge Status[/]", expand=False))


def _print_trend_report(report):
    """Render TrendReport with a sparkline table."""
    if report.insufficient_data:
        console.print(Panel(
            f"[yellow]Insufficient data[/] — only {len(report.buckets)} week(s) found in the last {report.lookback_days} days.\n"
            "Run [bold]obs analyze <vault>[/] and rescan to populate temporal data.",
            title="[bold]Vault Activity Trends[/]",
            expand=False,
        ))
        return

    bars = " ▁▂▃▄▅▆▇█"

    def sparkbar(counts):
        if not counts or max(counts) == 0:
            return "─" * len(counts)
        mx = max(counts)
        return "".join(bars[min(int(c / mx * 8), 8)] for c in counts)

    created = [b.notes_created for b in report.buckets]
    modified = [b.notes_modified for b in report.buckets]

    console.print(f"\n[bold]Vault Activity — last {report.lookback_days} days[/]  "
                  f"[dim]({len(report.buckets)} weeks, velocity {report.velocity_notes_per_week:.1f} notes/week)[/]\n")

    table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
    table.add_column("Week", width=10)
    table.add_column("Created", justify="right", width=8)
    table.add_column("Modified", justify="right", width=8)

    spark_created = sparkbar(created)
    spark_modified = sparkbar(modified)
    table.add_row("[dim]sparkline[/]", f"[cyan]{spark_created}[/]", f"[magenta]{spark_modified}[/]")

    for b in report.buckets[-16:]:  # Show last 16 weeks to avoid scroll
        table.add_row(b.week, str(b.notes_created) if b.notes_created else "—",
                      str(b.notes_modified) if b.notes_modified else "—")

    console.print(table)
    console.print(f"  [dim]Total notes:[/] {report.total_notes}")
    console.print()


def _print_stale_report(report):
    """Render StaleReport as a Rich table ranked by staleness."""
    if not report.notes:
        console.print("[green]✓[/] No stale notes found.")
        return

    rank_label = "PageRank×Age" if report.has_graph_metrics else "Age (no graph metrics — run 'obs analyze' first)"
    console.print(f"\n[bold]Stale Notes[/]  [dim]ranked by {rank_label}[/]\n")

    if not report.has_graph_metrics:
        console.print("[yellow]ℹ[/]  No graph metrics. Ranking by age only. Run [bold]obs analyze <vault>[/] for importance weighting.\n")

    table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
    table.add_column("#", justify="right", width=3)
    table.add_column("Title", width=40)
    table.add_column("Age (days)", justify="right", width=10)
    if report.has_graph_metrics:
        table.add_column("PageRank", justify="right", width=9)
        table.add_column("Score", justify="right", width=7)

    for i, n in enumerate(report.notes, 1):
        age_color = "red" if n.days_since_modified > 180 else "yellow" if n.days_since_modified > 90 else "white"
        row = [str(i), n.title[:40] or n.path[:40], f"[{age_color}]{n.days_since_modified}[/]"]
        if report.has_graph_metrics:
            row += [f"{n.pagerank:.4f}", f"{n.staleness_score:.3f}"]
        table.add_row(*row)

    console.print(table)
    console.print()


def _print_doctor_results(results):
    """Render DoctorResult list as a layered Rich table."""
    from rich.table import Table

    STATUS_ICON = {"pass": "✅", "warn": "⚠️ ", "fail": "❌", "skip": "⬜", "error": "🔥"}
    STATUS_COLOR = {"pass": "green", "warn": "yellow", "fail": "red", "skip": "dim", "error": "bold red"}

    current_layer = None
    table = None

    counts = {"pass": 0, "warn": 0, "fail": 0, "skip": 0, "error": 0}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1

    for r in results:
        if r.layer != current_layer:
            if table is not None:
                console.print(table)
                console.print()
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("Icon", width=3)
            table.add_column("Label", style="bold", min_width=28)
            table.add_column("Message")
            table.add_column("Fix", style="dim")
            console.print(f"[bold blue]── {r.layer.upper()} ──────────────────────────────────────[/]")
            current_layer = r.layer

        icon = STATUS_ICON.get(r.status, "?")
        color = STATUS_COLOR.get(r.status, "white")
        table.add_row(
            icon,
            f"[{color}]{r.label}[/]",
            f"[{color}]{r.message}[/]",
            r.fix_hint or "",
        )

    if table is not None:
        console.print(table)
        console.print()

    # Summary line
    parts = []
    if counts["fail"]:
        parts.append(f"[red]{counts['fail']} fail[/]")
    if counts["error"]:
        parts.append(f"[bold red]{counts['error']} error[/]")
    if counts["warn"]:
        parts.append(f"[yellow]{counts['warn']} warn[/]")
    if counts["pass"]:
        parts.append(f"[green]{counts['pass']} pass[/]")
    if counts["skip"]:
        parts.append(f"[dim]{counts['skip']} skip[/]")
    verdict = "[bold green]All checks passed ✅[/]" if not counts["fail"] and not counts["error"] else "[bold red]Issues found — see hints above[/]"
    console.print(f"{verdict}  ({', '.join(parts)})")


def _print_digest_report(report):
    """Render DigestReport as a three-section Rich summary."""
    console.print(f"\n[bold cyan]Daily Digest[/] — [dim]{report.vault_id}[/]\n")

    # Bridge
    b = report.bridge
    bridge_icon = "🟢" if b.cli_installed else "🔴"
    app_icon = "🟢" if b.app_running else "🔴"
    console.print(f"[bold]Bridge[/]  {bridge_icon} CLI {'v' + b.cli_version if b.cli_version else 'not found'}  {app_icon} App {'running' if b.app_running else 'not running'}")
    console.print()

    # Trends summary
    tr = report.trends
    if tr.insufficient_data:
        console.print("[dim]Trends[/]  Insufficient data (<2 weeks)")
    else:
        console.print(f"[bold]Trends[/]  {tr.velocity_notes_per_week:.1f} notes/week  ({len(tr.buckets)} weeks, {tr.lookback_days}d window)")
    console.print()

    # Top stale notes
    _print_stale_report(report.stale)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Obsidian CLI Ops - Knowledge Graph Management',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # discover command
    discover_parser = subparsers.add_parser('discover',
                                           help='Discover vaults in directory')
    discover_parser.add_argument('path', help='Root directory to search')
    discover_parser.add_argument('--scan', action='store_true',
                                help='Scan discovered vaults')

    # scan command
    scan_parser = subparsers.add_parser('scan',
                                       help='Scan a vault')
    scan_parser.add_argument('path', help='Vault path')
    scan_parser.add_argument('--name', help='Vault name')
    scan_parser.add_argument('--analyze', action='store_true',
                            help='Analyze graph after scan')

    # analyze command
    analyze_parser = subparsers.add_parser('analyze',
                                          help='Analyze vault graph')
    analyze_parser.add_argument('vault', help='Vault name or ID')

    # stats command
    stats_parser = subparsers.add_parser('stats',
                                        help='Show statistics')
    stats_parser.add_argument('--vault', help='Vault name or ID')

    # vaults command
    subparsers.add_parser('vaults',
                         help='List all vaults')

    # db command
    db_parser = subparsers.add_parser('db',
                                     help='Database management')
    db_subparsers = db_parser.add_subparsers(dest='db_command')
    init_parser = db_subparsers.add_parser('init', help='Initialize database')
    init_parser.add_argument('--force', action='store_true',
                             help='Force reinitialize existing database')
    db_subparsers.add_parser('stats', help='Show database stats')

    # search command
    search_parser = subparsers.add_parser('search', help='Search notes by title')
    search_parser.add_argument('query', help='Search query (title match)')
    search_parser.add_argument('--vault', '-v', help='Limit search to vault name or ID')
    search_parser.add_argument('--limit', '-n', type=int, default=20,
                               help='Max results (default: 20)')

    # health command
    health_parser = subparsers.add_parser('health', help='Vault health dashboard')
    health_parser.add_argument('vault', help='Vault name or ID')
    health_parser.add_argument('--json', action='store_true', dest='json_output',
                               help='Output as JSON')

    # ai command
    ai_parser = subparsers.add_parser('ai',
                                      help='AI provider management')
    ai_subparsers = ai_parser.add_subparsers(dest='ai_command')

    ai_subparsers.add_parser('status', help='Show AI provider status')
    ai_subparsers.add_parser('setup', help='Interactive AI setup wizard')
    test_parser = ai_subparsers.add_parser('test', help='Test AI providers')
    test_parser.add_argument('--provider', help='Test specific provider')

    # AI feature commands
    similar_parser = ai_subparsers.add_parser('similar', help='Find similar notes')
    similar_parser.add_argument('note_id', help='Note ID to find similar notes for')
    similar_parser.add_argument('--limit', type=int, default=10, help='Max results')
    similar_parser.add_argument('--threshold', type=float, default=0.3, help='Min similarity (0-1)')
    similar_parser.add_argument('--provider', help='Use specific AI provider')

    ai_analyze_parser = ai_subparsers.add_parser('analyze', help='Analyze a note')
    ai_analyze_parser.add_argument('note_id', help='Note ID to analyze')
    ai_analyze_parser.add_argument('--provider', help='Use specific AI provider')

    duplicates_parser = ai_subparsers.add_parser('duplicates', help='Find duplicate notes')
    duplicates_parser.add_argument('vault_id', help='Vault ID to scan')
    duplicates_parser.add_argument('--threshold', type=float, default=0.85, help='Similarity threshold')
    duplicates_parser.add_argument('--limit', type=int, default=50, help='Max duplicate groups')
    duplicates_parser.add_argument('--provider', help='Use specific AI provider')

    # New AI commands (Increment 5)
    suggest_parser = ai_subparsers.add_parser('suggest-links', help='Suggest new links for a note')
    suggest_parser.add_argument('note_id', help='Note ID to suggest links for')
    suggest_parser.add_argument('--limit', type=int, default=5, help='Number of suggestions')
    suggest_parser.add_argument('--provider', help='Use specific AI provider')

    gaps_parser = ai_subparsers.add_parser('gaps', help='Find knowledge gaps in vault')
    gaps_parser.add_argument('vault_id', help='Vault ID to analyze')
    gaps_parser.add_argument('--provider', help='Use specific AI provider')

    summarize_parser = ai_subparsers.add_parser('summarize', help='Summarize vault themes and stats')
    summarize_parser.add_argument('vault_id', help='Vault ID to summarize')
    summarize_parser.add_argument('--folder', help='Scope to folder path')
    summarize_parser.add_argument('--tag', help='Scope to tag')
    summarize_parser.add_argument('--provider', help='Use specific AI provider')

    refactor_parser = ai_subparsers.add_parser('refactor', help='AI-powered vault reorganization suggestions')
    refactor_parser.add_argument('vault_id', help='Vault name or ID')
    refactor_parser.add_argument('--dry-run', action='store_true', help='Show scope without AI calls')
    refactor_parser.add_argument('--provider', help='Use specific AI provider')

    # v3.2.0: Quality feature commands
    merge_parser = ai_subparsers.add_parser('merge-suggest', help='Find potential note merge candidates')
    merge_parser.add_argument('vault_id', help='Vault name or ID')
    merge_parser.add_argument('--threshold', type=float, default=0.8, help='Min similarity (0-1, default 0.8)')
    merge_parser.add_argument('--provider', help='Use specific AI provider')

    tag_suggest_parser = ai_subparsers.add_parser('tag-suggest', help='Suggest tags for untagged notes')
    tag_suggest_parser.add_argument('target', help='Vault name/ID (vault-wide) or note ID (single note)')
    tag_suggest_parser.add_argument('--apply', action='store_true', help='Auto-apply tags with >80%% confidence')
    tag_suggest_parser.add_argument('--min-confidence', type=float, default=0.0, help='Min confidence threshold (0-1)')
    tag_suggest_parser.add_argument('--provider', help='Use specific AI provider')

    quality_parser = ai_subparsers.add_parser('quality', help='Score notes on quality dimensions')
    quality_parser.add_argument('target', help='Vault name/ID (vault-wide) or note ID (single note)')

    # --- v3.4.0: Bridge + Temporal Analytics ---
    bridge_parser = subparsers.add_parser('bridge', help='Obsidian CLI bridge commands')
    bridge_subparsers = bridge_parser.add_subparsers(dest='bridge_command', help='Bridge subcommands')
    bridge_subparsers.add_parser('status', help='Show Obsidian CLI bridge status')

    trends_parser = subparsers.add_parser('trends', help='Show vault activity trends (weekly buckets)')
    trends_parser.add_argument('vault', help='Vault name or ID')
    trends_parser.add_argument('--days', type=int, default=90, help='Lookback window in days (default: 90)')

    stale_parser = subparsers.add_parser('stale', help='Find stale high-importance notes')
    stale_parser.add_argument('vault', help='Vault name or ID')
    stale_parser.add_argument('--limit', type=int, default=20, help='Max notes to show (default: 20)')

    digest_parser = subparsers.add_parser('daily-digest', help='Combined bridge + trends + stale summary')
    digest_parser.add_argument('vault', help='Vault name or ID')
    digest_parser.add_argument('--days', type=int, default=90, help='Trend lookback window in days (default: 90)')
    digest_parser.add_argument('--limit', type=int, default=5, help='Max stale notes to show (default: 5)')

    doctor_parser = subparsers.add_parser('doctor', help='Run self-diagnostic checks')
    doctor_parser.add_argument('--vault', default=None, help='Limit vault checks to this vault ID or name')
    doctor_parser.add_argument('--layer', action='append', dest='layers',
                               choices=['python', 'database', 'vault', 'mcp', 'docs', 'icloud'],
                               help='Run only specified layer(s) (repeatable)')
    doctor_parser.add_argument('--json', action='store_true', help='Output results as JSON')

    link_parser = subparsers.add_parser('link', help='Create the per-project .obs/sync.yml mirror map (ADR-001)')
    link_parser.add_argument('project_dir', nargs='?', default='.', help='Project directory (default: cwd)')
    link_parser.add_argument('--vault-root', default=None, help='Vault root for an active mirror')
    link_parser.add_argument('--mirror', choices=['auto', 'mirror', 'none'], default='auto', help='Mirror mode (default: auto)')
    link_parser.add_argument('--force', action='store_true', help='Overwrite an existing map')
    link_parser.add_argument('--json', action='store_true', help='Output result as JSON')

    config_parser = subparsers.add_parser('config', help='Manage obs unified config (~/.config/obs/config.yaml)')
    config_sub = config_parser.add_subparsers(dest='config_command')
    config_sub.add_parser('show', help='Print current config and its source')
    config_sub.add_parser('validate', help='Validate config and report errors')
    config_migrate = config_sub.add_parser('migrate', help='Convert legacy obs/nexus config to unified YAML')
    config_migrate.add_argument('--dry-run', action='store_true', help='Print migration result without writing')
    config_sub.add_parser('init', help='Interactive wizard to create a fresh config')
    config_sub.add_parser('edit', help='Open config file in $EDITOR')

    # --- Phase 4: obs research namespace (D8) ---
    research_parser = subparsers.add_parser('research', help='Research domain commands (Zotero, PDF, courses, manuscripts)')
    research_sub = research_parser.add_subparsers(dest='research_command')

    # research board — atlas state -> vault dashboard (SPEC-obs)
    board_parser = research_sub.add_parser('board', help='Render the research action board from atlas state')
    board_parser.add_argument('--out', default=None, help='Vault file to update (marker-bounded); prints to stdout if omitted')
    board_parser.add_argument('--kind', default=None, help='Filter to a kind (manuscript|program|package)')
    board_parser.add_argument('--dry-run', action='store_true', help='With --out, show what would change without writing')

    # zotero subcommands
    zotero_parser = research_sub.add_parser('zotero', help='Zotero library commands')
    zotero_sub = zotero_parser.add_subparsers(dest='zotero_command')
    zot_search = zotero_sub.add_parser('search', help='Search Zotero library')
    zot_search.add_argument('query', help='Search query')
    zot_search.add_argument('--limit', '-n', type=int, default=20, help='Max results (default: 20)')
    zot_search.add_argument('--type', dest='item_type', default='', help='Filter by item type (e.g. journalArticle)')
    zot_search.add_argument('--tag', default='', help='Filter by tag')
    zot_get = zotero_sub.add_parser('get', help='Get a Zotero item by key')
    zot_get.add_argument('key', help='Zotero item key')
    zot_get.add_argument('--format', default='apa', choices=['apa', 'bibtex', 'full'], help='Output format (default: apa)')
    zot_recent = zotero_sub.add_parser('recent', help='List recently modified Zotero items')
    zot_recent.add_argument('--limit', '-n', type=int, default=10, help='Max results (default: 10)')

    # pdf subcommands
    pdf_parser = research_sub.add_parser('pdf', help='PDF search commands')
    pdf_sub = pdf_parser.add_subparsers(dest='pdf_command')
    pdf_search = pdf_sub.add_parser('search', help='Search PDF content')
    pdf_search.add_argument('query', help='Search query')
    pdf_search.add_argument('--limit', '-n', type=int, default=10, help='Max results (default: 10)')

    # course subcommands
    course_parser = research_sub.add_parser('course', help='Course management commands')
    course_sub = course_parser.add_subparsers(dest='course_command')
    course_sub.add_parser('list', help='List all courses')
    course_show = course_sub.add_parser('show', help='Show course details')
    course_show.add_argument('name', help='Course name or directory name')
    course_lec = course_sub.add_parser('lectures', help='List lectures for a course')
    course_lec.add_argument('name', help='Course name or directory name')

    # manuscript subcommands
    ms_parser = research_sub.add_parser('manuscript', help='Manuscript management commands')
    ms_sub = ms_parser.add_subparsers(dest='manuscript_command')
    ms_list = ms_sub.add_parser('list', help='List all manuscripts')
    ms_list.add_argument('--archived', action='store_true', help='Include archived manuscripts')
    ms_show = ms_sub.add_parser('show', help='Show manuscript details')
    ms_show.add_argument('name', help='Manuscript name or directory name')
    ms_sub.add_parser('stats', help='Show manuscript statistics')

    # bib subcommands
    bib_parser = research_sub.add_parser('bib', help='Bibliography commands')
    bib_sub = bib_parser.add_subparsers(dest='bib_command')
    bib_check = bib_sub.add_parser('check', help='Check citations in a manuscript')
    bib_check.add_argument('name', help='Manuscript name or directory name')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize CLI
    cli = ObsCLI()

    # Execute command
    try:
        if args.command == 'discover':
            cli.discover(args.path, scan=args.scan, verbose=args.verbose)

        elif args.command == 'scan':
            cli.scan(args.path, vault_name=args.name,
                    analyze=args.analyze, verbose=args.verbose)

        elif args.command == 'analyze':
            if args.json:
                try:
                    vault = cli.db.get_vault_by_name_or_id(args.vault)
                except ValueError as e:
                    print(json.dumps({"error": str(e)}), file=sys.stderr)
                    sys.exit(1)
                if not vault:
                    print(json.dumps({"error": f"Vault not found: {args.vault}"}), file=sys.stderr)
                    sys.exit(1)
                cli._warn_if_stale(vault['id'])
                result = cli.graph_analyzer.analyze_vault(vault['id'])
                print(json.dumps(result, indent=2, default=str))
            else:
                cli._warn_if_stale(args.vault)
                cli.analyze(args.vault, verbose=args.verbose)

        elif args.command == 'stats':
            if args.json:
                if args.vault:
                    try:
                        vault = cli.db.get_vault_by_name_or_id(args.vault)
                    except ValueError as e:
                        print(json.dumps({"error": str(e)}), file=sys.stderr)
                        sys.exit(1)
                    if not vault:
                        print(json.dumps({"error": f"Vault not found: {args.vault}"}), file=sys.stderr)
                        sys.exit(1)
                    vault_id = vault['id']
                    notes = cli.db.list_notes(vault_id)
                    with cli.db.get_connection() as conn:
                        cursor = conn.execute("""
                            SELECT COUNT(*) FROM links l
                            JOIN notes n ON l.source_note_id = n.id
                            WHERE l.link_type = 'internal'
                            AND n.vault_id = ?
                        """, (vault_id,))
                        link_count = cursor.fetchone()[0]
                    tag_stats = cli.db.get_tag_stats()
                    orphans = cli.db.get_orphaned_notes(vault_id)
                    hubs = cli.db.get_hub_notes(vault_id, limit=10)
                    broken = cli.db.get_broken_links(vault_id)
                    broken_count = sum(b['broken_count'] for b in broken)
                    print(json.dumps({
                        "vault": vault['name'],
                        "path": vault['path'],
                        "notes": len(notes),
                        "links": link_count,
                        "broken_links": broken_count,
                        "tags": len(tag_stats),
                        "orphaned": len(orphans),
                        "hubs": len(hubs),
                    }, indent=2, default=str))
                else:
                    db_stats = cli.db.get_stats()
                    print(json.dumps({
                        "vaults": db_stats['vaults'],
                        "notes": db_stats['notes'],
                        "links": db_stats['links'],
                        "tags": db_stats['tags'],
                        "orphaned_notes": db_stats['orphaned_notes'],
                        "broken_links": db_stats['broken_links'],
                    }, indent=2, default=str))
            else:
                cli.stats(vault_identifier=args.vault, verbose=args.verbose)

        elif args.command == 'search':
            query = args.query
            vault_id = None
            if args.vault:
                try:
                    vault = cli.db.get_vault_by_name_or_id(args.vault)
                except ValueError as e:
                    if args.json:
                        print(json.dumps({"error": str(e)}), file=sys.stderr)
                    else:
                        console.print(f"[red]❌ {e}[/]")
                    sys.exit(1)
                if not vault:
                    if args.json:
                        print(json.dumps({"error": f"Vault not found: {args.vault}"}), file=sys.stderr)
                    else:
                        console.print(f"[red]❌ Vault not found: {args.vault}[/]")
                    sys.exit(1)
                vault_id = vault['id']
                cli._warn_if_stale(vault_id)

            results = cli.db.search_notes(query, vault_id=vault_id, limit=args.limit)

            if args.json:
                print(json.dumps(results, indent=2, default=str))
            else:
                if not results:
                    console.print(f"[dim]No notes found matching '{query}'[/]")
                else:
                    table = Table(
                        title=f"🔍 Search: {query}  ({len(results)} result{'s' if len(results) != 1 else ''})",
                        box=box.ROUNDED,
                        header_style="bold cyan",
                    )
                    table.add_column("Title", style="bold", min_width=20)
                    table.add_column("Vault", style="cyan", min_width=10)
                    table.add_column("Path", style="dim")
                    for r in results:
                        table.add_row(r['title'], r.get('vault_name', ''), r['path'])
                    console.print()
                    console.print(table)
                    console.print()

        elif args.command == 'vaults':
            if args.json:
                vaults = cli.vault_manager.list_vaults()
                print(json.dumps([v.to_dict() for v in vaults], indent=2, default=str))
            else:
                cli.list_vaults()

        elif args.command == 'health':
            try:
                vault = cli.db.get_vault_by_name_or_id(args.vault)
            except ValueError as e:
                console.print(f"[red]{e}[/]")
                sys.exit(1)
            if not vault:
                console.print(f"[red]Vault not found: {args.vault}[/]")
                console.print(f"[dim]  Tip: Run 'obs' to list known vaults[/]")
                console.print(f"[dim]  Tip: Run 'obs discover <path>' to find new vaults[/]")
                sys.exit(1)

            cli._warn_if_stale(vault['id'])
            health = cli.vault_manager.get_vault_health(args.vault)

            if getattr(args, 'json_output', False):
                import json as json_mod
                print(json_mod.dumps(health.to_dict(), indent=2, default=str))
            else:
                _print_health_dashboard(health)

        elif args.command == 'db':
            if args.db_command == 'init':
                db_path = Path("~/.config/obs/vault_db.sqlite").expanduser()
                if db_path.exists() and not getattr(args, 'force', False):
                    console.print("[yellow]Database already exists. Use --force to reinitialize.[/]")
                    return
                cli.db_init()
            elif args.db_command == 'stats':
                cli.stats()
            else:
                db_parser.print_help()

        elif args.command == 'ai':
            # Import AI module only when needed
            from ai import print_status, setup_wizard
            from ai.router import AIRouter, PROVIDER_CLASSES

            if args.ai_command == 'status':
                print_status()

            elif args.ai_command == 'setup':
                setup_wizard()

            elif args.ai_command == 'test':
                # Test providers
                print("🧪 Testing AI Providers\n")
                router = AIRouter()

                providers_to_test = [args.provider] if args.provider else list(PROVIDER_CLASSES.keys())

                for name in providers_to_test:
                    if name not in PROVIDER_CLASSES:
                        print(f"  ✗ Unknown provider: {name}")
                        continue

                    try:
                        provider = PROVIDER_CLASSES[name]()
                        available = provider.is_available()
                        if available:
                            print(f"  ✓ {name}: available")
                            # Quick test if analysis is supported
                            if provider.capabilities.analysis:
                                try:
                                    result = provider.analyze_note("Test note content", "Test")
                                    print(f"    └─ Analysis: working")
                                except Exception as e:
                                    print(f"    └─ Analysis: {e}")
                        else:
                            print(f"  ✗ {name}: not available")
                    except Exception as e:
                        print(f"  ✗ {name}: {e}")

                print()

            elif args.ai_command == 'similar':
                # Find similar notes
                from ai.features import find_similar_notes

                try:
                    matches = find_similar_notes(
                        args.note_id,
                        cli.db,
                        limit=args.limit,
                        min_similarity=args.threshold,
                        provider=args.provider
                    )

                    if args.json:
                        print(json.dumps([{
                            "note_id": m.note_id,
                            "title": m.title,
                            "similarity": m.similarity,
                            "path": m.path,
                        } for m in matches], indent=2, default=str))
                    else:
                        print(f"🔍 Finding similar notes to: {args.note_id}\n")
                        if matches:
                            print(f"Found {len(matches)} similar notes:\n")
                            for i, match in enumerate(matches, 1):
                                print(f"  {i}. {match.title}")
                                print(f"     Similarity: {match.similarity:.1%}")
                                print(f"     Path: {match.path}")
                                print(f"     ID: {match.note_id}")
                                print()
                        else:
                            print("No similar notes found.")
                except ValueError as e:
                    if args.json:
                        print(json.dumps({"error": str(e)}), file=sys.stderr)
                    else:
                        print(f"❌ {e}")
                    sys.exit(1)
                except RuntimeError as e:
                    if args.json:
                        print(json.dumps({"error": str(e)}), file=sys.stderr)
                    else:
                        print(f"❌ {e}")
                    sys.exit(1)

            elif args.ai_command == 'analyze':
                # Analyze a note
                from ai.features import analyze_note as ai_analyze_note

                try:
                    result = ai_analyze_note(
                        args.note_id,
                        cli.db,
                        provider=args.provider
                    )

                    if args.json:
                        print(json.dumps({
                            "summary": result.summary,
                            "themes": result.themes,
                            "quality_score": result.quality_score,
                            "connections": result.connections,
                            "suggestions": result.suggestions,
                        }, indent=2, default=str))
                    else:
                        print(f"🔬 Analyzing note: {args.note_id}\n")
                        print("📊 Analysis Results:\n")

                        if result.summary:
                            print(f"  Summary: {result.summary}")
                        if result.themes:
                            print(f"  Themes: {', '.join(result.themes)}")
                        if result.quality_score > 0:
                            print(f"  Quality: {result.quality_score:.0%}")
                        if result.connections:
                            print(f"  Connections: {', '.join(result.connections)}")

                        if result.suggestions:
                            print()
                            print("  💡 Suggestions:")
                            for suggestion in result.suggestions:
                                print(f"    • {suggestion}")

                except ValueError as e:
                    if args.json:
                        print(json.dumps({"error": str(e)}), file=sys.stderr)
                    else:
                        print(f"❌ {e}")
                    sys.exit(1)
                except RuntimeError as e:
                    if args.json:
                        print(json.dumps({"error": str(e)}), file=sys.stderr)
                    else:
                        print(f"❌ {e}")
                    sys.exit(1)

            elif args.ai_command == 'duplicates':
                # Find duplicate notes
                from ai.features import find_duplicates

                try:
                    groups = find_duplicates(
                        args.vault_id,
                        cli.db,
                        threshold=args.threshold,
                        limit=args.limit,
                        provider=args.provider
                    )

                    if args.json:
                        print(json.dumps([{
                            "similarity": g.similarity,
                            "notes": [{"title": n['title'], "path": n['path']} for n in g.notes],
                        } for g in groups], indent=2, default=str))
                    else:
                        print(f"🔍 Scanning vault for duplicates: {args.vault_id}\n")
                        if groups:
                            print(f"Found {len(groups)} potential duplicate groups:\n")
                            for i, group in enumerate(groups, 1):
                                print(f"  Group {i} ({group.similarity:.1%} similarity):")
                                for note in group.notes:
                                    print(f"    • {note['title']}")
                                    print(f"      {note['path']}")
                                print()
                        else:
                            print("No duplicate notes found.")
                except ValueError as e:
                    if args.json:
                        print(json.dumps({"error": str(e)}), file=sys.stderr)
                    else:
                        print(f"❌ {e}")
                    sys.exit(1)
                except RuntimeError as e:
                    if args.json:
                        print(json.dumps({"error": str(e)}), file=sys.stderr)
                    else:
                        print(f"❌ {e}")
                    sys.exit(1)

            elif args.ai_command == 'suggest-links':
                from ai.features import suggest_links

                try:
                    suggestions = suggest_links(
                        args.note_id,
                        cli.db,
                        limit=args.limit,
                        provider=args.provider,
                        verbose=args.verbose,
                    )

                    if args.json:
                        print(json.dumps([{
                            "target_title": s.target_title,
                            "target_path": s.target_path,
                            "similarity": s.similarity,
                            "reason": s.reason,
                        } for s in suggestions], indent=2, default=str))
                    else:
                        print(f"🔗 Suggesting links for note: {args.note_id}\n")
                        if suggestions:
                            print(f"Found {len(suggestions)} link suggestions:\n")
                            for i, s in enumerate(suggestions, 1):
                                print(f"  {i}. [[{s.target_title}]] ({s.similarity:.0%})")
                                print(f"     {s.target_path}")
                                if s.reason:
                                    print(f"     {s.reason}")
                                print()
                        else:
                            print("No link suggestions found.")
                except (ValueError, RuntimeError) as e:
                    if args.json:
                        print(json.dumps({"error": str(e)}), file=sys.stderr)
                    else:
                        print(f"❌ {e}")
                    sys.exit(1)

            elif args.ai_command == 'gaps':
                from ai.features import find_gaps

                try:
                    gaps = find_gaps(
                        args.vault_id,
                        cli.db,
                        provider=args.provider,
                        verbose=args.verbose,
                    )

                    if args.json:
                        print(json.dumps([{
                            "description": g.description,
                            "related_notes": g.related_notes,
                            "suggested_action": g.suggested_action,
                        } for g in gaps], indent=2, default=str))
                    else:
                        print(f"🔍 Analyzing knowledge gaps: {args.vault_id}\n")
                        if gaps:
                            print(f"Found {len(gaps)} knowledge gaps:\n")
                            for i, gap in enumerate(gaps, 1):
                                print(f"  {i}. {gap.description}")
                                if gap.related_notes:
                                    for note in gap.related_notes[:3]:
                                        print(f"     • {note}")
                                if gap.suggested_action:
                                    print(f"     → {gap.suggested_action}")
                                print()
                        else:
                            print("No knowledge gaps found.")
                except (ValueError, RuntimeError) as e:
                    if args.json:
                        print(json.dumps({"error": str(e)}), file=sys.stderr)
                    else:
                        print(f"❌ {e}")
                    sys.exit(1)

            elif args.ai_command == 'summarize':
                from ai.features import summarize_vault

                try:
                    # Skip progress callback in JSON mode (no Rich/terminal output)
                    progress_cb = None
                    if not args.json:
                        scope = args.vault_id
                        if args.folder:
                            scope += f" (folder: {args.folder})"
                        if args.tag:
                            scope += f" (tag: {args.tag})"
                        print(f"📊 Summarizing vault: {scope}\n")

                        def progress_cb(current, total):
                            pct = current / total * 100 if total > 0 else 0
                            print(f"\r  Processing: {current}/{total} ({pct:.0f}%)", end="", flush=True)

                    summary = summarize_vault(
                        args.vault_id,
                        cli.db,
                        folder=args.folder,
                        tag=args.tag,
                        provider=args.provider,
                        verbose=args.verbose,
                        progress_callback=progress_cb,
                    )

                    if args.json:
                        print(json.dumps({
                            "note_count": summary.note_count,
                            "themes": summary.themes,
                            "top_hubs": summary.top_hubs,
                            "orphan_count": summary.orphan_count,
                            "summary_text": summary.summary_text,
                        }, indent=2, default=str))
                    else:
                        print("\r" + " " * 40 + "\r", end="")  # Clear progress line

                        print(f"  Notes: {summary.note_count}")
                        if summary.themes:
                            print(f"  Themes: {', '.join(summary.themes[:5])}")
                        if summary.top_hubs:
                            print(f"  Top hubs:")
                            for hub in summary.top_hubs:
                                print(f"    • {hub['title']} ({hub['connections']} connections)")
                        print(f"  Orphans: {summary.orphan_count}")
                        print()
                        if summary.summary_text:
                            print(f"  {summary.summary_text}")

                except (ValueError, RuntimeError) as e:
                    if args.json:
                        print(json.dumps({"error": str(e)}), file=sys.stderr)
                    else:
                        print(f"❌ {e}")
                    sys.exit(1)

            elif args.ai_command == 'refactor':
                from ai.features import refactor_vault

                try:
                    plan = refactor_vault(
                        args.vault_id,
                        cli.db,
                        provider=args.provider,
                        dry_run=getattr(args, 'dry_run', False),
                        verbose=args.verbose,
                    )

                    if args.json:
                        print(json.dumps(plan.to_dict(), indent=2, default=str))
                    else:
                        _print_refactor_plan(plan)
                except (ValueError, RuntimeError) as e:
                    if args.json:
                        print(json.dumps({"error": str(e)}), file=sys.stderr)
                    else:
                        print(f"❌ {e}")
                    sys.exit(1)

            elif args.ai_command == 'merge-suggest':
                from ai.features_vault import merge_suggest_vault

                try:
                    candidates = merge_suggest_vault(
                        args.vault_id,
                        cli.db,
                        threshold=args.threshold,
                        provider=getattr(args, 'provider', None),
                        verbose=args.verbose,
                    )

                    if args.json:
                        print(json.dumps([c.to_dict() for c in candidates], indent=2, default=str))
                    else:
                        _print_merge_candidates(candidates)
                except (ValueError, RuntimeError) as e:
                    if args.json:
                        print(json.dumps({"error": str(e)}), file=sys.stderr)
                    else:
                        print(f"❌ {e}")
                    sys.exit(1)

            elif args.ai_command == 'tag-suggest':
                from ai.features_vault import tag_suggest_vault, tag_suggest_note

                try:
                    # Detect if target is a note ID or vault name
                    note = cli.db.get_note(args.target)
                    if note:
                        result = tag_suggest_note(
                            args.target,
                            cli.db,
                            provider=getattr(args, 'provider', None),
                            verbose=args.verbose,
                        )
                        suggestions = [result] if result else []
                    else:
                        suggestions = tag_suggest_vault(
                            args.target,
                            cli.db,
                            provider=getattr(args, 'provider', None),
                            min_confidence=getattr(args, 'min_confidence', 0.0),
                            apply=getattr(args, 'apply', False),
                            verbose=args.verbose,
                        )

                    if args.json:
                        print(json.dumps([s.to_dict() for s in suggestions], indent=2, default=str))
                    else:
                        _print_tag_suggestions(suggestions)
                except (ValueError, RuntimeError) as e:
                    if args.json:
                        print(json.dumps({"error": str(e)}), file=sys.stderr)
                    else:
                        print(f"❌ {e}")
                    sys.exit(1)

            elif args.ai_command == 'quality':
                from ai.features_vault import note_quality_vault, note_quality_note

                try:
                    # Detect if target is a note ID or vault name
                    note = cli.db.get_note(args.target)
                    if note:
                        result = note_quality_note(
                            args.target,
                            cli.db,
                            verbose=args.verbose,
                        )
                        scores = [result] if result else []
                    else:
                        scores = note_quality_vault(
                            args.target,
                            cli.db,
                            verbose=args.verbose,
                        )

                    if args.json:
                        print(json.dumps([s.to_dict() for s in scores], indent=2, default=str))
                    else:
                        _print_quality_scores(scores)
                except (ValueError, RuntimeError) as e:
                    if args.json:
                        print(json.dumps({"error": str(e)}), file=sys.stderr)
                    else:
                        print(f"❌ {e}")
                    sys.exit(1)

            else:
                ai_parser.print_help()

        elif args.command == 'bridge':
            bridge_cmd = getattr(args, 'bridge_command', None)
            if not bridge_cmd:
                bridge_parser.print_help()
            elif bridge_cmd == 'status':
                status = cli.vault_manager.get_bridge_status()
                if args.json:
                    print(json.dumps(status.to_dict(), indent=2))
                else:
                    _print_bridge_status(status)

        elif args.command == 'trends':
            try:
                report = cli.vault_manager.get_trends(args.vault, lookback_days=args.days)
            except (VaultNotFoundError, ValueError) as e:
                if args.json:
                    print(json.dumps({"error": str(e)}), file=sys.stderr)
                else:
                    print(f"❌ {e}")
                sys.exit(1)
            if args.json:
                print(json.dumps(report.to_dict(), indent=2, default=str))
            else:
                _print_trend_report(report)

        elif args.command == 'stale':
            try:
                report = cli.vault_manager.get_stale_notes(args.vault, limit=args.limit)
            except (VaultNotFoundError, ValueError) as e:
                if args.json:
                    print(json.dumps({"error": str(e)}), file=sys.stderr)
                else:
                    print(f"❌ {e}")
                sys.exit(1)
            if args.json:
                print(json.dumps(report.to_dict(), indent=2, default=str))
            else:
                _print_stale_report(report)

        elif args.command == 'daily-digest':
            try:
                report = cli.vault_manager.get_daily_digest(
                    args.vault, lookback_days=args.days, stale_limit=args.limit)
            except (VaultNotFoundError, ValueError) as e:
                if args.json:
                    print(json.dumps({"error": str(e)}), file=sys.stderr)
                else:
                    print(f"❌ {e}")
                sys.exit(1)
            if args.json:
                print(json.dumps(report.to_dict(), indent=2, default=str))
            else:
                _print_digest_report(report)

        elif args.command == 'doctor':
            import sys as _sys
            _vault_arg = getattr(args, 'vault', None)
            _layers = getattr(args, 'layers', None)
            vault_id = None
            if _vault_arg:
                try:
                    vault = cli.db.get_vault_by_name_or_id(_vault_arg)
                    vault_id = vault['id'] if vault else None
                    if vault_id is None:
                        print(f"❌ Vault not found: {_vault_arg}", file=sys.stderr)
                        sys.exit(1)
                except ValueError as e:
                    print(f"❌ {e}", file=sys.stderr)
                    sys.exit(1)
            from core.doctor import run_checks
            results = run_checks(vault_id=vault_id, layers=_layers)
            if args.json:
                print(json.dumps([r.to_dict() for r in results], indent=2))
            else:
                _print_doctor_results(results)
            has_fail = any(r.status == 'fail' for r in results)
            sys.exit(1 if has_fail else 0)

        elif args.command == 'link':
            from research.obs_link import write_link
            mirror = None if args.mirror == 'auto' else args.mirror
            res = write_link(args.project_dir, vault_root=args.vault_root, mirror=mirror, force=args.force)
            if args.json:
                print(json.dumps(res))
            else:
                verb = 'Created' if res['created'] else 'Exists'
                print(f"{verb}: {res['path']} (mirror: {res['mirror']})")

        elif args.command == 'config':
            sub = getattr(args, 'config_command', None)
            if sub == 'show':
                sys.exit(config_loader.cmd_show())
            elif sub == 'validate':
                sys.exit(config_loader.cmd_validate())
            elif sub == 'migrate':
                sys.exit(config_loader.cmd_migrate(dry_run=getattr(args, 'dry_run', False)))
            elif sub == 'init':
                sys.exit(config_loader.cmd_init())
            elif sub == 'edit':
                sys.exit(config_loader.cmd_edit())
            else:
                config_parser.print_help()

        elif args.command == 'research':
            sys.path.insert(0, str(Path(__file__).parent))
            cfg = config_loader.load()

            sub = getattr(args, 'research_command', None)

            if sub == 'board':
                from research.research_board import load_projects, build_block, write_marked_block
                projects = load_projects(kind=getattr(args, 'kind', None))
                block = build_block(projects)
                out = getattr(args, 'out', None)
                if out:
                    res = write_marked_block(out, block, dry_run=getattr(args, 'dry_run', False))
                    print(f"{res['action']}: {res['path']} (changed={res['changed']})")
                else:
                    print(block)
                sys.exit(0)

            if sub == 'zotero':
                if cfg is None or cfg.research is None or cfg.research.zotero is None:
                    print("research.zotero not configured — run `obs config show` for details")
                    sys.exit(1)
                from research.zotero import ZoteroClient
                zc = ZoteroClient(cfg.research.zotero.database)
                zcmd = getattr(args, 'zotero_command', None)
                if zcmd == 'search':
                    items = zc.search(args.query, limit=args.limit,
                                      item_type=args.item_type, tag=args.tag)
                    if not items:
                        print("No results.")
                    else:
                        for i, item in enumerate(items, 1):
                            print(f"{i}. [{item.key}] {item.title}")
                            if item.authors:
                                print(f"   {', '.join(item.authors[:3])}"
                                      + (' et al.' if len(item.authors) > 3 else ''))
                elif zcmd == 'get':
                    item = zc.get(args.key)
                    if item is None:
                        print(f"Key not found: {args.key}")
                        sys.exit(1)
                    if args.format == 'bibtex':
                        print(item.citation_bibtex())
                    elif args.format == 'full':
                        d = item.to_dict()
                        for k, v in d.items():
                            if v:
                                print(f"{k}: {v}")
                    else:
                        print(item.citation_apa())
                elif zcmd == 'recent':
                    items = zc.recent(limit=args.limit)
                    if not items:
                        print("No recent items.")
                    else:
                        for i, item in enumerate(items, 1):
                            print(f"{i}. [{item.key}] {item.title}")
                else:
                    zotero_parser.print_help()

            elif sub == 'pdf':
                if cfg is None or cfg.research is None or not cfg.research.pdf_directories:
                    print("research.pdf not configured — run `obs config show` for details")
                    sys.exit(1)
                from research.pdf import PDFExtractor
                extractor = PDFExtractor(cfg.research.pdf_directories)
                pcmd = getattr(args, 'pdf_command', None)
                if pcmd == 'search':
                    if not extractor.available():
                        print("pdftotext not found — install poppler: brew install poppler")
                        sys.exit(1)
                    results = extractor.search(args.query, limit=args.limit)
                    if not results:
                        print("No matches.")
                    else:
                        for r in results:
                            print(f"[p.{r.page}] {r.filename}")
                            print(f"  …{r.context}…")
                else:
                    pdf_parser.print_help()

            elif sub == 'course':
                if cfg is None or cfg.research is None or cfg.research.teaching is None:
                    print("research.teaching not configured — run `obs config show` for details")
                    sys.exit(1)
                from research.courses import CourseManager
                cm = CourseManager(cfg.research.teaching.courses_dir)
                ccmd = getattr(args, 'course_command', None)
                if ccmd == 'list':
                    courses = cm.list_courses()
                    if not courses:
                        print("No courses found.")
                    else:
                        print(f"{'Course':<30} {'Status':<10} {'Progress':<10} {'Week':<6} {'Lectures'}")
                        print("-" * 70)
                        for c in courses:
                            print(f"{c.name:<30} {(c.status.status or '-'):<10} "
                                  f"{(c.status.progress or '-'):<10} "
                                  f"{str(c.status.current_week or '-'):<6} {c.lecture_count}")
                elif ccmd == 'show':
                    course = cm.get_course(args.name)
                    if course is None:
                        print(f"Course not found: {args.name}")
                        sys.exit(1)
                    print(f"Course: {course.name}")
                    if course.quarto_config:
                        print(f"Title:  {course.quarto_config.title}")
                    print(f"Status: {course.status.status or '-'}")
                    print(f"Progress: {course.status.progress or '-'}")
                    print(f"Week: {course.status.current_week or '-'}")
                    if course.status.next_action:
                        print(f"Next: {course.status.next_action}")
                    print(f"Lectures: {course.lecture_count}")
                elif ccmd == 'lectures':
                    course = cm.get_course(args.name)
                    if course is None:
                        print(f"Course not found: {args.name}")
                        sys.exit(1)
                    lectures = cm.list_lectures(course)
                    if not lectures:
                        print("No lectures found.")
                    else:
                        for lec in lectures:
                            week = f"Week {lec.week_number}" if lec.week_number else "    "
                            print(f"  {week:<8} {lec.title or lec.filename}")
                else:
                    course_parser.print_help()

            elif sub == 'manuscript':
                if cfg is None or cfg.research is None or cfg.research.writing is None:
                    print("research.writing not configured — run `obs config show` for details")
                    sys.exit(1)
                from research.manuscript import ManuscriptManager
                mm = ManuscriptManager(cfg.research.writing.manuscripts_dir)
                mcmd = getattr(args, 'manuscript_command', None)
                if mcmd == 'list':
                    manuscripts = mm.list_manuscripts(
                        include_archived=getattr(args, 'archived', False))
                    if not manuscripts:
                        print("No manuscripts found.")
                    else:
                        print(f"{'Manuscript':<35} {'Status':<12} {'Progress':<10} {'Words'}")
                        print("-" * 70)
                        for m in manuscripts:
                            print(f"{m.name:<35} {(m.status.status or '-'):<12} "
                                  f"{(m.status.progress or '-'):<10} "
                                  f"{m.word_count or '-'}")
                elif mcmd == 'show':
                    ms = mm.get_manuscript(args.name)
                    if ms is None:
                        print(f"Manuscript not found: {args.name}")
                        sys.exit(1)
                    print(f"Manuscript: {ms.name}")
                    if ms.quarto_config:
                        print(f"Title:    {ms.quarto_config.title}")
                        if ms.quarto_config.authors:
                            print(f"Authors:  {', '.join(ms.quarto_config.authors)}")
                    print(f"Status:   {ms.status.status or '-'}")
                    print(f"Progress: {ms.status.progress or '-'}")
                    if ms.status.target:
                        print(f"Target:   {ms.status.target}")
                    if ms.word_count:
                        print(f"Words:    {ms.word_count}")
                    print(f"Format:   {ms.format}")
                elif mcmd == 'stats':
                    stats = mm.get_statistics()
                    print(f"Total manuscripts: {stats['total']}")
                    print(f"Active:            {stats['by_status'].get('active', 0)}")
                    print(f"Total words:       {stats.get('total_words', 0)}")
                    for fmt, count in stats.get('by_format', {}).items():
                        print(f"  {fmt}: {count}")
                else:
                    ms_parser.print_help()

            elif sub == 'bib':
                if cfg is None or cfg.research is None or cfg.research.writing is None:
                    print("research.writing not configured — run `obs config show` for details")
                    sys.exit(1)
                from research.bibliography import BibliographyManager
                bm = BibliographyManager(cfg.research.writing.manuscripts_dir)
                bcmd = getattr(args, 'bib_command', None)
                if bcmd == 'check':
                    result = bm.check_citations(args.name)
                    if result is None:
                        print(f"Manuscript not found or no .bib file: {args.name}")
                        sys.exit(1)
                    print(f"Cited: {result['cited_count']}  Bibliography: {result['bibliography_count']}")
                    if result['missing']:
                        print(f"\nMissing from bibliography ({len(result['missing'])}):")
                        for k in result['missing']:
                            print(f"  ❌ {k}")
                    if result['unused']:
                        print(f"\nUnused bibliography entries ({len(result['unused'])}):")
                        for k in result['unused']:
                            print(f"  ⚠️  {k}")
                    if result['all_good']:
                        print("✅ All citations match bibliography.")
                else:
                    bib_parser.print_help()

            else:
                research_parser.print_help()

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)


if __name__ == '__main__':
    main()
