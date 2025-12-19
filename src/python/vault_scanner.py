#!/usr/bin/env python3
"""
Vault Scanner for Obsidian CLI Ops v2.0

Scans Obsidian vaults, parses markdown files, and populates the database
with notes, links, tags, and metadata.
"""
import asyncio
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple, Callable, Coroutine
from dataclasses import dataclass
import frontmatter

from db_manager import DatabaseManager


@dataclass
class NoteData:
    """Structured note data extracted from markdown file."""
    path: str
    title: str
    content: str
    frontmatter: Dict
    tags: Set[str]
    wikilinks: List[Tuple[str, Optional[str]]]  # (target, display_text)
    word_count: int
    created_at: datetime
    modified_at: datetime


class MarkdownParser:
    """Parses markdown files and extracts metadata, links, and tags."""

    # Regex patterns
    WIKILINK_PATTERN = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')
    TAG_PATTERN = re.compile(r'#([a-zA-Z0-9_/-]+)')
    HEADING_PATTERN = re.compile(r'^#\s+(.+)$', re.MULTILINE)

    @classmethod
    def parse_file(cls, file_path: Path) -> NoteData:
        """
        Parse a markdown file and extract all relevant data.

        Args:
            file_path: Path to markdown file

        Returns:
            NoteData object with extracted information
        """
        # Read file with frontmatter
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        content = post.content
        fm = post.metadata

        # Extract title
        title = cls._extract_title(file_path, content, fm)

        # Extract tags
        tags = cls._extract_tags(content, fm)

        # Extract wikilinks
        wikilinks = cls._extract_wikilinks(content)

        # Get file metadata
        stat = file_path.stat()
        created_at = datetime.fromtimestamp(stat.st_ctime)
        modified_at = datetime.fromtimestamp(stat.st_mtime)

        # Override with frontmatter dates if available
        if 'created' in fm:
            created_at = cls._parse_date(fm['created'])
        if 'modified' in fm or 'updated' in fm:
            modified_at = cls._parse_date(fm.get('modified', fm.get('updated')))

        # Word count
        word_count = len(content.split())

        return NoteData(
            path=str(file_path),
            title=title,
            content=content,
            frontmatter=fm,
            tags=tags,
            wikilinks=wikilinks,
            word_count=word_count,
            created_at=created_at,
            modified_at=modified_at
        )

    @staticmethod
    def _extract_title(file_path: Path, content: str, frontmatter: Dict) -> str:
        """Extract title from frontmatter, first heading, or filename."""
        # 1. Try frontmatter
        if 'title' in frontmatter:
            return frontmatter['title']

        # 2. Try first H1 heading
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        # 3. Use filename
        return file_path.stem

    @classmethod
    def _extract_tags(cls, content: str, frontmatter: Dict) -> Set[str]:
        """Extract tags from content and frontmatter."""
        tags = set()

        # From frontmatter
        if 'tags' in frontmatter:
            fm_tags = frontmatter['tags']
            if isinstance(fm_tags, list):
                tags.update(tag.strip('#') for tag in fm_tags)
            elif isinstance(fm_tags, str):
                tags.update(tag.strip('#') for tag in fm_tags.split(','))

        # From content (inline #tags)
        for match in cls.TAG_PATTERN.finditer(content):
            tags.add(match.group(1))

        return tags

    @classmethod
    def _extract_wikilinks(cls, content: str) -> List[Tuple[str, Optional[str]]]:
        """
        Extract wikilinks from content.

        Returns:
            List of (target, display_text) tuples
        """
        links = []
        for match in cls.WIKILINK_PATTERN.finditer(content):
            target = match.group(1).strip()
            display = match.group(2).strip() if match.group(2) else None
            links.append((target, display))
        return links

    @staticmethod
    def _parse_date(date_str) -> datetime:
        """Parse date from various formats."""
        if isinstance(date_str, datetime):
            return date_str

        # Try common formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue

        # Fallback to current time
        return datetime.now()


