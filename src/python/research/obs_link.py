"""obs link — create the per-project ``.obs/sync.yml`` mirror map (docs-standards ADR-001).

The mirror map is **obs-owned**: every project carries one (settings contract, ADR-001).
Vault-mirroring projects (research / teaching) declare a ``vault_root`` + ``pairs``;
non-vault projects (packages / dev-tools) use ``mirror: none`` so the file exists but is a
no-op. Idempotent: never clobbers an existing map unless ``force=True``.

This module is the durable core invoked by the ``obs link`` CLI command and (eventually) by
``atlas doctor --fix``'s ``.obs`` half.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

SCHEMA_VERSION = 1
DEFAULT_INCLUDE = ["*.md"]
DEFAULT_EXCLUDE = ["_archive"]


def build_sync_map(
    vault_root: str | None = None,
    pairs: list[dict] | None = None,
    mirror: str | None = None,
) -> dict[str, Any]:
    """Build the ``.obs/sync.yml`` document.

    ``mirror``: ``"mirror"`` (active vault<->repo sync) or ``"none"`` (no-op placeholder).
    Defaults to ``"none"`` when no ``vault_root``/``pairs`` are given, else ``"mirror"``.
    """
    if mirror is None:
        mirror = "mirror" if (vault_root or pairs) else "none"

    doc: dict[str, Any] = {"schema": SCHEMA_VERSION, "mirror": mirror}
    if mirror == "none":
        return doc

    doc["vault_root"] = vault_root or ""
    doc["pairs"] = pairs or []
    doc["include"] = list(DEFAULT_INCLUDE)
    doc["exclude"] = list(DEFAULT_EXCLUDE)
    return doc


def write_link(
    project_dir: str | Path,
    vault_root: str | None = None,
    pairs: list[dict] | None = None,
    mirror: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Create ``<project_dir>/.obs/sync.yml``. Idempotent unless ``force``.

    Returns ``{created, existed, path, mirror}``.
    """
    proj = Path(project_dir).expanduser()
    target = proj / ".obs" / "sync.yml"
    existed = target.exists()

    if existed and not force:
        return {
            "created": False,
            "existed": True,
            "path": str(target),
            "mirror": _read_mirror(target),
        }

    doc = build_sync_map(vault_root=vault_root, pairs=pairs, mirror=mirror)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return {
        "created": True,
        "existed": existed,
        "path": str(target),
        "mirror": doc["mirror"],
    }


def _read_mirror(path: Path) -> str:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return str(data.get("mirror", "unknown"))
    except Exception:
        return "unknown"
