"""Zotero library integration (ported from nexus-cli)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ZoteroItem:
    """A Zotero library item."""

    item_id: int
    key: str
    item_type: str
    title: str
    authors: list[str] = field(default_factory=list)
    date: str = ""
    abstract: str = ""
    doi: str = ""
    url: str = ""
    tags: list[str] = field(default_factory=list)
    collections: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Return the item as a plain dict (abstract truncated to 200 chars)."""
        return {
            "item_id": self.item_id,
            "key": self.key,
            "item_type": self.item_type,
            "title": self.title,
            "authors": self.authors,
            "date": self.date,
            "abstract": self.abstract[:200] + "..." if len(self.abstract) > 200 else self.abstract,
            "doi": self.doi,
            "url": self.url,
            "tags": self.tags,
            "collections": self.collections,
        }

    def citation_apa(self) -> str:
        """Format the item as an APA-style citation string.

        Collapses 6+ authors to "First et al.", joins 2-5 with ", & ",
        and uses "n.d." when no date is present.
        """
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
        year = self.date[:4] if self.date else "n.d."
        return f"{author_str} ({year}). {self.title}."

    def citation_bibtex(self) -> str:
        """Format the item as a BibTeX entry.

        Derives the cite key from the first author's surname plus year,
        maps the Zotero item type to a BibTeX entry type (defaulting to
        "misc"), and emits only the fields that are populated.
        """
        if self.authors:
            first_author = self.authors[0].split()[-1].lower()
        else:
            first_author = "unknown"
        year = self.date[:4] if self.date else "0000"
        cite_key = f"{first_author}{year}"
        bibtex_type = {
            "journalArticle": "article",
            "book": "book",
            "bookSection": "incollection",
            "conferencePaper": "inproceedings",
            "thesis": "phdthesis",
            "report": "techreport",
        }.get(self.item_type, "misc")
        lines = [f"@{bibtex_type}{{{cite_key},"]
        lines.append(f"  title = {{{self.title}}},")
        if self.authors:
            lines.append(f"  author = {{{' and '.join(self.authors)}}},")
        if self.date:
            lines.append(f"  year = {{{year}}},")
        if self.doi:
            lines.append(f"  doi = {{{self.doi}}},")
        if self.url:
            lines.append(f"  url = {{{self.url}}},")
        lines.append("}")
        return "\n".join(lines)


