# Spec: Vault Reorganization Path Migration (Issue #86)

## Objective
Update all hardcoded and default references in the `obsidian-cli-ops` codebase to reflect today's vault consolidation:
1. Retire the root-level `Software_Engineering/` vault folder in favor of `Engineering/`.
2. Retire the root-level `00_meta/` and `Research_Lab/` vault folders.
3. Migrate `Research_Lab/` references to `Research/` (for research projects) and `Engineering/packages/` (for packages).
4. Relocate the fallback research board output path from `00_meta/` to `Engineering/`.

## Tech Stack
* Language: ZSH (aliases / shell commands), Python 3.9+ (board path resolution, tests)
* Configuration: JSON (project maps)

## Commands
* Test execution: `pytest src/python/tests/test_board.py`
* Verify aliases: `source src/obs.zsh`
* Board path dry-run: `obs board refresh --dry-run`

## Project Structure
* `config/example.project_map.json` &rarr; Example mappings from code workspace directories to Obsidian folders.
* `src/python/core/board.py` &rarr; Python logic for action board path resolution.
* `src/python/tests/test_board.py` &rarr; Pytest cases verifying correct board resolution and path construction.

## Code Style
Any Python path manipulations must use standard `pathlib.Path` objects. ZSH configuration variables should expand consistently.

```python
# pathlib.Path manipulation
fallback_path = vault_root / "Engineering" / "_ACTION-BOARD.md"
```

## Testing Strategy
1. **Unit Tests:** Update unit tests in `src/python/tests/test_board.py` that verify default action board resolution to test the new fallback (`Engineering/_ACTION-BOARD.md`) and remove assertions checking for root-level `00_meta/` fallbacks.
2. **Integration Verification:** Run `obs board refresh --dry-run` to ensure it resolves the correct board path under the consolidated layout.

## Boundaries
* **Always do:** Preserve shortest-path wikilink behavior and resolve paths relative to the vault root directory.
* **Ask first:** Modifying core `obs` subcommands not specified in this spec.
* **Never do:** Commit production releases or tag main branch without explicit user sign-off.

## Success Criteria
- [x] No occurrences of `Software_Engineering` or `Research_Lab` remain in `config/` or `src/`.
- [x] `config/example.project_map.json` maps packages to `Engineering/packages/` and research projects to `Research/`.
- [x] `src/python/core/board.py` resolves fallback paths to `Engineering/_ACTION-BOARD.md` instead of `00_meta/_ACTION-BOARD.md`.
- [x] All `pytest` tests pass successfully (520 passed).

## Open Questions
1. ~~Do you agree with using `Engineering/_ACTION-BOARD.md` as the default fallback dashboard path when `Research/00_meta/_ACTION-BOARD.md` is not present?~~ Resolved: yes, implemented as the new default.
