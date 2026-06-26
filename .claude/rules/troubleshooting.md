---
paths:
  - "**"
---

# Troubleshooting

## Python CLI Not Found
- Check that `src/python/obs_cli.py` exists
- Verify file is executable: `chmod +x src/python/obs_cli.py`
- Run from project root directory

## Database Errors
- Initialize database: `python3 src/python/obs_cli.py db init`
- Check permissions on `~/.config/obs/`
- Verify SQLite3 is installed

## Import Errors (`ModuleNotFoundError`)
- Deps live in an **isolated venv**, not system Python. Provision it:
  `./install.sh` (creates `~/.local/share/obs/venv` from `requirements.lock`)
  or `brew reinstall obsidian-cli-ops` (Homebrew `libexec/venv`).
- A `[obs] WARN: ... ambient python3 ... deps may be missing` line means the
  launcher fell through to the ambient interpreter — run one of the above.
- Force a specific interpreter with `export OBS_PYTHON=/path/to/python` (tier 1).
- Check Python version: `python3 --version` (must be 3.9+)

## Link Resolution Issues
- Verify wikilinks are in standard format: `[[target]]` or `[[target|display]]`
- Check for relative path issues
- Review broken links: `obs stats <vault>`

## Deleted/Renamed Notes Still Show Up
- A plain `obs scan` is **additive** — it adds and updates notes but never removes
  rows. A note deleted or renamed on disk lingers in the index as a "ghost" and keeps
  appearing in `obs search`, stats counts, and as a link target.
- Fix: re-scan with `obs scan <vault> --prune`. This sweeps rows whose path is gone
  from disk (cascading to their links, tags, metrics, and embeddings).
- Diagnose first without changing anything: `obs doctor --layer sync` flags `sync-ghosts`
  (rows whose file is gone) and gives a `sync-drift` summary (`disk=N db=M (X ghost ...)`).
- Safety: `--prune` is skipped with a warning if the scan sees zero files (e.g. a
  mis-pointed path or an un-materialised iCloud vault), so it won't wipe the index.

## AI Re-embeds Everything on Every Scan
- This was a bug fixed in v4.2.0. Previously each `obs scan` re-inserted every note
  unconditionally, and the `ON DELETE CASCADE` from the row replace wiped each note's
  `note_embeddings` row — so the next AI op recomputed the whole cache (latency + paid-API cost).
- Now the scanner compares each file's `content_hash` against the stored one and **skips
  unchanged notes**, leaving their embeddings (and links/tags) intact. The scan summary
  reports an "unchanged" count.
- If you still see full re-embedding, confirm content actually changed (the hash covers
  body text) and that you are on v4.2.0+ (`obs version`).

## Performance Considerations

### Database Optimization
- Indexes are created automatically via schema
- Use `VACUUM` periodically to reclaim space
- Consider `ANALYZE` for query optimization

### Scanning Large Vaults
- Use `--verbose` to monitor progress
- Scanner processes ~100 notes/second
- Graph metrics calculation is O(n²) for centrality

### Memory Usage
- NetworkX graphs held in memory during analysis
- Large vaults (>10k notes) may need 1-2GB RAM
- Consider batch processing for very large vaults

## Security and Privacy

### Local-First Design
- All data stored locally in SQLite
- No data sent to cloud by default
- AI features use local models (100% private)

### AI Privacy (Phase 2)
- **Default providers are 100% local** (HuggingFace, Ollama)
- No API keys required for default setup
- No data sent to external servers
- Models run on your machine
- Complete privacy and offline capability

### API Key Management (Optional)
- Paid APIs (Claude, Gemini) are **optional** and commented out
- If using paid APIs, store keys in environment variables
- Never commit API keys to git
- Use `.env` file for local development
