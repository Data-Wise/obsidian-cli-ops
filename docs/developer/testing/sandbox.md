# Sandbox Testing Guide

**Complete guide for testing Obsidian CLI Ops TUI features using synthetic test vaults.**

---

## 🎯 Quick Start (5 minutes)

### Option 1: Generate Small Test Vault

```bash
# Generate a small vault (10 notes)
python3 src/python/generate_test_vault.py ~/Documents/TestVault-Small \
  --notes 10 --density 0.3 --tags 5

# Scan it
python3 src/python/obs_cli.py discover ~/Documents/TestVault-Small --scan

# Launch TUI
python3 src/python/obs_cli.py tui
```

**Test workflow:**
1. Press `v` → Vault Browser
2. Select "TestVault-Small"
3. Press `n` → Note Explorer (search, filter, preview)
4. Press `g` → Graph Visualizer (view connections)
5. Press `s` → Statistics Dashboard
   - Press `Tab` to cycle through views (tags, distribution, history)
   - Press `r` to refresh data
6. Press `Esc` to go back
7. Press `q` to quit

---

## 📦 Vault Generator Tool

### Overview

**Script:** `src/python/generate_test_vault.py`

**Purpose:** Creates realistic synthetic Obsidian vaults with configurable:
- Number of notes (1-1000+)
- Link density (0.0-1.0)
- Tag distribution
- Content variety

**Special Features:**
- Generates `.obsidian` directory (valid Obsidian vault)
- Creates wikilinks with proper `[[link]]` and `[[link|alias]]` syntax
- Adds YAML frontmatter (30% of notes)
- Includes special test notes (orphan, hub, broken links, index)
- Reproducible with `--seed` parameter

### Usage

```bash
python3 src/python/generate_test_vault.py <output_dir> [options]
```

### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--notes` | `-n` | 20 | Number of notes to generate |
| `--density` | `-d` | 0.3 | Link density (avg links/note as fraction) |
| `--tags` | `-t` | 10 | Number of unique tags |
| `--seed` | `-s` | None | Random seed for reproducibility |

### Examples

```bash
# Small vault (quick tests)
python3 src/python/generate_test_vault.py ~/Documents/TestVault-Small \
  --notes 10 --density 0.2 --tags 5

# Medium vault (realistic)
python3 src/python/generate_test_vault.py ~/Documents/TestVault-Medium \
  --notes 50 --density 0.3 --tags 15

# Large vault (stress test)
python3 src/python/generate_test_vault.py ~/Documents/TestVault-Large \
  --notes 200 --density 0.4 --tags 30

# Reproducible vault (same content every time)
python3 src/python/generate_test_vault.py ~/Documents/TestVault \
  --notes 20 --seed 42
```

### Output Structure

```
TestVault-Small/
├── .obsidian/
│   ├── app.json
│   └── workspace.json
├── Index.md                          # Main entry point
├── Hub Note.md                       # Highly connected (10+ links)
├── Orphan Note.md                    # No incoming links
├── Broken Links Test.md              # Contains broken references
├── Understanding Data Structures.md  # Regular notes (30% with frontmatter)
├── Introduction to Productivity.md
├── Note 001.md
├── Note 002.md
└── ...
```

---

## 🧪 Testing Scenarios

### Scenario 1: Basic TUI Navigation

**Vault:** Small (10 notes)

**Steps:**
1. Generate vault
2. Scan vault
3. Launch TUI
4. Navigate through all screens (v, n, g, s)
5. Test keyboard shortcuts (arrows, Esc, q, Tab, r)

**What to verify:**
- ✅ All screens load without errors
- ✅ Navigation between screens works
- ✅ Data displays correctly
- ✅ Help screen accessible (?)

---

### Scenario 2: Note Explorer Features

**Vault:** Medium (50 notes)

**Steps:**
1. Navigate to Note Explorer (v → select vault → n)
2. Test search/filter functionality
3. Preview different notes
4. View note metadata (links, tags, size)

**What to verify:**
- ✅ Search finds notes correctly
- ✅ Preview shows content
- ✅ Metadata displays accurate info
- ✅ Scrolling works for long lists

---

### Scenario 3: Graph Analysis

**Vault:** Medium (50 notes)

**Steps:**
1. Navigate to Graph Visualizer (v → select vault → g)
2. View different graph modes (orphans, hubs, clusters)
3. Select individual nodes
4. Check metrics accuracy

