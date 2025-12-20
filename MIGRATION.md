# Migration Guide: v2.x → v3.0.0

**Obsidian CLI Ops v3.0.0** represents a major simplification focused on core Obsidian vault management. This guide helps you transition from v2.x to v3.0.0.

---

## Overview of Changes

### Philosophy Shift: Proposal A

**v2.x**: Multi-purpose tool (Obsidian + TUI + R-Dev integration)
**v3.0.0**: Laser-focused Obsidian vault manager

**Key Changes:**
- ✅ **Simplified CLI**: 20+ commands → 10 focused commands
- ❌ **Removed TUI**: Full-screen interface removed (CLI-only)
- ❌ **Removed R-Dev**: R project integration removed
- ❌ **Removed Legacy**: v1.x commands removed
- 📉 **Code Reduction**: 11,500 → ~7,400 lines (36% so far, target 61%)

---

## Command Migration Table

### Removed Commands

| v2.x Command | v3.0.0 Replacement | Notes |
|--------------|-------------------|-------|
| `obs` (no args) | `obs` | Now lists all vaults instead of opening TUI |
| `obs tui` | `obs` | TUI removed - use CLI commands |
| `obs tui --vault-id <id>` | `obs stats <id>` | CLI vault statistics |
| `obs switch` | `obs` | Vault list is the default view |
| `obs open <name>` | `obs stats <id>` | Use vault ID instead of name |
| `obs manage` | `obs discover` + `obs stats` | Split into focused commands |
| `obs graph` | `obs analyze <id>` | Graph analysis via CLI |
| `obs r link` | *(removed)* | Use R package ecosystem instead |
| `obs r log` | *(removed)* | Use R package ecosystem instead |
| `obs r context` | *(removed)* | Use R package ecosystem instead |
| `obs check` | *(removed)* | Low-value utility |
| `obs list` | `obs` | Default command lists vaults |
| `obs sync` | *(removed)* | Legacy v1.x command |
| `obs install` | *(removed)* | Legacy v1.x command |
| `obs audit` | *(removed)* | Legacy v1.x command |
| `obs search` | *(removed)* | Legacy v1.x command |

### Retained Commands

| Command | Status | Changes |
|---------|--------|---------|
| `obs` | ✅ Enhanced | Now lists vaults (was TUI launcher) |
| `obs stats <vault_id>` | ✅ Retained | Same functionality |
| `obs discover <path>` | ✅ Retained | Same functionality |
| `obs analyze <vault_id>` | ✅ Retained | Same functionality |
| `obs vaults` | ✅ Retained | Same as `obs` (alias) |
| `obs ai status` | ✅ Retained | Same functionality |
| `obs ai setup` | ✅ Retained | Same functionality |
| `obs ai test` | ✅ Retained | Same functionality |
| `obs ai similar` | ✅ Retained | Same functionality |
| `obs ai analyze` | ✅ Retained | Same functionality |
| `obs ai duplicates` | ✅ Retained | Same functionality |
| `obs help` | ✅ Enhanced | Cleaner output |
| `obs version` | ✅ Retained | Same functionality |

---

## Workflow Changes

### Before (v2.x): TUI-Centric

```bash
# Launch TUI
obs

# Or launch specific vault
obs tui --vault-id my-vault

# Switch vaults
obs switch

# Manage vaults
obs manage
```

### After (v3.0.0): CLI-First

```bash
# List all vaults
obs

# Show vault statistics
obs stats my-vault

# Discover new vaults
obs discover ~/Documents

# Analyze vault graph
obs analyze my-vault
```

---

## Feature Removal Details

### 1. TUI (Terminal User Interface)

**Why Removed:**
- Added 1,701 lines of code
- Duplicated CLI functionality
- Required Textual dependency (~500KB)
- Maintenance burden without unique value

**Alternative Workflow:**

Instead of navigating TUI screens:

