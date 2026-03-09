# BRAINSTORM: Website Redesign & Stale Docs Audit

**Mode:** Feature | **Depth:** Deep (8 questions) | **Date:** 2026-03-05
**Site:** https://data-wise.github.io/obsidian-cli-ops/

---

## Current State Analysis

### Staleness Audit

| File | Last Modified | Status | Issue |
|------|--------------|--------|-------|
| `configuration.md` | 2025-12-09 | **CRITICAL** | References R-Dev (`obs r-dev link`) — removed in v3.0 |
| `installation.md` | 2025-12-15 | **CRITICAL** | References TUI, `obs manage open`, `install.sh` — all removed |
| `archive/r-dev.md` | 2025-12-12 | OK | Historical, but should be hidden |
| `developer/testing/*.md` | 2025-12-17 | STALE | Test count wrong (186 vs 202), references may be outdated |
| `planning/phases/*.md` | 2025-12-17 | OK | Internal artifacts — removing from nav |
| `tutorials/getting-started.md` | 2026-03-02 | OK | Recently updated |
| `tutorials/graph-analysis.md` | 2026-03-02 | OK | Recently updated |
| `v3.0.md` | 2026-03-05 | **DELETE** | README copy causing strict-mode warnings |
| `migration.md` | 2026-03-04 | OK | Recently updated |

### Critical Content Bugs

1. **installation.md:49** — `obs manage open ~/Documents` — command doesn't exist
2. **installation.md:60** — "Press `d` in the TUI" — TUI was removed in v3.0
3. **configuration.md:17** — `obs r-dev link` — R-Dev integration removed in v3.0
4. **configuration.md:3** — `~/.config/obs/config` — config file format may be outdated
5. **index.md:90** — Links to `v3.0.md` which is being deleted
6. **index.md:113-140** — "Project Status" section with internal phase history

### Navigation Issues (Current 7 Tabs)

```
Home | Getting Started | Features | Tutorials | Archive | Developer | Planning | Releases
                                                 ↑          ↑           ↑
                                              Remove      Keep       Remove
```

---

## Quick Wins (< 30 min each)

1. **Delete `v3.0.md`** — Remove from nav, update index.md link to point elsewhere
2. **Remove Archive + Planning from nav** — Files stay, just hidden from public
3. **Fix installation.md critical bugs** — Remove TUI/`obs manage` references
4. **Fix configuration.md** — Remove R-Dev, update to v3.0 config format
5. **Update index.md "v3.0 Features" button** — Point to features section or refcard

---

## Medium Effort (1-2 hours each)

### 1. Navigation Redesign: 7 Tabs → 4 Tabs

**Proposed structure:**

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
      - CLI Reference: cli-reference.md  # NEW — promote from docs/user/
      - AI Setup Guide: ai-setup.md
      - Changelog: changelog.md          # NEW — consolidated
  - Developer:
      - Architecture: developer/architecture.md  # NEW — promote from docs/
      - Testing: developer/testing/overview.md
      - Migration Guide: migration.md
```

**What changes:**
- "Features" tab absorbed into Home (hero section) + Reference
- "Tutorials" tab replaced by Cookbook in Reference
- "Archive" removed from nav (files retained)
- "Planning" removed from nav (files retained)
- "Releases" becomes single Changelog in Reference

### 2. Hero Landing Page Redesign

**Current index.md:** Dense feature list, raw code blocks, internal phase history

**Proposed index.md:**

```markdown
# obs — Your Vault's Command Line

> 15 commands. 5 AI providers. One tool to understand your Obsidian vault.

[Install Now](installation.md){ .md-button .md-button--primary }
[Quick Reference](refcard.md){ .md-button }

---

## What can obs do?

<feature cards with icons — 3 columns>
- Vault Discovery & Graph Analysis
- AI-Powered Insights (similar, duplicates, gaps)
- Reorganization Planning (refactor command)

---

## See it in action

<terminal GIF showing: obs → obs analyze → obs ai refactor>

---

## Quick Start (3 steps)

​```bash
brew install data-wise/tap/obsidian-cli-ops   # Install
obs discover ~/Documents --scan               # Find vaults
obs health MyVault                            # Check health
​```

---

## Architecture at a Glance

<Mermaid diagram: ZSH → Python Core → SQLite>
```

**Key changes:**
- Remove "Project Status" phase history (internal)
- Remove "Documentation" links section (nav handles this)
- Remove "Community" section (repo link in header)
- Add hero tagline + CTA buttons
- Add terminal GIF placeholder
- Add Mermaid architecture diagram
- Feature cards instead of bullet lists

### 3. Full Rewrite: installation.md

**Current problems:**
- References `install.sh` (may not exist)
- References TUI and `obs manage open`
- Missing Homebrew install method
- Missing Python path note

**Proposed structure:**
```markdown
# Installation

## Method 1: Homebrew (Recommended)
brew install data-wise/tap/obsidian-cli-ops

## Method 2: Manual Install
git clone → pip install → symlink → db init

