"""
obs flow init — Interactive wizard to create .flow/obsidian-sync.yml.

Provides both interactive (TTY) and non-interactive (flags) modes.
Validates output against JSON Schema before writing.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

_SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "schema" / "obsidian-sync.schema.json"
_FLOW_DIR = ".flow"
_FLOW_FILE = "obsidian-sync.yml"


@dataclass
class FlowConfig:
    """In-memory representation of .flow/obsidian-sync.yml."""
    vault_root: str
    pairs: list[dict[str, str]]
    include: list[str] = field(default_factory=lambda: ["*.md"])
    exclude: list[str] = field(default_factory=lambda: ["_archive"])

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "vault_root": self.vault_root,
            "pairs": self.pairs,
        }
        if self.include != ["*.md"]:
            d["include"] = self.include
        if self.exclude != ["_archive"]:
            d["exclude"] = self.exclude
        return d

    def to_yaml(self) -> str:
        return yaml.dump(
            self.to_dict(),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )


def _load_schema() -> dict[str, Any]:
    """Load the JSON Schema for obsidian-sync.yml."""
    if not _SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema not found: {_SCHEMA_PATH}")
    with open(_SCHEMA_PATH) as f:
        return json.load(f)


def validate_config(config: FlowConfig) -> list[str]:
    """Validate a FlowConfig against JSON Schema. Returns list of errors (empty = valid)."""
    schema = _load_schema()
    data = config.to_dict()
    errors: list[str] = []

    # Check required fields
    for key in schema.get("required", []):
        if key not in data:
            errors.append(f"Missing required field: {key}")

    # Validate vault_root
    if "vault_root" in data:
        vr = data["vault_root"]
        if not isinstance(vr, str) or not vr.strip():
            errors.append("vault_root must be a non-empty string")
        else:
            expanded = Path(vr).expanduser()
            if not expanded.exists():
                errors.append(f"vault_root path not found: {vr}")

    # Validate pairs
    if "pairs" in data:
        pairs = data["pairs"]
        if not isinstance(pairs, list) or len(pairs) == 0:
            errors.append("pairs must be a non-empty list")
        else:
            seen: set[tuple[str, str]] = set()
            for i, pair in enumerate(pairs):
                if not isinstance(pair, dict):
                    errors.append(f"pairs[{i}] must be an object")
                    continue
                for key in ("vault", "repo"):
                    if key not in pair:
                        errors.append(f"pairs[{i}] missing required field: {key}")
                    elif not isinstance(pair[key], str) or not pair[key].strip():
                        errors.append(f"pairs[{i}].{key} must be a non-empty string")
                    elif pair[key].startswith("/"):
                        errors.append(f"pairs[{i}].{key} must not start with /")
                    elif ".." in pair[key]:
                        errors.append(f"pairs[{i}].{key} must not contain ..")
                if "vault" in pair and "repo" in pair:
                    if pair["vault"] == pair["repo"]:
                        errors.append(f"pairs[{i}]: vault and repo are identical (no-op)")
                    pair_key = (pair.get("vault", ""), pair.get("repo", ""))
                    if pair_key in seen:
                        errors.append(f"pairs[{i}]: duplicate vault→repo mapping")
                    seen.add(pair_key)

    return errors


def _infer_vault_root(cwd: Path) -> str:
    """Try to infer vault_root from repo structure."""
    # Look for .obsidian directory up the tree
    current = cwd
    for _ in range(5):
        if (current / ".obsidian").is_dir():
            return str(current)
        parent = current.parent
        if parent == current:
            break
        current = parent
    # Default to iCloud research path
    return "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Research"


def _infer_pairs(cwd: Path) -> list[dict[str, str]]:
    """Try to infer pairs from repo structure.

    Returns empty list — inference is unreliable and creates invalid configs.
    Users should specify pairs explicitly via --pairs or interactive prompts.
    """
    return []


def init_flow_config(
    directory: str = ".",
    vault_root: Optional[str] = None,
    pairs_json: Optional[str] = None,
    force: bool = False,
    non_interactive: bool = False,
) -> FlowConfig:
    """
    Create .flow/obsidian-sync.yml config.

    Args:
        directory: Target directory (default: current dir)
        vault_root: Vault root path (non-interactive mode)
        pairs_json: JSON array of pairs (non-interactive mode)
        force: Overwrite existing config
        non_interactive: Skip prompts, use flags only

    Returns:
        FlowConfig that was written

    Raises:
        FileExistsError: If config exists and --force not set
        ValueError: If validation fails
    """
    target = Path(directory).resolve()
    flow_dir = target / _FLOW_DIR
    flow_file = flow_dir / _FLOW_FILE

    # Check existing
    if flow_file.exists() and not force:
        raise FileExistsError(
            f"Config already exists: {flow_file}\n"
            "Use --force to overwrite"
        )

    # Backup before overwrite
    if flow_file.exists() and force:
        backup = flow_file.with_suffix(".yml.bak")
        shutil.copy2(flow_file, backup)

    # Build config
    if non_interactive:
        if not vault_root:
            raise ValueError("--vault-root required in non-interactive mode")
        if not pairs_json:
            raise ValueError("--pairs required in non-interactive mode")
        pairs = json.loads(pairs_json)
        if not isinstance(pairs, list):
            raise ValueError("--pairs must be a JSON array")
        for i, pair in enumerate(pairs):
            if not isinstance(pair, dict):
                raise ValueError(f"--pairs[{i}] must be a JSON object")
            if "vault" not in pair or "repo" not in pair:
                raise ValueError(f"--pairs[{i}] must have 'vault' and 'repo' keys")
        config = FlowConfig(vault_root=vault_root, pairs=pairs)
    else:
        config = _interactive_init(target)

    # Validate
    errors = validate_config(config)
    if errors:
        raise ValueError(f"Validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    # Write (atomic via temp + rename)
    flow_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=flow_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write("# Vault↔repo mirror map for savant `plan:obsidian-sync`\n")
            f.write(f"# Created: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n")
            f.write(config.to_yaml())
        os.replace(tmp_path, flow_file)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    return config


def _interactive_init(target: Path) -> FlowConfig:
    """Interactive wizard to build FlowConfig."""
    print(f"\nInitializing {_FLOW_FILE} for: {target.name}\n")

    # Vault root
    default_root = _infer_vault_root(target)
    vr_input = input(f"vault_root [{default_root}]: ").strip()
    vault_root = vr_input if vr_input else default_root

    # Pairs
    pairs: list[dict[str, str]] = []
    print("\npairs (vault → repo):")
    suggested = _infer_pairs(target)

    while True:
        if suggested:
            use_suggested = input(f"  Use suggested pairs ({len(suggested)} found)? [Y/n]: ").strip().lower()
            if use_suggested != "n":
                pairs = suggested
                for p in pairs:
                    print(f"    vault: {p['vault']}  →  repo: {p['repo']}")
                break

        add = input("  Add pair? [Y/n]: ").strip().lower()
        if add == "n":
            break
        vault = input("    vault (relative to vault_root): ").strip()
        repo = input("    repo (relative to repo root): ").strip()
        if vault and repo:
            pairs.append({"vault": vault, "repo": repo})

        another = input("  Add another pair? [N]: ").strip().lower()
        if another != "y":
            break

    if not pairs:
        print("  Warning: no pairs defined — config will be incomplete")

    # Include/exclude
    include_input = input("\ninclude [*.md]: ").strip()
    include = [s.strip() for s in include_input.split(",")] if include_input else ["*.md"]

    exclude_input = input("exclude [_archive]: ").strip()
    exclude = [s.strip() for s in exclude_input.split(",")] if exclude_input else ["_archive"]

    return FlowConfig(
        vault_root=vault_root,
        pairs=pairs,
        include=include,
        exclude=exclude,
    )


def get_config_for_vault(vault_path: str) -> Optional[FlowConfig]:
    """Load existing .flow/obsidian-sync.yml for a vault."""
    flow_file = Path(vault_path) / _FLOW_DIR / _FLOW_FILE
    if not flow_file.exists():
        return None
    try:
        with open(flow_file) as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return None
        return FlowConfig(
            vault_root=data.get("vault_root", ""),
            pairs=data.get("pairs", []),
            include=data.get("include", ["*.md"]),
            exclude=data.get("exclude", ["_archive"]),
        )
    except (yaml.YAMLError, OSError, KeyError):
        return None
