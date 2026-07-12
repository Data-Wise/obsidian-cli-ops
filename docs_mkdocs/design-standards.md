# Design Standards

Contributor-facing conventions for the three first-class, convention-driven surfaces in `obs`:

1. **Local config file contracts** — vault-rooted YAML maps that another command reads.
2. **Their related commands** — the CLI verbs that create, validate, and consume a contract.
3. **Obsidian dashboards** — deterministic, marker-bounded markdown rendered *into* a vault.

This is **not** a user tutorial. End users should read
[CLI Reference](cli-reference.md) and [The Research Board tutorial](tutorials/research-board.md).
The [Architecture → Config File Contracts](developer/architecture.md#config-file-contracts)
section is the code-level companion to §2 below.

---

## 1. Overview

A "design standard" here means: when you add a new local config contract, a config/sync
command, or a vault dashboard, it must follow the patterns below. They exist so that every
surface is **validated**, **atomic**, **idempotent**, and **scriptable** (non-interactive
path + `--dry-run` where it writes). Deviations need an explicit ADR.

The canonical example of all three working together is `.flow/obsidian-sync.yml`:

- the **contract** (§2) is a vault-rooted mirror map,
- **`obs flow init`** creates it and **`obs doctor --layer flow`** validates it (§3),
- and the research/action **dashboards** (§4) are the same shape of vault-writing surface.

---

## 2. Local Config File Contracts

A *config contract* is a small YAML file `obs` reads to drive a sync or mirror operation.
There is exactly **one** today: `.flow/obsidian-sync.yml`.

### Location & ownership

| Property | Value |
|----------|-------|
| Path | `<vault_dir>/.flow/obsidian-sync.yml` — **vault-rooted**, one per vault directory |
| Owner | `obs flow init` (v4.3.0) |
| Validator | `obs doctor --layer flow` (JSON Schema) |
| Schema | `schema/obsidian-sync.schema.json` |

> A config contract is **vault-rooted**, not project-rooted. Do not put repo/settings
> state in a vault file, and do not invent a second `.obs/*` or `.flow/*` map without
> extending this standard.

### Must

- Validate the file against a JSON Schema (`schema/obsidian-sync.schema.json`) before use.
- Use a **bare** `vault_root` + `pairs` shape — no `schema:` / `mirror:` envelope.
- Reject pair paths that start with `/` **or** contain `..` (path-traversal guard).
- Reject a `vault`/`repo` pair that is identical (no-op mirror).
- Refuse to overwrite an existing file unless `--force` is passed.
- Write atomically via `os.replace(tmp, target)` (never a bare `open("w")`).
- On `--force`, back up the prior file to `<file>.bak` before replacing.

### Must not

- Emit a `vault == repo` identity pair.
- Allow duplicate `vault→repo` mappings.
- Read or write outside the vault tree (no `..`, no absolute paths in pairs).
- Trust unvalidated YAML — a parse failure must surface as a clear error, not a crash.

### Worked example

A minimal valid `.flow/obsidian-sync.yml`:

```yaml
vault_root: "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Research"
pairs:
  - { vault: "teaching", repo: "teaching" }
  - { vault: "04_gauge/teaching", repo: "01-gauge-pmed/teaching" }
include: ["*.md"]
exclude: ["_archive"]
```

Produced non-interactively by:

```bash
obs flow init ~/vaults/MyVault \
  --vault-root "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Research" \
  --pairs '[{"vault":"teaching","repo":"teaching"}]' --json
```

---

## 3. Related Commands

Every contract ships **two** commands: one to *create* it, one to *validate* it. This pair
is the standard — do not add a contract without both.

| Command | Purpose | Key flags | Convention it enforces |
|---------|---------|-----------|------------------------|
| `obs flow init [directory]` | Create `.flow/obsidian-sync.yml` | `--vault-root`, `--pairs` (JSON), `--force`, `--json` | Interactive **and** non-interactive mode; refuses overwrite without `--force`; atomic write + `.bak` backup |
| `obs doctor --layer flow [--vault X]` | Validate every vault's config | `--layer flow`, `--json` | 6 checks (below); `warn`/`fail` levels; part of default `all_layers` |

### `obs doctor --layer flow` checks

| Check ID | Level | Triggers when |
|----------|-------|---------------|
| `flow-sync-missing` | warn | Vault has no `.flow/obsidian-sync.yml` |
| `flow-sync-schema` | fail | File fails JSON Schema validation |
| `flow-sync-stale` | warn | Config is > 90 days old |
| `flow-sync-vault-root` | warn | `vault_root` path not found on disk |
| `flow-sync-pair-dup` | warn | Duplicate `vault→repo` mapping |
| `flow-sync-pair-identity` | fail | `vault` and `repo` are identical |

**Why two commands:** creation is interactive-for-humans but scriptable-for-CI
(`--pairs` JSON + `--json`); validation is what hooks into `savant:restore`,
`craft:recap`, and MCP `diagnose()` so drift is caught at session start, not at sync time.

---

## 4. Obsidian Dashboards

A *dashboard* is a deterministic markdown view `obs` renders **into** a vault file. There
are two, both following the same marker-bounded, atomic, zero-diff-on-unchanged standard.

| Command | Output file | Source |
|---------|-------------|--------|
| `obs research board [--out F] [--kind K]` | `_RESEARCH-BOARD.md` | atlas `project list --json` |
| `obs board refresh [--vault V] [--all]` | `_ACTION-BOARD.md` | atlas + vault DB (ghost drift) + `.STATUS` |

### Must

- Wrap all generated content in `<!-- obs:board:start -->` … `<!-- obs:board:end -->`
  markers; only the region between markers is replaced.
- Write atomically via `os.replace` (marker-bounded region only).
- Be **deterministic**: re-running on unchanged source state produces **zero diff**.
- Support `--dry-run`: show what would change and **exit non-zero when the file would
  change** — this is the drift guard for cron/launchd.
- Support `--out <file>` (write) vs. stdout (print) — stdout is the default.

### Must not

- Touch hand-written prose outside the markers.
- Mutate the vault database or notes other than the single target file.
- Embed non-deterministic content (timestamps in the body, sorted-by-time tables) that
  would break the zero-diff guarantee.

### Worked example

The marker block in the target file:

```markdown
<!-- obs:board:start -->
| Manuscript | Venue | Status | Progress |
|------------|-------|--------|----------|
| Bridge calibration | JASA  | 🟢    | ████████░░ |
<!-- obs:board:end -->
```

Schedule a drift guard (exits non-zero if the board would change):

```bash
# crontab — nightly staleness check
obs research board --out ~/vault/00_meta/_RESEARCH-BOARD.md --dry-run \
  || echo "RESEARCH-BOARD drift detected"
```

---

## 5. Checklist for new surfaces

Copy this into a PR description. A new contract / command / dashboard is **not** done until
every box is checked:

- [ ] **Contract** validates against a JSON Schema in `schema/` (not ad-hoc dict access).
- [ ] **Create command** has both interactive and non-interactive (`--json` / `--pairs`)
      modes; refuses overwrite without `--force`; writes via `os.replace`; backs up on
      `--force`.
- [ ] **Validate command** exists (`obs doctor --layer flow` style) with `warn`/`fail`
      levels and is wired into the default `all_layers` set.
- [ ] **Dashboard** (if any) is marker-bounded, atomic, deterministic (zero diff on
      unchanged state), and supports `--dry-run` with non-zero exit on drift.
- [ ] **Path safety**: no `..` or leading `/` in any user-supplied path; no writes outside
      the intended tree.
- [ ] **Docs**: this page updated; [CLI Reference](cli-reference.md) lists the command;
      [Architecture → Config File Contracts](developer/architecture.md#config-file-contracts)
      lists the contract; `mkdocs.yml` nav includes any new page.
- [ ] **Tests**: unit + (where it writes files) dogfood/e2e covering invalid input,
      overwrite refusal, and atomic write.
- [ ] **Verification**: `mkdocs build --strict` and
       `python3 -m pytest src/python/tests/test_doc_counts.py` pass.

---

## 6. Website & Brand

The published documentation site and the project's visual identity follow the same
discipline as the code surfaces above: validated, deliberate, and free of generic
"AI slop" (no purple gradient washes, no uniform rounded corners, no default Inter).

- **Palette** — ink `#15161a`, paper `#f7f6f2`, teal `#0d9488` (single accent that marks
  the active node). Implemented in `docs_mkdocs/stylesheets/redesign.css` and wired into
  `mkdocs.yml` via `theme.logo` / `theme.favicon` / `extra_css`.
- **Logo** — a faceted obsidian diamond as the graph hub ringed by note nodes, documented
  in `docs/proposals/brand/PHILOSOPHY.md`; the full mark/lockup/favicon set and a one-page
  spec sheet are in [brand/logo-sheet.pdf](proposals/brand/logo-sheet.pdf).
- **Redesign proposal** — the interactive audit + before/after mockup that motivated the
  palette is preserved as a self-contained artifact:
  [proposals/docs-redesign.html](proposals/docs-redesign.html) (opens standalone; the
  mark is embedded, no external assets).

> The artifact and brand sheet live under `docs/proposals/` (source of truth) and are
> mirrored into `docs_mkdocs/proposals/` so they are served by the site.
