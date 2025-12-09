# Configuration

The tool reads its settings from `~/.config/obs/config`.

## Standard Config

```bash
# Root directory of your Obsidian iCloud folder
OBS_ROOT="/Users/username/Library/Mobile Documents/iCloud~md~obsidian/Documents"

# List of Sub-Vaults to manage
VAULTS=("Research_Lab" "Knowledge_Base" "Life_Admin")
```

## Project Mapping

Mappings between R Projects and Obsidian folders are stored in `~/.config/obs/project_map.json`.

You can manage these via the CLI:
```bash
cd ~/projects/my-r-package
obs r-dev link Research_Lab/MyPackage
```
