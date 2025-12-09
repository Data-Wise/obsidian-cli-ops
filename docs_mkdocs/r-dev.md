# R-Dev Integration

The `r-dev` module connects your R/Emacs workflow to your Obsidian "Lab Notebook".

## Workflow

### 1. Link a Project
Tell `obs` where this R project lives in your vault.

```bash
cd ~/projects/RMediation
obs r-dev link Research_Lab/RMediation_Package
```

### 2. Log Results
Push simulation plots or HTML reports to the `06_Analysis` folder.

```bash
obs r-dev log results/plot.png -m "Sensitivity analysis n=500"
```

### 3. Fetch Theory
Grab mathematical context from your Knowledge Base while coding.

```bash
obs r-dev context "Sobel Test"
```

### 4. Sync Drafts
Push a vignette or RMarkdown file to `02_Drafts` for prose editing in Obsidian.

```bash
obs r-dev draft vignettes/intro.Rmd
```
