# R-Dev Integration

The `r-dev` module connects your R/Emacs workflow to your Obsidian "Lab Notebook".

## Workflow

### 1. Link a Project
Tell `obs` where this R project lives in your vault.

```bash
cd ~/projects/RMediation
obs r-dev link Research_Lab/RMediation_Package
```

This creates a mapping in `~/.config/obs/project_map.json` so future commands auto-detect the correct Obsidian folder.

### 2. Check Status (Optional)
See if the current R project is linked.

```bash
obs r-dev status
```

Shows:
- R project root path
- Mapped Obsidian folder
- Whether the mapping exists

### 3. Log Results
Push simulation plots or HTML reports to the `06_Analysis` folder.

```bash
obs r-dev log results/plot.png -m "Sensitivity analysis n=500"
```

Files are automatically timestamped to prevent overwrites.

### 4. Fetch Theory
Grab mathematical context from your Knowledge Base while coding.

```bash
obs r-dev context "Sobel Test"
```

### 5. Sync Drafts
Push a vignette or RMarkdown file to `02_Drafts` for prose editing in Obsidian.

```bash
obs r-dev draft vignettes/intro.Rmd
```

### 6. Unlink a Project
Remove the R project mapping when you're done.

```bash
cd ~/projects/RMediation
obs r-dev unlink
```

## Tips

- Use `obs list` to see all your R project mappings at a glance
- Use `--verbose` flag to debug mapping issues: `obs --verbose r-dev log plot.png`
- The mapping file is plain JSON, you can edit `~/.config/obs/project_map.json` directly if needed
