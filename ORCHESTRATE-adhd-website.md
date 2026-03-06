# ADHD-Friendly Website Enhancement

> **Branch:** `feature/adhd-website`
> **Base:** `dev`
> **Worktree:** `~/.git-worktrees/obsidian-cli-ops/feature-adhd-website`

## Objective

Improve the MkDocs Material documentation site's ADHD-friendliness score from 45/100 (Grade F) to 85+ (Grade B). Three phases of enhancements targeting visual hierarchy, time estimates, workflow diagrams, mobile responsiveness, and content density.

## Current Score Breakdown

| Category | Weight | Score | Gap |
|----------|--------|-------|-----|
| Visual Hierarchy | 25% | 43 | TL;DR boxes: 0/14 pages |
| Time Estimates | 20% | 50 | Guides: 0/5 have estimates |
| Workflow Diagrams | 20% | 35 | Only 3 Mermaid diagrams |
| Mobile Responsive | 15% | 20 | No custom CSS |
| Content Density | 20% | 72 | 43% pages have callouts |
| **Overall** | | **45** | **Target: 85+** |

## Phase Overview

| Phase | Task | Priority | Impact | Status |
|-------|------|----------|--------|--------|
| 1 | Quick Wins: TL;DR boxes, time estimates, callouts | High | +25 pts | Pending |
| 2 | Structure: Mermaid diagrams, custom CSS, emoji headings | Medium | +15 pts | Pending |
| 3 | Polish: ADHD Quick Start page, visual workflows page | Low | +10 pts | Pending |

---

## Phase 1: Quick Wins (+25 points)

### 1.1 Add TL;DR Boxes (8 pages)

Add `> **TL;DR**` blockquote boxes after H1 on these pages:

| Page | What/Why/How summary |
|------|---------------------|
| `usage.md` | 15 commands, vault management, `obs` |
| `cookbook.md` | Task-based recipes, common tasks |
| `ai-setup.md` | 5 AI providers, privacy-first, `obs ai setup` |
| `installation.md` | Homebrew or manual, 2 min setup |
| `configuration.md` | iCloud auto-detect, DB location, OBS_ROOT |
| `cli-reference.md` | Full command list, flags, examples |
| `refcard.md` | Printable cheat sheet, all commands |
| `migration.md` | v2.x to v3.0 breaking changes |

**Template:**

```markdown
> **TL;DR** (30 seconds)
> - **What:** [one sentence]
> - **Why:** [one benefit]
> - **How:** `[one command]`
> - **Next:** [link to next step]
```

### 1.2 Add Time Estimates to Guides (5 pages)

Add time/level/steps badge after H1:

```markdown
**Time:** ~X minutes | **Level:** Beginner/Intermediate | **Steps:** N
```

Target pages: `usage.md`, `cookbook.md`, `ai-setup.md`, `configuration.md`, `migration.md`

### 1.3 Add Callout Boxes to Reference Pages

Add `!!! tip`, `!!! warning`, `??? info` boxes to:
- `cli-reference.md` — pro tips per command section
- `refcard.md` — quick tips for common patterns
- `cookbook.md` — tips within recipes

Target: every page has at least 1 callout box.

### 1.4 Validate

```bash
mkdocs build --strict   # 0 warnings
```

---

## Phase 2: Structure (+15 points)

### 2.1 Add Custom CSS for Mobile + Mermaid

Create `docs_mkdocs/stylesheets/adhd.css`:
- Mermaid overflow fix (scroll on mobile)
- Touch target minimum 44px
- Card-style layout for feature grid on index
- TL;DR box styling (subtle background)

Add to `mkdocs.yml`:

```yaml
extra_css:
  - stylesheets/adhd.css
```

### 2.2 Add Mermaid Workflow Diagrams (4 new)

Add diagrams to existing pages:

| Page | Diagram | Type |
|------|---------|------|
| `usage.md` | Daily workflow: obs -> stats -> analyze -> ai | flowchart |
| `ai-setup.md` | Provider selection decision tree | flowchart |
| `cookbook.md` | First-time setup flow | flowchart |
| `configuration.md` | Config lookup order | flowchart |

### 2.3 Add Emoji Headings to Remaining Pages

Pages missing emoji headings: `cli-reference.md`, `refcard.md`, `changelog.md`, `migration.md`, `configuration.md`, `installation.md`, developer/*.md

Pattern: use relevant emoji before section headings (not H1).

### 2.4 Validate

```bash
mkdocs build --strict   # 0 warnings
```

---

## Phase 3: Polish (+10 points)

### 3.1 ADHD Quick Start Page

Create `docs_mkdocs/adhd-quick-start.md`:
- First 30 Seconds (3 commands)
- Next 5 Minutes (learn/configure/status)
- Stuck? (diagnostics)
- ADHD-Friendly Features list

Add to nav under "Getting Started".

### 3.2 Visual Workflows Page

Create `docs_mkdocs/workflows.md`:
- Onboarding workflow (Mermaid)
- Daily usage workflow (Mermaid)
- AI analysis pipeline (Mermaid)
- Vault health check workflow (Mermaid)

Add to nav under "Reference".

### 3.3 Update Nav

```yaml
nav:
  - Home: index.md
  - Getting Started:
      - ADHD Quick Start: adhd-quick-start.md   # NEW
      - Installation: installation.md
      - Configuration: configuration.md
      - Usage: usage.md
  - Reference:
      - Quick Reference: refcard.md
      - Visual Workflows: workflows.md          # NEW
      - Cookbook: cookbook.md
      - CLI Reference: cli-reference.md
      - AI Setup Guide: ai-setup.md
      - Changelog: changelog.md
  - Developer:
      - ...
```

### 3.4 Final Validate + Score

```bash
mkdocs build --strict
# Recalculate ADHD score -> target 85+
```

---

## Acceptance Criteria

- [ ] ADHD score >= 85/100 (Grade B)
- [ ] All 14 nav pages have at least 1 callout box
- [ ] 8 pages have TL;DR boxes
- [ ] 5 guide pages have time estimates
- [ ] 7+ Mermaid diagrams across site
- [ ] Custom CSS for mobile/Mermaid overflow
- [ ] ADHD Quick Start page created
- [ ] Visual Workflows page created
- [ ] `mkdocs build --strict` passes with 0 warnings
- [ ] All 3 tutorials retain time estimates

## How to Start

```bash
cd ~/.git-worktrees/obsidian-cli-ops/feature-adhd-website
claude
# Start with Phase 1
```