| TUI Screen | CLI Equivalent |
|------------|----------------|
| Vault Browser | `obs` (list vaults) |
| Vault Stats | `obs stats <vault_id>` |
| Note Explorer | `obs analyze <vault_id>` |
| Graph View | `obs analyze <vault_id>` |
| Statistics | `obs stats <vault_id>` |

**Example Migration:**

```bash
# v2.x: Open TUI, navigate to vaults, select vault, view stats
obs
# (press keys: v → Enter → s)

# v3.0.0: Direct CLI command
obs stats my-vault
```

### 2. R-Dev Integration

**Why Removed:**
- R integration belongs in R package ecosystem
- Added 307 lines to codebase
- Limited to R users only
- Better served by dedicated R package

**Recommended Alternative:**

Use R packages for Obsidian integration:
- Create R package with `usethis::create_package()`
- Use `here::here()` for path management
- Use `fs` package for file operations
- Consider creating dedicated R-Obsidian package

**Example R Package Setup:**

```r
# In your R project
library(usethis)
library(fs)

# Create functions for Obsidian integration
write_to_obsidian <- function(content, vault_path) {
  path <- fs::path(vault_path, "R-Notes", paste0(Sys.Date(), ".md"))
  writeLines(content, path)
  message("✓ Written to Obsidian: ", path)
}

# Use it
write_to_obsidian("# Analysis Results\n\n...", "~/Vaults/Research")
```

### 3. Legacy v1.x Commands

**Why Removed:**
- Designed for single-vault, OBS_ROOT configuration
- Overlapped with other tools (plugin management better served by Obsidian UI)
- Low usage
- 126 lines of code

**Commands Removed:**
- `obs check` - Dependency checking
- `obs sync` - Configuration sync
- `obs install` - Plugin installation
- `obs audit` - Vault structure audit
- `obs search` - Plugin search
- `obs list` - Vault listing (replaced by `obs`)

**Alternatives:**
- Plugin management: Use Obsidian's built-in Community Plugins interface
- Vault auditing: Use `obs stats <vault_id>`
- Configuration sync: Use git or cloud storage directly

---

## Breaking Changes

### 1. Default Behavior (`obs` with no args)

**v2.x:**
```bash
obs          # Launched TUI with last vault
```

**v3.0.0:**
```bash
obs          # Lists all vaults in database
```

**Migration:**
- Update scripts that relied on TUI launching
- Use `obs stats <vault_id>` for specific vault info

### 2. Vault Selection

**v2.x:**
```bash
obs open my-vault-name      # Open by name
obs tui --vault-id abc123   # Open by ID
```

**v3.0.0:**
```bash
obs stats <vault_id>        # Use ID only
```

**Migration:**
- Update scripts to use vault IDs instead of names
- Get IDs with `obs` command

### 3. R Integration Workflow

**v2.x:**
```bash
obs r link                  # Link R project
obs r log results.png       # Copy to vault
```

**v3.0.0:**
```bash
# No direct equivalent - use R package approach
# See "R-Dev Integration" section above
```

---

## Installation & Upgrade

### Clean Install (Recommended)

```bash
# Backup your database
cp ~/.config/obs/obsidian_vaults.db ~/.config/obs/obsidian_vaults.db.backup

# Pull latest code
cd ~/projects/dev-tools/obsidian-cli-ops
git checkout main
git pull origin main

# Reinstall dependencies (Textual removed, Rich added)
pip3 install -r src/python/requirements.txt

# Database is compatible - no migration needed
```

### Dependency Changes

**Removed:**
```
textual>=0.52.0      # TUI framework (no longer needed)
```

**Added:**
```
rich>=13.7.0         # CLI output formatting (replaces Textual tables)
```

**Update:**
```bash
pip3 uninstall textual
pip3 install rich
```

---

## Database Compatibility

✅ **Database schema is fully compatible** - no migration needed!

Your existing vault data will work with v3.0.0:
- Vault registrations preserved
- Notes and links preserved
- Graph metrics preserved
- AI embeddings preserved (if using AI features)

