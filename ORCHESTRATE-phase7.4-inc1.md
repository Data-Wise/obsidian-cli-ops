# ORCHESTRATE: Phase 7.4 Increment 1 — Version Sync & Stale Cleanup

## Goal

Synchronize all version strings to `3.0.0-beta.2`, remove stale v2.x artifacts (TUI dep, dead scripts, deprecated SDK), consolidate pytest config, update TODOS.md, and extend version consistency tests.

## Pre-flight

```bash
git branch --show-current  # Must be feature/phase7.4-inc1
python3 -m pytest src/python/tests/ -q  # Baseline: 183 tests pass
```

## Steps

### Step 1: Version Bump — 3 files

**`pyproject.toml` line 7:**
- `version = "2.1.0"` → `version = "3.0.0-beta.2"`

**`package.json` line 3:**
- `"version": "2.0.0-beta"` → `"version": "3.0.0-beta.2"`

**`src/python/__init__.py` line 7:**
- `__version__ = "2.0.0-beta"` → `__version__ = "3.0.0-beta.2"`

**Commit:** `chore: sync version strings to 3.0.0-beta.2`

### Step 2: Clean stale deps & scripts in pyproject.toml

1. **Remove `tui` optional dep** (lines 52-55): delete the `tui = [...]` block
2. **Remove `tui` from `all`** (line 59): `"obsidian-cli-ops[gemini,ollama,local,tui]"` → `"obsidian-cli-ops[gemini,ollama,local]"`
3. **Fix Gemini SDK** (line 42): `"google-generativeai>=0.8.0"` → `"google-genai>=1.0.0"`
4. **Update keywords** (line 12): remove `"tui"` from keywords list
5. **Add `anthropic` optional dep** (new block after gemini):
   ```toml
   anthropic = [
       "anthropic>=0.40.0",
   ]
   ```
6. **Update `all`**: `"obsidian-cli-ops[gemini,anthropic,ollama,local]"`

### Step 3: Clean stale scripts in package.json

Remove these dead scripts:
- `"test:shell": "bash tests/test_r_dev.sh"` — R-Dev removed in v3.0
- `"test:all"` — references `test:shell`

Keep: `test`, `test:js`, `test:py`, `test:py:unit`, `test:py:integration`, `test:py:ai`, `test:coverage`, `lint`, `format`

**Commit:** `chore: remove stale TUI dep, fix Gemini SDK, clean dead scripts`

### Step 4: Consolidate pytest config

`pytest.ini` and `pyproject.toml [tool.pytest.ini_options]` both exist. Keep `pyproject.toml` as single source of truth.

1. **Merge unique settings** from `pytest.ini` into `pyproject.toml`:
   - Add `python_classes = ["Test*"]`
   - Add `python_functions = ["test_*"]`
   - Add `--strict-markers` and `--disable-warnings` to addopts
   - Add `markers` block
2. **Delete `pytest.ini`**

**Updated `[tool.pytest.ini_options]` in pyproject.toml:**
```toml
[tool.pytest.ini_options]
testpaths = ["src/python/tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short --strict-markers --disable-warnings"
asyncio_mode = "auto"
markers = [
    "unit: Unit tests for individual components",
    "integration: Integration tests across multiple components",
    "slow: Tests that take longer to run",
    "ai: Tests requiring AI providers (Ollama/HuggingFace)",
]
```

**Commit:** `chore: consolidate pytest config into pyproject.toml`

### Step 5: Extend version consistency tests

**`src/python/tests/test_version_consistency.py`** — add 3 new test methods:

```python
def test_pyproject_toml_matches(self):
    """pyproject.toml version should match obs.zsh VERSION."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    assert pyproject.exists()
    content = pyproject.read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match, "version not found in pyproject.toml"
    assert match.group(1) == self.version, (
        f"pyproject.toml version {match.group(1)!r} != obs.zsh {self.version!r}"
    )

def test_package_json_matches(self):
    """package.json version should match obs.zsh VERSION."""
    pkg = PROJECT_ROOT / "package.json"
    assert pkg.exists()
    content = pkg.read_text()
    match = re.search(r'"version":\s*"([^"]+)"', content)
    assert match, "version not found in package.json"
    assert match.group(1) == self.version, (
        f"package.json version {match.group(1)!r} != obs.zsh {self.version!r}"
    )

def test_init_py_matches(self):
    """__init__.py __version__ should match obs.zsh VERSION."""
    init = PROJECT_ROOT / "src" / "python" / "__init__.py"
    assert init.exists()
    content = init.read_text()
    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    assert match, "__version__ not found in __init__.py"
    assert match.group(1) == self.version, (
        f"__init__.py version {match.group(1)!r} != obs.zsh {self.version!r}"
    )
```

**Commit:** `test: extend version consistency to pyproject.toml, package.json, __init__.py`

### Step 6: Update TODOS.md

Replace the entire file with current state reflecting:
- Phase 7.1 (Simplification) ✅ Complete
- Phase 7.2 (AI Architecture) ✅ Complete
- Phase 7.3 (Testing & Polish) ✅ Complete
- Phase 7.4 (Testing & Release Prep) 🔄 In Progress
- Remove stale TUI/R-Dev references
- Remove completed items that are >2 months old
- Keep active backlog items

**Commit:** `docs: update TODOS.md to reflect Phase 7.1-7.3 completion`

## Verification

```bash
python3 -m pytest src/python/tests/ -q
# Expected: 186+ tests (183 existing + 3 new version checks)

# Verify no old versions remain
grep -rn "2.1.0\|2.0.0-beta" --include="*.py" --include="*.toml" --include="*.json" . | grep -v node_modules | grep -v .git
# Should return nothing
```

## Post-flight

```bash
gh pr create --base dev --title "Phase 7.4 Inc 1: Version sync & stale cleanup"
```
