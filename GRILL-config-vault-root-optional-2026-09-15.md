# GRILL: Make vault.root optional in config_loader.ObsConfig

**Interrogates:** [SPEC-config-vault-root-optional-2026-09-15.md](SPEC-config-vault-root-optional-2026-09-15.md)
**Date:** 2026-09-15
**Owner:** @dtofighi

Convergent interrogation of the spec before implementation. 5 load-bearing branches resolved; wrapped up at the first milestone checkpoint (spec is small and well-scoped).

## Decision Ledger

| # | Branch | Decision |
|---|---|---|
| 1 | obs config validate semantics for a vault-less (e.g. board-only) config | Keep vault-centric contract (b): validate still fails without vault.root; only load()'s silent full-discard is fixed so show/other readers still see the rest of the doc. |
| 2 | Implement now vs. hold as backlog (benefit honesty -- no user has hit this gap yet) | Implement now: fix is small, consumer audit already proved zero blast radius outside config_loader.py; cheaper now than re-deriving the audit later. |
| 3 | templates_resolved behavior when both root and templates are unset | Raise ValueError at the property -- fail loudly at the one call site (cmd_show) rather than return a look-alike None further from the cause. |
| 4 | _to_yaml() blast radius: unconditionally writes root: "{cfg.root}" (would emit literal "None" for a root-less config) | Add a defensive assert/guard now, even though today's only caller (cmd_migrate) always supplies a root-set config -- closes the landmine this spec's own change opens. |
| 5 | Landing path for this small, already-audited change | Small standalone commit directly on dev -- matches how the two prior related fixes this session landed (e1f5c6d, 083d78d); no worktree/PR ceremony. |

## Open Questions

- Exact wording/format of test cases for the new vault-less config_loader.py test cases (deferred to implementation -- test plan already outlined in the SPEC).
- Whether doctor.py needs any awareness of a vault-less config (not raised as a branch; doctor.py checks the vault DB, not config_loader.ObsConfig, so likely N/A -- flagged for a quick sanity check during implementation, not before).
