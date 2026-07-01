"""Unified search across all knowledge sources (ported from nexus-cli)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class UnifiedSearchResult:
    """A unified search result from any source."""

    source: str
    path: str
    title: str
    snippet: str
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "path": self.path,
            "title": self.title,
            "snippet": self.snippet,
            "score": self.score,
            "metadata": self.metadata,
        }


class UnifiedSearch:
    """Unified search across vault, Zotero, and PDF sources."""

    def __init__(
        self,
        db_manager: Any | None = None,
        zotero_db: Path | None = None,
        pdf_dirs: list[Path] | None = None,
    ):
        self.db = db_manager
        self.zotero_db = Path(zotero_db).expanduser() if zotero_db else None
        self.pdf_dirs = [Path(d).expanduser() for d in pdf_dirs] if pdf_dirs else []

    def available_sources(self) -> list[str]:
        sources = []
        if self.db:
            sources.append("vault")
        if self.zotero_db and self.zotero_db.exists():
            sources.append("zotero")
        for pdf_dir in self.pdf_dirs:
            if pdf_dir.exists():
                sources.append("pdf")
                break
        return sources

    def search(
        self,
        query: str,
        sources: list[str] | None = None,
        limit_per_source: int = 10,
    ) -> list[UnifiedSearchResult]:
        if sources is None:
            sources = self.available_sources()

        results: list[UnifiedSearchResult] = []

        for source in sources:
            if source == "vault":
                results.extend(self._search_vault(query, limit_per_source))
            elif source == "zotero":
                results.extend(self._search_zotero(query, limit_per_source))
            elif source == "pdf":
                results.extend(self._search_pdfs(query, limit_per_source))

        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def _search_vault(self, query: str, limit: int) -> list[UnifiedSearchResult]:
        if not self.db:
            return []
        try:
            notes = self.db.search_notes(query, limit=limit)
        except Exception:
            return []
        results = []
        for n in notes:
            score = 2.0 if query.lower() in n.get("title", "").lower() else 1.0
            results.append(
                UnifiedSearchResult(
                    source="vault",
                    path=n.get("path", ""),
                    title=n.get("title", ""),
                    snippet=f"Vault: {n.get('vault_name', '?')}",
                    score=score,
                    metadata={"vault_name": n.get("vault_name", ""), "id": n.get("id", "")},
                )
            )
        return results

    def _search_zotero(self, query: str, limit: int) -> list[UnifiedSearchResult]:
        if not self.zotero_db or not self.zotero_db.exists():
            return []
        try:
            from research.zotero import ZoteroClient
            client = ZoteroClient(self.zotero_db)
            items = client.search(query, limit=limit)
        except Exception:
            return []
        results = []
        for item in items:
            author_str = item.authors[0] + " et al." if len(item.authors) > 2 else ", ".join(item.authors) if item.authors else "Unknown"
            year = item.date[:4] if item.date else "n.d."
            score = 2.5 if query.lower() in item.title.lower() else 1.5
            results.append(
                UnifiedSearchResult(
                    source="zotero",
                    path=item.key,
                    title=item.title,
                    snippet=f"{author_str} ({year})",
                    score=score,
                    metadata={"key": item.key, "item_type": item.item_type, "authors": item.authors, "date": item.date, "tags": item.tags},
                )
            )
        return results

    def _search_pdfs(self, query: str, limit: int) -> list[UnifiedSearchResult]:
        if not self.pdf_dirs:
            return []
        try:
            from research.pdf import PDFExtractor
            extractor = PDFExtractor(directories=self.pdf_dirs)
            pdf_results = extractor.search(query, limit=limit)
        except Exception:
            return []
        results = []
        for pr in pdf_results:
            results.append(
                UnifiedSearchResult(
                    source="pdf",
                    path=pr.path,
                    title=pr.filename,
                    snippet=pr.context[:150] + "..." if len(pr.context) > 150 else pr.context,
                    score=1.0,
                    metadata={"page": pr.page, "match_text": pr.match_text},
                )
            )
        return results