**What to verify:**
- ✅ Graph renders correctly
- ✅ Orphan detection works
- ✅ Hub detection works (highly connected notes)
- ✅ Metrics match database values
- ✅ ASCII art displays properly

---

### Scenario 4: Statistics Dashboard

**Vault:** Medium (50 notes)

**Steps:**
1. Navigate to Statistics Dashboard (v → select vault → s)
2. View tag analytics (Tab to first view)
3. View link distribution (Tab to second view)
4. View scan history (Tab to third view)
5. Refresh data (press r)

**What to verify:**
- ✅ Tab cycling works (tags → distribution → history → tags)
- ✅ Tag bar charts display correctly
- ✅ Link distribution buckets accurate
- ✅ Scan history shows recent scans
- ✅ Refresh updates all panels
- ✅ Overview panel always visible (left side)

---

### Scenario 5: Edge Cases

**Vault:** Custom configurations

**Test cases:**

```bash
# Empty vault (0 notes)
mkdir -p ~/Documents/TestVault-Empty/.obsidian
python3 src/python/obs_cli.py discover ~/Documents/TestVault-Empty --scan
# Verify: TUI handles gracefully, shows "no notes" messages

# Vault with no tags
python3 src/python/generate_test_vault.py ~/Documents/TestVault-NoTags \
  --notes 10 --tags 0
# Verify: Statistics dashboard shows "no tags found"

# Vault with very long note titles
cat > ~/Documents/TestVault-Small/"This Is A Very Long Note Title With Many Words That Should Be Truncated When Displayed.md" << 'EOF'
# Long Title Test
Test content
EOF
# Verify: Title truncation works (shows "..." for long titles)

# Vault with special characters
cat > ~/Documents/TestVault-Small/"Note with !@#$%^&*() special chars.md" << 'EOF'
# Special Characters Test
EOF
# Verify: Special characters handled correctly
```

---

### Scenario 6: Stress Testing

**Vault:** Large (200+ notes)

**Steps:**
1. Generate large vault
2. Scan vault (may take 10-30 seconds)
3. Test all TUI features with large dataset
4. Monitor performance

**What to verify:**
- ✅ Scanning completes within reasonable time
- ✅ Graph metrics calculate correctly
- ✅ TUI remains responsive
- ✅ Memory usage acceptable
- ✅ No crashes or freezes

---

## 📊 Test Vault Comparison

| Vault Size | Notes | Links | Tags | Scan Time | Best For |
|-----------|-------|-------|------|-----------|----------|
| **Small** | 10 | ~3/note | 5 | <1s | Feature testing, quick iterations |
| **Medium** | 50 | ~15/note | 15 | ~2s | Realistic workflows, UI testing |
| **Large** | 200 | ~80/note | 30 | ~10s | Stress testing, performance |
| **Custom** | Variable | Variable | Variable | Variable | Edge cases, specific scenarios |

---

## 🔄 Resetting Test Vaults

### Quick Reset (Regenerate)

```bash
# Delete and regenerate vault
rm -rf ~/Documents/TestVault-Small
python3 src/python/generate_test_vault.py ~/Documents/TestVault-Small \
  --notes 10 --density 0.3 --tags 5
python3 src/python/obs_cli.py discover ~/Documents/TestVault-Small --scan
```

### Reproducible Reset (Using Seed)

```bash
# Generate with seed
python3 src/python/generate_test_vault.py ~/Documents/TestVault \
  --notes 20 --seed 42

# Later, regenerate exact same vault
rm -rf ~/Documents/TestVault
python3 src/python/generate_test_vault.py ~/Documents/TestVault \
  --notes 20 --seed 42
```

### Git-Based Snapshots

```bash
# Initialize vault as git repo
cd ~/Documents/TestVault-Small
git init
git add .
git commit -m "Initial vault state"

# Later, reset to original state
git reset --hard HEAD
```

---

## 🐛 Common Issues and Fixes

### Issue: "Vault not found" in TUI

**Cause:** Vault not scanned or database out of sync

**Fix:**
```bash
python3 src/python/obs_cli.py discover ~/Documents/TestVault-Small --scan
```

---

### Issue: Statistics showing 0 or empty

**Cause:** Vault scan incomplete or failed

**Fix:**
```bash
# Reinitialize database
python3 src/python/obs_cli.py db init

# Rescan vault
python3 src/python/obs_cli.py discover ~/Documents/TestVault-Small --scan
```

---

### Issue: Graph metrics not calculated

