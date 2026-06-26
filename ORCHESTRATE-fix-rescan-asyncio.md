# Fix rescan_vault asyncio crash (#62) + async-run guard + stale-server detection (#53) — Orchestration Plan

> **Branch:** `feature/fix-rescan-asyncio`
> **Base:** `dev`
> **Worktree:** `~/.git-worktrees/obsidian-cli-ops/feature-fix-rescan-asyncio`
> **Source:** GitHub issue [#62](https://github.com/Data-Wise/obsidian-cli-ops/issues/62) (detailed root-cause), related [#53](https://github.com/Data-Wise/obsidian-cli-ops/issues/53), [#52](https://github.com/Data-Wise/obsidian-cli-ops/issues/52)
> **Version Target:** v4.0.2 (patch — bug fix) or fold into v4.1.0

## Objective

`rescan_vault` MCP tool crashes on every call (`asyncio.run() cannot be called from a running event loop`), leaving the obs DB/search index silently stale after every write tool. Fix the crash, add a static guard so the bug class can't recur, and (enhancement) make a stale in-process MCP server detectable so this confusion doesn't repeat.

## Root Cause (confirmed)

`src/python/mcp_server.py:1070` — `rescan_vault` is a **sync** `@mcp.tool()` calling
`asyncio.run(vault_manager.scan_vault(...))`. FastMCP dispatches the handler inside an
already-running event loop, so `asyncio.run()` raises `RuntimeError`. The tool *always*
fails → reads (`search_notes`, `unified_search`, graph metrics) return stale/empty
results after writes, with no working refresh from the MCP surface.

- **Isolated:** `asyncio.run(` appears **exactly once** in the entire MCP server.
- **Fix is unconditional:** `vault_manager.scan_vault` is genuinely async
  (`await self.scanner.scan_vault(...)` at `core/vault_manager.py:167`), so
  `async def` + `await` is correct and idiomatic for FastMCP.
- **CLI path is unaffected:** `obs scan` calls the same coroutine from a sync caller
  where `asyncio.run()` is valid. Only the MCP (in-loop) host breaks. (Workaround
  for users today: `obs scan <vault>`.)

## Phase Overview

| Phase | Increment | Priority | Effort | Status |
|-------|-----------|----------|--------|--------|
| 1 | Fix #62 (async handler) + live-loop regression test | High | ~1h | |
| 2 | Doctor AST guard `mcp-async-run` + unit test | High | ~1h | |
| 3 | (Enhancement) #53 server version / restart-recommended | Medium | ~1.5h | |
| 4 | Docs & Discoverability | Required | ~45m | |

Phase 1 is **shippable on its own** as the bug fix. Phases 2–4 are additive on the
same PR (or split if reviewer prefers a minimal patch).

---

## Phase 1: Fix the crash (#62)

**Scope:** Convert `rescan_vault` to an async handler and `await` the scan. Rewrite its
tests so they actually exercise the failure mode.

- [ ] 1.1 In `src/python/mcp_server.py`, change `def rescan_vault(vault_id: str)` →
      `async def rescan_vault(vault_id: str)`; replace
      `result = asyncio.run(vault_manager.scan_vault(...))` with
      `result = await vault_manager.scan_vault(vault["path"], vault["name"])`.
      Keep `_resolve_vault()` routing and the success/error message format unchanged.
- [ ] 1.2 **Rewrite the rescan tests** at `src/python/tests/test_mcp_server.py:504-533`.
      The current tests call `mcp_mod.rescan_vault(...)` **synchronously** → no running
      loop → `asyncio.run()` succeeds → **the bug is invisible**. (Same class as the
      "fake-schema test masked a real doctor crash" trap from v4.0.0.) New tests MUST
      drive the handler **inside a live event loop**:
      - Define an inner `async def _call(): return await mcp_mod.rescan_vault(vault_id)`
        and run via `asyncio.run(_call())` — the plain pattern already used at
        `test_mcp_server.py:134` and `:192`.
      - **Do NOT** use `@pytest.mark.asyncio` — pytest-asyncio is not in the CI test
        deps and strict-markers would reject an unregistered `asyncio` marker
        (see memory: v3.2.3 CI trap).
      - Update the AsyncMock assertion test (currently `scan_mock.assert_awaited_once()`
        called synchronously) to await through the real async handler.
      - Add a guard test asserting a successful return string contains
        `Rescanned`/notes/links so a future regression to a no-op is caught.
- [ ] 1.3 Confirm `import asyncio` is still needed (it is — for the test driver; the
      handler no longer calls `asyncio.run`).

**Key files:**
- `src/python/mcp_server.py` (update — line ~1051-1078)
- `src/python/tests/test_mcp_server.py` (update — TestRescan block ~504-533)

**Noted follow-up (do NOT gate Phase 1 on it):** `await`ing the scan in-loop blocks the
MCP event loop for the scan duration (5–60s on large vaults) *iff* `scanner.scan_vault`
does sync file I/O without yielding. That is a performance question, not the crash. If
it proves to block, offload via a worker-thread helper
(`anyio.to_thread.run_sync` / `loop.run_in_executor`) in a follow-up — the thread-offload
pattern's correctness depends on FastMCP dispatch internals, so keep it out of the fix PR.

---

## Phase 2: Durable guard — `mcp-async-run` doctor check

**Scope:** Mirror the existing `_check_mcp_tool_resolvers` AST check so any sync
`@mcp.tool` handler calling `asyncio.run(` fails `obs doctor`. Catches the whole bug
class statically.

- [ ] 2.1 In `src/python/core/doctor.py`, add `_collect_mcp_async_run_offenders(source)`
      modeled on `_collect_*` for `mcp-tool-resolvers` (lines ~442-476): AST-walk each
      `@mcp.tool` `FunctionDef` (reuse the `is_mcp_tool` decorator matcher); flag it if
      it is a **sync** def (not `AsyncFunctionDef`) AND its body contains a `Call` to
      `asyncio.run`. Return `"<tool>()"` names.
- [ ] 2.2 Add `_check_mcp_async_run(server_path)` returning a `DoctorResult`
      (`id="mcp-async-run"`, `layer="mcp"`), and register it in `_check_mcp()` next to
      `mcp-tool-resolvers` (~line 435). skip/error/pass/fail states matching the sibling.
- [ ] 2.3 Add unit tests in `src/python/tests/test_*doctor*` (match existing doctor test
      file): a `pass` case (current fixed source) and a `fail` case (synthetic source
      string with a sync `@mcp.tool` calling `asyncio.run`).

**Key files:**
- `src/python/core/doctor.py` (update — new check + registration)
- existing doctor test file (update — 2 cases)

---

## Phase 3: Enhancement — detect a stale MCP server (#53)

**Scope:** The reason #62 confusion happened: a v4.0.0-fixed tool still failed because
the *running* in-process server predated the fix, and nothing surfaces the server's
version. Make it observable.

- [ ] 3.1 Add `version` / `started_at` to `get_bridge_status` output (or a dedicated
      `server_info` `@mcp.tool`). Read the installed package version the same way the
      `obs version` path does (single source — do not hardcode).
- [ ] 3.2 Optional `restart_recommended: true` when the running server's version differs
      from the installed CLI version, with a "restart the host app" hint.
- [ ] 3.3 Unit test: status surfaces a version string; mismatch path sets the flag.
- [ ] **Decision gate:** if reviewer wants a minimal patch, split Phase 3 into its own
      PR/issue and ship Phases 1–2 + 4 first.

**Key files:**
- `src/python/mcp_server.py` (update — `get_bridge_status` ~1132 or new tool)
- test file (update)

---

## Documentation & Discoverability (REQUIRED — final phase)

- [ ] CHANGELOG `[Unreleased]` (`docs_mkdocs/changelog.md`) — fix #62, doctor guard, #53.
- [ ] MCP tool reference / docstrings — note `rescan_vault` is now async; if #53 adds a
      field/tool, document it.
- [ ] REFCARD / MCP tool tables — update if tool count or signatures changed
      (`core/doc_counts.py` is the single source — run `./scripts/validate-counts.sh`).
- [ ] `obs doctor` docs — list the new `mcp-async-run` check under the mcp layer.
- [ ] N/A: tutorials/website nav (no new user-facing CLI command) — mark explicitly.
- [ ] Count bumps if any tool added (#53 path): `.STATUS`, plugin/version surfaces;
      `pytest src/python/tests/test_doc_counts.py` green.

---

## Friction Prevention

- **Context first:** read this file + issue #62 (full root-cause) BEFORE editing.
- **Verify location:** confirm CWD is the worktree
  (`~/.git-worktrees/obsidian-cli-ops/feature-fix-rescan-asyncio`), not the main repo.
- **The test must fail pre-fix:** before applying the 1.1 handler change, run the new
  live-loop test against the *current* sync handler and confirm it raises the
  `asyncio.run() ... running event loop` error. If it passes, the test isn't exercising
  the bug (the original trap) — fix the test, not the assertion.
- **Run pytest from `src/python/`** (not repo root) to avoid import errors.
- **No autonomous phase jumps:** STOP and confirm after each phase.

## Acceptance Criteria

- [ ] `rescan_vault` succeeds when called inside a running event loop (no `RuntimeError`).
- [ ] A regression test **fails against the old sync+`asyncio.run` handler** and passes
      after the fix (proves it exercises the real failure mode).
- [ ] After a real rescan via MCP, `search_notes`/`list_notes`/graph metrics reflect
      on-disk changes (the original #62 symptom is gone).
- [ ] `obs doctor` includes `mcp-async-run`; it FAILs on a synthetic offender and PASSes
      on the fixed tree.
- [ ] (#53, if kept) a client can read the running server's version without restarting;
      a stale server surfaces `restart_recommended`.
- [ ] Full suite green: `pytest src/python/tests/` + `npx jest`.
- [ ] Documentation & Discoverability phase complete.

## Commit Strategy

- Phase 1: `fix(mcp): rescan_vault await coroutine instead of asyncio.run (#62)`
- Phase 1 tests: `test(mcp): drive rescan_vault inside a live event loop (regression for #62)`
- Phase 2: `feat(doctor): mcp-async-run AST guard against asyncio.run in sync @mcp.tool`
- Phase 3: `feat(mcp): expose running-server version + restart_recommended (#53)`
- Phase 4: `docs: changelog + mcp tool/doctor docs for rescan fix`

## Verification

After each phase (run from `src/python/`):

```bash
pytest src/python/tests/test_mcp_server.py -v        # rescan + (later) #53
pytest src/python/tests/ -q                          # full unit suite
npx jest                                              # zsh/install + cli tests
python3 src/python/obs_cli.py doctor <a-real-vault>  # Phase 2: mcp-async-run present
```

**CRITICAL — restart the MCP host before "confirming fixed":** an in-process MCP server
keeps the OLD code in memory (this is exactly what masked the v4.0.0 fix and motivated
#53). Reload the MCP server / restart the host app (Cowork/Claude) before asserting the
live tool works. Do not validate #62 against a server started before this branch.

## Session Instructions

### Context

You are in the **obsidian-cli-ops worktree** for the rescan-asyncio fix. Issue #62 has
the full root-cause; this file has the phase plan.

### How to Start

```bash
cd ~/.git-worktrees/obsidian-cli-ops/feature-fix-rescan-asyncio
claude
```

On session start, paste:

> Read `ORCHESTRATE-fix-rescan-asyncio.md` and issue #62. Start Phase 1. Before changing
> the handler, write the live-loop test and confirm it reproduces the crash.

### Phase-by-Phase

1. Read current state of each file listed in the phase.
2. Implement per this plan (test-first for Phase 1).
3. Run verification after each phase.
4. Commit in logical groups (see Commit Strategy).
5. STOP and confirm before the next phase.

### Cleanup (at merge)

Delete this `ORCHESTRATE-*.md` before merging `feature/fix-rescan-asyncio` → `dev`
(ORCHESTRATE files are feature-branch working artifacts).
