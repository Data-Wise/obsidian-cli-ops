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

from db_manager import DatabaseManager
from core.vault_manager import VaultManager
from core.graph_analyzer import GraphAnalyzer
from core.exceptions import VaultNotFoundError, ScanError, AnalysisError
from utils import format_relative_time


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
        Show database statistics.

        Args:
            vault_id: Optional vault ID to filter
        """
        if vault_id:
            vault = self.db.get_vault(vault_id)
            if not vault:
                print(f"❌ Vault not found: {vault_id}")
                sys.exit(1)

            print(f"\n📊 Vault Statistics: {vault['name']}")
            print(f"   Path: {vault['path']}")
            print(f"   Last scanned: {format_relative_time(vault.get('last_scanned'))}")

            notes = self.db.list_notes(vault_id)
            print(f"\n   Notes: {len(notes)}")

            # Count links
            link_count = 0
            for note in notes:
                link_count += len(self.db.get_outgoing_links(note['id']))
            print(f"   Links: {link_count}")

            # Tag stats
            tag_stats = self.db.get_tag_stats()
            vault_tags = [t for t in tag_stats]  # TODO: Filter by vault
            print(f"   Tags: {len(vault_tags)}")

            # Graph stats
            orphans = self.db.get_orphaned_notes(vault_id)
            hubs = self.db.get_hub_notes(vault_id, limit=1)
            broken = self.db.get_broken_links(vault_id)

            print(f"\n   Orphaned notes: {len(orphans)}")
            print(f"   Hub notes (>10 links): {len(hubs)}")
            print(f"   Broken links: {sum(b['broken_count'] for b in broken)}")

        else:
            # Global stats
            stats = self.db.get_stats()
            print("\n📊 Database Statistics:")
            print(f"   Vaults: {stats['vaults']}")
            print(f"   Notes: {stats['notes']}")
            print(f"   Links: {stats['links']}")
            print(f"   Tags: {stats['tags']}")
            print(f"   Orphaned notes: {stats['orphaned_notes']}")
            print(f"   Broken links: {stats['broken_links']}")

    def list_vaults(self):
        """List all vaults in database."""
        vaults = self.vault_manager.list_vaults()

        if not vaults:
            print("No vaults in database.")
            print("\nUse 'obs discover' to find and scan vaults.")
            return

        print("\n📚 Vaults:\n")
        for vault in vaults:
            print(f"  {vault.name}")
            print(f"    Path: {vault.path}")
            print(f"    Notes: {vault.note_count}")
            print(f"    Last scanned: {format_relative_time(vault.last_scanned)}")
            print(f"    ID: {vault.id}")
            print("")

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

    # tui command
    tui_parser = subparsers.add_parser('tui',
                                       help='Launch interactive TUI')
    tui_parser.add_argument('--vault-id', type=int, help='Open specific vault')
    tui_parser.add_argument('--screen', choices=['vaults', 'notes', 'graph', 'stats'],
                           help='Open specific screen')

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

            else:
                ai_parser.print_help()

        elif args.command == 'tui':
            # Import TUI app only when needed
            try:
                from tui.app import ObsidianTUI

                app = ObsidianTUI()
                app.run()

            except ImportError as e:
                print(f"❌ Error: TUI dependencies not available")
                print(f"   Please ensure 'textual' is installed:")
                print(f"   pip install textual")
                sys.exit(1)
            except Exception as e:
                print(f"❌ Error launching TUI: {e}")
                sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)


if __name__ == '__main__':
    main()
