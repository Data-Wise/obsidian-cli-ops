"""obs board — multi-source board refresh engine (SPEC-board-sync-automation).

Connector-based architecture that reads from atlas, vault DB, and .STATUS files,
merges into a unified ProjectStatus model, and renders deterministic markdown
boards in the Obsidian vault.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml

from .vault_manager import VaultManager
from db_manager import DatabaseManager  # noqa: E402

log = logging.getLogger(__name__)

MARKER_START = "<!-- obs:board:start -->"
MARKER_END = "<!-- obs:board:end -->"

# ── Data model ──────────────────────────────────────────────────────────────

@dataclass
class ProjectStatus:
    name: str
    kind: str = "manuscript"
    venue: str = ""
    status: str = ""
    progress: int = 0
    priority: str = ""
    next_action: str = ""
    source: str = ""  # connector name that provided this record

@dataclass
class VaultHealthSummary:
    vault_name: str
    total_notes: int = 0
    total_links: int = 0
    broken_links: int = 0
    last_scanned: str = ""
    ghost_rows: int = 0

# ── Connector ABC ───────────────────────────────────────────────────────────

class Connector(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def fetch(self) -> list[ProjectStatus]:
        ...

# ── Atlas connector ─────────────────────────────────────────────────────────

class AtlasConnector(Connector):
    def __init__(self, atlas_bin: str = "atlas"):
        self._bin = atlas_bin

    @property
    def name(self) -> str:
        return "atlas"

    def fetch(self) -> list[ProjectStatus]:
        """Load manuscripts + programs from atlas registry."""
        items: list[ProjectStatus] = []
        for kind in ("manuscript", "program"):
            raw = self._load_projects(kind=kind)
            for p in raw:
                items.append(ProjectStatus(
                    name=p.get("name", "?"),
                    kind=kind,
                    venue=p.get("target") or "",
                    status=p.get("status") or "",
                    progress=p.get("progress") or 0,
                    priority=p.get("priority") or "",
                    next_action=p.get("next") or "",
                    source="atlas",
                ))
        return items

    def _load_projects(self, kind: str) -> list[dict]:
        cmd = [self._bin, "project", "list", "--kind", kind, "--format", "json"]
        out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
        return json.loads(out)

# ── Vault DB connector ──────────────────────────────────────────────────────

class VaultConnector(Connector):
    def __init__(self, db_path: str | None = None):
        self._db_path = db_path

    @property
    def name(self) -> str:
        return "vault"

    def fetch(self) -> list[ProjectStatus]:
        """Fetch vault health summary as a pseudo-project entry."""
        results: list[ProjectStatus] = []
        db = DatabaseManager(db_path=self._db_path)
        vaults = db.get_vaults()
        for v in vaults:
            stats = db.get_vault_stats(v.id)
            if not stats:
                continue
            last_scan = v.last_scanned or ""
            ghost = 0
            if last_scan:
                try:
                    ghost = self._count_ghosts(db, v.id)
                except Exception:
                    pass
            results.append(ProjectStatus(
                name=v.name,
                kind="vault",
                venue="",
                status="healthy" if ghost == 0 else "drift",
                progress=100 if ghost == 0 else max(0, 100 - ghost),
                priority="",
                next_action=f"prune {ghost} ghost(s)" if ghost > 0 else "",
                source="vault",
            ))
        return results

    def _count_ghosts(self, db: DatabaseManager, vault_id: str) -> int:
        path_rows = db.execute("SELECT path FROM notes WHERE vault_id=?", (vault_id,))
        if not path_rows:
            return 0
        count = 0
        for row in path_rows:
            p = row[0] if isinstance(row, (list, tuple)) else row.get("path", "")
            if p and not os.path.exists(p):
                count += 1
        return count

# ── STATUS file connector ───────────────────────────────────────────────────

class StatusConnector(Connector):
    def __init__(self, research_dirs: list[str] | None = None):
        self._dirs = research_dirs or [
            os.path.expanduser("~/projects/research"),
            os.path.expanduser("~/projects/r-packages/active"),
        ]

    @property
    def name(self) -> str:
        return "status"

    def fetch(self) -> list[ProjectStatus]:
        """Parse .STATUS files from research and r-packages directories."""
        items: list[ProjectStatus] = []
        for root_dir in self._dirs:
            if not os.path.isdir(root_dir):
                continue
            for entry in os.listdir(root_dir):
                project_dir = os.path.join(root_dir, entry)
                status_file = os.path.join(project_dir, ".STATUS")
                if not os.path.isdir(project_dir) or not os.path.isfile(status_file):
                    continue
                status = self._parse_status_file(status_file)
                kind = "package" if "r-packages" in root_dir else "manuscript"
                items.append(ProjectStatus(
                    name=entry,
                    kind=kind,
                    venue=status.get("target", ""),
                    status=status.get("status", ""),
                    progress=status.get("progress", 0),
                    priority=status.get("priority", ""),
                    next_action=status.get("next", ""),
                    source="status",
                ))
        return items

    def _parse_status_file(self, path: str) -> dict:
        result: dict[str, Any] = {}
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except Exception:
            return result

        # Try full YAML first; fall back to frontmatter-only or line parsing on failure.
        try:
            parsed = yaml.safe_load(text)
            if isinstance(parsed, dict):
                result = parsed
            else:
                result = self._parse_status_lines(text)
        except Exception:
            result = self._parse_status_lines(text)

        # Normalize progress to int
        if "progress" in result:
            try:
                result["progress"] = int(result["progress"])
            except (ValueError, TypeError):
                result["progress"] = 0
        return result

    def _parse_status_lines(self, text: str) -> dict:
        result: dict[str, Any] = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                # Stop at the first line that is not a simple key:value (e.g. markdown body).
                if result:
                    break
                continue
            parts = line.split(":", 1)
            key = parts[0].strip().lower()
            val = parts[1].strip()
            if key in ("status", "priority", "target", "next", "progress", "kind"):
                result[key] = val
        return result

# ── Merger ──────────────────────────────────────────────────────────────────

class Merger:
    def merge(self, sources: list[list[ProjectStatus]]) -> list[ProjectStatus]:
        seen: dict[str, ProjectStatus] = {}
        for batch in sources:
            for item in batch:
                key = f"{item.kind}:{item.name}"
                existing = seen.get(key)
                if existing is None:
                    seen[key] = item
                else:
                    seen[key] = self._merge_item(existing, item)
        return list(seen.values())

    def _merge_item(self, a: ProjectStatus, b: ProjectStatus) -> ProjectStatus:
        if a.source == "atlas":
            return a
        if b.source == "atlas":
            return b
        return b

# ── Renderer ────────────────────────────────────────────────────────────────

_STATUS_ICONS = [
    (("blocked", "deadline", "revise", "r&r", "resubmit"), "🔴"),
    (("paused", "wip", "in-progress", "in-development", "developing"), "🟡"),
    (("active", "ready", "draft", "complete", "released", "stable", "healthy"), "🟢"),
]

_PRIORITY_WEIGHT = {"p0": 0, "p1": 1, "p2": 2, "high": 1, "med": 3, "medium": 3, "low": 5}

_DONE_STATUSES = {"complete", "done", "archive", "archived", "released", "stable", "shipped"}

class BoardRenderer:
    def render(self, projects: list[ProjectStatus]) -> str:
        date = datetime.now().strftime("%Y-%m-%d")
        ranked = sorted(projects, key=self._sort_key)
        action_items = self._pick_action_items(projects)
        lines: list[str] = [
            f"# 🎯 Research Action Board — {date}",
            "> Front door — open this first. Tactical (this week). Strategic → [[RESEARCH_HUB]].",
            f"> Last refreshed {date} · auto-generated by `obs board refresh`; augment thinking on demand via `research--action-board` prompt.",
            "",
            "## TL;DR",
            "- *(LLM augments this section on demand)*",
            "",
            self._render_act_now(action_items),
            self._render_status_tables(ranked),
            "## 💡 Future ideas & new proposals",
            "- *(LLM augments this section on demand from radar + ledger)*",
            "",
            "## 🔴 Threats / scoop-watch",
            "- *(LLM augments this section on demand from radar)*",
            "",
            "## ⏭️ This week (sequenced)",
            "1. *(LLM augments this section on demand)*",
            "",
            "## 🔗 Feeds",
            "[[RESEARCH_HUB]] · [[MediationVerse_Dashboard]] · [[_RADAR-MOC]] · [[_IDEA-LEDGER]] · program MOCs",
            "",
        ]
        return "\n".join(lines)

    def _render_act_now(self, items: list[ProjectStatus]) -> str:
        lines = [
            "## 🎯 Act on now (ranked — pick one)",
            "| # | action | domain | [time] | leverage | risk |",
            "|---|---|---|---|---|---|",
        ]
        if not items:
            lines.append("| — | — | — | — | — | — |")
        for i, p in enumerate(items, 1):
            time_est = self._time_estimate(p)
            leverage = self._leverage_score(p)
            risk = "🔴 high" if leverage >= 80 else "🟡 med" if leverage >= 50 else "🟢 low"
            action = self._shorten(p.next_action or f"advance {p.name}")
            lines.append(
                f"| {i} | {action} | {p.kind} | {time_est} | {leverage} | {risk} |"
            )
        lines.append("")
        return "\n".join(lines)

    def _shorten(self, text: str, max_len: int = 70) -> str:
        t = text.replace("\n", " ").strip()
        if len(t) <= max_len:
            return t
        return t[:max_len].rsplit(" ", 1)[0] + "…"

    def _render_status_tables(self, projects: list[ProjectStatus]) -> str:
        lines = ["## 📊 Status at a glance", ""]
        sections = [
            ("Manuscripts", lambda p: p.kind == "manuscript"),
            ("Programs", lambda p: p.kind == "program"),
            ("Packages", lambda p: p.kind == "package"),
            ("Vaults", lambda p: p.kind == "vault"),
        ]
        for label, pred in sections:
            sel = [p for p in projects if pred(p)]
            if not sel:
                continue
            lines.append(f"### {label}")
            lines.append("| Project | Venue | Status | Progress | Next |")
            lines.append("|---|---|---|---|---|")
            lines.extend(self._row(p) for p in sel)
            lines.append("")
        return "\n".join(lines)

    def _pick_action_items(self, projects: list[ProjectStatus], cap: int = 7) -> list[ProjectStatus]:
        active = [p for p in projects if not self._is_done(p)]
        scored = sorted(active, key=self._action_key)
        return scored[:cap]

    def _is_done(self, p: ProjectStatus) -> bool:
        s = (p.status or "").lower()
        return any(d in s for d in _DONE_STATUSES) or p.progress == 100

    def _action_key(self, p: ProjectStatus) -> tuple:
        pw = _PRIORITY_WEIGHT.get((p.priority or "").lower(), 9)
        readiness = abs(p.progress - 75)  # closest to 75% is most ready
        return (pw, readiness, -p.progress, p.name)

    def _time_estimate(self, p: ProjectStatus) -> str:
        if p.progress >= 90:
            return "30m"
        if p.progress >= 50:
            return "2h"
        if p.progress > 0:
            return "1d"
        return "2d"

    def _leverage_score(self, p: ProjectStatus) -> int:
        pw = _PRIORITY_WEIGHT.get((p.priority or "").lower(), 5)
        progress_factor = max(0, 100 - abs(p.progress - 75))  # 100 at 75%, 0 at -25/175
        return max(0, min(100, (10 - pw) * 10 + progress_factor // 2))

    def _row(self, p: ProjectStatus) -> str:
        icon = self._status_icon(p.status)
        bar = self._progress_bar(p.progress)
        return (
            f"| {p.name} "
            f"| {p.venue or '—'} "
            f"| {icon} {p.status or '—'} "
            f"| {bar} "
            f"| {p.next_action or '—'} |"
        )

    def _status_icon(self, status: str) -> str:
        s = (status or "").lower()
        for keys, icon in _STATUS_ICONS:
            if any(k in s for k in keys):
                return icon
        return "⚪"

    def _progress_bar(self, pct: int, width: int = 8) -> str:
        try:
            p = max(0, min(100, int(pct)))
        except (TypeError, ValueError):
            return "—"
        filled = round(p / 100 * width)
        return "█" * filled + "░" * (width - filled) + f" {p}%"

    def _sort_key(self, p: ProjectStatus) -> tuple:
        pw = _PRIORITY_WEIGHT.get((p.priority or "").lower(), 9)
        return (pw, -p.progress, p.name)

# ── Vault writer ────────────────────────────────────────────────────────────

class VaultWriter:
    def write(self, path: str, block: str, dry_run: bool = False) -> dict:
        p = Path(path).expanduser()
        existing = p.read_text(encoding="utf-8") if p.exists() else ""
        if MARKER_START in existing and MARKER_END in existing:
            # Embedded board: replace only the marked region, preserving surrounding content.
            pre = existing.split(MARKER_START)[0]
            post = existing.split(MARKER_END, 1)[1]
            new = pre + block.rstrip("\n") + post
        else:
            # Standalone board file: deterministic refresh owns the whole file.
            new = block
        changed = new != existing
        if changed and not dry_run:
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(p.suffix + ".tmp")
            tmp.write_text(new, encoding="utf-8")
            os.replace(tmp, p)
        return {"path": str(p), "changed": changed, "action": "dry-run" if dry_run else "write"}

# ── Engine ──────────────────────────────────────────────────────────────────

class BoardEngine:
    def __init__(
        self,
        vault_manager: Optional[VaultManager] = None,
    ):
        self._vm = vault_manager or VaultManager()
        self._merger = Merger()
        self._renderer = BoardRenderer()
        self._writer = VaultWriter()

    def refresh(
        self,
        vault_id: str,
        dry_run: bool = False,
        board_rel_path: str | None = None,
    ) -> dict:
        vault = self._vm.get_vault(vault_id)
        if not vault:
            return {"error": f"Vault not found: {vault_id}", "path": "", "changed": False}

        projects = self._collect_projects()
        block = self._build_block(projects)
        board_file = self._resolve_board_path(vault, board_rel_path)
        return self._writer.write(board_file, block, dry_run=dry_run)

    def refresh_all(self, dry_run: bool = False) -> list[dict]:
        results: list[dict] = []
        for v in self._vm.list_vaults():
            result = self.refresh(v.id, dry_run=dry_run)
            results.append(result)
        return results

    def status(self, vault_id: str) -> dict:
        vault = self._vm.get_vault(vault_id)
        if not vault:
            return {"error": f"Vault not found: {vault_id}"}
        board_file = self._resolve_board_path(vault)
        if board_file.exists():
            content = board_file.read_text(encoding="utf-8")
            staleness = self._staleness_days(content)
            return {
                "vault": vault.name,
                "board_exists": True,
                "board_path": str(board_file),
                "last_refreshed_days_ago": staleness,
                "drift": self._has_drift(vault.id),
            }
        return {
            "vault": vault.name,
            "board_exists": False,
            "board_path": str(board_file),
            "last_refreshed_days_ago": None,
            "drift": self._has_drift(vault.id),
        }

    def refresh_for_vault_name(self, name: str, dry_run: bool = False) -> dict:
        """Refresh based on vault display name (e.g. 'Research' -> Documents/Research)."""
        vaults = self._vm.list_vaults()
        # Try exact match
        for v in vaults:
            if v.name.lower() == name.lower():
                return self.refresh(v.id, dry_run=dry_run)
        # Try prefix match (e.g. 'Doc' matches 'Documents')
        for v in vaults:
            if v.name.lower().startswith(name.lower()):
                return self.refresh(v.id, dry_run=dry_run)
        return {"error": f"Vault not found by name: {name}", "path": "", "changed": False}

    def _resolve_board_path(self, vault, board_rel_path: str | None = None) -> Path:
        """Resolve board file path, checking known sub-vaults then vault-root."""
        vault_root = Path(vault.path).expanduser()
        if board_rel_path:
            return vault_root / board_rel_path

        # Prefer known sub-vaults (e.g. Research/ inside Documents/) if the directory exists.
        for sub in ("Research",):
            candidate = vault_root / sub / "Engineering" / "_ACTION-BOARD.md"
            if candidate.exists() or (vault_root / sub).is_dir():
                return candidate

        # Fall back to vault-root path
        return vault_root / "Engineering" / "_ACTION-BOARD.md"

    def _collect_projects(self) -> list[ProjectStatus]:
        sources: list[list[ProjectStatus]] = []
        try:
            sources.append(AtlasConnector().fetch())
        except Exception:
            pass
        try:
            sources.append(StatusConnector().fetch())
        except Exception:
            pass
        return self._merger.merge(sources)

    def _build_block(self, projects: list[ProjectStatus]) -> str:
        body = self._renderer.render(projects)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"{MARKER_START}\n> generated: {timestamp} by obs board refresh\n\n{body}{MARKER_END}\n"

    def _staleness_days(self, content: str) -> int:
        import re
        m = re.search(r"generated:\s*(\d{4}-\d{2}-\d{2})", content)
        if m:
            try:
                gen = datetime.strptime(m.group(1), "%Y-%m-%d")
                return (datetime.now() - gen).days
            except ValueError:
                pass
        return -1

    def _has_drift(self, vault_id: str) -> bool:
        """True if the sync layer reports disk<->DB divergence for this vault.

        Checks all three drift-bearing check families (sync-ghosts, sync-missing,
        sync-errors) at fail/warn/error status — sync-drift is excluded (always
        'info', never actionable). 'error' is included deliberately: a check that
        couldn't run (query failure, corrupt schema) is not evidence of "no
        drift" and must not be conflated with an actual clean pass.
        """
        try:
            from core.doctor import run_checks  # noqa: E402
            results = run_checks(vault_id=vault_id, layers=["sync"])
            for r in results:
                check_id = r.id.split(":", 1)[0]
                if r.status in ("fail", "warn", "error") and check_id in (
                    "sync-ghosts", "sync-missing", "sync-errors",
                ):
                    return True
        except Exception:
            log.exception("_has_drift: sync check failed for vault %s", vault_id)
        return False