class VaultScanner:
    """Scans Obsidian vaults and populates the database."""

    def __init__(self, db: DatabaseManager):
        """
        Initialize vault scanner.

        Args:
            db: Database manager instance
        """
        self.db = db
        self.parser = MarkdownParser()

    async def scan_vault(
        self, 
        vault_path: str, 
        vault_name: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], Coroutine]] = None
    ) -> Dict:
        """
        Asynchronously scan an Obsidian vault and populate database.

        Args:
            vault_path: Path to vault directory
            vault_name: Display name (defaults to directory name)
            progress_callback: Async function to call with (current, total) progress.

        Returns:
            Dictionary with scan statistics
        """
        vault_path = Path(vault_path).resolve()

        if not vault_path.exists():
            raise FileNotFoundError(f"Vault not found: {vault_path}")

        if vault_name is None:
            vault_name = vault_path.name

        # Add vault to database
        vault_id = self.db.add_vault(vault_name, str(vault_path))

        # Start scan record
        scan_id = self.db.start_scan(vault_id)

        try:
            md_files = [
                p for p in vault_path.rglob('*.md') 
                if not any(part.startswith('.') for part in p.parts)
            ]
            total_files = len(md_files)
            
            stats = {
                'notes_scanned': 0, 'notes_added': 0, 'notes_updated': 0,
                'links_added': 0, 'tags_added': 0
            }

            # Process files in batches to avoid blocking
            batch_size = 50
            for i in range(0, total_files, batch_size):
                batch = md_files[i:i + batch_size]
                for md_file in batch:
                    relative_path = str(md_file.relative_to(vault_path))
                    try:
                        note_data = self.parser.parse_file(md_file)
                        existing_note = self.db.get_note_by_path(vault_id, relative_path)
                        
                        metadata = note_data.frontmatter.copy()
                        metadata['created_at'] = note_data.created_at.isoformat()
                        metadata['modified_at'] = note_data.modified_at.isoformat()

                        note_id = self.db.add_note(
                            vault_id=vault_id, path=relative_path, title=note_data.title,
                            content=note_data.content, metadata=metadata
                        )

                        if existing_note:
                            stats['notes_updated'] += 1
                        else:
                            stats['notes_added'] += 1
                        stats['notes_scanned'] += 1

                        for tag in note_data.tags:
                            self.db.add_note_tag(note_id, tag)
                            stats['tags_added'] += 1
                        for target, display_text in note_data.wikilinks:
                            self.db.add_link(note_id, target, display_text)
                            stats['links_added'] += 1

                    except Exception:
                        continue
                
                # Report progress
                if progress_callback:
                    await progress_callback(i + len(batch), total_files)
                
                await asyncio.sleep(0.01) # Yield control to the event loop

            self.db.update_vault_scan_time(vault_id)
            self.db.complete_scan(
                scan_id, stats['notes_scanned'], stats['notes_added'],
                stats['notes_updated'], 0
            )

            return stats

        except Exception as e:
            self.db.fail_scan(scan_id, str(e))
            raise

    def discover_vaults(self, root_path: str, verbose: bool = False) -> List[str]:
        """
        Discover Obsidian vaults in a directory tree.

        Looks for directories containing .obsidian folders.

        Args:
            root_path: Root directory to search
            verbose: Print progress

        Returns:
            List of vault paths found
        """
        root_path = Path(root_path).resolve()
        vaults = []

        if verbose:
            print(f"🔍 Searching for vaults in: {root_path}")

        for dirpath, dirnames, filenames in os.walk(root_path):
            # Check if this directory has .obsidian subdirectory
            if '.obsidian' in dirnames:
                vaults.append(dirpath)
                if verbose:
                    print(f"   Found vault: {dirpath}")

                # Don't recurse into found vaults
                dirnames.clear()

        if verbose:
            print(f"\n✓ Found {len(vaults)} vault(s)")

        return vaults


def main():
    """CLI interface for vault scanner."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python vault_scanner.py <vault_path>")
        sys.exit(1)

    vault_path = sys.argv[1]

    # Initialize database
    db = DatabaseManager()

    # Create scanner
    scanner = VaultScanner(db)

    # Scan vault
    try:
        # Since this is a CLI, we don't have an event loop.
        # We run the async scan_vault using asyncio.run
        stats = asyncio.run(scanner.scan_vault(vault_path, verbose=True))
        print("\n📊 Database Stats:")
        db_stats = db.get_stats()
        for key, value in db_stats.items():
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()