# Managing Configuration with `obs config`

> **TL;DR** (30 seconds)
>
> - **What:** Inspect, validate, migrate, create, and edit the `obs` config (unified YAML)
> - **Why:** One place for AI provider keys, paths, and preferences — no more scattered dotfiles
> - **How:** `obs config show` · `obs config validate` · `obs config init` · `obs config migrate` · `obs config edit`
> - **Next:** see [Cookbook → Manage Configuration](../cookbook.md#manage-configuration)
{ .tldr }

**Level:** 🟢 Beginner | **Time:** ~10 min | **Commands:** `obs config show|validate|migrate|init|edit`

---

## What You'll Learn

- Print the active config and see which file it loaded from
- Validate the config file and surface errors
- Create a fresh config interactively (`init`)
- Migrate a legacy `obs` / `nexus-cli` config to the unified YAML format
- Open the config in your editor (`edit`)

---

## Prerequisites

- `obs` v4.0.0+ (shipped with the nexus-cli absorption; available to Homebrew users)
- Config lives at `~/.config/obs/` by default

---

## Step 1 — Show the current config

```bash
obs config show
```

Prints the merged config and the path of the file it was loaded from, so you always
know which source is active.

---

## Step 2 — Validate

```bash
obs config validate
```

Reports any schema or structure errors in the config file. Run this after a manual
edit or before reporting a bug.

---

## Step 3 — Create a fresh config

```bash
obs config init
```

Interactive wizard that writes a new unified config from scratch. Use it on a fresh
install or to reset a corrupted file.

---

## Step 4 — Migrate a legacy config

If you have an old `obs` or `nexus-cli` config, convert it to the unified format:

```bash
obs config migrate                  # writes to ~/.config/obs/ by default
obs config migrate --target-dir ~/my-config   # write elsewhere
```

| Argument | Description |
|----------|-------------|
| `--target-dir` | Where to write the unified config (default: `~/.config/obs/`) |

---

## Step 5 — Edit in your editor

```bash
obs config edit
```

Opens the config file in `$EDITOR`. After saving and closing, run
`obs config validate` to confirm the change is well-formed.

---

## Common tasks

| Goal | Command |
|------|---------|
| Where is my config? | `obs config show` |
| Did my edit break anything? | `obs config validate` |
| Fresh start | `obs config init` |
| Move an old `nexus-cli` config over | `obs config migrate --target-dir ~/.config/obs` |
| Tweak a value by hand | `obs config edit` → `obs config validate` |

---

## Next Steps

- [CLI Reference → `obs config`](../cli-reference.md#obs-config-show) — all subcommands
- [AI Setup Guide](../ai-setup.md) — configure AI providers
- [Cookbook → Manage Configuration](../cookbook.md#manage-configuration) — copy-paste recipes
