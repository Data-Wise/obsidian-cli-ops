# BRAINSTORM: v3.4.0 — Bridge + Temporal Analytics

**Date:** 2026-06-19
**Mode:** feature+arch / default depth
**Source spec:** `docs/specs/SPEC-v3.3.0-bridge-temporal-2026-06-04.md` (reviewed, 0 open questions)
**Context:** SPEC build order is explicit. v3.3.0 shipped as MCP release; bridge+temporal is now v3.4.0. Foundation in place: `ai/obsidian_bridge.py` (122 lines, read-only, `is_available()` works). No new deps. No schema migration.

---

## Increment Plan

### INC 1 — Detection + Temporal (offline, zero-risk) ~4-6h ✅ Start here

All three are offline, zero-risk, zero-dep, independently testable.

#### `obs bridge status`
- Extend `is_available()` → `BridgeStatus` dataclass (`{cli_installed, cli_version, app_running, capabilities[]}`)
- Add `bridge_status()` to core (thin wrapper)
- Wire: `obs_cli.py` argparse → `obs.zsh` dispatcher
- Output: Rich table; `--json`
- **Risk:** none — detection-only, no mutations

#### `obs trends <vault>`
- New `core/temporal.py`: `compute_trends()`
- Sources: `scan_history` + `notes.created_at/modified_at`
- Output: weekly buckets + Rich sparkline + `--json`
- **Risk:** `scan_history` may be sparse (last scan 2026-02-28 for real vaults — 1 row). Degrade gracefully: "insufficient scan history" notice

#### `obs stale <vault>`
- In same `core/temporal.py`: `compute_stale()`
- SQL: `JOIN graph_metrics.pagerank × notes.modified_at`; `staleness_score = pagerank × age_factor`
- Output: importance-ranked Rich table + `--json`
- **Risk:** `graph_metrics` may be empty if `obs analyze` never run → fall back to plain date sort with notice

#### INC 1 Housekeeping (quick, same PR)
- Remove stale `e2e_vault0` test vaults from registered vault list (2 artifacts polluting `obs list`)
- Investigate `Links: 0` display in `obs stats` — likely `analyze` must run post-scan to populate `graph_metrics`

---

### INC 2 — Bridge Write Path (app-required) ~4-6h

**⚠️ SPIKE FIRST (30 min):** Verify official Obsidian CLI write command syntax:
```bash
obsidian --help | grep -E 'property|tag|append'
obsidian property:set --help
```
Confirm: arg style (`key=val` vs `--key val`), vault context handling, exit codes.

#### `obs ai tag-suggest --apply` (make inert flag real)
- Add write method to `ObsidianBridge`: `set_property(file, key, value) → bool`
- ZSH handler already has the `--apply` boolean flag slot; route to bridge instead of no-op

#### `obs apply <plan-file> [--execute]`
- Reads `refactor`/`tag-suggest` `--json` output (plan-file format = their JSON contract)
- Dry-run default: print `"Would: property:set ..."` per action
- `--execute`: interactive confirm per action → bridge call
- Partial-failure: stop on first error (safe default)

---

### INC 3 — AI Daily Digest ~3-4h

#### `obs ai daily-digest <vault>`
- Compose: health + trends delta + stale-but-important + new duplicates (from existing AI features)
- Delta source: diff last two `scan_history` rows
- AI provider: optional (narrative summary if available)
- Pure-offline fallback: structured report, no AI text
- Cron-friendly: `--json` output, exit 0 always

---

### INC 4 — Read-Side Enrichment (optional) ~2h

#### Alias resolution from official CLI when app running
- Fixes `graph_builder.py:57` alias TODO
- Auto-enable when bridge is available; `--no-bridge` opt-out
- Low risk: read-only, silent fallback already wired

---

## Key Risks

| Risk | Mitigation |
|---|---|
| Official CLI write syntax unknown | Spike `obsidian property:set --help` before INC 2 |
| Sparse `scan_history` (1 row) | `trends` degrades to "insufficient history" notice |
| Empty `graph_metrics` | `stale` falls back to plain date sort with notice |
| `apply` plan-file format drift | Pin to `--json` contract of `refactor`/`tag-suggest`; test it |

---

## Long-term (v3.5.0+)

- Theme C: community detection, eigenvector centrality
- Theme D: watch-daemon + batch-tag/batch-link (trivial once `apply` lands)
- Cross-vault ops (bridge queries across multiple vault IDs)
- Phase 2: Cowork plugin bundle (`obsidian-cli-ops-plugin/` repo)

---

## Recommended Path

**Start with INC 1** — bridge status + trends + stale in one feature worktree.

All three are offline, zero-risk, and deliver immediate value:
- `bridge status` validates the detection pattern before any write logic
- `trends` + `stale` are the "pure moat" temporals the official CLI structurally cannot do
- INC 1 gives a clean PR that runs offline without needing the Obsidian app

**Then spike INC 2** (write-API verification) before committing to the bridge write path.
