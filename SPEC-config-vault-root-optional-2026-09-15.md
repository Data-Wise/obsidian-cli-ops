# SPEC: Make `vault.root` optional in `config_loader.ObsConfig`

**Status:** DRAFT
**Date:** 2026-09-15
**Owner:** @dtofighi
**Affects:** `src/python/config_loader.py`, `src/python/obs_cli.py` (`obs config show`/`validate`), `src/python/mcp_server.py` (unaffected, confirmed below), `src/python/core/board.py` (unaffected, confirmed below)

## Background

On `dev@083d78d`, `BoardEngine._configured_board_path()` was reconciled to read
`board.path` via a new `config_loader.read_unified_doc()` helper instead of
duplicating YAML parsing. That fix deliberately did **not** route through
`config_loader.load()`/`ObsConfig`, because `_load_unified()` requires
`vault.root` and returns `None` for the **entire** config otherwise. A user
whose `~/.config/obs/config.yaml` has only a `board:` section (no `vault:`
section) gets correct `board.path` resolution from `board.py`, but that same
config is invisible to `obs config show`/`obs config validate` — they report
"no config found" even though the file parses fine.

This spec scopes that follow-up: make `vault.root` optional throughout
`config_loader.py` so a vault-less config (currently only `board.path`, but
this generalizes to any future top-level key) is visible and validatable.

## Objective

`obs config show` and `obs config validate` see and report on a `board:`-only
(or any-key-without-`vault:`) unified config, instead of treating it as
absent.

## Current behavior (verified 2026-09-15)

- `ObsConfig.root: Path` is a required (non-`Optional`) dataclass field.
- `_load_unified()` returns `None` immediately if
  `doc.get("vault", {}).get("root")` is falsy — the whole config is
  discarded, not just the vault section. ([config_loader.py:150](src/python/config_loader.py))
- `cmd_show()` / `cmd_validate()` both call `load()` and treat `None` as "no
  config found."
- `cmd_validate()` additionally does a second, redundant check:
  `if not cfg.root: print("INVALID: vault.root is empty")`.
- Consumers of `cfg.root` are narrow: `cmd_show()` (prints it),
  `cmd_validate()` (validates it), `_to_yaml()` (round-trips it for
  `cmd_migrate`/`cmd_init`), and the `templates_resolved` property (falls
  back to `root / DEFAULT_TEMPLATES_SUBPATH`).
- The two live `research`-domain consumers — `obs_cli.py:2015`
  (`config_loader.load()` inside the `research` command) and
  `mcp_server.py:1467`/`1571` (`_cl.load()` inside `_load_cfg()` /
  the stats-tool helper) — only ever read `cfg.research`, never `cfg.root`.
  **Confirmed unaffected** by `root` becoming `Optional`.
- `board.py` needs **no further change** — it already reads via
  `read_unified_doc()` and never touches `ObsConfig` (see the dev@083d78d
  decision this spec follows up on).

## Design

1. `ObsConfig.root: Path` → `ObsConfig.root: Optional[Path] = None`.
2. `_load_unified()`: stop early-returning when `root_raw` is falsy.
   `root = _expand(root_raw) if root_raw else None`; only the
   missing-file/unparseable case (already handled inside
   `read_unified_doc()`, which returns `None`) should make `_load_unified()`
   return `None`.
3. `templates_resolved` property: guard the `root`-based fallback. Today
   `root / DEFAULT_TEMPLATES_SUBPATH` assumes `root` is always a `Path`; with
   `root: Optional[Path]`, that call needs a guard (raise `ValueError` on
   `root is None and templates is None`, or return `None` — pick per the
   open question below). Only caller today is `cmd_show()`, already inside
   an `if cfg:` block.
4. `cmd_show()`: print `vault.root: (not set)` instead of the raw value (or
   crashing on `templates_resolved`) when `cfg.root is None`.
5. `cmd_validate()` — **the one open design fork, needs a decision before
   implementation**: a config with no `vault:` section but a valid `board:`
   section is not malformed, just vault-less. Two options:
   - **(a) Split validity**: `validate` reports "OK (vault-less, source: X)"
     for a parseable, vault-less config.
   - **(b) Keep `validate`'s existing vault-centric contract**: a config
     without `vault.root` still fails `obs config validate` (since `obs`'s
     primary purpose is vault management), but `load()` itself no longer
     discards the rest of the doc — so `show` and any future non-vault-only
     reader still see it; only `validate`'s pass/fail semantics stay as they
     are today.
   - **Recommendation: (b)** — smallest behavior change, keeps `validate`'s
     current contract stable for every existing vault-based config, and
     only fixes the actual bug (`show`/`load()` silently discarding
     non-vault data).
6. Legacy loaders (`_load_legacy_obs`, `_load_legacy_nexus`) are **untouched**
   — both predate `board.path`, have no vault-less use case, and keep their
   existing `root`-required early return.

## Non-goals

- Not adding a `board` field to `ObsConfig` — `board.py` already reads
  independently via `read_unified_doc()` (dev@083d78d) and doesn't need
  `ObsConfig` involvement.
- Not changing `cmd_init()` / `cmd_migrate()` / `_to_yaml()` — those flows
  are explicitly about setting up a vault+research config; a vault-less
  config isn't something `init`/`migrate` need to produce.
- Not touching `obs_cli.py`'s `research` command or `mcp_server.py`'s
  research tools — confirmed above they never read `cfg.root`.

## Testing plan

- `test_config_loader.py`: add cases for
  - a unified config with `board:` and no `vault:` section →
    `load()` returns a non-`None` `ObsConfig` with `root=None`.
  - `cmd_show()` on that config prints `vault.root: (not set)` without
    raising.
  - `cmd_validate()` behavior matching whichever of (a)/(b) is chosen.
- Re-run the full suite (629 passed / 4 skipped baseline, confirmed
  2026-09-15) to confirm zero regression on existing vault-root-present
  configs — the common case must be provably unchanged.

## Open question (blocks implementation)

Step 5: should `obs config validate` treat a vault-less-but-otherwise-valid
config as OK or INVALID? Recommendation above is **(b)** — keep `validate`'s
current pass/fail contract, fix only `load()`'s silent full-discard. Needs
sign-off before coding starts.

> Interrogated by grill — see [GRILL-config-vault-root-optional-2026-09-15.md](GRILL-config-vault-root-optional-2026-09-15.md)
