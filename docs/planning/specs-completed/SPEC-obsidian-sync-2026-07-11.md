# Spec: `.flow/obsidian-sync.yml` — Validate, Create, and Hook into Sessions

## Objective

Standardize the `.flow/obsidian-sync.yml` config across all Obsidian-backed repos:
1. **Validate** existing configs via `obs doctor --layer flow`
2. **Create** missing configs via `obs flow init`
3. **Hook** validation into session entry points (`savant:restore`, `craft:recap`, MCP first use)

Scope: **only** `.flow/obsidian-sync.yml`. All other `.flow/` configs (`research-config.yml`, `voice-profiles/`, `teach-config.yml`) are out of bounds.

---

## Motivation

| Problem | Impact |
|---------|--------|
| No schema for `obsidian-sync.yml` | Typos and missing fields go unnoticed |
| No validator in `obs doctor` | Drift undetected until sync breaks |
| No creator command | Users must manually write YAML from memory |
| No session-time check | Stale configs persist across sessions |

Audit of 12 `.flow/` directories found 2 with `obsidian-sync.yml` — both consistent today. The value is locking this down before drift occurs.

---

## Part 1: JSON Schema (implemented)

**File:** `schema/obsidian-sync.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "flow/obsidian-sync.yml",
  "type": "object",
  "required": ["vault_root", "pairs"],
  "properties": {
    "vault_root": {
      "type": "string",
      "description": "Absolute path to Obsidian vault root (tilde-expanded)"
    },
    "pairs": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["vault", "repo"],
        "properties": {
          "vault": {
            "type": "string",
            "pattern": "^[^/].*",
            "description": "Relative path within vault (no leading /)"
          },
          "repo": {
            "type": "string",
            "pattern": "^[^/].*",
            "description": "Relative path within repo (no leading /)"
          }
        },
        "additionalProperties": false
      }
    },
    "include": {
      "type": "array",
      "items": { "type": "string" },
      "default": ["*.md"]
    },
    "exclude": {
      "type": "array",
      "items": { "type": "string" },
      "default": ["_archive"]
    }
  },
  "additionalProperties": false
}
```

**Status:** ✅ Created and validated against existing configs.

---

## Part 2: `obs doctor --layer flow` (implemented)

**Status:** ✅ Implemented with 6 checks.

| Check ID | Level | Description |
|----------|-------|-------------|
| `flow-sync-missing` | warn | Vault has no `.flow/obsidian-sync.yml` — suggests creation |
| `flow-sync-schema` | fail | Config fails JSON Schema validation |
| `flow-sync-stale` | warn | Config is >90 days old — may be outdated |
| `flow-sync-vault-root` | warn | `vault_root` path not found on disk |
| `flow-sync-pair-dup` | warn | Duplicate vault→repo mapping |
| `flow-sync-pair-identity` | fail | `vault` and `repo` are identical (no-op) |

**Usage:**
```bash
obs doctor --layer flow           # all vaults
obs doctor --layer flow --vault X # specific vault
```

---

## Part 3: `obs flow init` (proposed)

**Purpose:** Interactive wizard to create `.flow/obsidian-sync.yml`.

### Command

```bash
obs flow init [directory]
```

- `directory` defaults to `.` (current repo)
- Creates `.flow/` dir if missing
- Prompts for each field, suggests defaults from repo structure
- Validates against JSON Schema before writing
- Refuses to overwrite existing config (use `--force`)

### Interactive Flow

```
$ obs flow init

Initializing .flow/obsidian-sync.yml for: pmed-modern

vault_root [~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Research/20_projects/pmed_extensions]:

pairs (vault → repo):
  Add pair? [Y/n]: Y
    vault (relative to vault_root): teaching
    repo (relative to repo root): teaching
  Add another pair? [Y/n]: Y
    vault: 04_gauge_calibrated_pmed/teaching
    repo: 01-gauge-pmed/teaching
  Add another pair? [N]: N

include [*.md]:
exclude [_archive]:

✓ Created .flow/obsidian-sync.yml
✓ Validated against schema — 2 pairs, vault_root OK
```

### Non-Interactive Mode (for MCP/automation)

```bash
obs flow init --vault-root ~/path --pairs '[{"vault":"a","repo":"b"}]' --json
```

### Implementation

| File | Action |
|------|--------|
| `src/python/obs_cli.py` | Edit — add `flow` subcommand group + `init` subcommand |
| `src/python/core/flow_init.py` | **New** — `init_flow_config()` logic |
| `src/python/tests/test_flow_init.py` | **New** — tests for init wizard |

---

## Part 4: Session Hooks (proposed)

### Hook Map

| Context | Entry point | What runs | Behavior |
|---------|-------------|-----------|----------|
| Research | `savant:restore` | `obs doctor --layer flow --json` | Warn if missing or stale, suggest `obs flow init` |
| Dev-tools / R packages | `craft:recap` | `obs doctor --layer flow --json` | Warn if missing only (no staleness check) |
| MCP / Cowork | First `obs sync` call | `obs doctor --layer flow --json` | Warn only, no interactive prompts |

### savant:restore Hook

```
savant:restore
  └─ subprocess: obs doctor --layer flow --vault <id> --json
       ├─ flow-sync-missing → "⚠️ No .flow/obsidian-sync.yml. Run: obs flow init"
       ├─ flow-sync-stale → "⚠️ Config is {N} days old. Run: obs flow init to update"
       └─ all pass → (no output, continue restore)
```

