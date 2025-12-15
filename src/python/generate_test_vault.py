#!/usr/bin/env python3
"""
Generate synthetic Obsidian vault for testing.

This tool creates realistic test vaults with configurable:
- Number of notes
- Link density (connectivity)
- Tag distribution
- Content variety

Perfect for testing TUI features, graph analysis, and edge cases.
"""

import random
import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta


class VaultGenerator:
    """Generate synthetic Obsidian vaults for testing."""

    def __init__(self, output_dir, num_notes=20, link_density=0.3, tag_count=10, seed=None):
        """Initialize vault generator.

        Args:
            output_dir: Output directory path
            num_notes: Number of notes to generate
            link_density: Average links per note (0.0-1.0)
            tag_count: Number of unique tags
            seed: Random seed for reproducibility
        """
        self.output = Path(output_dir)
        self.num_notes = num_notes
        self.link_density = link_density
        self.tag_count = tag_count

        if seed:
            random.seed(seed)

        self.note_titles = []
        self.tags = []

    def generate(self):
        """Generate complete vault."""
        print(f"🏗️  Generating vault: {self.output}")

        # Create directory structure
        self._create_structure()

        # Generate tag pool
        self._generate_tags()

        # Generate note titles
        self._generate_note_titles()

        # Create notes with links and tags
        self._create_notes()

        # Create special notes (orphans, hubs)
        self._create_special_notes()

        # Summary
        self._print_summary()

    def _create_structure(self):
        """Create vault directory structure."""
        self.output.mkdir(parents=True, exist_ok=True)

        # Create .obsidian directory
        obsidian_dir = self.output / ".obsidian"
        obsidian_dir.mkdir(exist_ok=True)

        # Create app.json
        app_config = {
            "theme": "obsidian",
            "showLineNumber": False,
            "readableLineLength": True
        }
        (obsidian_dir / "app.json").write_text(json.dumps(app_config, indent=2))

        # Create workspace.json (minimal)
        workspace = {
            "main": {
                "id": "test-workspace",
                "type": "split"
            }
        }
        (obsidian_dir / "workspace.json").write_text(json.dumps(workspace, indent=2))

    def _generate_tags(self):
        """Generate tag pool."""
        categories = ["research", "work", "personal", "ideas", "projects", "notes", "reference", "todo"]
        subcategories = ["important", "draft", "review", "archive", "active", "planning"]

        self.tags = []

        # Single-level tags
        for i in range(self.tag_count // 2):
            self.tags.append(random.choice(categories) + f"-{i+1}")

        # Nested tags
        for i in range(self.tag_count - len(self.tags)):
            cat = random.choice(categories)
            sub = random.choice(subcategories)
            self.tags.append(f"{cat}/{sub}")

    def _generate_note_titles(self):
        """Generate note titles."""
        prefixes = ["Introduction to", "Understanding", "Guide to", "Notes on", "Summary of", "Analysis of"]
        topics = [
            "Knowledge Management", "Graph Theory", "Data Structures", "Machine Learning",
            "Statistics", "Research Methods", "Project Planning", "Workflow Design",
            "Productivity", "Note-Taking", "Information Architecture", "Systems Thinking"
        ]

        # Structured titles
        for i in range(self.num_notes // 2):
            prefix = random.choice(prefixes)
            topic = random.choice(topics)
            self.note_titles.append(f"{prefix} {topic}")

        # Simple titles
        for i in range(self.num_notes - len(self.note_titles)):
            self.note_titles.append(f"Note {i+1:03d}")

        # Shuffle for variety
        random.shuffle(self.note_titles)

    def _create_notes(self):
        """Create regular notes with links and tags."""
        for i, title in enumerate(self.note_titles):
            content = self._generate_note_content(title, i)
            filepath = self.output / f"{title}.md"
            filepath.write_text(content)

    def _generate_note_content(self, title, index):
        """Generate content for a single note."""
        lines = []

        # Add frontmatter (30% of notes)
        if random.random() < 0.3:
            lines.append("---")
            lines.append(f"created: {self._random_date()}")
            lines.append(f"modified: {self._random_date()}")
            lines.append(f"status: {random.choice(['draft', 'active', 'review', 'complete'])}")
            lines.append("---")
            lines.append("")

        # Title
        lines.append(f"# {title}")
        lines.append("")

        # Introduction paragraph
        lines.append(f"This is note {index+1} in the test vault. It contains information about {title.lower()}.")
        lines.append("")

        # Add links section
        num_links = random.randint(0, max(1, int(self.num_notes * self.link_density)))
        if num_links > 0:
            lines.append("## Related Notes")
            lines.append("")

            # Select random notes to link to (excluding self)
            available_notes = [t for t in self.note_titles if t != title]
            if available_notes:
                linked_notes = random.sample(available_notes, min(num_links, len(available_notes)))

                for link in linked_notes:
                    # Mix of regular links and aliased links
                    if random.random() < 0.2:
                        alias = f"see {link.split()[-1]}"
                        lines.append(f"- [[{link}|{alias}]]")
                    else:
                        lines.append(f"- [[{link}]]")

                lines.append("")

        # Add content section
        lines.append("## Content")
        lines.append("")
        paragraphs = random.randint(1, 3)
        for _ in range(paragraphs):
            lines.append(f"This is paragraph {_+1} with some content about {title.lower()}. "
                        f"It provides context and information for testing purposes.")
            lines.append("")

        # Add tags
        num_tags = random.randint(1, min(4, len(self.tags)))
        selected_tags = random.sample(self.tags, num_tags)
        lines.append(" ".join(f"#{tag}" for tag in selected_tags))
        lines.append("")

        return "\n".join(lines)

    def _create_special_notes(self):
        """Create special test notes (orphans, hubs, broken links)."""

        # Create orphan note (no incoming links)
        orphan_content = """# Orphan Note

This note has no incoming links from other notes.
It's useful for testing orphan detection.

#orphan #isolated
"""
        (self.output / "Orphan Note.md").write_text(orphan_content)

        # Create hub note (many outgoing links)
        hub_links = "\n".join(f"- [[{title}]]" for title in random.sample(self.note_titles, min(10, len(self.note_titles))))
        hub_content = f"""# Hub Note

This note links to many other notes (hub).
Useful for testing centrality metrics.

## Connections

{hub_links}

#hub #central #important
"""
        (self.output / "Hub Note.md").write_text(hub_content)

        # Create note with broken links
        broken_content = """# Note with Broken Links

This note has links to non-existent notes.

## Broken Links
- [[Non Existent Note 1]]
- [[Missing Note]]
- [[Does Not Exist]]

#broken-links #test
"""
        (self.output / "Broken Links Test.md").write_text(broken_content)

        # Create index note
        index_content = f"""# Index

Welcome to the test vault!

## Overview
- Total notes: {self.num_notes + 3}
- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- Purpose: Testing TUI features

## Special Notes
- [[Hub Note]] - Highly connected
- [[Orphan Note]] - No incoming links
- [[Broken Links Test]] - Contains broken links

## Random Samples
{chr(10).join(f"- [[{title}]]" for title in random.sample(self.note_titles, min(5, len(self.note_titles))))}

#index #main
"""
        (self.output / "Index.md").write_text(index_content)

    def _random_date(self):
        """Generate random date string."""
        days_ago = random.randint(1, 365)
        date = datetime.now() - timedelta(days=days_ago)
        return date.strftime('%Y-%m-%d')

    def _print_summary(self):
        """Print generation summary."""
        actual_files = len(list(self.output.glob("*.md")))

        print(f"✅ Vault generated successfully!")
        print(f"")
        print(f"📊 Statistics:")
        print(f"   Location: {self.output}")
        print(f"   Notes: {actual_files}")
        print(f"   Tags: {len(self.tags)}")
        print(f"   Avg links/note: ~{int(self.num_notes * self.link_density)}")
        print(f"")
        print(f"🧪 Special notes:")
        print(f"   - Index.md (main entry point)")
        print(f"   - Hub Note.md (highly connected)")
        print(f"   - Orphan Note.md (no incoming links)")
        print(f"   - Broken Links Test.md (broken references)")
        print(f"")
        print(f"🚀 Next steps:")
        print(f"   1. obs discover {self.output} --scan -v")
        print(f"   2. obs tui")
        print(f"   3. Test all TUI features!")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic Obsidian vault for testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Small vault (quick tests)
  %(prog)s ~/Documents/TestVault-Small --notes 10 --density 0.2 --tags 5

  # Medium vault (realistic)
  %(prog)s ~/Documents/TestVault-Medium --notes 50 --density 0.3 --tags 15

  # Large vault (stress test)
  %(prog)s ~/Documents/TestVault-Large --notes 200 --density 0.4 --tags 30

  # Reproducible vault (with seed)
  %(prog)s ~/Documents/TestVault --notes 20 --seed 42
        """
    )

    parser.add_argument(
        "output_dir",
        help="Output directory for vault (will be created)"
    )
    parser.add_argument(
        "--notes", "-n",
        type=int,
        default=20,
        help="Number of notes to generate (default: 20)"
    )
    parser.add_argument(
        "--density", "-d",
        type=float,
        default=0.3,
        help="Link density - avg links per note as fraction of total notes (default: 0.3)"
    )
    parser.add_argument(
        "--tags", "-t",
        type=int,
        default=10,
        help="Number of unique tags (default: 10)"
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        help="Random seed for reproducibility (optional)"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.notes < 1:
        parser.error("--notes must be at least 1")
    if not 0.0 <= args.density <= 1.0:
        parser.error("--density must be between 0.0 and 1.0")
    if args.tags < 1:
        parser.error("--tags must be at least 1")

    # Generate vault
    generator = VaultGenerator(
        output_dir=args.output_dir,
        num_notes=args.notes,
        link_density=args.density,
        tag_count=args.tags,
        seed=args.seed
    )

    generator.generate()


if __name__ == "__main__":
    main()
