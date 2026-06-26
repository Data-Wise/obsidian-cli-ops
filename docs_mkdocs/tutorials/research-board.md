# Tutorial — The Research Board

`obs research board` renders a **deterministic dashboard of your manuscripts and programs** from
[atlas](https://github.com/Data-Wise/atlas) state into your Obsidian vault. Re-running on unchanged state
produces **zero diff**, and it writes only between markers — your hand-written prose is safe.

## Prerequisites

`atlas` installed, with research `.STATUS` files tagged (`kind: manuscript|program`). See the atlas
[Research Registry tutorial](https://data-wise.github.io/atlas/tutorials/research-registry/).

## Render to stdout

```bash
obs research board                 # manuscripts + programs
obs research board --kind program  # one kind
```

## Write into the vault (marker-bounded)

```bash
obs research board --out ~/vault/00_meta/_RESEARCH-BOARD.md
obs research board --out ~/vault/00_meta/_RESEARCH-BOARD.md --dry-run   # show changes, write nothing
```

The board is wrapped in `<!-- obs:board:start -->` … `<!-- obs:board:end -->`; only that region is
replaced (atomic write via `os.replace`). Put your own notes outside the markers.

## What it shows

A table per kind (Manuscripts, Programs, …) with venue, status icon, an 8-cell progress bar, and the next
action — sorted deterministically (priority → progress → name). Status icons: 🔴 blocked/deadline ·
🟡 paused/wip · 🟢 active/ready.

## Schedule it (drift guard)

`--dry-run` exits non-zero when the rendered board differs from the file on disk — wire it into
launchd/cron to catch staleness, then add a write step on a cadence.

## How it fits

`.STATUS` → **atlas** (`project list --json`) → **`obs research board`** → vault dashboard. The
per-project mirror map is [`.obs/sync.yml`](../obs-sync-yml.md).
