#!/usr/bin/env python3
"""
Obsidian CLI Ops - Python CLI Entry Point

Main CLI for v2.0 Python functionality:
- Vault discovery and scanning
- Graph analysis and metrics
- Database management
"""

import sys
import argparse
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
                    result = self.vault_manager.scan_vault(vault_path, vault_name)
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
            result = self.vault_manager.scan_vault(vault_path, vault_name)

            # Print scan result
            self._print_scan_result(result, verbose)

            # Analyze graph if requested
            if analyze:
                print("")
                self.analyze(result.vault_id, verbose=verbose)

        except (VaultNotFoundError, ScanError) as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    def analyze(self, vault_id: str, verbose: bool = False):
        """
        Analyze vault graph and calculate metrics.

        Args:
            vault_id: Vault ID to analyze
            verbose: Print detailed output
        """
        try:
            # Run analysis using core layer
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

    def stats(self, vault_id: Optional[str] = None):
        """
        Show database statistics with Rich panels.

        Args:
            vault_id: Optional vault ID to filter
        """
        if vault_id:
            vault = self.db.get_vault(vault_id)
            if not vault:
                console.print(f"[red]❌ Vault not found: {vault_id}[/]")
                sys.exit(1)

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


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Obsidian CLI Ops - Knowledge Graph Management',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')

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
    analyze_parser.add_argument('vault_id', help='Vault ID')

    # stats command
    stats_parser = subparsers.add_parser('stats',
                                        help='Show statistics')
    stats_parser.add_argument('--vault', help='Vault ID')

    # vaults command
    subparsers.add_parser('vaults',
                         help='List all vaults')

    # db command
    db_parser = subparsers.add_parser('db',
                                     help='Database management')
    db_subparsers = db_parser.add_subparsers(dest='db_command')
    db_subparsers.add_parser('init', help='Initialize database')
    db_subparsers.add_parser('stats', help='Show database stats')

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

    analyze_parser = ai_subparsers.add_parser('analyze', help='Analyze a note')
    analyze_parser.add_argument('note_id', help='Note ID to analyze')
    analyze_parser.add_argument('--provider', help='Use specific AI provider')

    duplicates_parser = ai_subparsers.add_parser('duplicates', help='Find duplicate notes')
    duplicates_parser.add_argument('vault_id', help='Vault ID to scan')
    duplicates_parser.add_argument('--threshold', type=float, default=0.85, help='Similarity threshold')
    duplicates_parser.add_argument('--limit', type=int, default=50, help='Max duplicate groups')
    duplicates_parser.add_argument('--provider', help='Use specific AI provider')


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
            cli.analyze(args.vault_id, verbose=args.verbose)

        elif args.command == 'stats':
            cli.stats(vault_id=args.vault)

        elif args.command == 'vaults':
            cli.list_vaults()

        elif args.command == 'db':
            if args.db_command == 'init':
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

                print(f"🔍 Finding similar notes to: {args.note_id}\n")
                try:
                    matches = find_similar_notes(
                        args.note_id,
                        cli.db,
                        limit=args.limit,
                        min_similarity=args.threshold,
                        provider=args.provider
                    )

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
                    print(f"❌ {e}")
                    sys.exit(1)
                except RuntimeError as e:
                    print(f"❌ {e}")
                    sys.exit(1)

            elif args.ai_command == 'analyze':
                # Analyze a note
                from ai.features import analyze_note as ai_analyze_note

                print(f"🔬 Analyzing note: {args.note_id}\n")
                try:
                    result = ai_analyze_note(
                        args.note_id,
                        cli.db,
                        provider=args.provider
                    )

                    # Print analysis results
                    print("📊 Analysis Results:\n")

                    if result.topics:
                        print(f"  Topics: {', '.join(result.topics)}")
                    if result.themes:
                        print(f"  Themes: {', '.join(result.themes)}")
                    if result.suggested_tags:
                        print(f"  Suggested Tags: {', '.join(result.suggested_tags)}")

                    print()
                    print("  Quality Scores:")
                    for key, value in result.quality.items():
                        print(f"    • {key}: {value}/10")

                    if result.suggestions:
                        print()
                        print("  💡 Suggestions:")
                        for suggestion in result.suggestions:
                            print(f"    • {suggestion}")

                except ValueError as e:
                    print(f"❌ {e}")
                    sys.exit(1)
                except RuntimeError as e:
                    print(f"❌ {e}")
                    sys.exit(1)

            elif args.ai_command == 'duplicates':
                # Find duplicate notes
                from ai.features import find_duplicates

                print(f"🔍 Scanning vault for duplicates: {args.vault_id}\n")
                try:
                    groups = find_duplicates(
                        args.vault_id,
                        cli.db,
                        threshold=args.threshold,
                        limit=args.limit,
                        provider=args.provider
                    )

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
                    print(f"❌ {e}")
                    sys.exit(1)
                except RuntimeError as e:
                    print(f"❌ {e}")
                    sys.exit(1)

            else:
                ai_parser.print_help()


    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)


if __name__ == '__main__':
    main()