The database location remains the same: `~/.config/obs/obsidian_vaults.db`

---

## Configuration Changes

### Removed Configuration

**v1.x OBS_ROOT:**
```bash
# No longer needed or used
# export OBS_ROOT="$HOME/Vaults/Main"
```

**R-Dev Mappings:**
```bash
# ~/.config/obs/r_project_mappings (no longer used)
```

### Retained Configuration

**Last Vault:**
```bash
# ~/.config/obs/last_vault (still used by some commands)
```

**AI Configuration:**
```bash
# ~/.config/obs/ai_config.json (still used by AI features)
```

---

## Testing Your Migration

After upgrading, verify everything works:

```bash
# 1. List vaults (should show your existing vaults)
obs

# 2. Check a vault's statistics
obs stats <vault_id>

# 3. Analyze graph (should show existing metrics)
obs analyze <vault_id>

# 4. Test AI features (if configured)
obs ai status
obs ai test

# 5. Discover new vaults
obs discover ~/Documents

# 6. Verify help
obs help --all
```

---

## Troubleshooting

### "Command not found" errors

If you get errors for removed commands:

```bash
# v2.x script:
obs tui --vault-id my-vault   # ERROR in v3.0.0

# Update to:
obs stats my-vault
```

### Missing TUI

If you relied heavily on TUI:

**Option 1:** Stay on v2.2.0
```bash
git checkout v2.2.0
```

**Option 2:** Learn CLI equivalents (recommended)
- See "Workflow Changes" section above
- CLI is faster for power users
- All functionality is available via CLI

### R Integration Missing

See "R-Dev Integration" section above for R package approach.

---

## What's Coming in v3.0.0

### Phase 7.2: AI-Powered Note Operations (Planned)

```bash
obs refactor <vault>         # AI-powered vault reorganization
obs tag-suggest <note>       # Intelligent tag suggestions
obs quality <note>           # Note quality assessment
obs merge-suggest <vault>    # Find merge candidates
```

### Phase 7.3: Vault Health & Polish (Planned)

```bash
obs health <vault>           # Comprehensive vault health check
obs fix <vault>              # Auto-fix common issues
```

---

## Getting Help

### Documentation

- **Quick Reference**: `obs help --all`
- **User Guide**: https://data-wise.github.io/obsidian-cli-ops/
- **Developer Guide**: `CLAUDE.md` in repository
- **GitHub Issues**: https://github.com/Data-Wise/obsidian-cli-ops/issues

### Common Questions

**Q: Why remove TUI?**
A: TUI added 1,701 lines of code but duplicated CLI functionality. CLI-only simplifies codebase and focuses on core value.

**Q: Why remove R-Dev?**
A: R integration belongs in R package ecosystem where it can be more powerful and focused.

**Q: Can I still use v2.2.0?**
A: Yes! v2.2.0 is stable and will remain available. Just checkout `v2.2.0` tag.

**Q: Will my data be lost?**
A: No! Database is fully compatible. Your vaults, notes, links, and AI embeddings are preserved.

**Q: Are AI features still available?**
A: Yes! All AI features (similar, analyze, duplicates) are retained and improved.

---

## Summary

**What Changed:**
- ❌ TUI removed (1,701 lines)
- ❌ R-Dev removed (307 lines)
- ❌ Legacy commands removed (126 lines)
- ✅ Simplified to 10 focused commands
- ✅ Database 100% compatible
- ✅ All AI features retained

**Action Items:**
1. ✅ Update dependencies (`pip3 install -r requirements.txt`)
2. ✅ Update scripts to use new command syntax
3. ✅ Test with `obs` and `obs stats <vault_id>`
4. ✅ For R integration, create dedicated R package
5. ✅ Join us for Phase 7.2 AI features!

**Questions?** Open an issue on GitHub: https://github.com/Data-Wise/obsidian-cli-ops/issues

---

**Last Updated:** 2025-12-20
**Version:** v3.0.0-dev (Phase 7.1)
