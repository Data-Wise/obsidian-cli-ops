# Power-User Search with `obs search`

> **TL;DR** (30 seconds)
>
> - **What:** Find notes by title across all registered vaults
> - **Why:** Jump to the right note fast, then hand the result to AI features
> - **How:** `obs search "<query>" --vault Research --limit 5 --json`
> - **Next:** pipe JSON to scripts, or feed a note ID to `obs ai similar`
{ .tldr }

**Level:** 🟢 Beginner | **Time:** ~5 min | **Command:** `obs search`

---

## What You'll Learn

- Search by title across all vaults (or one vault)
- Cap result count with `--limit`
- Get machine-readable output with `--json`
- Pipe results into scripts or into AI features

---

## Step 1 — Basic title search

```bash
obs search "causal mediation"
```

Matches note **titles** across every registered vault. Returns up to 20 hits by default.

---

## Step 2 — Scope to one vault

```bash
obs search "causal mediation" --vault Research
# short form:
obs search "causal mediation" -v Research
```

Limits results to a single vault by name or ID.

---

## Step 3 — Cap the result count

```bash
obs search "meeting" --limit 5
# short form:
obs search "meeting" -n 5
```

Useful when a query is broad and you only want the top few.

---

## Step 4 — Machine-readable output

```bash
obs search "causal" --json
```

Returns a JSON array — perfect for scripting or piping into `jq` / `python3`:

```bash
obs search "causal" --json | python3 -c "
import json, sys
for n in json.load(sys.stdin):
    print(f\"{n['id']}  {n['title']}\")
"
```

---

## Step 5 — Hand a result to AI

Search gives you a note ID; pass it to an AI feature for deeper work:

```bash
obs search "collider bias" --json | python3 -c "
import json, sys
print(json.load(sys.stdin)[0]['id'])
" | xargs -I{} obs ai similar {} --limit 5
```

---

## Next Steps

- [CLI Reference → `obs search`](../cli-reference.md#obs-search) — all flags
- [AI Features tutorial](../tutorials/ai-features.md) — `obs ai similar`, `gaps`, `refactor`
- [Cookbook → Initialize or Rebuild the Database](../cookbook.md#initialize-or-rebuild-the-database) — when search returns nothing
