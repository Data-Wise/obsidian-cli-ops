# Diagnostics with `obs doctor`

> **TL;DR** (30 seconds)
>
> - **What:** Self-diagnostic checks on your `obs` install — runtime, DB, vault health, sync drift, MCP, docs, iCloud
> - **Why:** Find broken links, ghost notes, and doc/count drift before they bite
> - **How:** `obs doctor` (full) or `obs doctor --layer sync` (one layer) or `obs doctor --vault Research` (scope)
> - **Next:** heal drift with `obs scan <vault> --prune`
{ .tldr }

**Level:** 🟡 Intermediate | **Time:** ~10 min | **Commands:** `obs doctor`, `obs scan --prune`

---

## What You'll Learn

- Run the full diagnostic and read pass/warn/fail verdicts
- Scope checks to one vault with `--vault`
- Target a single layer with `--layer` (repeatable)
- Interpret the **sync** layer and heal ghost notes with `obs scan --prune`
- Capture JSON output for CI / automation

---

## Prerequisites

- `obs` installed and at least one vault scanned (`obs scan` or `obs discover --scan`)
- The database initialized (`obs db init`, or done automatically on first scan)

---

## Step 1 — Run the full diagnostic

```bash
obs doctor
```

`obs doctor` runs every layer and prints a verdict per check. Each check is one of
**pass**, **warn** (non-blocking), or **fail** (something needs fixing).

Layers checked: `python`, `database`, `vault`, `sync`, `mcp`, `docs`, `icloud` —
plus `flow` for vault↔repo mirror config (see the
[Vault↔Repo Mirroring tutorial](flow-init.md)).

---

## Step 2 — Scope to one vault

Limit vault-level and sync checks to a single vault by name or ID:

```bash
obs doctor --vault Research
```

Useful when one vault is misbehaving and you don't want the noise from the others.

---

## Step 3 — Target a single layer

`--layer` is repeatable and skips everything else. Common targets:

```bash
obs doctor --layer sync                 # Vault↔index drift only
obs doctor --layer database --json      # DB integrity as JSON
obs doctor --layer docs                 # Doc/count accuracy (release gate)
obs doctor --layer flow                 # Vault↔repo mirror config
```

`obs doctor --layer docs` is part of the release harness — it catches count drift
between source code and documentation before a release lands.

---

## Step 4 — The sync layer (most useful)

`obs doctor --layer sync` compares each vault's files on disk against its index rows
(content-based, not just mtime). It reports:

| Check | Verdict | Catches | Fix |
|-------|---------|---------|-----|
| `sync-ghosts` | warn | DB rows whose file is gone from disk (deleted / renamed) | `obs scan <vault> --prune` |
| `sync-missing` | warn | `*.md` on disk absent from the DB (never scanned, or a swallowed error) | `obs scan <vault>` (check logs) |
| `sync-errors` | warn/fail | last `scan_history` row recorded per-note failures | inspect the failing paths in the scan log |
| `sync-drift` | info | one-line summary: `disk=N db=M (X ghost, Y missing)` | — |

---

## Step 5 — Heal a vault

A plain `obs scan` is **additive** — it never removes rows. To clear ghost notes
(rows whose file is gone), re-scan with `--prune`:

```bash
obs doctor --vault Research --layer sync   # confirm sync-ghosts first
obs scan Research --prune                   # sweep rows whose path is gone
obs doctor --vault Research --layer sync    # verify drift is gone
```

!!! warning "Safety guard"
    `--prune` is skipped (with a warning) if the scan sees **zero** files — so a
    mis-pointed path or an un-materialised iCloud vault won't wipe your index.

---

## Step 6 — JSON for automation

Every check supports `--json` for scripting and CI:

```bash
obs doctor --layer database --json | python3 -c "
import json, sys
r = json.load(sys.stdin)
fails = [c for c in r['checks'] if c['status'] == 'fail']
print(f'{len(fails)} failing checks')
"
```

---

## Common scenarios

| Symptom | Command | Fix |
|---------|---------|-----|
| A deleted note still shows in `obs search` | `obs doctor --layer sync` | `obs scan <vault> --prune` |
| `Links: N (M broken)` in `obs stats` | `obs doctor --vault <vault> --layer vault` | fix or remove the broken wikilinks |
| iCloud vault looks empty | `obs doctor --layer icloud` | materialise the vault (open in Obsidian) |
| Docs/count mismatch before release | `obs doctor --layer docs` | run `scripts/validate-counts.sh --fix` |
| MCP server misbehaves | `obs doctor --layer mcp` | review the AST guard failures it reports |

---

## Next Steps

- [CLI Reference → `obs doctor`](../cli-reference.md#obs-doctor) — all flags and examples
- [Vault↔Repo Mirroring](flow-init.md) — the `flow` layer in detail
- [Cookbook → Diagnose & Heal a Vault](../cookbook.md#diagnose-heal-a-vault) — copy-paste recipes
