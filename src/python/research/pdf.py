"""PDF extraction and search (ported from nexus-cli)."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class PDFDocument:
    """Text and metadata extracted from a single PDF file."""

    path: str
    filename: str
    title: str = ""
    text: str = ""
    page_count: int = 0
    size_bytes: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Return the document as a dict, with the full text reduced to a 500-char preview."""
        return {
            "path": self.path,
            "filename": self.filename,
            "title": self.title or self.filename,
            "page_count": self.page_count,
            "size_bytes": self.size_bytes,
            "text_preview": self.text[:500] + "..." if len(self.text) > 500 else self.text,
        }


@dataclass
class PDFSearchResult:
    """A single match found while searching PDFs by filename or content."""

    path: str
    filename: str
    page: int
    context: str
    match_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return the search result as a dict of its fields."""
        return {
            "path": self.path,
            "filename": self.filename,
            "page": self.page,
            "context": self.context,
            "match_text": self.match_text,
        }


class PDFExtractor:
    """Extract text from PDF files using pdftotext."""

    def __init__(self, directories: list[Path] | None = None):
        self.directories = [Path(d).expanduser() for d in (directories or [])]
        self._pdftotext_path = shutil.which("pdftotext")

    def available(self) -> bool:
        """Return True if the ``pdftotext`` binary was found on PATH."""
        return self._pdftotext_path is not None

    def pdf_count(self) -> int:
        """Return the total number of ``.pdf`` files found recursively in the configured directories."""
        count = 0
        for directory in self.directories:
            if directory.exists():
                count += len(list(directory.rglob("*.pdf")))
        return count

    def extract(self, pdf_path: Path, pages: str | None = None, layout: bool = False) -> PDFDocument:
        """Extract text and metadata from a PDF by shelling out to ``pdftotext``.

        Args:
            pdf_path: Path to the PDF file to extract.
            pages: Optional page selection, either a single page (``"3"``) or a
                range (``"1-5"``); ``None`` extracts the whole document.
            layout: If True, use ``pdftotext -layout`` to preserve the visual
                layout; otherwise use ``-raw``.

        Returns:
            A ``PDFDocument`` with cleaned text, an inferred title, the page
            count (via ``pdfinfo`` when available), and the file size. Extraction
            failures or timeouts are captured as placeholder text rather than raised.

        Raises:
            FileNotFoundError: If ``pdf_path`` does not exist.
            RuntimeError: If the ``pdftotext`` binary is not installed.
        """
        pdf_path = Path(pdf_path).expanduser()
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        if not self.available():
            raise RuntimeError("pdftotext not installed. Run: brew install poppler")

        assert self._pdftotext_path is not None
        cmd: list[str] = [self._pdftotext_path]
        cmd.append("-layout" if layout else "-raw")

        if pages:
            if "-" in pages:
                parts = pages.split("-")
                first_page = int(parts[0])
                last_page = int(parts[1]) if len(parts) > 1 and parts[1] else None
            elif pages.isdigit():
                first_page = int(pages)
                last_page = int(pages)
            else:
                first_page = last_page = None

            if "first_page" in dir() and first_page:
                cmd.extend(["-f", str(first_page)])
            if "last_page" in dir() and last_page:
                cmd.extend(["-l", str(last_page)])

        cmd.extend([str(pdf_path), "-"])
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            text = result.stdout
        except subprocess.TimeoutExpired:
            text = "[Extraction timed out]"
        except Exception as e:
            text = f"[Extraction failed: {e}]"

        text = self._clean_text(text)
        page_count = self._get_page_count(pdf_path)
        title = self._extract_title(text, pdf_path)

        return PDFDocument(
            path=str(pdf_path),
            filename=pdf_path.name,
            title=title,
            text=text,
            page_count=page_count,
            size_bytes=pdf_path.stat().st_size,
        )

    def _clean_text(self, text: str) -> str:
        if not text or text.startswith("["):
            return text
        text = re.sub(r"  +", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
        text = text.replace("­", "")
        text = text.replace("ﬀ", "ff").replace("ﬁ", "fi").replace("ﬂ", "fl")
        text = text.replace("ﬃ", "ffi").replace("ﬄ", "ffl")
        text = re.sub(r"\(cid:\d+\)", "", text)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines)

    def _extract_title(self, text: str, pdf_path: Path) -> str:
        if not text or text.startswith("["):
            return pdf_path.stem
        for line in text.strip().split("\n")[:10]:
            line = line.strip()
            if not line or re.match(r"^\d+$", line) or len(line) < 10:
                continue
            if len(line) > 15 and len(line) < 200 and not line.endswith(".") and line[0].isupper():
                title = re.sub(r"\s+", " ", line)
                return re.sub(r"[,;:]$", "", title)
        return pdf_path.stem

    def _get_page_count(self, pdf_path: Path) -> int:
        pdfinfo = shutil.which("pdfinfo")
        if not pdfinfo:
            return 0
        try:
            result = subprocess.run([pdfinfo, str(pdf_path)], capture_output=True, text=True, timeout=10)
            for line in result.stdout.split("\n"):
                if line.startswith("Pages:"):
                    return int(line.split(":")[1].strip())
        except Exception:
            pass
        return 0

    def search(
        self,
        query: str,
        limit: int = 20,
        directories: list[Path] | None = None,
        search_depth: int = 5,
    ) -> list[PDFSearchResult]:
        """Search PDFs by filename and content, returning scored, ranked matches.

        Filenames are matched against ``query`` (a case-insensitive regex). When
        ``pdftotext`` is available, the first ``search_depth`` pages of up to 50
        PDFs are also content-searched; content matches are scored by match count,
        early position, and title overlap, and are ranked above filename matches.

        Args:
            query: Regular expression to search for (case-insensitive).
            limit: Maximum number of results to return.
            directories: Directories to search; falls back to the instance's
                configured directories when omitted.
            search_depth: Number of leading pages to extract per PDF for content search.

        Returns:
            Up to ``limit`` ``PDFSearchResult`` objects, sorted by descending score.
        """
        search_dirs = directories or self.directories
        pattern = re.compile(query, re.IGNORECASE)

        filename_matches: list[tuple[PDFSearchResult, float]] = []
        for directory in search_dirs:
            if not directory.exists():
                continue
            for pdf_path in directory.rglob("*.pdf"):
                if len(filename_matches) >= limit * 2:
                    break
                if pattern.search(pdf_path.name):
                    filename_matches.append((
                        PDFSearchResult(
                            path=str(pdf_path),
                            filename=pdf_path.name,
                            page=0,
                            context=f"Filename match: {pdf_path.name}",
                            match_text=query,
                        ),
                        0.5,
                    ))

        content_matches: list[tuple[PDFSearchResult, float]] = []
        if self.available():
            searched_count = 0
            for directory in search_dirs:
                if not directory.exists():
                    continue
                for pdf_path in directory.rglob("*.pdf"):
                    if searched_count >= 50:
                        break
                    if any(r[0].path == str(pdf_path) for r in filename_matches):
                        continue
                    searched_count += 1
                    try:
                        doc = self.extract(pdf_path, pages=f"1-{search_depth}")
                        matches = list(pattern.finditer(doc.text))
                        if matches:
                            match = matches[0]
                            context = self._extract_context(doc.text, match)
                            score = 1.0
                            if len(matches) > 1:
                                score += 0.1 * min(len(matches) - 1, 5)
                            if match.start() < 500:
                                score += 0.2
                            if doc.title and query.lower() in doc.title.lower():
                                score += 0.3
                            content_matches.append((
                                PDFSearchResult(
                                    path=str(pdf_path),
                                    filename=pdf_path.name,
                                    page=1,
                                    context=context,
                                    match_text=match.group(),
                                ),
                                score,
                            ))
                    except Exception:
                        continue

        all_matches = content_matches + filename_matches
        all_matches.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in all_matches[:limit]]

    def _extract_context(self, text: str, match: re.Match, window: int = 150) -> str:
        start = max(0, match.start() - window)
        end = min(len(text), match.end() + window)
        while start > 0 and text[start] not in ".!?\n":
            start -= 1
            if match.start() - start > window * 2:
                break
        while end < len(text) and text[end] not in ".!?\n":
            end += 1
            if end - match.end() > window * 2:
                break
        context = re.sub(r"\s+", " ", text[start:end].strip())
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."
        return context
