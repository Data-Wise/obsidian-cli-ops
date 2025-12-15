# Sandbox Testing - Quick Reference

**One-page guide for testing Obsidian TUI features with synthetic vaults.**

---

## ⚡ 3-Command Quick Start

```bash
# 1. Generate test vault
python3 src/python/generate_test_vault.py ~/Documents/TestVault --notes 20

# 2. Scan it
python3 src/python/obs_cli.py discover ~/Documents/TestVault --scan

# 3. Launch TUI
python3 src/python/obs_cli.py tui
```

**Then:** Press `v` → Select vault → Test features (`n`, `g`, `s`)

---

## 🏗️ Generator Templates

```bash
# Small (10 notes) - Quick tests
python3 src/python/generate_test_vault.py ~/Documents/TestVault-Small \
  --notes 10 --density 0.2 --tags 5

# Medium (50 notes) - Realistic
python3 src/python/generate_test_vault.py ~/Documents/TestVault-Medium \
  --notes 50 --density 0.3 --tags 15

# Large (200 notes) - Stress test
python3 src/python/generate_test_vault.py ~/Documents/TestVault-Large \
  --notes 200 --density 0.4 --tags 30

# Reproducible (same every time)
python3 src/python/generate_test_vault.py ~/Documents/TestVault \
  --notes 20 --seed 42
```

---

## 🧪 TUI Test Workflow

| Screen | Key | What to Test |
|--------|-----|--------------|
| **Vault Browser** | `v` | Selection, stats display, refresh (r) |
| **Note Explorer** | `n` | Search, filter, preview, metadata |
| **Graph Visualizer** | `g` | Orphans, hubs, connections, metrics |
| **Statistics Dashboard** | `s` | Tab cycling, bar charts, refresh |
| **Help** | `?` | Shortcuts, navigation |
| **Quit** | `q` | Clean exit |

---

## 🔄 Quick Reset

```bash
# Regenerate vault
rm -rf ~/Documents/TestVault-Small
python3 src/python/generate_test_vault.py ~/Documents/TestVault-Small \
  --notes 10 --density 0.2 --tags 5
python3 src/python/obs_cli.py discover ~/Documents/TestVault-Small --scan
```

---

## 📊 Statistics Dashboard Testing

```bash
# After launching TUI:
v               # Vault Browser
↓ (select)      # Choose vault
s               # Statistics Dashboard
Tab             # Cycle: Tags → Distribution → History
r               # Refresh data
Esc             # Back to vaults
```

**Verify:**
- ✅ Tag bar charts display (`▓░` characters)
- ✅ Link distribution shows 4 buckets (0-2, 3-5, 6-10, 11+)
- ✅ Scan history shows recent scans
- ✅ Overview panel always visible (left 35%)

---

## 🐛 Troubleshooting

**Vault not showing in TUI?**
```bash
python3 src/python/obs_cli.py discover ~/Documents/TestVault --scan
```

**Statistics empty?**
```bash
python3 src/python/obs_cli.py vaults  # Get vault ID
python3 src/python/obs_cli.py analyze <vault_id>
```

**Want to start fresh?**
```bash
python3 src/python/obs_cli.py db init  # Reset database
```

---

## 📋 Testing Checklist

### Phase 4.5 (Statistics Dashboard)
- [ ] Tab cycling works (tags → distribution → history → tags)
- [ ] Tag analytics shows top 20 tags with bars
- [ ] Link distribution shows 4 buckets with emojis (🔴🟡🟢🔵)
- [ ] Scan history shows last 10 scans
- [ ] Refresh (r) updates all panels
- [ ] Overview panel persistent (left side, 35%)
- [ ] Color coding: red (>10%), yellow (5-10%), dim (<5%)
- [ ] Empty states handled (no tags, no scans)

### All Phases
- [ ] TUI launches without errors
- [ ] All screens accessible (v, n, g, s, ?)
- [ ] Navigation works (arrows, Enter, Esc, q)
- [ ] Data displays correctly
- [ ] No crashes with edge cases

---

## 🎯 Edge Cases to Test

```bash
# Empty vault
mkdir -p ~/Documents/TestVault-Empty/.obsidian

# Vault with 1 note
python3 src/python/generate_test_vault.py ~/Documents/TestVault-Tiny --notes 1

# Vault with very long titles
# (manually create note with 100+ character title)

# Vault with special characters
# (manually create notes with !@#$%^&*() in names)
```

---

**Full Guide:** See `SANDBOX_TESTING_GUIDE.md` for complete documentation.
**Generator Script:** `src/python/generate_test_vault.py --help`
