---
name: docs-quality
description: Validate documentation quality — markdown syntax, link health, nav alignment, and build integrity.
hot_reload: true
---

# Docs Quality Validator

Validates that documentation is healthy before commit/PR/deploy. Runs as part of the `preflight-check` suite.

## Check Set

### 1. Markdown Syntax (markdownlint)

```bash
# Uses project .markdownlint.json config
markdownlint -c .markdownlint.json docs/
```

**Failure modes:**
- MD013 line length > 120 (configurable in .markdownlint.json)
- MD040 code block without language specifier
- MD024 duplicate headings (same file only)
- MD032 list spacing

### 2. Link Health (lychee)

```bash
# Offline mode for commit/PR (fast, internal only)
lychee --offline docs/

# Full check for release/deploy (requires network)
lychee docs/
```

**Config**: `lychee.toml` at project root controls exclusions (anchor-only, localhost, mailto).

### 3. Navigation Alignment (nav-sync)

```bash
# Check for drift between docs/ directory and mkdocs.yml nav
# See nav-sync skill for full sync workflow
```

**Checks:**
- Files in docs/ not in nav (orphans)
- Nav entries with no file (stale refs)
- Orphan quality: files < 100 words flagged for review

### 4. Build Integrity

```bash
mkdocs build --strict
```

### 5. Mermaid Diagrams (mermaid-linter)

Delegated to `mermaid-linter` skill. Validates syntax, direction (TD preferred), text length.

## Mode Behavior

| Mode | Scope | Behavior |
|------|-------|----------|
| `default` | Changed files only | Fail-fast, summary output |
| `debug` | All docs | Verbose, no fail-fast, surface all warnings |
| `thorough` | All docs | Full pipeline, combined health score |
| `release` | All docs | Strictest: health score >= 80 required, nav drift = fatal |

## Output

```text
DOCS QUALITY VALIDATION
  markdownlint: PASS (0 errors)
  lychee:       FAIL (1 broken link)
  nav-sync:     PASS (0 orphans, 0 stale)
  build:        PASS (mkdocs build --strict clean)
  mermaid:      PASS (3/3 valid)
  Health score: 85/100 (WARNING)

Result: FAIL — fix broken link before proceeding
```