class ZoteroClient:
    """Client for querying Zotero SQLite database."""

    FIELD_TITLE = 1
    FIELD_ABSTRACT = 2
    FIELD_DATE = 6
    FIELD_URL = 13
    FIELD_DOI = 59

    def __init__(self, db_path: Path, storage_path: Path | None = None):
        self.db_path = Path(db_path).expanduser()
        self.storage_path = Path(storage_path).expanduser() if storage_path else None

    def exists(self) -> bool:
        """Return True if the Zotero database file exists on disk."""
        return self.db_path.exists()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def count(self) -> int:
        """Return the number of library items, excluding attachments, annotations, and notes.

        Returns 0 if the database does not exist.
        """
        if not self.exists():
            return 0
        conn = self._connect()
        try:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM items i
                JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
                WHERE it.typeName NOT IN ('attachment', 'annotation', 'note')
            """)
            result = cursor.fetchone()
            return int(result[0]) if result else 0
        finally:
            conn.close()

    def _get_field_value(self, conn: sqlite3.Connection, item_id: int, field_id: int) -> str:
        cursor = conn.execute(
            "SELECT idv.value FROM itemData id "
            "JOIN itemDataValues idv ON id.valueID = idv.valueID "
            "WHERE id.itemID = ? AND id.fieldID = ?",
            (item_id, field_id),
        )
        row = cursor.fetchone()
        return row[0] if row else ""

    def _get_authors(self, conn: sqlite3.Connection, item_id: int) -> list[str]:
        cursor = conn.execute(
            "SELECT c.firstName, c.lastName FROM itemCreators ic "
            "JOIN creators c ON ic.creatorID = c.creatorID "
            "JOIN creatorTypes ct ON ic.creatorTypeID = ct.creatorTypeID "
            "WHERE ic.itemID = ? AND ct.creatorType = 'author' ORDER BY ic.orderIndex",
            (item_id,),
        )
        authors = []
        for row in cursor:
            first = row["firstName"] or ""
            last = row["lastName"] or ""
            if first and last:
                authors.append(f"{first} {last}")
            elif last:
                authors.append(last)
            elif first:
                authors.append(first)
        return authors

    def _get_tags(self, conn: sqlite3.Connection, item_id: int) -> list[str]:
        cursor = conn.execute(
            "SELECT t.name FROM itemTags it JOIN tags t ON it.tagID = t.tagID WHERE it.itemID = ?",
            (item_id,),
        )
        return [row["name"] for row in cursor]

    def _get_collections(self, conn: sqlite3.Connection, item_id: int) -> list[str]:
        cursor = conn.execute(
            "SELECT c.collectionName FROM collectionItems ci "
            "JOIN collections c ON ci.collectionID = c.collectionID WHERE ci.itemID = ?",
            (item_id,),
        )
        return [row["collectionName"] for row in cursor]

    def _build_item(self, conn: sqlite3.Connection, row: sqlite3.Row) -> ZoteroItem:
        item_id = row["itemID"]
        return ZoteroItem(
            item_id=item_id,
            key=row["key"],
            item_type=row["typeName"],
            title=self._get_field_value(conn, item_id, self.FIELD_TITLE),
            authors=self._get_authors(conn, item_id),
            date=self._get_field_value(conn, item_id, self.FIELD_DATE),
            abstract=self._get_field_value(conn, item_id, self.FIELD_ABSTRACT),
            doi=self._get_field_value(conn, item_id, self.FIELD_DOI),
            url=self._get_field_value(conn, item_id, self.FIELD_URL),
            tags=self._get_tags(conn, item_id),
            collections=self._get_collections(conn, item_id),
        )

    def search(
        self,
        query: str,
        limit: int = 20,
        item_type: str | None = None,
        tag: str | None = None,
    ) -> list[ZoteroItem]:
        """Search the library by matching the query against title/field values and author names.

        Args:
            query: Substring matched (LIKE) against item field values and
                creator first/last names.
            limit: Maximum number of items to return.
            item_type: Optional exact item-type name to filter by.
            tag: Optional tag name (LIKE-matched) to further restrict results.

        Returns:
            Matching items ordered by most recently modified, or an empty
            list if the database does not exist.
        """
        if not self.exists():
            return []
        conn = self._connect()
        try:
            sql = """
                SELECT DISTINCT i.itemID, i.key, it.typeName
                FROM items i
                JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
                LEFT JOIN itemData id ON i.itemID = id.itemID
                LEFT JOIN itemDataValues idv ON id.valueID = idv.valueID
                LEFT JOIN itemCreators ic ON i.itemID = ic.itemID
                LEFT JOIN creators c ON ic.creatorID = c.creatorID
                WHERE it.typeName NOT IN ('attachment', 'annotation', 'note')
                AND (idv.value LIKE ? OR c.firstName LIKE ? OR c.lastName LIKE ?)
            """
            params: list[str] = [f"%{query}%", f"%{query}%", f"%{query}%"]
            if item_type:
                sql += " AND it.typeName = ?"
                params.append(item_type)
            if tag:
                sql += (
                    " AND i.itemID IN ("
                    "SELECT it2.itemID FROM itemTags it2 "
                    "JOIN tags t ON it2.tagID = t.tagID WHERE t.name LIKE ?)"
                )
                params.append(f"%{tag}%")
            sql += f" ORDER BY i.dateModified DESC LIMIT {limit}"
            cursor = conn.execute(sql, params)
            return [self._build_item(conn, row) for row in cursor]
        finally:
            conn.close()

    def get(self, key: str) -> ZoteroItem | None:
        """Return the item with the given Zotero key, or None if not found or no database."""
        if not self.exists():
            return None
        conn = self._connect()
        try:
            cursor = conn.execute(
                "SELECT i.itemID, i.key, it.typeName FROM items i "
                "JOIN itemTypes it ON i.itemTypeID = it.itemTypeID WHERE i.key = ?",
                (key,),
            )
            row = cursor.fetchone()
            return self._build_item(conn, row) if row else None
        finally:
            conn.close()

    def recent(self, limit: int = 20) -> list[ZoteroItem]:
        """Return up to ``limit`` most recently modified items.

        Excludes attachments, annotations, and notes; returns an empty list
        if the database does not exist.
        """
        if not self.exists():
            return []
        conn = self._connect()
        try:
            cursor = conn.execute(
                "SELECT i.itemID, i.key, it.typeName FROM items i "
                "JOIN itemTypes it ON i.itemTypeID = it.itemTypeID "
                "WHERE it.typeName NOT IN ('attachment', 'annotation', 'note') "
                "ORDER BY i.dateModified DESC LIMIT ?",
                (limit,),
            )
            return [self._build_item(conn, row) for row in cursor]
        finally:
            conn.close()

    def by_tag(self, tag: str, limit: int = 50) -> list[ZoteroItem]:
        """Return items whose tags LIKE-match ``tag``, ordered by most recently modified.

        Excludes attachments, annotations, and notes; returns an empty list
        if the database does not exist.
        """
        if not self.exists():
            return []
        conn = self._connect()
        try:
            cursor = conn.execute(
                "SELECT DISTINCT i.itemID, i.key, it.typeName FROM items i "
                "JOIN itemTypes it ON i.itemTypeID = it.itemTypeID "
                "JOIN itemTags itg ON i.itemID = itg.itemID "
                "JOIN tags t ON itg.tagID = t.tagID "
                "WHERE t.name LIKE ? AND it.typeName NOT IN ('attachment', 'annotation', 'note') "
                "ORDER BY i.dateModified DESC LIMIT ?",
                (f"%{tag}%", limit),
            )
            return [self._build_item(conn, row) for row in cursor]
        finally:
            conn.close()

    def tags(self, limit: int = 100) -> list[tuple[str, int]]:
        """Return up to ``limit`` ``(tag_name, item_count)`` pairs ordered by descending count.

        Returns an empty list if the database does not exist.
        """
        if not self.exists():
            return []
        conn = self._connect()
        try:
            cursor = conn.execute(
                "SELECT t.name, COUNT(it.itemID) as cnt FROM tags t "
                "JOIN itemTags it ON t.tagID = it.tagID "
                "GROUP BY t.tagID ORDER BY cnt DESC LIMIT ?",
                (limit,),
            )
            return [(row["name"], row["cnt"]) for row in cursor]
        finally:
            conn.close()

    def collections(self, limit: int = 100) -> list[tuple[str, int]]:
        """List all collections with item counts.

        Args:
            limit: Max collections to return (default: 100).

        Returns:
            List of ``(collection_name, item_count)`` tuples sorted by name.
        """
        if not self.exists():
            return []
        conn = self._connect()
        try:
            cursor = conn.execute(
                "SELECT c.collectionName, COUNT(ci.itemID) as cnt "
                "FROM collections c "
                "LEFT JOIN collectionItems ci ON c.collectionID = ci.collectionID "
                "GROUP BY c.collectionID ORDER BY c.collectionName LIMIT ?",
                (limit,),
            )
            return [(row["collectionName"], row["cnt"]) for row in cursor]
        finally:
            conn.close()

    def get_attachment_path(self, key: str) -> Path | None:
        """Resolve the filesystem path of the attachment for the item with ``key``.

        Stored "storage:" paths are joined under the configured storage
        directory; other paths are returned as-is. Returns None if the
        database or storage path is unset, or no attachment is found.
        """
        if not self.exists() or not self.storage_path:
            return None
        conn = self._connect()
        try:
            cursor = conn.execute(
                "SELECT ia.path FROM items i "
                "JOIN itemAttachments ia ON i.itemID = ia.itemID WHERE i.key = ?",
                (key,),
            )
            row = cursor.fetchone()
            if not row or not row["path"]:
                return None
            path = str(row["path"])
            if path.startswith("storage:"):
                return self.storage_path / key / path[8:]
            return Path(path)
        finally:
            conn.close()
