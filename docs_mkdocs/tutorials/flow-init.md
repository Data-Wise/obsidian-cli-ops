# Vault↔Repo Mirroring with `obs flow init`

> **TL;DR** (30 seconds)
>
> - **What:** Create `.flow/obsidian-sync.yml` — the single vault↔repo mirror map for savant `plan:obsidian-sync`
> - **Why:** Declare which vault folders sync to which repo folders so planning tools can bridge them
> - **How:** `obs flow init` (wizard) or `obs flow init --vault-root ~/vault --pairs '[{"vault":"a","repo":"b"}]'`
> - **Next:** `obs doctor --layer flow` to validate the config
{ .tldr }

**Level:** 🟡 Intermediate | **Time:** ~10 min | **Commands:** `obs flow init`, `obs doctor --layer flow`

---

## What You'll Learn

- Create a `.flow/obsidian-sync.yml` interactively (wizard) or non-interactively (flags/CI)
- Understand the four config fields: `vault_root`, `pairs`, `include`, `exclude`
- Validate the config against the JSON Schema with `obs doctor --layer flow`
- Overwrite an existing config safely (automatic `.bak` backup)

---

## Prerequisites

- `obs` installed (Homebrew or manual venv)
- A target **repo** directory (where the `.flow/` folder will live)
- The path to your Obsidian **vault** root (the folder containing `.obsidian/`)
- Optional: `obs doctor` available for the validation step

---

## Step 1 — Run the interactive wizard

From inside your repo, run `obs flow init`. The wizard infers a default `vault_root`
by walking up to five directories looking for a `.obsidian` folder; if none is found
it falls back to the iCloud Research path.

```bash
cd ~/code/my-repo
obs flow init
```

Sample session:

```
Initializing obsidian-sync.yml for: my-repo

vault_root [~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Research]: ~/vaults/Research

pairs (vault → repo):
  Add pair? [Y/n]: y
    vault (relative to vault_root): projects/atlas
    repo (relative to repo root): atlas
  Add another pair? [N]: n

include [*.md]:
exclude [_archive]:

✓ Wrote .flow/obsidian-sync.yml
```

!!! tip "Empty pairs are allowed (with a warning)"
    If you skip pairs, the wizard writes the file but warns it is incomplete.
    `pairs` is **required** by the schema, so `obs doctor --layer flow` will flag it later.

---

## Step 2 — Non-interactive mode (CI / scripts)

For automation, supply `--vault-root` and `--pairs` (a JSON array of
`{"vault": ..., "repo": ...}` objects). Both are required in non-interactive mode.

```bash
obs flow init \
  --vault-root ~/vaults/Research \
  --pairs '[{"vault":"projects/atlas","repo":"atlas"},{"vault":"notes","repo":"docs/notes"}]' \
  --json
```

`--json` returns the written config as machine-readable output:

```json
{
  "vault_root": "/Users/you/vaults/Research",
  "pairs": [
    {"vault": "projects/atlas", "repo": "atlas"},
    {"vault": "notes", "repo": "docs/notes"}
  ],
  "include": ["*.md"],
  "exclude": ["_archive"]
}
```

---

## Step 3 — Inspect the generated config

`obs flow init` writes `.flow/obsidian-sync.yml` atomically (temp file + `os.replace`)
and stamps a created date. The default contents:

```yaml
# Vault↔repo mirror map for savant `plan:obsidian-sync`
# Created: 2026-07-11
vault_root: ~/vaults/Research
pairs:
  - vault: projects/atlas
    repo: atlas
  - vault: notes
    repo: docs/notes
include:
  - "*.md"
exclude:
  - _archive
```

| Field | Required | Default | Notes |
|-------|----------|---------|-------|
| `vault_root` | yes | — | Absolute (or `~`-expanded) path to the vault root; must exist on disk |
| `pairs` | yes | — | Non-empty list of `{vault, repo}` objects |
| `include` | no | `["*.md"]` | Glob filters for files to mirror (omitted from file if default) |
| `exclude` | no | `["_archive"]` | Glob filters to skip (omitted from file if default) |

- `vault` / `repo` are **relative** paths (no leading `/`, no `..`)
- `vault` and `repo` must differ (a `vault == repo` pair is a no-op)
- Duplicate `vault → repo` mappings are rejected

See [Design Standards → Config File Contracts](../design-standards.md) and the
[CLI Reference](../cli-reference.md#obs-flow-init) for the full schema contract.

---

## Step 4 — Validate with `obs doctor --layer flow`

`obs doctor --layer flow` runs six checks against every `.flow/obsidian-sync.yml`:

| Check | What it catches |
|-------|-----------------|
| `flow-sync-missing` | No config found in the target repo (warn) |
| `flow-sync-schema` | Config fails JSON Schema validation |
| `flow-sync-stale` | Config unchanged for > 90 days |
| `flow-sync-vault-root` | `vault_root` path does not exist |
| `flow-sync-pair-duplicate` | Two pairs map the same `vault → repo` |
| `flow-sync-pair-identity` | A pair where `vault == repo` |

```bash
obs doctor --layer flow
```

A clean config reports no `flow-sync-*` errors. The `flow` layer is part of the
default `all_layers` set, so a plain `obs doctor` covers it too.

---

## Step 5 — Overwrite safely

`obs flow init` refuses to clobber an existing config unless you pass `--force`.
With `--force`, the previous file is copied to `.flow/obsidian-sync.yml.bak` first.

```bash
obs flow init --vault-root ~/vaults/Research --pairs '[{"vault":"projects/atlas","repo":"atlas"}]' --force
```

---

## Common validation errors

`obs flow init` validates before writing and prints every problem:

| Error | Cause | Fix |
|-------|-------|-----|
| `vault_root path not found` | Path doesn't exist on disk | Use the real vault root |
| `pairs must be a non-empty list` | No pairs supplied | Add at least one pair |
| `pairs[i] missing required field: vault` | Pair lacks `vault` or `repo` | Include both keys |
| `pairs[i].vault must not start with /` | Absolute path in a pair | Use a path relative to `vault_root` |
| `pairs[i].repo must not contain ..` | Path-traversal in a pair | Use a plain relative path |
| `pairs[i]: vault and repo are identical` | No-op mapping | Point repo somewhere else |
| `pairs[i]: duplicate vault→repo mapping` | Same pair twice | Remove the duplicate |

---

## Next Steps

- [Design Standards → Config File Contracts](../design-standards.md) — the full contract for `.flow/obsidian-sync.yml`
- [CLI Reference → `obs flow init`](../cli-reference.md#obs-flow-init) — all flags and examples
- [Doctor & Diagnostics](../cli-reference.md#obs-doctor) — all seven doctor layers
- [Cookbook → Vault↔Repo Mirroring](../cookbook.md#vaultrepo-mirroring) — copy-paste recipes
