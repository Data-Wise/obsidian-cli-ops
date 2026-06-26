# Vault Management

Inspect, rename, and safely remove vaults from the obs index using the `obs vault` command family. These operate on the **database index only** — your markdown files on disk are never touched.

**Time:** ~10 minutes | **Level:** 🟢 Beginner | **Steps:** 5

**Prerequisites:** Complete [Getting Started](getting-started.md) and have at least one scanned vault.

---

## The `obs vault` Family

| Command | What it does | Touches disk? |
|---------|--------------|---------------|
| `obs vault info <vault>` | Show one vault's metadata | No (read-only) |
| `obs vault rename <vault> <name>` | Change the display name | No (index only) |
| `obs vault delete <vault>` | Remove the vault from the index | **No** — files stay |

All three accept a vault **name**, full **ID**, or unambiguous **ID prefix** — the same resolution used by `obs stats` and `obs health`. Add `--json` to any of them for machine-readable output.

---

## Step 1: Inspect a Vault

Start by looking at what obs knows about a vault:

```bash
obs vault info Research
```

```
╭─────────────── 📁 Research ───────────────╮
│ Name: Research                            │
│ ID: a1b2c3d4e5f6...                       │
│ Path: /Users/you/Documents/Research       │
│ Notes: 482                                │
│ Last scanned: 2 hours ago                 │
│ Registered: 3 months ago                  │
╰───────────────────────────────────────────╯
```

For scripting, request JSON instead:

```bash
obs vault info Research --json
# {"id": "a1b2c3...", "name": "Research", "path": "/Users/you/Documents/Research",
#  "notes": 482, "last_scanned": "...", "created_at": "..."}
```

---

## Step 2: Rename a Vault

When a vault was registered with an awkward auto-generated name (often the directory basename), give it a friendlier label:

```bash
obs vault rename Research "Research Vault"
# ✏️  Renamed Research → Research Vault
```

The **path and ID are unchanged** — only the display name moves. Every note, link, and graph metric stays valid because they key off the ID (a hash of the path), not the name.

!!! warning "Collisions are refused"
    If another vault already uses the target name, the rename fails:

    ```bash
    obs vault rename WorkNotes "Research Vault"
    # ❌ Another vault already uses the name 'Research Vault' (id b7c8...);
    #    names must stay unambiguous.
    ```

    This keeps name-based lookup (`obs stats "Research Vault"`) deterministic.

---

## Step 3: Preview a Deletion (dry-run)

Deletion is **dry-run by default** — running it without `--force` changes nothing and just previews the impact:

```bash
obs vault delete "Old Archive"
```

```
╭──────────── ⚠️  DRY RUN — nothing deleted ────────────╮
│ Name: Old Archive                                    │
│ ID: f9e8d7c6...                                      │
│ Path: /Users/you/Documents/OldArchive                │
│ Notes that will be removed: 137                      │
│                                                      │
│ The vault folder on disk is NOT touched — only the   │
│ obs index.                                           │
│ Re-run with --force to delete.                       │
╰──────────────────────────────────────────────────────╯
```

Read the note count carefully — that's how many index rows (and their links, tags, and graph metrics) will cascade away.

---

## Step 4: Commit the Deletion

When the preview looks right, pass `--force`:

```bash
obs vault delete "Old Archive" --force
# 🗑️  Deleted vault Old Archive (137 notes removed from the obs index).
```

What happens under the hood:

- The `vaults` row is deleted.
- A SQLite `ON DELETE CASCADE` foreign key removes the vault's notes, and that cascades again to the notes' links, tags, graph metrics, and embeddings.
- **The markdown files on disk are untouched.**

!!! tip "Deletion is reversible by re-scanning"
    Because the files are never removed, you can rebuild the index any time:

    ```bash
    obs scan ~/Documents/OldArchive --analyze
    ```

---

## Step 5: A Full "Reset" Workflow

Combining the verbs lets you reset a vault's index without risking data:

```bash
# Drop a stale or corrupted index
obs vault delete MyVault --force

# Rebuild it cleanly from the files on disk
obs scan ~/Documents/MyVault --analyze

# Give it a tidy display name
obs vault rename MyVault "My Vault"
```

---

## From Claude Desktop (MCP)

The same operations are available as MCP tools when obs is connected to Claude Desktop, Claude Code, or Cowork:

| Ask Claude | Tool called |
|------------|-------------|
| *"Rename my Research vault to Archive"* | `rename_vault("Research", "Archive")` |
| *"Remove the Old Archive vault — preview first"* | `delete_vault("Old Archive", confirm=False)` |
| *"Yes, delete it"* | `delete_vault("Old Archive", confirm=True)` |

`delete_vault` follows the same dry-run-then-confirm safety contract as the CLI: `confirm=False` (the default) previews, `confirm=True` commits.

There is no separate `vault info` MCP tool — `get_vault_stats(vault_id)` already returns a vault's metadata and content stats.

---

## Recap

- `obs vault info` — read-only inspection of one vault.
- `obs vault rename` — relabel without moving anything; collisions refused.
- `obs vault delete` — dry-run by default, `--force` to commit, **files always safe**.
- Deletion cascades through the index but never touches disk, so re-scanning fully restores a vault.

**Next:** [Monitoring & Health](monitoring-and-health.md) to track vaults over time, or the [Cookbook](../cookbook.md) for copy-paste recipes.
