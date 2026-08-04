# Flow — Claude Code plugin

This is the **Claude Code surface** of [Flow](../README.md), the governed AI-DLC
methodology: the `/flow-*` slash commands, the phase agents (Scope → Shape →
Build → Ship), and the governance hooks.

> This directory is a **build artifact**. It is regenerated from the engine
> assets (`src/flow_aidlc/engine/claude/`) by `flow plugin build`. Don't edit it
> by hand — edit the engine and rebuild.

## Composition: plugin **+** `flow init`

Flow has two halves that work together:

| Half | Provides | How you get it |
|---|---|---|
| **This plugin** | the Claude Code surface: `/flow-*` commands, phase agents, hooks | `/plugin install flow` |
| **The `flow` CLI** | per-project scaffolding (`flow init`) and the quality gate (`flow check`) | `pipx install flow-aidlc` |

The hooks and commands in this plugin operate on the **`.flow/` instance** that
`flow init` creates in your repo. Install the plugin **and** run `flow init` —
neither half is useful without the other.

## Install

From this repo (local marketplace):

```
# In Claude Code:
/plugin marketplace add /absolute/path/to/flow-aidlc
/plugin install flow
```

`/plugin marketplace add` reads `.claude-plugin/marketplace.json` at the repo
root, which lists this one plugin (`source: "./plugin"`).

Then, in your target repo:

```
pipx install flow-aidlc      # the CLI half
cd your-repo
flow init                    # scaffold .flow/ (+ knowledge/, config)
flow doctor                  # verify the install
```

Now the `/flow-*` commands and the hooks act on that `.flow/` instance.

## What's inside

- `commands/` — the `/flow-*` slash commands.
- `agents/` — the phase agents (scope / shape / build / review / knowledge).
- `hooks/` — the hook scripts and `hooks.json` (wired to `SessionStart`,
  `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`,
  `PreCompact`). Scripts resolve via `${CLAUDE_PLUGIN_ROOT}/hooks/`.
- `.claude-plugin/plugin.json` — the plugin manifest.

## Regenerate

```
flow plugin build            # rewrites ./plugin from the engine
flow plugin build --out /tmp/x   # build elsewhere (idempotent)
```
