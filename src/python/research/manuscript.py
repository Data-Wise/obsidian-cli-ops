"""Manuscript management (ported from nexus-cli)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ManuscriptStatus:
    """Status metadata for a manuscript, parsed from its ``.STATUS`` file."""

    status: str = "unknown"
    priority: str = "--"
    progress: int = 0
    next_action: str = ""
    manuscript_type: str = "research"
    target: str = ""

    @classmethod
    def from_file(cls, path: Path) -> ManuscriptStatus:
        """Parse a ``.STATUS`` file into a ``ManuscriptStatus``.

        Args:
            path: Path to the ``.STATUS`` file.

        Returns:
            A populated ``ManuscriptStatus``, or one with default values if
            the file does not exist.
        """
        if not path.exists():
            return cls()
        content = path.read_text()
        result = cls()
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("status:"):
                result.status = line.split(":", 1)[1].strip()
            elif line.startswith("priority:"):
                result.priority = line.split(":", 1)[1].strip()
            elif line.startswith("progress:"):
                try:
                    result.progress = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("next:"):
                result.next_action = line.split(":", 1)[1].strip()
            elif line.startswith("type:"):
                result.manuscript_type = line.split(":", 1)[1].strip()
            elif line.startswith("target:"):
                result.target = line.split(":", 1)[1].strip()
        return result


@dataclass
class QuartoManuscript:
    """Manuscript metadata parsed from a Quarto ``_quarto.yml`` config."""

    title: str = ""
    authors: list[str] = field(default_factory=list)
    article_file: str = "index.qmd"
    format_type: str = "manuscript"

    @classmethod
    def from_file(cls, path: Path) -> QuartoManuscript | None:
        """Parse a Quarto ``_quarto.yml`` file into a ``QuartoManuscript``.

        Args:
            path: Path to the ``_quarto.yml`` config file.

        Returns:
            A populated ``QuartoManuscript``, or ``None`` if the file does not
            exist or cannot be parsed as YAML.
        """
        if not path.exists():
            return None
        try:
            with open(path) as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            return None
        result = cls()
        project = data.get("project", {})
        result.format_type = project.get("type", "default")
        manuscript = data.get("manuscript", {})
        result.article_file = manuscript.get("article", "index.qmd")
        result.title = data.get("title", "")
        authors = data.get("author", [])
        if isinstance(authors, list):
            for author in authors:
                if isinstance(author, dict):
                    name = author.get("name", "")
                    if name:
                        result.authors.append(name)
                elif isinstance(author, str):
                    result.authors.append(author)
        return result


@dataclass
class Manuscript:
    """A single research manuscript with its status, format, and metadata."""

    name: str
    path: str
    title: str = ""
    status: str = "unknown"
    progress: int = 0
    target: str = ""
    next_action: str = ""
    authors: list[str] = field(default_factory=list)
    format_type: str = "unknown"
    main_file: str = ""
    word_count: int = 0
    last_modified: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict of the manuscript's fields.

        ``title`` falls back to ``name`` when empty, and ``last_modified`` is
        rendered as an ISO-8601 string (or ``None``).
        """
        return {
            "name": self.name,
            "path": self.path,
            "title": self.title or self.name,
            "status": self.status,
            "progress": self.progress,
            "target": self.target,
            "next_action": self.next_action,
            "authors": self.authors,
            "format_type": self.format_type,
            "main_file": self.main_file,
            "word_count": self.word_count,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
        }


