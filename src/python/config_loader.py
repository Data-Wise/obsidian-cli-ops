"""
obs config loader — Phase 1 (ARTIFACT-config-schema-2026-06-21.md §4)

Priority chain (first hit wins):
  1. ~/.config/obs/config.yaml       — new unified format
  2. ~/.config/obs/config             — legacy obs shell-env
  3. ~/.config/nexus/config.yaml      — legacy nexus YAML
  4. None → caller prompts `obs config init`
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

# ──────────────────────────────────────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_REGISTRY = (
    "https://raw.githubusercontent.com/obsidianmd/"
    "obsidian-releases/master/community-plugins.json"
)
DEFAULT_TEMPLATES_SUBPATH = "_SYSTEM/templates"


@dataclass
class ZoteroConfig:
    """Zotero `research.zotero` config section (database + storage paths)."""

    database: Path
    storage: Path


@dataclass
class TeachingConfig:
    """Teaching `research.teaching` config section (courses + materials dirs)."""

    courses_dir: Path
    materials_dir: Optional[Path] = None


@dataclass
class WritingConfig:
    """Writing `research.writing` config section (manuscripts + templates dirs)."""

    manuscripts_dir: Path
    templates_dir: Optional[Path] = None


@dataclass
class ResearchConfig:
    """`research` config section (zotero, pdf dirs, teaching, writing)."""

    zotero: Optional[ZoteroConfig] = None
    pdf_directories: list[Path] = field(default_factory=list)
    teaching: Optional[TeachingConfig] = None
    writing: Optional[WritingConfig] = None


@dataclass
class ObsConfig:
    """Top-level obs config (vault, research, plugins sections + source tag)."""

    # vault section
    root: Path
    active: list[str] = field(default_factory=list)
    templates: Optional[Path] = None
    # research section (absent for vault-only installs)
    research: Optional[ResearchConfig] = None
    # plugins section
    registry: str = DEFAULT_REGISTRY
    # metadata
    source: str = "unknown"  # which file was read

    @property
    def templates_resolved(self) -> Path:
        """Return the explicit templates path, or the default under vault root."""
        if self.templates:
            return self.templates
        return self.root / DEFAULT_TEMPLATES_SUBPATH


# ──────────────────────────────────────────────────────────────────────────────
# Loader
# ──────────────────────────────────────────────────────────────────────────────

_UNIFIED_PATH = Path("~/.config/obs/config.yaml")
_LEGACY_OBS_PATH = Path("~/.config/obs/config")
_LEGACY_NEXUS_PATH = Path("~/.config/nexus/config.yaml")


def load() -> Optional[ObsConfig]:
    """Walk the priority chain and return the first parseable config, or None."""
    for loader_fn, source_tag in [
        (_load_unified, "unified"),
        (_load_legacy_obs, "legacy-obs"),
        (_load_legacy_nexus, "legacy-nexus"),
    ]:
        cfg = loader_fn()
        if cfg is not None:
            cfg.source = source_tag
            return cfg
    return None


def load_or_exit() -> ObsConfig:
    """Load config; print a helpful message and exit(1) if nothing found."""
    cfg = load()
    if cfg is None:
        print(
            "[obs] No config found. Run `obs config init` to create one, or\n"
            "[obs] `obs config migrate` to convert an existing obs/nexus config.",
            file=sys.stderr,
        )
        sys.exit(1)
    return cfg


# ──────────────────────────────────────────────────────────────────────────────
# Format readers
# ──────────────────────────────────────────────────────────────────────────────

def _expand(raw: str) -> Path:
    return Path(os.path.expanduser(raw))


def _load_unified() -> Optional[ObsConfig]:
    path = _UNIFIED_PATH.expanduser()
    if not path.exists():
        return None
    if yaml is None:
        raise RuntimeError("PyYAML required for config loading: pip install pyyaml")
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    v = doc.get("vault", {})
    root_raw = v.get("root")
    if not root_raw:
        return None

    root = _expand(root_raw)
    active = list(v.get("active") or [])
    templates_raw = v.get("templates")
    templates = _expand(templates_raw) if templates_raw else None

    research = _parse_research(doc.get("research"))

    plugins = doc.get("plugins", {}) or {}
    registry = plugins.get("registry") or DEFAULT_REGISTRY

    return ObsConfig(
        root=root,
        active=active,
        templates=templates,
        research=research,
        registry=registry,
    )


def _load_legacy_obs() -> Optional[ObsConfig]:
    path = _LEGACY_OBS_PATH.expanduser()
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")

    root_raw = _shell_str(text, "OBS_ROOT")
    if not root_raw:
        return None
    root = _expand(root_raw)

    vaults_raw = _shell_array(text, "VAULTS")
    registry_raw = _shell_str(text, "PLUGIN_REGISTRY") or DEFAULT_REGISTRY

    templates = root / DEFAULT_TEMPLATES_SUBPATH

    return ObsConfig(
        root=root,
        active=vaults_raw,
        templates=templates,
        registry=registry_raw,
    )


def _load_legacy_nexus() -> Optional[ObsConfig]:
    path = _LEGACY_NEXUS_PATH.expanduser()
    if not path.exists():
        return None
    if yaml is None:
        raise RuntimeError("PyYAML required for config loading: pip install pyyaml")
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    v = doc.get("vault", {}) or {}
    root_raw = v.get("path")
    if not root_raw:
        return None
    root = _expand(root_raw)

    templates_raw = v.get("templates")
    templates = _expand(templates_raw) if templates_raw else root / DEFAULT_TEMPLATES_SUBPATH

    # nexus stores zotero/pdf at top level; teaching/writing under their own keys
    research = _parse_research(doc)

    return ObsConfig(
        root=root,
        active=[],   # nexus had a single vault root, not named sub-vaults
        templates=templates,
        research=research,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _shell_str(text: str, key: str) -> Optional[str]:
    """Extract `KEY="value"` or `KEY=value` from a shell-env file."""
    m = re.search(rf'^{re.escape(key)}=(.*)', text, re.MULTILINE)
    if not m:
        return None
    return m.group(1).strip().strip("\"'")


def _shell_array(text: str, key: str) -> list[str]:
    """Extract `KEY=(a b c)` or `KEY=("a" "b" "c")` from a shell-env file."""
    m = re.search(rf'^{re.escape(key)}=\(([^)]*)\)', text, re.MULTILINE)
    if not m:
        return []
    raw = m.group(1)
    # items may be quoted or bare, separated by whitespace
    return [item.strip('"\'') for item in raw.split() if item.strip('"\'')]


def _parse_research(doc: Optional[dict]) -> Optional[ResearchConfig]:
    if not doc:
        return None
    z_raw = doc.get("zotero") or {}
    pdf_raw = (doc.get("pdf") or {}).get("directories") or []
    t_raw = doc.get("teaching") or {}
    w_raw = doc.get("writing") or {}

    if not z_raw and not pdf_raw and not t_raw and not w_raw:
        return None

    zotero = None
    if z_raw.get("database"):
        zotero = ZoteroConfig(
            database=_expand(z_raw["database"]),
            storage=_expand(z_raw.get("storage", "~/Zotero/storage")),
        )

    teaching = None
    if t_raw.get("courses_dir"):
        teaching = TeachingConfig(
            courses_dir=_expand(t_raw["courses_dir"]),
            materials_dir=_expand(t_raw["materials_dir"]) if t_raw.get("materials_dir") else None,
        )

    writing = None
    if w_raw.get("manuscripts_dir"):
        writing = WritingConfig(
            manuscripts_dir=_expand(w_raw["manuscripts_dir"]),
            templates_dir=_expand(w_raw["templates_dir"]) if w_raw.get("templates_dir") else None,
        )

    pdf_dirs = [_expand(d) for d in pdf_raw]
    return ResearchConfig(zotero=zotero, pdf_directories=pdf_dirs, teaching=teaching, writing=writing)


# ──────────────────────────────────────────────────────────────────────────────
# `obs config` CLI commands
# ──────────────────────────────────────────────────────────────────────────────

def cmd_show() -> int:
    """Print the resolved config; return exit code (1 if none found)."""
    cfg = load()
    if cfg is None:
        print("[obs] No config found. Run `obs config init`.")
        return 1
    print(f"# obs config  (source: {cfg.source})")
    print(f"vault.root:      {cfg.root}")
    print(f"vault.active:    {cfg.active}")
    print(f"vault.templates: {cfg.templates_resolved}")
    if cfg.research:
        if cfg.research.zotero:
            print(f"research.zotero.database: {cfg.research.zotero.database}")
            print(f"research.zotero.storage:  {cfg.research.zotero.storage}")
        if cfg.research.pdf_directories:
            for d in cfg.research.pdf_directories:
                print(f"research.pdf.directory:   {d}")
        if cfg.research.teaching:
            print(f"research.teaching.courses_dir:   {cfg.research.teaching.courses_dir}")
            if cfg.research.teaching.materials_dir:
                print(f"research.teaching.materials_dir: {cfg.research.teaching.materials_dir}")
        if cfg.research.writing:
            print(f"research.writing.manuscripts_dir: {cfg.research.writing.manuscripts_dir}")
            if cfg.research.writing.templates_dir:
                print(f"research.writing.templates_dir:  {cfg.research.writing.templates_dir}")
    print(f"plugins.registry: {cfg.registry}")
    return 0


def cmd_validate() -> int:
    """Validate the config; return exit code (1 if missing or invalid)."""
    cfg = load()
    if cfg is None:
        print("INVALID: no config found")
        return 1
    if not cfg.root:
        print("INVALID: vault.root is empty")
        return 1
    print(f"OK (source: {cfg.source})")
    return 0


def cmd_migrate(dry_run: bool = False) -> int:
    """Read any legacy format, show the unified YAML, and optionally write it."""
    # Skip unified if it already exists — nothing to migrate
    unified = _UNIFIED_PATH.expanduser()
    if unified.exists():
        print(f"[obs] {unified} already exists — nothing to migrate.")
        return 0

    # Try reading a legacy source
    cfg = None
    for loader_fn, tag in [(_load_legacy_obs, "obs shell-env"), (_load_legacy_nexus, "nexus YAML")]:
        cfg = loader_fn()
        if cfg:
            cfg.source = tag
            break

    if cfg is None:
        print("[obs] No legacy config found. Run `obs config init` to create one.")
        return 1

    yaml_out = _to_yaml(cfg)
    print(f"# Migrated from: {cfg.source}")
    print(yaml_out)

    if dry_run:
        print(f"# Dry-run — would write to {unified}")
        return 0

    answer = input(f"Write to {unified}? [y/N] ").strip().lower()
    if answer != "y":
        print("Aborted.")
        return 0
    unified.parent.mkdir(parents=True, exist_ok=True)
    unified.write_text(yaml_out, encoding="utf-8")
    print(f"[obs] Written: {unified}")
    return 0


def cmd_init() -> int:
    """Interactive wizard to create ~/.config/obs/config.yaml."""
    unified = _UNIFIED_PATH.expanduser()
    if unified.exists():
        answer = input(f"{unified} already exists. Overwrite? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return 0

    default_root = "~/Library/Mobile Documents/iCloud~md~obsidian/Documents"
    root = input(f"Vault root [{default_root}]: ").strip() or default_root

    vaults_input = input("Active sub-vaults (space-separated) [Research]: ").strip()
    vaults = vaults_input.split() if vaults_input else ["Research"]

    yaml_out = _to_yaml(ObsConfig(
        root=_expand(root),
        active=vaults,
        source="init",
    ))
    unified.parent.mkdir(parents=True, exist_ok=True)
    unified.write_text(yaml_out, encoding="utf-8")
    print(f"[obs] Created: {unified}")
    print("[obs] Edit with `obs config edit`, validate with `obs config validate`.")
    return 0


def cmd_edit() -> int:
    """Open the unified config in $EDITOR; return 1 if it does not exist."""
    unified = _UNIFIED_PATH.expanduser()
    if not unified.exists():
        print(f"[obs] {unified} does not exist. Run `obs config init` first.")
        return 1
    editor = os.environ.get("EDITOR", "vi")
    os.execvp(editor, [editor, str(unified)])
    return 0  # unreachable; exec replaces process


def _to_yaml(cfg: ObsConfig) -> str:
    lines = [
        "# obs unified config — https://data-wise.github.io/obsidian-cli-ops/",
        "version: 1",
        "",
        "vault:",
        f'  root: "{cfg.root}"',
    ]
    if cfg.active:
        lines.append("  active:")
        for v in cfg.active:
            lines.append(f"    - {v}")
    if cfg.templates:
        lines.append(f'  templates: "{cfg.templates}"')
    if cfg.research:
        lines.append("")
        lines.append("research:")
        if cfg.research.zotero:
            lines.append("  zotero:")
            lines.append(f'    database: "{cfg.research.zotero.database}"')
            lines.append(f'    storage: "{cfg.research.zotero.storage}"')
        if cfg.research.pdf_directories:
            lines.append("  pdf:")
            lines.append("    directories:")
            for d in cfg.research.pdf_directories:
                lines.append(f'      - "{d}"')
        if cfg.research.teaching:
            lines.append("  teaching:")
            lines.append(f'    courses_dir: "{cfg.research.teaching.courses_dir}"')
            if cfg.research.teaching.materials_dir:
                lines.append(f'    materials_dir: "{cfg.research.teaching.materials_dir}"')
        if cfg.research.writing:
            lines.append("  writing:")
            lines.append(f'    manuscripts_dir: "{cfg.research.writing.manuscripts_dir}"')
            if cfg.research.writing.templates_dir:
                lines.append(f'    templates_dir: "{cfg.research.writing.templates_dir}"')
    if cfg.registry != DEFAULT_REGISTRY:
        lines.append("")
        lines.append("plugins:")
        lines.append(f'  registry: "{cfg.registry}"')
    lines.append("")
    return "\n".join(lines)
