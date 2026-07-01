# SPEC: Harden Docs/Website Skills

**Date**: 2026-06-30
**Status**: Planned
**Origin**: docs-audit session exposed detection gaps in 4 skills; need for 2 new skills + 1 project config file
**Mode**: explore → refine (15 decisions across 14 grilling interactions)

---

## Detection Gaps

| What was caught | Who should've caught it | Root cause |
|---|---|---|
| `graph`→`flowchart`, `LR`→`TD` | `mermaid-linter` | Skill correct, not invoked |
| MD040 (no code lang), MD024 (dupe heading) | `preflight-check` | No project `.markdownlint.json`; default 80-char limit noisy |
| `.markdownlint.yaml` not auto-detected | Tooling config | `markdownlint-cli` needs `.json`, not `.yaml` |
| Emoji shortcode anchor mismatch | `site-lifecycle check` | Only documents `&`→`and`, not emoji stripping |
| Orphan nav pages + content dedup | `nav-sync` + `site-lifecycle audit` | No automated gating runs before build |

---

## Decisions (from grilling)

| Dimension | Decision |
|---|---|
| **Fail-fast strategy** | Run all when `--for pr/deploy`; fail-fast when interactive |
| **Check pipeline** | markdownlint → mermaid-lint → nav-sync check → mkdocs build --strict |
| **MD024 scope** | Same-file only |
| **Orphan quality** | `<100 word` flag, new orphans only |
| **Config format** | `.markdownlint.json` preferred (document in site-lifecycle gotchas) |
| **docs-linter vs mermaid-linter** | Delegate — docs-linter runs mermaid-linter as sub-step |
| **Health score** | Combined: markdown 0.4 + links 0.3 + mermaid 0.3; gate ≥ 80 |
| **preflight-check validator** | Generate hot-reload script in `.claude-plugin/skills/validation/` |
| **lychee exclusions** | In project `lychee.toml` |
| **Hook framework** | Document both pre-commit AND lefthook |
| **docs-ops orchestrator** | New standalone skill at `skills/docs-ops/SKILL.md` |
| **docs-ops approach** | Delegates to sub-skills, no logic duplication |

---

## Implementation Order

### P0 — site-lifecycle (edit)

**File**: `skills/site-management/SKILL.md`

| Change | Section | Detail |
|--------|---------|--------|
| Check pipeline | `check` | Add: `markdownlint -c .markdownlint.json` → `mermaid-linter` → `nav-sync check` → `mkdocs build --strict`. Smart fail-fast per context. |
| Emoji-anchor gotcha | Constraints | MkDocs Material strips emoji shortcodes from heading IDs. Cross-refs must use plaintext version (e.g., `#vault-management` not `#:file_folder:vault-management`). |
| Config format | Constraints | `markdownlint-cli` auto-discovers `.json` but NOT `.yaml`. Use `.json` format. |
| Mermaid ref | check | Delegate mermaid validation to `mermaid-linter` sub-step. |

### P0 — docs-linter (create)

**File**: `skills/docs-linter/SKILL.md`

Wraps markdownlint-cli + lychee; delegates mermaid to mermaid-linter. Embedded defaults (120-char, table rules disabled) + project `.markdownlint.json` override. Health score composite. Operations: `lint`, `check-links`, `syntax`, `health`, `fix`.

### P0 — lychee.toml (create)

**File**: project root `lychee.toml`

Exclusions: anchor-only (`^#`), localhost, mailto, git URLs.

### P1 — preflight-check (edit + generate)

**File**: `skills/check/SKILL.md`

Add docs-content operation for `--for pr/deploy` when docs changed. Generate hot-reload validator `.claude-plugin/skills/validation/docs-quality.md`.

### P1 — nav-sync (edit)

**File**: `skills/navigation/SKILL.md`

Sync mode: flag `<100` word orphans (new only); MD024 duplicate heading grep within changed files (same-file only).

### P1 — mermaid-linter (edit)

**File**: `skills/mermaid-linter/SKILL.md`

Add CI / Pre-commit Integration section with pre-commit + lefthook examples. Document docs-linter delegation.

### P2 — docs-ops (create)

**File**: `skills/docs-ops/SKILL.md`

Orchestrator: runs docs-linter → nav-sync → site-lifecycle → mkdocs build --strict → combined report. Inputs: `mode` (optimize|status|quick), `scope` (all|changed), `dry_run`.

---

## File Manifest

| Action | Path |
|--------|------|
| Edit | `.config/opencode/skills/site-management/SKILL.md` |
| Create | `.config/opencode/skills/docs-linter/SKILL.md` |
| Create | `lychee.toml` |
| Edit | `.config/opencode/skills/check/SKILL.md` |
| Create | `.claude-plugin/skills/validation/docs-quality.md` |
| Edit | `.config/opencode/skills/navigation/SKILL.md` |
| Edit | `.config/opencode/skills/mermaid-linter/SKILL.md` |
| Create | `.config/opencode/skills/docs-ops/SKILL.md` |

---

## Verification

- `markdownlint -c .markdownlint.json docs_mkdocs/` — 0 errors
- `lychee docs_mkdocs/` — 0 broken links (offline mode)
- `mkdocs build --strict` — clean
- docs-ops dry-run full pipeline — all stages pass