class ManuscriptManager:
    """Manage research manuscripts."""

    def __init__(self, manuscripts_dir: Path, templates_dir: Path | None = None):
        self.manuscripts_dir = Path(manuscripts_dir).expanduser()
        self.templates_dir = Path(templates_dir).expanduser() if templates_dir else None

    def exists(self) -> bool:
        """Return whether the configured manuscripts directory exists."""
        return self.manuscripts_dir.exists()

    def list_manuscripts(self, include_archived: bool = False) -> list[Manuscript]:
        """List manuscripts found in the manuscripts directory.

        Each immediate subdirectory (excluding dotfiles) is loaded as a
        manuscript. Results are sorted with active/draft/revision items first,
        then by descending progress and name.

        Args:
            include_archived: If ``False`` (default), manuscripts whose status
                contains "archive" or "complete" are omitted.

        Returns:
            The matching manuscripts, or an empty list if the directory does
            not exist.
        """
        if not self.exists():
            return []
        manuscripts = []
        for ms_path in sorted(self.manuscripts_dir.iterdir()):
            if not ms_path.is_dir() or ms_path.name.startswith("."):
                continue
            manuscript = self._load_manuscript(ms_path)
            if manuscript:
                if not include_archived:
                    status_lower = manuscript.status.lower()
                    if "archive" in status_lower or "complete" in status_lower:
                        continue
                manuscripts.append(manuscript)
        manuscripts.sort(key=lambda m: (
            0 if m.status.lower() in ("active", "draft", "revision") else 1,
            -m.progress,
            m.name.lower(),
        ))
        return manuscripts

    def get_manuscript(self, name: str) -> Manuscript | None:
        """Load a single manuscript by directory name.

        Falls back to a case-insensitive exact or substring match against
        existing manuscript directories when there is no exact match.

        Args:
            name: Manuscript directory name (or partial name) to look up.

        Returns:
            The matching ``Manuscript``, or ``None`` if no match is found.
        """
        ms_path = self.manuscripts_dir / name
        if not ms_path.exists():
            for p in self.manuscripts_dir.iterdir():
                if p.name.lower() == name.lower() or name.lower() in p.name.lower():
                    ms_path = p
                    break
            else:
                return None
        return self._load_manuscript(ms_path)

    def _load_manuscript(self, ms_path: Path) -> Manuscript | None:
        if not ms_path.is_dir():
            return None
        status = ManuscriptStatus.from_file(ms_path / ".STATUS")
        format_type = "unknown"
        title = ""
        authors: list[str] = []
        main_file = ""

        quarto_file = ms_path / "_quarto.yml"
        if quarto_file.exists():
            format_type = "quarto"
            qc = QuartoManuscript.from_file(quarto_file)
            if qc:
                title = qc.title
                authors = qc.authors
                main_file = qc.article_file
                manuscript_subfolder = ms_path / "_manuscript"
                if manuscript_subfolder.exists():
                    index_file = manuscript_subfolder / "index.qmd"
                    if index_file.exists():
                        main_file = str(index_file.relative_to(ms_path))

        tex_files = list(ms_path.glob("*.tex"))
        if tex_files and format_type == "unknown":
            format_type = "latex"
            for tf in tex_files:
                if tf.stem in ("main", ms_path.name, "manuscript"):
                    main_file = tf.name
                    break
            if not main_file and tex_files:
                main_file = tex_files[0].name

        if format_type == "unknown":
            md_files = list(ms_path.glob("*.md"))
            if md_files:
                format_type = "markdown"
                for mf in md_files:
                    if mf.stem in ("manuscript", "main", "README"):
                        main_file = mf.name
                        break

        last_modified = None
        try:
            last_modified = datetime.fromtimestamp(ms_path.stat().st_mtime)
        except Exception:
            pass

        word_count = 0
        if main_file:
            main_path = ms_path / main_file
            if main_path.exists():
                word_count = self._estimate_word_count(main_path)

        return Manuscript(
            name=ms_path.name,
            path=str(ms_path),
            title=title or ms_path.name.replace("-", " ").replace("_", " ").title(),
            status=status.status,
            progress=status.progress,
            target=status.target,
            next_action=status.next_action,
            authors=authors,
            format_type=format_type,
            main_file=main_file,
            word_count=word_count,
            last_modified=last_modified,
        )

    def _estimate_word_count(self, path: Path) -> int:
        try:
            content = path.read_text()
            if content.startswith("---"):
                end = content.find("---", 3)
                if end > 0:
                    content = content[end + 3:]
            content = re.sub(r"```[\s\S]*?```", "", content)
            content = re.sub(r"`[^`]+`", "", content)
            content = re.sub(r"\$\$[\s\S]*?\$\$", "", content)
            content = re.sub(r"\$[^$]+\$", "", content)
            return len(content.split())
        except Exception:
            return 0

    def get_active(self) -> list[Manuscript]:
        """Return non-archived manuscripts in an active working state.

        Includes manuscripts whose status is active, draft, revision, or under
        review.
        """
        return [
            m for m in self.list_manuscripts(include_archived=False)
            if m.status.lower() in ("active", "draft", "revision", "under review")
        ]

    def search(self, query: str) -> list[Manuscript]:
        """Search all manuscripts (including archived) by name or title.

        Args:
            query: Regular-expression pattern matched case-insensitively
                against each manuscript's name and title.

        Returns:
            Manuscripts whose name or title matches the pattern.
        """
        pattern = re.compile(query, re.IGNORECASE)
        return [
            m for m in self.list_manuscripts(include_archived=True)
            if pattern.search(m.name) or pattern.search(m.title)
        ]

    def get_statistics(self) -> dict[str, Any]:
        """Compute aggregate statistics across all manuscripts.

        Returns:
            A dict with ``total`` count, ``by_status`` and ``by_format``
            breakdown counts, and ``total_words`` summed across manuscripts.
        """
        all_manuscripts = self.list_manuscripts(include_archived=True)
        stats: dict[str, Any] = {"total": len(all_manuscripts), "by_status": {}, "by_format": {}, "total_words": 0}
        for m in all_manuscripts:
            status = m.status.lower()
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            stats["by_format"][m.format_type] = stats["by_format"].get(m.format_type, 0) + 1
            stats["total_words"] += m.word_count
        return stats
