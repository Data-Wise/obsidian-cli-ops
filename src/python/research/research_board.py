"""obs research board — deterministic atlas-state -> vault dashboard renderer (SPEC-obs / ADR-001).

Pure functions render the marker-bounded `_ACTION-BOARD` block from a list of project dicts
(as produced by `atlas project list --kind ... --format json`, optionally enriched with
progress/next/priority). Output is a pure function of input — **no timestamps inside the marker
block** — so re-rendering unchanged state yields zero diff (golden-file + idempotency tested).

`write_marked_block` mutates only between the markers (hand-authored prose preserved) and writes
atomically via ``os.replace``.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

MARKER_START = "<!-- obs:board:start -->"
MARKER_END = "<!-- obs:board:end -->"

# status keyword -> icon (first matching group wins, checked in order)
_STATUS_ICONS = [
    (("blocked", "deadline", "revise", "r&r", "resubmit"), "🔴"),
    (("paused", "wip", "in-progress", "in-development", "developing"), "🟡"),
    (("active", "ready", "draft", "complete", "released", "stable"), "🟢"),
]
# priority -> sort weight (lower = more urgent)
_PRIORITY_WEIGHT = {"p0": 0, "p1": 1, "p2": 2, "high": 1, "med": 3, "medium": 3, "low": 5}


def status_icon(status: str | None) -> str:
    s = (status or "").lower()
    for keys, icon in _STATUS_ICONS:
        if any(k in s for k in keys):
            return icon
    return "⚪"


def progress_bar(pct: Any, width: int = 8) -> str:
    try:
        p = int(pct)
    except (TypeError, ValueError):
        return "—"
    p = max(0, min(100, p))
    filled = round(p / 100 * width)
    return "█" * filled + "░" * (width - filled) + f" {p}%"


def _priority_weight(p: dict) -> int:
    return _PRIORITY_WEIGHT.get(str(p.get("priority", "")).lower(), 9)


def rank(projects: list[dict]) -> list[dict]:
    """Deterministic order: priority weight, then progress desc, then name."""
    def key(p: dict):
        prog = p.get("progress")
        prog = prog if isinstance(prog, int) else -1
        return (_priority_weight(p), -prog, str(p.get("name", "")))
    return sorted(projects, key=key)


def _row(p: dict) -> str:
    return (
        f"| {p.get('name', '—')} "
        f"| {p.get('target') or '—'} "
        f"| {status_icon(p.get('status'))} {p.get('status') or '—'} "
        f"| {progress_bar(p.get('progress'))} "
        f"| {p.get('next') or '—'} |"
    )


def render_action_board(projects: list[dict]) -> str:
    """Render the marker-block body (no enclosing markers, no timestamps)."""
    ranked = rank(projects)
    lines: list[str] = ["## 🎯 Research Action Board", ""]
    sections = [
        ("Manuscripts", lambda k: k == "manuscript"),
        ("Programs", lambda k: k == "program"),
        ("Packages & other", lambda k: k not in ("manuscript", "program")),
    ]
    for label, pred in sections:
        sel = [p for p in ranked if pred(p.get("kind"))]
        if not sel:
            continue
        lines.append(f"### {label}")
        lines.append("| Project | Venue | Status | Progress | Next |")
        lines.append("|---|---|---|---|---|")
        lines.extend(_row(p) for p in sel)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_block(projects: list[dict]) -> str:
    return f"{MARKER_START}\n{render_action_board(projects)}{MARKER_END}\n"


def write_marked_block(path: str | Path, block: str, dry_run: bool = False) -> dict:
    """Atomically replace the marker-bounded region in ``path`` with ``block``.

    Content outside the markers is preserved. If the file/markers are absent, the block is
    appended. Returns ``{path, changed, action}``.
    """
    p = Path(path).expanduser()
    existing = p.read_text(encoding="utf-8") if p.exists() else ""
    if MARKER_START in existing and MARKER_END in existing:
        pre = existing.split(MARKER_START)[0]
        post = existing.split(MARKER_END, 1)[1]
        new = pre + block.rstrip("\n") + post
    elif existing:
        new = existing.rstrip("\n") + "\n\n" + block
    else:
        new = block
    changed = new != existing
    if changed and not dry_run:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(new, encoding="utf-8")
        os.replace(tmp, p)
    return {"path": str(p), "changed": changed, "action": "dry-run" if dry_run else "write"}


def load_projects(kind: str | None = None, atlas_bin: str = "atlas") -> list[dict]:
    """Load projects from atlas (`atlas project list [--kind] --format json`)."""
    cmd = [atlas_bin, "project", "list", "--format", "json"]
    if kind:
        cmd += ["--kind", kind]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return json.loads(out)
