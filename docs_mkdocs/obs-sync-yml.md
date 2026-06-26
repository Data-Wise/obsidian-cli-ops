# `.obs/sync.yml` — Project Mirror Map

Every project carries a `.obs/sync.yml` (docs-standards **ADR-001** settings contract). It is
**obs-owned** and created by [`obs link`](cli-reference.md). Vault-mirroring projects (research /
teaching) declare a `vault_root` + `pairs`; everything else uses `mirror: none` so the file exists but
is a no-op.

## Schema

Placeholder (non-vault project):

```yaml
schema: 1
mirror: none
```

Active mirror:

```yaml
schema: 1
mirror: mirror
vault_root: "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Research/20_projects/pmed_extensions"
pairs:
  - { vault: "teaching", repo: "teaching" }
  - { vault: "04_gauge/teaching", repo: "01-gauge-pmed/teaching" }
include: ["*.md"]
exclude: ["_archive"]
```

## Fields

| Field | Meaning |
|---|---|
| `schema` | Format version (currently `1`). |
| `mirror` | `none` (placeholder) or `mirror` (sync vault↔repo). |
| `vault_root` | iCloud Obsidian vault path the project mirrors (mirror mode). |
| `pairs` | `{ vault, repo }` directory pairings (numbering may differ). |
| `include` / `exclude` | Glob filters (default `*.md` / `_archive`). |

## Create / refresh

```bash
obs link                                  # mirror: none (non-vault project)
obs link --vault-root ~/vault/Research/x  # active mirror
obs link --force                          # overwrite an existing map
```

`obs link` is **idempotent** — an existing map is never clobbered unless `--force`. `atlas doctor` audits
that every project has one.
