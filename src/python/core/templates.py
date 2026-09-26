"""Vault template ops — list templates and create notes from them (nexus port).

Filesystem-direct (SPEC-merge-nexus-cli-v2 decision D3): works on the vault's
files, not the obs index. Interface-agnostic — the CLI and the MCP server both
call these functions and format the result themselves.

Rendering covers Obsidian's core Templates plugin variables only:
``{{title}}``, ``{{date}}``, ``{{time}}``, ``{{date:FORMAT}}`` / ``{{time:FORMAT}}``
(a moment.js token subset), plus caller-supplied ``{{key}}`` variables.
Unknown ``{{...}}`` placeholders and Templater ``<% %>`` blocks are left untouched.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

# Fallback template folders, relative to the vault root, tried in order.
# `_SYSTEM/templates` is the obs config default (config_loader.DEFAULT_TEMPLATES_SUBPATH).
FALLBACK_DIRS = ("_SYSTEM/templates", "templates", "Templates", "_templates")
TEMPLATE_PREFIX = "tpl-"


class TemplateError(Exception):
    """A template op was refused (bad destination, existing note, missing template)."""


@dataclass
class TemplateDir:
    path: Path
    source: str  # 'obsidian', 'config', or 'fallback'


def _obsidian_templates_folder(vault_root: Path) -> Optional[Path]:
    """Folder set in Obsidian's core Templates plugin (.obsidian/templates.json)."""
    cfg = vault_root / ".obsidian" / "templates.json"
    try:
        folder = json.loads(cfg.read_text(encoding="utf-8")).get("folder")
    except (OSError, ValueError, AttributeError):
        return None
    return vault_root / folder.strip("/") if isinstance(folder, str) and folder.strip("/") else None


def _config_templates_folder(vault_root: Path) -> Optional[Path]:
    """obs config `vault.templates`, only when that config's vault is this vault."""
    try:
        import config_loader
        cfg = config_loader.load()
    except Exception:  # a broken config must not break template listing
        return None
    if cfg is None:
        return None
    try:
        tdir = cfg.templates_resolved
    except ValueError:  # vault-less config with no explicit templates path
        return None
    root = vault_root.resolve()
    if cfg.root is not None and cfg.root.resolve() == root:
        return tdir
    return tdir if tdir.resolve().is_relative_to(root) else None


def find_templates_dir(vault_root: Path) -> Optional[TemplateDir]:
    """Resolve a vault's templates folder: Obsidian setting → obs config → fallbacks."""
    vault_root = Path(vault_root)
    for path, source in (
        (_obsidian_templates_folder(vault_root), "obsidian"),
        (_config_templates_folder(vault_root), "config"),
    ):
        if path is not None and path.is_dir():
            return TemplateDir(path, source)
    for rel in FALLBACK_DIRS:
        path = vault_root / rel
        if path.is_dir():
            return TemplateDir(path, "fallback")
    return None


def _display_name(stem: str) -> str:
    return stem[len(TEMPLATE_PREFIX):] if stem.startswith(TEMPLATE_PREFIX) else stem


def list_templates(vault_root: Path) -> list[dict]:
    """Templates in the vault's templates folder, sorted by name.

    Each entry: ``{"name", "path", "relative"}``. ``name`` drops a ``tpl-`` prefix.
    Returns [] when the vault has no templates folder.
    """
    tdir = find_templates_dir(vault_root)
    if tdir is None:
        return []
    out = [
        {"name": _display_name(p.stem), "path": str(p), "relative": str(p.relative_to(tdir.path))}
        for p in tdir.path.rglob("*.md")
    ]
    return sorted(out, key=lambda t: t["name"].lower())


def resolve_template(vault_root: Path, name: str) -> Path:
    """Find a template by name (with or without `.md` / `tpl-` prefix)."""
    tdir = find_templates_dir(vault_root)
    if tdir is None:
        raise TemplateError(f"No templates folder found in vault: {vault_root}")
    stem = name[:-3] if name.endswith(".md") else name
    candidates = [tdir.path / f"{stem}.md", tdir.path / f"{TEMPLATE_PREFIX}{stem}.md"]
    for cand in candidates:
        if cand.is_file():
            return cand
    for t in list_templates(vault_root):  # nested folders, matched by display name
        if t["name"] == _display_name(stem):
            return Path(t["path"])
    raise TemplateError(f"Template not found: {name} (in {tdir.path})")


# moment.js tokens → strftime, longest first so YYYY wins over YY.
_MOMENT_TOKENS = [
    ("YYYY", "%Y"), ("YY", "%y"), ("MMMM", "%B"), ("MMM", "%b"), ("MM", "%m"),
    ("dddd", "%A"), ("ddd", "%a"), ("DD", "%d"), ("HH", "%H"), ("hh", "%I"),
    ("mm", "%M"), ("ss", "%S"), ("A", "%p"),
]
_MOMENT_RE = re.compile("|".join(re.escape(t) for t, _ in _MOMENT_TOKENS))
_MOMENT_MAP = dict(_MOMENT_TOKENS)


def format_moment(fmt: str, when: datetime) -> str:
    """Format `when` with a moment.js-style format string (common tokens only)."""
    return _MOMENT_RE.sub(lambda m: when.strftime(_MOMENT_MAP[m.group(0)]), fmt)


_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][\w-]*)\s*(?::([^}]*))?\}\}")


def render(text: str, title: str, variables: Optional[dict] = None,
           now: Optional[datetime] = None) -> str:
    """Substitute template placeholders; unknown ones are left as-is."""
    now = now or datetime.now()
    variables = {str(k): str(v) for k, v in (variables or {}).items()}

    def sub(m: re.Match) -> str:
        key, fmt = m.group(1), m.group(2)
        if key in variables and fmt is None:
            return variables[key]
        if key == "title" and fmt is None:
            return title
        if key == "date":
            return format_moment(fmt, now) if fmt else now.strftime("%Y-%m-%d")
        if key == "time":
            return format_moment(fmt, now) if fmt else now.strftime("%H:%M")
        return m.group(0)

    return _PLACEHOLDER_RE.sub(sub, text)


def resolve_destination(vault_root: Path, dest: str) -> Path:
    """Vault-relative destination → absolute path; refuses anything outside the vault."""
    if not dest or not dest.strip():
        raise TemplateError("Destination path is empty")
    rel = Path(dest.strip())
    if rel.is_absolute():
        raise TemplateError(f"Destination must be relative to the vault: {dest}")
    if rel.suffix != ".md":
        rel = rel.with_name(rel.name + ".md")
    root = Path(vault_root).resolve()
    target = (root / rel).resolve()
    if not target.is_relative_to(root):
        raise TemplateError(f"Destination escapes the vault: {dest}")
    return target


def create_from_template(vault_root: Path, template: str, dest: str,
                         variables: Optional[dict] = None,
                         now: Optional[datetime] = None) -> dict:
    """Render `template` into a new note at vault-relative `dest`.

    Refuses to overwrite an existing note. Returns
    ``{"path", "relative", "template", "words"}``.
    """
    vault_root = Path(vault_root)
    tpl_path = resolve_template(vault_root, template)
    target = resolve_destination(vault_root, dest)
    if target.exists():
        raise TemplateError(f"Note already exists: {target}")
    content = render(tpl_path.read_text(encoding="utf-8"), target.stem, variables, now)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {
        "path": str(target),
        "relative": str(target.relative_to(vault_root.resolve())),
        "template": str(tpl_path),
        "words": len(content.split()),
    }