**Pros:** User sees staleness immediately at session start.
**Cons:** Subprocess call adds ~100ms to restore.

### craft:recap Hook

```
craft:recap
  └─ subprocess: obs doctor --layer flow --json
       ├─ flow-sync-missing → "⚠️ No .flow/obsidian-sync.yml. Run: obs flow init"
       ├─ flow-sync-stale → "⚠️ Config is {N} days old. Run: obs flow init to update"
       └─ all pass or no vaults → (no output)
```

**Pros:** Catches stale configs at recap time — user sees it before pushing.
**Cons:** Subprocess call adds ~100ms to recap.

### MCP/Cowork (no change needed)

MCP `diagnose(layers="flow")` already works. The `flow-sync-missing` check warns with a suggestion to run `obs flow init`. No interactive prompts — user runs init manually in terminal.

---

## Part 5: Context-Aware Behavior

### When does `flow` layer run?

| Context | Auto-run? | Staleness check? | Why |
|---------|-----------|-------------------|-----|
| `obs doctor` (CLI, no args) | Yes | Yes | Full diagnostic |
| `obs doctor --layer flow` | Explicit | Yes | User-requested |
| `savant:restore` | Yes (via subprocess) | Yes | Research needs fresh configs |
| `craft:recap` | Yes (via subprocess) | Yes | Catches stale configs before push |
| MCP `diagnose()` | Yes (if no layers specified) | Yes | Catches drift in chat context |
| MCP `diagnose(layers="flow")` | Explicit | Yes | User-requested |

### Decision: Keep `flow` in default layer set

`flow` stays in the default `all_layers` dict in `run_checks()`. The `flow-sync-missing` check is `warn` level (not `fail`), so it's visible but not alarming. This means:

- `obs doctor` (no args) → includes flow checks
- MCP `diagnose()` → includes flow checks
- Both show "⚠️ No .flow/obsidian-sync.yml — Run: obs flow init"

The warning is helpful, not noisy. Users who don't care about `.flow/` can ignore it.

---

## Success Criteria

- [x] `schema/obsidian-sync.schema.json` exists and validates existing configs
- [x] `obs doctor --layer flow` runs 6 checks per vault
- [x] `obs flow init` creates valid `.flow/obsidian-sync.yml` interactively
- [x] `savant:restore` warns about missing/stale configs
- [x] `craft:recap` warns about missing configs (no staleness)
- [x] MCP `diagnose()` includes flow checks in default output
- [x] All existing pytest tests still pass
- [x] New tests for `obs flow init` pass

## Adversarial Fixes (2026-07-12, 52e5a46)

17 issues fixed across 3 files:

| # | Severity | Fix | File |
|---|----------|-----|------|
| 1 | Critical | `_infer_pairs` returns empty (prevents vault==repo pairs) | flow_init.py |
| 2 | Critical | Variable shadowing `key` → `pair_key` in `validate_config` | flow_init.py |
| 3 | Critical | `conn = None` before try (no NameError in finally block) | doctor.py |
| 4 | Critical | Misleading error message fixed | obs_cli.py |
| 5 | Security | Path traversal (`..`) blocked in pair validation | flow_init.py |
| 6 | Security | `pairs_json` structure validated (array of objects with vault/repo) | flow_init.py |
| 7 | Correctness | Pass check includes `warn` status | doctor.py |
| 8 | Correctness | Duplicate `DoctorResult` IDs get `:{idx}` suffix | doctor.py |
| 9 | Correctness | Comma parsing for include/exclude patterns | flow_init.py |
| 10 | Design | Atomic write (temp + rename) prevents corruption | flow_init.py |
| 11 | Design | Backup before `--force` overwrite (`.bak`) | flow_init.py |
| 12 | Design | `_SCHEMA_PATH` uses 4 parents (correct path) | flow_init.py |
| 13-17 | Tests | 13 new tests (path traversal, infer, corrupted YAML, etc.) | test_flow_init.py |

---

## Files Touched

| File | Action | Status |
|------|--------|--------|
| `schema/obsidian-sync.schema.json` | **New** | ✅ Done |
| `src/python/core/doctor.py` | Edit — `_check_obsidian_sync` | ✅ Done |
| `src/python/tests/test_doctor.py` | Edit — 10 test cases | ✅ Done |
| `src/python/obs_cli.py` | Edit — `--layer flow` choice + `flow init` subcommand | ✅ Done |
| `src/python/core/flow_init.py` | **New** — init wizard logic (36 unit tests) | ✅ Done |
| `src/python/tests/test_flow_init.py` | **New** — 36 tests (unit + adversarial) | ✅ Done |
| `src/python/tests/test_flow_dogfood.py` | **New** — 19 dogfood tests | ✅ Done |
| `src/python/tests/e2e/test_e2e_flow.py` | **New** — 16 e2e tests | ✅ Done |

## Implementation Order

| Phase | What | Effort | Status |
|-------|------|--------|--------|
| 1 | JSON Schema + doctor validation | S | ✅ Done |
| 2 | `obs flow init` command | M | ✅ Done |
| 3 | savant:restore hook | S | ✅ Done |
| 4 | craft:recap hook | S | ✅ Done |
| 5 | Verify + commit | S | ✅ Done |
| 6 | Adversarial review + fixes | M | ✅ Done |