## Post-Install
obs                          # Verify installation
obs discover ~/Documents     # Find vaults

## Troubleshooting
- Python path issues
- ZSH autoload issues
```

### 4. Full Rewrite: configuration.md

**Current problems:**
- References R-Dev integration (removed)
- Only 23 lines — barely a page
- Doesn't mention AI configuration

**Proposed structure:**
```markdown
# Configuration

## Database Location
~/.config/obs/vault_db.sqlite

## AI Provider Configuration
### API Keys (env vars)
### Ollama Setup
### Provider Priority

## Shell Integration
### ZSH Setup
### Shell Aliases

## Advanced
### Custom Python Path
### Verbose Mode
```

### 5. Tutorials → Cookbook Transition

**Current:** 3 linear tutorials (getting-started, graph-analysis, ai-features)
**Proposed:** Merge tutorial content into expanded cookbook

**New cookbook sections:**
- Getting Started (from tutorials/getting-started.md)
- Vault Cleanup (existing cookbook content)
- Knowledge Graph Analysis (from tutorials/graph-analysis.md)
- AI-Powered Discovery (existing + tutorials/ai-features.md)
- Multi-Vault Management (existing)
- Scripting & Automation (existing)
- Advanced Workflows (new)

**Action:** Merge tutorial content into cookbook, remove tutorials section

### 6. CLI Reference Page (Promote)

Currently `docs/user/cli-reference.md` (465 lines) exists but isn't in the MkDocs nav.

**Action:** Copy to `docs_mkdocs/cli-reference.md` and add to Reference tab.

### 7. Changelog Page (Consolidate Releases)

**Current:** 3 separate release pages (v1.1.0, v2.2.0, v3.0.0)
**Proposed:** Single `changelog.md` with all versions in reverse-chronological order

---

## Long-Term (Future Sessions)

### 1. Terminal GIF Generation
- Record actual `obs` command output using `asciinema` or `terminalizer`
- Convert to GIF for homepage and tutorial pages
- Show: vault listing, health check, AI refactor output

### 2. Mermaid Architecture Diagrams
- Three-layer architecture diagram on homepage
- AI provider routing diagram on AI setup page
- Data flow diagram on developer/architecture page

### 3. Consistent Page Template
Every page should follow:
```markdown
# Page Title
> One-line description

[Content sections]

---
## Next Steps
- [Related page 1](link)
- [Related page 2](link)
```

### 4. Search Enhancement
- Add `search` plugin configuration for better results
- Consider adding tags/categories for filtering

---

## Recommended Implementation Path

### Increment 1: Critical Fixes & Nav Cleanup (1-2 hours)
1. Delete `v3.0.md` from nav
2. Remove Archive + Planning from nav
3. Fix installation.md (remove TUI/manage refs)
4. Fix configuration.md (remove R-Dev refs)
5. Fix index.md (remove v3.0 button, clean up)

### Increment 2: 4-Tab Navigation + Content Moves (2-3 hours)
1. Restructure mkdocs.yml to 4 tabs
2. Promote cli-reference.md to docs_mkdocs
3. Create consolidated changelog.md
4. Remove old releases pages from nav

### Increment 3: Hero Landing Page (1-2 hours)
1. Rewrite index.md with hero section
2. Add Mermaid architecture diagram
3. Add 3-step quick start
4. Remove internal phase history

### Increment 4: Content Rewrites (2-3 hours)
1. Full rewrite of installation.md (Homebrew + manual)
2. Full rewrite of configuration.md (AI + shell + advanced)
3. Merge tutorials into expanded cookbook
4. Delete tutorials section

### Increment 5: Visual Polish (Future)
1. Generate terminal GIFs
2. Add Mermaid diagrams to key pages
3. Apply consistent page template
4. Deploy and validate

---

## Files Affected

| Action | File | Change |
|--------|------|--------|
| DELETE from nav | `v3.0.md` | Remove from mkdocs.yml, keep file |
| DELETE from nav | `archive/*` | Remove section from nav |
| DELETE from nav | `planning/*` | Remove section from nav |
| DELETE from nav | `releases/v1.1.0.md` | Merged into changelog |
| DELETE from nav | `releases/v2.2.0.md` | Merged into changelog |
| DELETE from nav | `releases/v3.0.0.md` | Merged into changelog |
| DELETE from nav | `tutorials/*` | Content merged into cookbook |
| REWRITE | `index.md` | Hero section, no phase history |
| REWRITE | `installation.md` | Homebrew + manual, no TUI |
| REWRITE | `configuration.md` | AI + shell + advanced |
| REWRITE | `cookbook.md` | Absorb tutorial content |
| CREATE | `cli-reference.md` | Copy from docs/user/ |
| CREATE | `changelog.md` | Consolidated from 3 release pages |
| MODIFY | `mkdocs.yml` | 4-tab nav structure |

**Total: ~14 files, 5 increments**

---

**Completed in deep mode (8 questions gathered)**
**Saved to:** `BRAINSTORM-website-redesign-2026-03-05.md`
