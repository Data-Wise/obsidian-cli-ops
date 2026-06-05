# SPEC: Ship an `obs` man page (own the binary's docs)

**Status:** Implemented (feature/obs-manpage) — man page + help backfill + install.sh wiring + `.TH` version-sync guard done; Homebrew-formula man1 install wired on a separate tap branch (`homebrew-tap/feature/obs-manpage-install`)
**Created:** 2026-06-04
**Type:** docs / packaging
**Origin:** flow-cli is removing its `man/man1/obs.1` because it doesn't own `obs` (see `flow-cli/docs/specs/SPEC-obs-dispatcher-shadowing-2026-06-04.md` → "Man-Page Ownership"). obsidian-cli-ops owns `/opt/homebrew/bin/obs` and currently ships **zero** man pages — the page should live here.

---

## Why

flow-cli's broken `obs` dispatcher shadowed the real Homebrew binary; the fix deletes that dispatcher **and** flow-cli's `obs.1`. To avoid losing man-page coverage entirely, the canonical owner (this repo) should provide it.

## Scope

Author `obs.1` (troff) covering the **v3.2.1** command surface, built from the **dispatch table in `src/obs.zsh`**, not from `obs help` (the two disagree — see finding below).

### Command surface (v3.2.1)

| Group | Commands |
|---|---|
| Primary | `obs` (list vaults / last-vault stats), `obs stats [vault]`, `obs discover <path>` |
| Graph | `obs analyze <vault>`, `obs health <vault>` |
| AI | `obs ai status|setup|test`, `obs ai similar <note>`, `obs ai analyze <note>`, `obs ai duplicates <vault>`, `obs ai suggest-links <note>`, `obs ai gaps <vault>`, `obs ai summarize <vault>`, `obs ai refactor <vault>` |
| **AI — undocumented in `obs help --all`** | **`obs ai merge-suggest`, `obs ai tag-suggest`, `obs ai quality`** |
| Utilities | `obs help [--all]`, `obs version` |

### ⚠️ Finding: 3 AI subcommands ship without help text

`obs ai merge-suggest`, `obs ai tag-suggest`, `obs ai quality` are handled in `src/obs.zsh` (`case` block, ≈ lines 464–513) but absent from `obs_help()` (≈ lines 163–174). Tasks:

1. Cover all dispatch-table commands in the man page.
2. **Backfill** the three missing commands into `obs help --all` so help and man page agree.

## Suggested shape

- `obs.1` top-level with `ai` documented inline, **or** `obs.1` + `obs-ai.1` (SEE ALSO cross-links) if the ~13-command AI surface warrants its own page.
- Mirror flow-cli's troff conventions (model `flow-cli/man/man1/g.1`).
- Add a `.TH`-version anti-drift guard (model `flow-cli/tests/test-manpage-version-sync.zsh`) so the page tracks the package version on release.
- Wire man-page install into the Homebrew formula (`man1` dir).

## Out of scope

- The flow-cli dispatcher removal + binary-precedence guard (tracked in flow-cli).

## History

- **2026-06-04** — Captured during flow-cli's obs-dispatcher-shadowing planning, which audited this repo's v3.2.1 surface and found the 3 undocumented AI subcommands.
- **2026-06-05** — Implemented on `feature/obs-manpage`: authored `man/man1/obs.1` (single page, all v3.2.1 commands incl. the 3 AI ones missing from help; modeled on flow-cli `g.1`), backfilled `merge-suggest`/`tag-suggest`/`quality` into `obs_help()` so help and man page agree, and wired `install.sh` to symlink the page into the user man dir. Single-page chosen over `obs.1`+`obs-ai.1` for simpler version tracking.
- **2026-06-05** — Added `__tests__/man-page-version-sync.test.js` (jest): asserts the `obs.1` `.TH` product is `obsidian-cli-ops` and its version matches `package.json`, with parser self-tests proving it catches drift (verified: a simulated 3.2.1→9.9.9 edit fails the guard). Jest suite 59 → 65. Homebrew-formula `man1.install` wired on `homebrew-tap/feature/obs-manpage-install` (conditional, install-safe). Spec fully delivered.
