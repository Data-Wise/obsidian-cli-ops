"""Course management (ported from nexus-cli)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class CourseStatus:
    """Parsed fields from a course's ``.STATUS`` file."""

    status: str = "unknown"
    priority: str = "--"
    progress: int = 0
    next: str = ""
    course_type: str = "teaching"
    week: int | None = None
    target: str = ""

    @classmethod
    def from_file(cls, path: Path) -> CourseStatus:
        """Parse a ``.STATUS`` file into a ``CourseStatus``.

        Args:
            path: Path to the ``.STATUS`` file.

        Returns:
            A populated instance, or defaults if the file is missing.
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
                result.next = line.split(":", 1)[1].strip()
            elif line.startswith("type:"):
                result.course_type = line.split(":", 1)[1].strip()
            elif line.startswith("week:"):
                try:
                    result.week = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("target:"):
                result.target = line.split(":", 1)[1].strip()
        return result


@dataclass
class QuartoConfig:
    """Title, author, and formats parsed from a ``_quarto.yml`` file."""

    title: str = ""
    subtitle: str = ""
    author: str = ""
    formats: list[str] = field(default_factory=list)

    @classmethod
    def from_file(cls, path: Path) -> QuartoConfig:
        """Parse a ``_quarto.yml`` file into a ``QuartoConfig``.

        Args:
            path: Path to the ``_quarto.yml`` file.

        Returns:
            A populated instance, or defaults if the file is missing or unreadable.
        """
        if not path.exists():
            return cls()
        try:
            with open(path) as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            return cls()
        result = cls()
        project = data.get("project", {})
        book = data.get("book", {})
        website = data.get("website", {})
        result.title = book.get("title") or website.get("title") or project.get("title") or data.get("title", "")
        result.subtitle = book.get("subtitle") or data.get("subtitle", "")
        result.author = book.get("author") or data.get("author", "")
        if "format" in data:
            fmt = data["format"]
            if isinstance(fmt, dict):
                result.formats = list(fmt.keys())
            elif isinstance(fmt, str):
                result.formats = [fmt]
        return result


@dataclass
class Course:
    """A teaching course with its status and material counts."""

    name: str
    path: str
    title: str = ""
    status: str = "unknown"
    progress: int = 0
    week: int | None = None
    next_action: str = ""
    formats: list[str] = field(default_factory=list)
    lecture_count: int = 0
    assignment_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Return the course as a JSON-serializable dict."""
        return {
            "name": self.name,
            "path": self.path,
            "title": self.title or self.name,
            "status": self.status,
            "progress": self.progress,
            "week": self.week,
            "next_action": self.next_action,
            "formats": self.formats,
            "lecture_count": self.lecture_count,
            "assignment_count": self.assignment_count,
        }


@dataclass
class Lecture:
    """A single lecture (``.qmd`` file) belonging to a course."""

    name: str
    path: str
    course: str
    week: int | None = None
    title: str = ""
    format: str = "qmd"

    def to_dict(self) -> dict[str, Any]:
        """Return the lecture as a JSON-serializable dict."""
        return {
            "name": self.name,
            "path": self.path,
            "course": self.course,
            "week": self.week,
            "title": self.title or self.name,
            "format": self.format,
        }


class CourseManager:
    """Manage teaching courses."""

    def __init__(self, courses_dir: Path, materials_dir: Path | None = None):
        self.courses_dir = Path(courses_dir).expanduser()
        self.materials_dir = Path(materials_dir).expanduser() if materials_dir else None

    def exists(self) -> bool:
        """Return whether the configured courses directory exists."""
        return self.courses_dir.exists()

    def list_courses(self) -> list[Course]:
        """Load every course in the courses directory, sorted by name.

        Returns:
            A list of ``Course`` objects, or an empty list if the directory
            is missing. Hidden directories (dot-prefixed) are skipped.
        """
        if not self.exists():
            return []
        courses = []
        for course_path in sorted(self.courses_dir.iterdir()):
            if not course_path.is_dir() or course_path.name.startswith("."):
                continue
            course = self._load_course(course_path)
            if course:
                courses.append(course)
        return courses

    def get_course(self, name: str) -> Course | None:
        """Load a single course by directory name (case-insensitive fallback).

        Args:
            name: Course directory name; matched exactly first, then
                case-insensitively.

        Returns:
            The matching ``Course``, or ``None`` if no course matches.
        """
        course_path = self.courses_dir / name
        if not course_path.exists():
            for p in self.courses_dir.iterdir():
                if p.name.lower() == name.lower():
                    course_path = p
                    break
            else:
                return None
        return self._load_course(course_path)

    def _load_course(self, course_path: Path) -> Course | None:
        if not course_path.is_dir():
            return None
        status = CourseStatus.from_file(course_path / ".STATUS")
        quarto = QuartoConfig.from_file(course_path / "_quarto.yml")
        lecture_count = self._count_lectures(course_path)
        assignment_count = self._count_assignments(course_path)
        return Course(
            name=course_path.name,
            path=str(course_path),
            title=quarto.title or course_path.name,
            status=status.status,
            progress=status.progress,
            week=status.week,
            next_action=status.next,
            formats=quarto.formats,
            lecture_count=lecture_count,
            assignment_count=assignment_count,
        )

    def _count_lectures(self, course_path: Path) -> int:
        count = 0
        for pattern in ["lectures/*.qmd", "slides/*.qmd", "weeks/*.qmd"]:
            count += len(list(course_path.glob(pattern)))
        count += len(list(course_path.glob("week-*.qmd")))
        return count

    def _count_assignments(self, course_path: Path) -> int:
        count = 0
        for pattern in ["assignments/*.qmd", "homework/*.qmd", "labs/*.qmd"]:
            count += len(list(course_path.glob(pattern)))
        return count

    def list_lectures(self, course_name: str) -> list[Lecture]:
        """List the lectures for a course, scanning known ``.qmd`` locations.

        Args:
            course_name: Name of the course to scan.

        Returns:
            A list of ``Lecture`` objects gathered from the ``lectures/``,
            ``slides/``, ``weeks/`` subdirectories and root ``week-*`` files,
            or an empty list if the course is not found.
        """
        course = self.get_course(course_name)
        if not course:
            return []
        course_path = Path(course.path)
        lectures = []
        for location, pattern in [
            ("lectures", "lectures/*.qmd"),
            ("slides", "slides/*.qmd"),
            ("weeks", "weeks/*.qmd"),
            ("root", "week-*.qmd"),
            ("root", "_week-*.qmd"),
        ]:
            for qmd_file in sorted(course_path.glob(pattern)):
                lecture = self._parse_lecture(qmd_file, course_name)
                if lecture:
                    lectures.append(lecture)
        return lectures

    def _parse_lecture(self, qmd_path: Path, course_name: str) -> Lecture | None:
        name = qmd_path.stem
        week = None
        week_match = re.search(r"week[-_]?(\d+)", name, re.IGNORECASE)
        if week_match:
            week = int(week_match.group(1))
        title = ""
        try:
            content = qmd_path.read_text()
            if content.startswith("---"):
                end = content.find("---", 3)
                if end > 0:
                    for line in content[3:end].split("\n"):
                        if line.strip().startswith("title:"):
                            title = line.split(":", 1)[1].strip().strip("\"'")
                            break
        except Exception:
            pass
        return Lecture(
            name=name,
            path=str(qmd_path),
            course=course_name,
            week=week,
            title=title or name.replace("-", " ").replace("_", " ").title(),
            format="qmd",
        )
