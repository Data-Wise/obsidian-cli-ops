"""Bibliography management (ported from nexus-cli; imports from local research.zotero)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class BibEntry:
    key: str
    entry_type: str
    title: str
    authors: list[str] = field(default_factory=list)
    year: str = ""
    journal: str = ""
    doi: str = ""
    url: str = ""
    abstract: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "entry_type": self.entry_type,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "journal": self.journal,
            "doi": self.doi,
            "url": self.url,
            "abstract": self.abstract[:200] + "..." if len(self.abstract) > 200 else self.abstract,
        }

    def format_apa(self) -> str:
        if not self.authors:
            author_str = "Unknown"
        elif len(self.authors) == 1:
            author_str = self.authors[0]
        elif len(self.authors) == 2:
            author_str = f"{self.authors[0]} & {self.authors[1]}"
        elif len(self.authors) <= 5:
            author_str = ", ".join(self.authors[:-1]) + f", & {self.authors[-1]}"
        else:
            author_str = f"{self.authors[0]} et al."
        return f"{author_str} ({self.year or 'n.d.'}). {self.title}."


class BibFileParser:
    def parse_file(self, path: Path) -> list[BibEntry]:
        path = Path(path).expanduser()
        if not path.exists():
            return []
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            return self._parse_bibtex(content)
        except Exception:
            return []

    def _parse_bibtex(self, content: str) -> list[BibEntry]:
        entries = []
        entry_pattern = re.compile(r"@(\w+)\s*\{\s*([^,]+)\s*,(.+?)\n\s*\}", re.DOTALL | re.MULTILINE)
        for match in entry_pattern.finditer(content):
            entry_type = match.group(1).lower()
            if entry_type in ("preamble", "string", "comment"):
                continue
            key = match.group(2).strip()
            fields = self._parse_fields(match.group(3))
            entries.append(BibEntry(
                key=key,
                entry_type=entry_type,
                title=fields.get("title", ""),
                authors=self._parse_authors(fields.get("author", "")),
                year=fields.get("year", ""),
                journal=fields.get("journal", fields.get("booktitle", "")),
                doi=fields.get("doi", ""),
                url=fields.get("url", ""),
                abstract=fields.get("abstract", ""),
            ))
        return entries

    def _parse_fields(self, text: str) -> dict[str, str]:
        fields: dict[str, str] = {}
        field_pattern = re.compile(
            r"(\w+)\s*=\s*(?:\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}|\"([^\"]*)\"|(\d+))",
            re.DOTALL,
        )
        for match in field_pattern.finditer(text):
            field_name = match.group(1).lower()
            value = match.group(2) or match.group(3) or match.group(4) or ""
            value = re.sub(r"\s+", " ", value.strip()).replace("{", "").replace("}", "")
            fields[field_name] = value
        return fields

    def _parse_authors(self, author_str: str) -> list[str]:
        if not author_str:
            return []
        authors = re.split(r"\s+and\s+", author_str, flags=re.IGNORECASE)
        cleaned = []
        for author in authors:
            author = author.strip()
            if "," in author:
                parts = author.split(",", 1)
                if len(parts) == 2:
                    author = f"{parts[1].strip()} {parts[0].strip()}"
            cleaned.append(author)
        return cleaned


class BibliographyManager:
    """Manage bibliographies for manuscripts."""

    def __init__(self, zotero_db: Path | None = None):
        self.zotero_db = Path(zotero_db).expanduser() if zotero_db else None
        self._parser = BibFileParser()

    def find_bib_files(self, manuscript_path: Path) -> list[Path]:
        manuscript_path = Path(manuscript_path).expanduser()
        if not manuscript_path.exists():
            return []
        return sorted(manuscript_path.rglob("*.bib"))

    def get_manuscript_bibliography(self, manuscript_path: Path) -> list[BibEntry]:
        all_entries: list[BibEntry] = []
        for bib_file in self.find_bib_files(manuscript_path):
            all_entries.extend(self._parser.parse_file(bib_file))
        seen: set[str] = set()
        unique = []
        for entry in all_entries:
            if entry.key not in seen:
                seen.add(entry.key)
                unique.append(entry)
        return unique

    def find_cited_keys(self, content: str) -> list[str]:
        keys: set[str] = set()
        for match in re.compile(r"\\cite[pt]?\{([^}]+)\}").finditer(content):
            for key in match.group(1).split(","):
                keys.add(key.strip())
        for match in re.compile(r"@([\w:-]+)").finditer(content):
            key = match.group(1)
            if key not in ("fig", "tbl", "eq", "sec", "lst"):
                keys.add(key)
        return sorted(keys)

    def check_citations(self, manuscript_path: Path) -> dict[str, Any]:
        manuscript_path = Path(manuscript_path).expanduser()
        bib_entries = self.get_manuscript_bibliography(manuscript_path)
        bib_keys = {e.key for e in bib_entries}
        cited_keys: set[str] = set()
        for pattern in ["*.qmd", "*.tex"]:
            for source_file in manuscript_path.rglob(pattern):
                try:
                    cited_keys.update(self.find_cited_keys(source_file.read_text()))
                except Exception:
                    pass
        missing = cited_keys - bib_keys
        unused = bib_keys - cited_keys
        return {
            "cited_count": len(cited_keys),
            "bibliography_count": len(bib_keys),
            "missing": sorted(missing),
            "unused": sorted(unused),
            "all_good": len(missing) == 0,
        }
