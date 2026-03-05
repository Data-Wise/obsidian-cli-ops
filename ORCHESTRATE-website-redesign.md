# Website Redesign Orchestration Plan

> **Branch:** `feature/website-redesign`
> **Base:** `dev`
> **Worktree:** `~/.git-worktrees/obsidian-cli-ops/feature-website-redesign`
> **Spec:** `docs/specs/SPEC-website-redesign-2026-03-05.md`
> **Brainstorm:** `BRAINSTORM-website-redesign-2026-03-05.md`

## Objective

Redesign the MkDocs documentation site: simplify navigation from 7 tabs to 4, rewrite stale pages, replace tutorials with an expanded cookbook, add a hero landing page, and remove internal dev artifacts from the public site.

## Phase Overview

| Phase | Task | Priority | Est. Time | Status |
|-------|------|----------|-----------|--------|
| 1 | Critical Fixes & Nav Cleanup | High | ~1 hour | Pending |
| 2 | 4-Tab Nav Restructure | High | ~2 hours | Pending |
| 3 | Hero Landing Page | Medium | ~1 hour | Pending |
| 4 | Cookbook Expansion (absorb tutorials) | Medium | ~2 hours | Pending |
| 5 | Visual Polish (Mermaid diagrams, page templates) | Low | ~1 hour | Pending |

---

## Phase 1: Critical Fixes & Nav Cleanup

**Goal:** Fix broken/stale content and remove internal artifacts from public nav.

### Tasks

1. **Fix `installation.md`** — Full rewrite
   - Remove references to TUI, `obs manage open`, `install.sh`
   - Add Homebrew method: `brew install data-wise/tap/obsidian-cli-ops`
   - Add manual install method: git clone → pip install → symlink → db init
   - Add post-install verification section
   - Add troubleshooting section (Python path, ZSH autoload)

2. **Fix `configuration.md`** — Full rewrite
   - Remove R-Dev references (`obs r-dev link`, `project_map.json`)
   - Add sections: Database location, AI provider config (env vars, Ollama, priority), Shell integration, Advanced (custom Python path, verbose mode)

3. **Remove `v3.0.md` from nav**
   - Delete from `mkdocs.yml` nav only (keep file)
   - Update `index.md` line 90: change v3.0 button to point to refcard or remove

4. **Remove Archive + Planning from nav**
   - Delete Archive section from `mkdocs.yml`
   - Delete Planning section from `mkdocs.yml`
   - Files remain in `docs_mkdocs/` for historical reference

5. **Validate:** `mkdocs build` clean (no warnings)

### Files Modified
- `docs_mkdocs/installation.md` (rewrite)
- `docs_mkdocs/configuration.md` (rewrite)
- `docs_mkdocs/index.md` (remove v3.0 button)
- `mkdocs.yml` (remove Archive, Planning, v3.0 from nav)

### Commit
```
docs: fix stale installation/configuration pages, clean up nav
```

---

## Phase 2: 4-Tab Nav Restructure

**Goal:** Restructure navigation from 7 tabs to 4 clean tabs.

### Target Navigation

```yaml
nav:
  - Home: index.md
  - Getting Started:
      - Installation: installation.md
      - Configuration: configuration.md
      - Usage: usage.md
  - Reference:
      - Quick Reference: refcard.md
      - Cookbook: cookbook.md
      - CLI Reference: cli-reference.md
      - AI Setup Guide: ai-setup.md
      - Changelog: changelog.md
  - Developer:
      - Architecture: developer/architecture.md
      - Testing:
          - Overview: developer/testing/overview.md
          - Core Tests: developer/testing/core-tests.md
          - Sandbox: developer/testing/sandbox.md
      - Migration Guide: migration.md
```

### Tasks

1. **Promote CLI Reference**
   - Copy `docs/user/cli-reference.md` → `docs_mkdocs/cli-reference.md`
   - Update any internal links/references

2. **Create `changelog.md`**
   - Read `docs_mkdocs/releases/v3.0.0.md`, `v2.2.0.md`, `v1.1.0.md`
   - Consolidate into single reverse-chronological changelog
   - Remove individual release pages from nav

3. **Promote Architecture page**
   - Copy `docs/developer/architecture.md` → `docs_mkdocs/developer/architecture.md`
   - Verify links resolve correctly

4. **Rewrite `mkdocs.yml` nav** to 4-tab structure

5. **Update developer/testing pages**
   - Update test count from 186 → 202 in overview.md and core-tests.md
   - Verify content accuracy for v3.0

6. **Validate:** `mkdocs build` clean, all internal links resolve

### Files Created
- `docs_mkdocs/cli-reference.md`
- `docs_mkdocs/changelog.md`
- `docs_mkdocs/developer/architecture.md`

### Files Modified
- `mkdocs.yml` (new 4-tab nav)
- `docs_mkdocs/developer/testing/overview.md` (test count)
- `docs_mkdocs/developer/testing/core-tests.md` (test count)

### Commit
```
docs: restructure site to 4-tab navigation
```

---

## Phase 3: Hero Landing Page

**Goal:** Redesign index.md with a hero section, feature cards, and Mermaid architecture diagram.

### Target Structure

