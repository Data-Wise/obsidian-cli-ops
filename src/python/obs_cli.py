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
from core.vault_manager import VaultManager
from core.graph_analyzer import GraphAnalyzer
from core.exceptions import VaultNotFoundError, ScanError, AnalysisError
from utils import format_relative_time

# Rich console for formatted output
console = Console()


class ObsCLI:
    """Main CLI handler for obs Python commands (presentation layer only)."""

    def __init__(self):
        """Initialize CLI."""
        self.db = DatabaseManager()
        self.vault_manager = VaultManager(self.db)
        self.graph_analyzer = GraphAnalyzer(self.db)

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
            link_count = sum(len(self.db.get_outgoing_links(note['id'])) for note in notes)
            tag_stats = self.db.get_tag_stats()

            # Graph health
            orphans = self.db.get_orphaned_notes(vault_id)
            hubs = self.db.get_hub_notes(vault_id, limit=10)
            broken = self.db.get_broken_links(vault_id)
            broken_count = sum(b['broken_count'] for b in broken)

            # Build stats content
            stats_content = f"""[bold]Path:[/] {vault['path']}
[bold]Last Scanned:[/] {format_relative_time(vault.get('last_scanned'))}

[cyan]Content[/]
  Notes: [bold]{len(notes)}[/]
  Links: [bold]{link_count}[/]
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
                result = cli.graph_analyzer.analyze_vault(vault['id'])
                print(json.dumps(result, indent=2, default=str))
            else:
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
                    link_count = sum(len(cli.db.get_outgoing_links(note['id'])) for note in notes)
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
                        "tags": len(tag_stats),
                        "orphaned": len(orphans),
                        "hubs": len(hubs),
                        "broken_links": broken_count,
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


    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)


if __name__ == '__main__':
    main()
