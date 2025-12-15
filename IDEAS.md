# Ideas for obsidian-cli-ops

## 🧪 Testing & Quality Assurance

### Sandbox Testing Strategy (2025-12-15)

**Quick Wins (< 30 min):**
- [2025-12-15] Create minimal test vault - Single folder with 10-20 markdown files, basic wikilinks, no complexity
- [2025-12-15] Use existing vault as read-only - Point `obs` at your real vault, test without modifying
- [2025-12-15] ✅ **IMPLEMENTED** Generate synthetic vault with script - Python script creates notes/links/tags on demand

**Medium Effort (1-2 hrs):**
- [2025-12-15] Structured test vault with scenarios - Organized folders testing: orphans, hubs, broken links, tags, clusters
- [2025-12-15] Multi-vault test environment - 3 vaults (small/medium/large) for different test cases
- [2025-12-15] Docker-based sandbox - Containerized Obsidian vault + database for isolated testing
- [2025-12-15] Copy-on-write vault snapshots - rsync or git-based snapshots for quick reset between tests

**Big Ideas (3+ hrs):**
- [2025-12-15] Automated test data generator - CLI tool that creates realistic knowledge graphs with configurable parameters
- [2025-12-15] Test vault fixtures library - Reusable vault templates (empty, minimal, realistic, stress-test, edge-cases)
- [2025-12-15] CI/CD integration - Automated tests run against fixture vaults on every commit

**Tutorials Created:**
- Step-by-step guide for Option #1: Minimal Test Vault (manual creation)
- Step-by-step guide for Option #3: Synthetic Vault Generator (Python script)

**Recommended Path:**
1. Start with minimal vault (5 min setup) for immediate TUI testing
2. ✅ Add synthetic generator (15 min setup) for repeatable tests **[IMPLEMENTED 2025-12-15]**
3. Expand to structured scenarios as needed

**Implementation Details (Option #3 - Synthetic Generator):**
- **Script:** `src/python/generate_test_vault.py` (369 lines)
- **Features:** Configurable notes, links, tags, frontmatter, special test notes (orphan, hub, broken links)
- **Documentation:** `SANDBOX_TESTING_GUIDE.md` (complete guide), `SANDBOX_QUICK_REF.md` (quick reference)
- **Test Vaults Created:** TestVault-Small (10 notes), TestVault-Medium (50 notes), TestVault-Large (200 notes)
- **Time to Implement:** ~15 minutes (as estimated)
- **Status:** ✅ Fully functional and tested

## 🆕 New Features

*No items yet*

## 🔧 Improvements

*No items yet*

## 🐛 Bugs to Fix

*No items yet*

## 🤔 To Explore

*No items yet*
