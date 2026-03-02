# Getting Started

Get obs installed and scanning your first vault in under 10 minutes.

**Time:** ~10 minutes | **Level:** Beginner | **Steps:** 7

---

## Step 1: What is obs?

`obs` is a command-line tool for managing Obsidian vaults. It scans your vaults, builds a knowledge graph, and provides insights about your notes — which ones are well-connected, which are orphaned, and where broken links exist.

**What you'll learn in this tutorial:**

- Install dependencies and initialize the database
- Discover and scan Obsidian vaults
- View vault statistics

---

## Step 2: Install Dependencies

```bash
# Install Python dependencies
pip3 install -r src/python/requirements.txt
```

??? tip "Already have dependencies?"
    If you've installed before, you can skip this step. Run `python3 -c "import networkx; import rich"` to verify.

---

## Step 3: Initialize the Database

obs stores vault metadata in a local SQLite database. Initialize it once:

```bash
python3 src/python/obs_cli.py db init
```

**Expected output:**

```
✅ Database initialized at ~/.config/obs/vault_db.sqlite
```

The database is local-only — no data leaves your machine.

---

## Step 4: Discover Vaults

obs can automatically find Obsidian vaults on your system. It looks for directories containing `.obsidian` folders.

```bash
# Discover vaults in your Documents folder
obs discover ~/Documents

# Or let it check the standard iCloud location
obs discover ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents
```

**Expected output:**

```
🔍 Searching for Obsidian vaults...

✓ Found 2 vault(s):
  • /Users/you/Documents/MyVault
  • /Users/you/Documents/WorkNotes
```

??? tip "Auto-scan during discovery"
    Add `--scan` to discover and scan in one step:
    ```bash
    obs discover ~/Documents --scan
    ```

---

## Step 5: Scan a Vault

Scanning reads all markdown files, extracts wikilinks, tags, and metadata:

```bash
obs scan /path/to/your/vault
```

**Expected output:**

```
📂 Scanning vault: MyVault
  Notes: 142
  Links: 387
  Tags: 56
  ✅ Scan complete
```

This builds the knowledge graph that powers all analysis features.

---

## Step 6: List Vaults and View Stats

See all your registered vaults:

```bash
obs
```

View detailed statistics for a specific vault — use its name or ID:

```bash
obs stats --vault MyVault
```

**Expected output:**

```
📊 MyVault
  Path: /Users/you/Documents/MyVault
  Last Scanned: 2 minutes ago

  Content
    Notes: 142
    Links: 387
    Tags: 56

  Graph Health
    Orphaned: 12
    Hubs (>10 links): 5
    Broken Links: 3
```

---

## Step 7: Next Steps

You now have obs set up and your vault scanned. Here's where to go next:

| Want to... | Tutorial |
|------------|----------|
| Analyze your knowledge graph | [Graph Analysis](graph-analysis.md) |
| Set up AI-powered features | [AI Features](ai-features.md) |
| See all available commands | `obs help --all` |

---

**Summary:** You installed obs, initialized the database, discovered vaults, scanned one, and viewed its statistics. Your knowledge graph is ready for analysis.
