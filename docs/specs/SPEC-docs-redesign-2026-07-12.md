# Spec: Documentation Website Redesign & Brand System

## Objective

Give the published docs site (`docs_mkdocs/` → GitHub Pages) a deliberate, ownable
visual identity and close the content gaps the 2026-07-12 audit surfaced:

1. **Replace** Material for MkDocs' default indigo/purple palette ("AI slop") with a
   fixed ink / paper / teal system.
2. **Add** a project logo (mark + wordmark + favicon) and wire it into the site header.
3. **Document** the design system so future doc work stays consistent.
4. **Preserve** the interactive audit + before/after proposal as a self-contained artifact.

Scope: **only** the documentation site and brand assets. No product/CLI behaviour changes.

---

## Motivation

| Problem | Impact |
|---------|--------|
| Material default palette is indigo + purple | Generic, indistinguishable from every other MkDocs site ("AI slop") |
| No logo / favicon | Site reads as a template; weak project identity |
| Reported 404 | Stale bookmark to the removed `obs-sync-yml.md` (expected after ADR-001) |
| 11 orphan pages | `archive/*` (6) + `planning/phases/*` (5) not in nav |
| `reference/index.md` stale date | Doc drift |
| Missing tutorials | `flow-init`, `doctor`, `config`, `search` had no getting-started page |

The audit also confirmed the *good* news: `mkdocs build --strict` was already clean and
the 404 was a known removal, not a broken deploy.

---

## Part 1: Palette & Typography (implemented)

**File:** `docs_mkdocs/stylesheets/redesign.css` (loaded after the theme via `extra_css`).

| Token | Value | Use |
|-------|-------|-----|
| ink | `#15161a` | primary (header / nav rail), text |
| paper | `#f7f6f2` | default surface, primary text-on-ink |
| teal | `#0d9488` | single accent — links, focus, active node |

- Typography: **Space Grotesk** (headings/body) + **JetBrains Mono** (code), loaded via
  CSS `@import` with system fallbacks. No Inter.
- Antislop rules enforced: no purple gradient washes, no uniform rounded corners
  (admonitions/tabs kept at 4px), deliberate letter-spacing on headings.

---

## Part 2: Logo & Favicon (implemented)

**Philosophy:** `docs/proposals/brand/PHILOSOPHY.md` — *"Node Cartography"*: a faceted
obsidian diamond as the graph hub, ringed by plain note nodes; teal marks the active hub.

**Assets** (`docs/proposals/brand/`, mirrored into `docs_mkdocs/proposals/brand/` for
serving): `logo-mark-{ink,paper,transparent}.png`, `logo-lockup-{ink,paper}.png`,
`logo-favicon{,-transparent}.png`, `logo-sheet.pdf` / `logo-sheet.png`.

**Wiring** (`mkdocs.yml` `theme:`):
- `logo: assets/logo.png` — the **transparent** mark (ink header would hide a paper-bg mark)
- `favicon: assets/favicon.png` — transparent mark
- both copied to `docs_mkdocs/assets/`

Generator: `logo/gen_logo.py` (matplotlib) — regenerate marks by editing palette constants.

---

## Part 3: Content gap closure (implemented, 2026-07-12)

- 4 new tutorials: `tutorials/{flow-init,doctor,config,search}.md`
- 4 cookbook recipes in `cookbook.md` (Vault↔Repo Mirroring, Diagnose & Heal, Manage
  Configuration, Initialize/Rebuild DB)
- `reference/index.md` date + `flow-init` row fixed; `index.md` Diagnostics + Vault↔Repo tips
- `archive/*` surfaced via a new Archive nav section; `planning/phases/*` intentionally kept
  out of nav (internal)
- `design-standards.md` added (contributor reference for the three convention-driven surfaces)

---

## Part 4: Reproducing the proposal artifact

The interactive audit + before/after mockup lives at
`docs_mkdocs/proposals/docs-redesign.html` (linked from `design-standards.md` §6). It is a
**single self-contained file** — JS + CSS inlined, the logo mark embedded as a base64 data
URI, **zero external references**, so it opens from `file://` or when served.

To rebuild it for a future redesign pass:

1. Scaffold a React 18 + TS + Vite + Tailwind 3.4 + shadcn/ui app (the working project was
   `obs-docs-redesign/` in the session temp dir; persist the source under
   `docs/proposals/redesign-src/` if you want it version-controlled).
2. Put the mark you want inline in `src/assets/brand-mark.png` and `import` it in `App.tsx`
   (Parcel turns the import into an importmap URL).
3. Build: `npx parcel build index.html --dist-dir dist --no-cache`
4. Inline: run `inline.py` — it reads `dist/*.js`, `dist/*.css`, `dist/brand-mark*.png`,
   rewrites the importmap PNG URL to a `data:image/png;base64,…` URI, and writes a single
   `bundle.html` with JS+CSS inlined. (Do **not** commit `node_modules`/`.parcel-cache`.)
5. Copy `bundle.html` → `docs_mkdocs/proposals/docs-redesign.html` and link it from a doc.

The same inline step is what makes any future interactive proposal shareable as one file.

---

## Status

**Shipped 2026-07-12** (commits `0de8a05` palette+logo, `924ba77` proposal link; deployed to
GitHub Pages). `mkdocs build --strict` clean; `test_doc_counts.py` 7 passed (63 commands
unchanged — doc-only change).