```
1. Hero tagline + CTA buttons (Install Now, Quick Reference)
2. Feature cards (3 columns): Vault Discovery, AI Insights, Reorganization
3. Quick Start (3 steps): brew install → discover → health
4. Architecture diagram (Mermaid: ZSH → Python → SQLite)
5. Footer: GitHub link, license
```

### Tasks

1. **Rewrite `index.md`**
   - Hero: `obs — Your Vault's Command Line` + tagline
   - Feature highlights using Material grid cards (if supported) or admonition cards
   - 3-step Quick Start with code block
   - Mermaid three-layer architecture diagram
   - Remove: "Project Status" phase history, "Documentation" links section, "Community" section (repo link in header already)

2. **Validate:** Mermaid renders correctly, CTA buttons work

### Files Modified
- `docs_mkdocs/index.md` (full rewrite ~80 lines)

### Commit
```
docs: redesign landing page with hero section and architecture diagram
```

---

## Phase 4: Cookbook Expansion (Absorb Tutorials)

**Goal:** Merge tutorial content into an expanded cookbook; remove Tutorials from nav.

### Current Tutorials
- `tutorials/getting-started.md` (149 lines) — install, discover, scan, stats
- `tutorials/graph-analysis.md` (187 lines) — analyze, metrics, hubs, orphans
- `tutorials/ai-features.md` (284 lines) — AI setup, similar, duplicates, refactor

### Target Cookbook Sections

1. **Getting Started** (from tutorials/getting-started.md)
   - First-time setup recipe
   - Discover and scan vaults recipe
2. **Vault Health & Cleanup** (existing + expanded)
   - Health check recipe
   - Find and organize orphans
   - Archive stale folders
   - Consolidate small folders
3. **Knowledge Graph Analysis** (from tutorials/graph-analysis.md)
   - Full vault analysis recipe
   - Find hub notes
   - Export graph data
4. **AI-Powered Discovery** (existing + tutorials/ai-features.md)
   - AI provider setup recipe
   - Find related notes
   - Detect duplicates
   - Knowledge gaps analysis
   - Vault refactor recipe
5. **Multi-Vault Management** (existing)
6. **Scripting & Automation** (existing)

### Tasks

1. **Expand `cookbook.md`** — Merge tutorial content into recipe format
   - Each recipe: title, when to use, commands, expected output
   - Maintain task-based tone (not linear tutorial)
2. **Remove Tutorials from nav** — Keep files, just hide from nav
3. **Update cross-references** — Any pages linking to tutorials point to cookbook

### Files Modified
- `docs_mkdocs/cookbook.md` (expand from ~180 to ~400 lines)
- `mkdocs.yml` (remove Tutorials from nav)

### Commit
```
docs: expand cookbook with tutorial content, remove tutorials from nav
```

---

## Phase 5: Visual Polish

**Goal:** Add Mermaid diagrams to key pages, apply consistent page template.

### Tasks

1. **Add "Next Steps" footer to all content pages**
   - installation.md → configuration, usage
   - configuration.md → ai-setup, usage
   - usage.md → refcard, cookbook
   - cookbook.md → cli-reference, ai-setup
   - cli-reference.md → cookbook, refcard
   - ai-setup.md → cookbook (AI section)
   - changelog.md → (none needed)

2. **Add Mermaid diagrams**
   - `ai-setup.md`: Provider routing diagram (Gemini > Anthropic > Ollama > CLI)
   - `developer/architecture.md`: Data flow diagram (Scan → SQLite → Graph → AI)

3. **Verify page consistency**
   - Every page has: title, one-line description, content, next steps
   - Code blocks have language identifiers

4. **Final validation**
   - `mkdocs build` clean
   - `mkdocs build --strict` clean
   - All internal links resolve
   - All Mermaid diagrams render

### Files Modified
- Multiple content pages (add Next Steps footers)
- `docs_mkdocs/ai-setup.md` (add Mermaid diagram)
- `docs_mkdocs/developer/architecture.md` (add Mermaid diagram)

### Commit
```
docs: add consistent page templates and Mermaid diagrams
```

---

## Acceptance Criteria

- [ ] Navigation reduced to 4 tabs: Home | Getting Started | Reference | Developer
- [ ] All v2.x references removed from active pages (TUI, R-Dev, `obs manage`)
- [ ] installation.md rewritten with Homebrew + manual install
- [ ] configuration.md rewritten with AI + shell + advanced config
- [ ] v3.0.md, Archive, Planning removed from navigation
- [ ] Tutorials merged into expanded cookbook
- [ ] Landing page has hero section + Mermaid architecture diagram
- [ ] CLI reference promoted to site
- [ ] Releases consolidated into single changelog
- [ ] `mkdocs build --strict` passes clean
- [ ] All pages have consistent structure (title, description, content, next steps)
- [ ] 202 test count reflected across all pages

## How to Start

```bash
cd ~/.git-worktrees/obsidian-cli-ops/feature-website-redesign
claude
# Start with Phase 1: Critical Fixes & Nav Cleanup
```

## Notes

- Files removed from nav are NOT deleted — they stay in repo
- `docs_mkdocs/` is the MkDocs source dir (not `docs/`)
- `docs/` contains internal documentation (specs, developer guides)
- Each phase should end with `mkdocs build` validation
- Deploy after each phase if desired: `mkdocs gh-deploy`