**Cause:** Analysis not run after scan

**Fix:**
```bash
# Get vault ID
python3 src/python/obs_cli.py vaults

# Run analysis
python3 src/python/obs_cli.py analyze <vault_id>
```

---

### Issue: Generator creates wrong number of notes

**Cause:** Special notes (Index, Hub, Orphan, Broken Links) are added automatically

**Expected behavior:**
```bash
# Request 10 notes
--notes 10

# Actual output: 13 notes
# - 10 regular notes
# - 1 Index.md
# - 1 Hub Note.md
# - 1 Orphan Note.md
# - 1 Broken Links Test.md (total: 13)
```

---

## 🎓 Advanced Usage

### Custom Vault Templates

Create a template script for your specific testing needs:

```bash
#!/bin/bash
# custom_test_vault.sh

# Generate base vault
python3 src/python/generate_test_vault.py ~/Documents/MyTestVault \
  --notes 30 --density 0.25 --tags 12 --seed 100

# Add custom notes for specific tests
cat > ~/Documents/MyTestVault/"Special Test Case.md" << 'EOF'
# Special Test Case

This note tests a specific feature.

[[Index]] [[Hub Note]]

#test #custom
EOF

# Scan vault
python3 src/python/obs_cli.py discover ~/Documents/MyTestVault --scan

echo "✅ Custom test vault ready!"
```

---

### Batch Vault Generation

Generate multiple test vaults at once:

```bash
#!/bin/bash
# batch_generate.sh

for size in small medium large; do
  case $size in
    small)  notes=10; density=0.2; tags=5 ;;
    medium) notes=50; density=0.3; tags=15 ;;
    large)  notes=200; density=0.4; tags=30 ;;
  esac

  python3 src/python/generate_test_vault.py \
    ~/Documents/TestVault-$size \
    --notes $notes --density $density --tags $tags

  python3 src/python/obs_cli.py discover ~/Documents/TestVault-$size --scan
done

echo "✅ All test vaults generated and scanned!"
```

---

## 📝 Verification Checklist

Use this checklist for comprehensive testing:

### ✅ Phase 4.1: TUI Foundation
- [ ] TUI launches without errors
- [ ] Home screen displays correctly
- [ ] Help screen accessible (? key)
- [ ] Navigation shortcuts work (v, n, g, s, q)
- [ ] Footer shows keyboard bindings

### ✅ Phase 4.2: Vault Browser
- [ ] Lists all vaults from database
- [ ] Shows vault statistics (notes, links, tags)
- [ ] Vault selection works (arrow keys + Enter)
- [ ] Details panel displays correct data
- [ ] Refresh command works (r key)
- [ ] Empty state handles gracefully

### ✅ Phase 4.3: Note Explorer
- [ ] Lists all notes in selected vault
- [ ] Search/filter functionality works
- [ ] Note preview displays content
- [ ] Metadata shows links, tags, size
- [ ] Scrolling works for long lists
- [ ] Navigation between notes works

### ✅ Phase 4.4: Graph Visualizer
- [ ] ASCII graph renders correctly
- [ ] Orphan detection accurate
- [ ] Hub detection accurate (>10 links)
- [ ] Graph metrics display
- [ ] Node selection works
- [ ] Different views accessible (orphans, hubs, clusters)

### ✅ Phase 4.5: Statistics Dashboard
- [ ] Overview panel displays vault stats
- [ ] Tag analytics view works
- [ ] Link distribution view works
- [ ] Scan history view works
- [ ] Tab cycling works (tags → distribution → history)
- [ ] Refresh updates all data (r key)
- [ ] Bar charts render correctly
- [ ] Empty state handling (no tags, no history)
- [ ] Color coding works (red/yellow/dim for tags)

---

## 🚀 Next Steps

After testing with synthetic vaults:

1. **Test with Real Vaults:**
   - Point `obs` at your actual Obsidian vaults
   - Compare results with synthetic vaults
   - Verify accuracy of metrics

2. **Report Issues:**
   - Document any bugs found
   - Note performance issues with large vaults
   - Suggest improvements

3. **Automated Testing:**
   - Integrate vault generator into CI/CD
   - Add automated tests using fixture vaults
   - Set up regression testing

4. **Contribute:**
   - Share test vault templates
   - Document edge cases discovered
   - Improve generator features

---

**Generated:** 2025-12-15
**Version:** 1.0.0
**Tool:** `src/python/generate_test_vault.py`
