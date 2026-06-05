# HANDOFF: automatic Homebrew release via GitHub Actions

> **Pivot (per request):** Homebrew release moves from a local script → **GitHub
> CI**, modeled on the Data-Wise ecosystem (`flow-cli`, `nexus-cli`, `aiterm`).
> The workflow below is new code, which branch-guard blocks on `dev`, so it's
> delivered as markdown. Materialize it in a session **inside this worktree**.

Worktree: `~/.git-worktrees/obsidian-cli-ops/feature-release-homebrew` · branch `feature/release-homebrew` (off `dev`).

## What this delivers

`.github/workflows/homebrew-release.yml` — on every published GitHub release, it
computes the source-tarball sha256 and calls the tap's reusable
`update-formula.yml` to bump + push the formula. Fully hands-off.

**Design = hybrid of the two ecosystem models:**
- **GitHub-tarball sha256 computation** from `flow-cli` (obs ships from GitHub, *not* PyPI like `nexus-cli`).
- **Reusable `update-formula.yml` call** from `nexus-cli`/`aiterm`/`atlas` (DRYer than flow-cli's inlined copy; App-token auth, auto_merge/PR, manifest handling for free).

## ⚠️ Two prerequisites (one-time)

**1. Repo secrets** — this repo currently has none. Add the GitHub App auth (same
"Data-Wise Homebrew Automation" app `flow-cli` uses):

```bash
gh secret set APP_ID --repo Data-Wise/obsidian-cli-ops --body "<app-id>"
gh secret set APP_PRIVATE_KEY --repo Data-Wise/obsidian-cli-ops < app-private-key.pem
# (or set HOMEBREW_TAP_GITHUB_TOKEN as a PAT fallback)
```

**2. Transitive venv resources (one-time, NOT done by this workflow).** The
formula installs via `virtualenv_install_with_resources`, which needs the FULL
dependency tree as `resource` blocks. The v3.2.1 formula only has the 6 core
deps; the transitive deps (markdown-it-py, mdurl, pygments, certifi, idna,
urllib3, charset-normalizer, …) must be added **once**:

```bash
cd "$(brew --repository data-wise/tap)"
git fetch && git checkout feature/obs-v3.2.1-venv   # branch with v3.2.1 + filled sha
brew update-python-resources data-wise/tap/obsidian-cli-ops
brew install --build-from-source data-wise/tap/obsidian-cli-ops   # validate
brew audit --strict obsidian-cli-ops
# then merge feature/obs-v3.2.1-venv → tap main
```

After that, **this workflow handles every future release automatically** —
resources only need regenerating when `requirements.lock` changes.

## Materialize the workflow (run in a worktree session)

```bash
mkdir -p .github/workflows
# paste the YAML below into .github/workflows/homebrew-release.yml
git add .github/workflows/homebrew-release.yml
git commit -m "ci: automatic Homebrew release on published release (App auth)"
gh pr create --base dev
# cleanup: git rm HANDOFF-release-homebrew.md before the PR (working artifact)
```

For the already-published **v3.2.1**, trigger it manually after the secrets +
one-time resources are in place:
```bash
gh workflow run homebrew-release.yml -f version=3.2.1 -f auto_merge=true
```

## The workflow

```yaml
name: Homebrew Release

# Auto-updates Data-Wise/homebrew-tap when an obsidian-cli-ops release is
# published. Models the ecosystem (nexus-cli/aiterm) via the tap's reusable
# update-formula.yml, with flow-cli's GitHub-tarball sha256 step (obs is not on
# PyPI). Requires repo secrets APP_ID + APP_PRIVATE_KEY (GitHub App auth).
#
# Scope: bumps the formula `url` + main-package `sha256` only. Python `resource`
# blocks are static; regenerate by hand when requirements.lock changes:
#   brew update-python-resources data-wise/tap/obsidian-cli-ops

on:
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to release (e.g., 3.2.1)'
        required: true
        type: string
      auto_merge:
        description: 'Auto-merge formula update (true = push to tap main)'
        required: false
        type: boolean
        default: true

jobs:
  prepare:
    name: Prepare Release Info
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.release.outputs.version }}
      sha256: ${{ steps.release.outputs.sha256 }}
    steps:
      - name: Resolve version + source-tarball SHA256
        id: release
        env:
          EVENT_NAME: ${{ github.event_name }}
          INPUT_VERSION: ${{ github.event.inputs.version }}
        run: |
          if [ "$EVENT_NAME" = "workflow_dispatch" ]; then
            VERSION="$INPUT_VERSION"
          else
            VERSION="${GITHUB_REF#refs/tags/}"
          fi
          VERSION="${VERSION#v}"
          echo "version=$VERSION" >> "$GITHUB_OUTPUT"

          TARBALL="https://github.com/Data-Wise/obsidian-cli-ops/archive/refs/tags/v${VERSION}.tar.gz"
          SHA256="$(curl -sL --retry 3 --retry-delay 2 "$TARBALL" | sha256sum | cut -d' ' -f1)"
          if [ -z "$SHA256" ] || [ "${#SHA256}" -ne 64 ]; then
            echo "::error::SHA256 calculation failed for $TARBALL (got '$SHA256')"
            exit 1
          fi
          echo "sha256=$SHA256" >> "$GITHUB_OUTPUT"
          echo "Resolved v$VERSION -> $SHA256"

  update-homebrew:
    name: Update Homebrew Formula
    needs: prepare
    uses: Data-Wise/homebrew-tap/.github/workflows/update-formula.yml@main
    with:
      formula_name: obsidian-cli-ops
      version: ${{ needs.prepare.outputs.version }}
      sha256: ${{ needs.prepare.outputs.sha256 }}
      source_type: github
      auto_merge: ${{ github.event_name == 'release' || github.event.inputs.auto_merge == 'true' }}
    secrets:
      # GitHub App auth preferred (short-lived, scoped); PAT is the fallback.
      app_id: ${{ secrets.APP_ID }}
      app_private_key: ${{ secrets.APP_PRIVATE_KEY }}
      tap_token: ${{ secrets.HOMEBREW_TAP_GITHUB_TOKEN }}
```

## Why this over the earlier local script

| | Local script (superseded) | This workflow |
|---|---|---|
| Trigger | you run it | automatic on release publish |
| Auth | your git creds | GitHub App token (no PAT to rotate) |
| Consistency | obs-only | same pattern as flow-cli/nexus-cli/aiterm |
| Resources | `--update-resources` flag | one-time manual (same `brew update-python-resources`) |

The local `release-homebrew.sh` is still available in this branch's history as an
offline/manual fallback, but the workflow is now the primary path.

## Notes / gotchas

- **`source_type: github`** makes the reusable workflow bump `/v<old>.tar.gz` → `/v<new>.tar.gz` and the first `sha256` (the main package) — never a resource sha.
- **obs is hand-crafted** (not in the tap `generator/manifest.json`), so the reusable workflow's manifest step no-ops — correct.
- **auto_merge** pushes straight to tap `main` on a real release; set `false` on dispatch to get a tap PR instead.
- The workflow does NOT regenerate resources — by design. A dependency bump means: update `requirements.lock` → run `brew update-python-resources` once → commit the formula.
