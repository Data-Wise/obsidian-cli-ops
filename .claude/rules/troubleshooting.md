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

## Import Errors
- Install dependencies: `pip3 install -r src/python/requirements.txt`
- Check Python version: `python3 --version` (must be 3.9+)

## Link Resolution Issues
- Verify wikilinks are in standard format: `[[target]]` or `[[target|display]]`
- Check for relative path issues
- Review broken links: `obs stats <vault_id>`

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
