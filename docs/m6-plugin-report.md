# M6 — Claude Code plugin packaging: report

Package the Flow engine's Claude Code assets as an installable **Claude Code
plugin**, produced by a generator so `plugin/` stays a build artifact with a
single source of truth (`src/flow_aidlc/engine/claude/`).

## 1. The plugin schema I observed (not guessed)

I inspected real, installed plugins under `~/.claude/plugins/` rather than
inventing a format.

### Plugin manifest — `.claude-plugin/plugin.json`

Reference: `superpowers` plugin, cited from
`~/.claude/plugins/cache/claude-plugins-official/superpowers/6.2.0/.claude-plugin/plugin.json`:

```json
{
  "name": "superpowers",
  "description": "Core skills library for Claude Code: ...",
  "version": "6.2.0",
  "author": { "name": "Jesse Vincent", "email": "jesse@fsck.com" },
  "homepage": "...", "repository": "...", "license": "MIT",
  "keywords": ["skills", "tdd", ...]
}
```

`claude-security`
(`~/.claude/plugins/marketplaces/claude-plugins-official/plugins/claude-security/.claude-plugin/plugin.json`)
confirms the minimal required set is `name` + `version` + `description` +
`author` (object with `name`, optional `email`). We emit exactly those four.

### Commands & agents — conventional flat directories, Markdown with frontmatter

Commands and agents are **auto-discovered** from `commands/` and `agents/`
directories at the plugin root — there is no manifest listing them. Confirmed by:

- `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/pr-review-toolkit/commands/review-pr.md`
  — a command is a `.md` with YAML frontmatter (`description`, `argument-hint`,
  `allowed-tools`).
- `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/claude-security/agents/scan-inventory.md`
  — an agent is a `.md` with frontmatter (`name`, `description`, `model`,
  `tools`, ...).

Both dirs are **flat** in the reference plugins. The engine nests agents by
phase (`agents/scope/`, `agents/shape/`, ...), so the generator flattens them;
basenames are unique across the engine, so this is loss-free. The engine's
command/agent `.md` files already carry the right frontmatter, so they are
copied **verbatim**.

### Hooks — `hooks/hooks.json` + scripts addressed via `${CLAUDE_PLUGIN_ROOT}`

Reference: `superpowers/.../hooks/hooks.json` and
`.../claude-security/hooks/hooks.json`. Format:

```json
{
  "description": "…",
  "hooks": {
    "SessionStart": [
      { "matcher": "startup|clear|compact",
        "hooks": [ { "type": "command",
                     "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd\" session-start" } ] }
    ]
  }
}
```

Key observations: the top-level shape is `{ "description", "hooks": { <Event>: [ { matcher?, hooks: [...] } ] } }`
— identical to the engine's `settings.json` `hooks` block — and hook scripts are
referenced via the **`${CLAUDE_PLUGIN_ROOT}/hooks/...`** convention (the plugin
root, not `.claude/`).

### Marketplace manifest — `.claude-plugin/marketplace.json`

Reference: `superpowers/.claude-plugin/marketplace.json` and the official
directory `~/.claude/plugins/marketplaces/claude-plugins-official/.claude-plugin/marketplace.json`.
Shape: `{ "name", "description", "owner": {name,email}, "plugins": [ { "name",
"description", "version", "source", "author" } ] }`. A local/single-plugin
marketplace uses `"source": "./"` (superpowers) or `"source": "./plugins/<x>"`
(the official directory) — a **relative path** the marketplace root resolves.

`/plugin marketplace add <path>` reads this file; `/plugin install <name>` then
installs the named plugin.

## 2. The generator — `flow plugin build [--out DIR]`

New command module `src/flow_aidlc/commands/plugin.py`, registered in
`cli.py`'s `_COMMANDS` map as `plugin`. `flow plugin build` (bare `flow plugin`
defaults to build) assembles the tree, `--out DIR` targets an alternate location
(default `<repo>/plugin`).

It regenerates a clean tree each run (removes any existing output first, so the
build is deterministic/idempotent) and:

1. Flattens `engine/claude/commands/**.md` → `plugin/commands/*.md` (verbatim).
2. Flattens `engine/claude/agents/**.md` → `plugin/agents/*.md` (verbatim).
3. Copies `engine/claude/hooks/*.sh` → `plugin/hooks/` keeping the **executable
   bit**, and translates `engine/claude/settings.json`'s `hooks` block into
   `plugin/hooks/hooks.json`, rewriting each `.claude/hooks/<x>.sh` command to
   `${CLAUDE_PLUGIN_ROOT}/hooks/<x>.sh` (regex `_HOOK_PATH_RE`). `_lib.sh` is
   copied (shared library) but is not a hook entry.
4. Writes `plugin/.claude-plugin/plugin.json` — `name: "flow"`,
   `version` == package `__version__` (0.1.0), `description`, `author`.
5. Writes `plugin/README.md` (install flow + composition note).
6. Writes `.claude-plugin/marketplace.json` **beside the plugin dir** (repo root
   for the default `--out`), listing this one plugin with `source: "./plugin"`.

Single source of truth: `plugin/` is never hand-edited; the engine assets are.
The initial `plugin/` tree is committed too, so the repo ships a ready-to-install
plugin without a build step.

## 3. Composition model (documented in both READMEs)

- The **plugin** provides the Claude Code surface: `/flow-*` commands, phase
  agents, governance hooks. Installed via `/plugin install flow`.
- The **`flow` CLI** provides `flow init` (scaffolds the per-project `.flow/`
  instance) and `flow check` (the gate). Installed via `pipx install flow-aidlc`.
- The hooks/commands operate on the `.flow/` instance `flow init` creates — so a
  user installs the plugin **and** runs `flow init`.

## 4. Validation

| Check | Result |
|---|---|
| `plugin.json`, `hooks.json`, `marketplace.json` valid JSON | PASS (`json.load` on all three) |
| `plugin/commands/` count == engine (10) | PASS (10) |
| `plugin/agents/` count == engine (14) | PASS (14) |
| hooks translated (7 event entries) | PASS (7; `_lib.sh` excluded) |
| hook scripts executable | PASS (all `-rwxr-xr-x`) |
| hook commands rewritten to `${CLAUDE_PLUGIN_ROOT}/hooks/…` | PASS (all 7) |
| `flow plugin build --out /tmp/plugin-test` idempotent | PASS (`diff -r` identical) |
| package tests | PASS (74 passed) |

Build output:

```
Built Flow plugin at .../flow-aidlc/plugin
  commands: 10
  agents:   14
  hooks:    7
  version:  0.1.0
```

## 5. Files changed / added

- `src/flow_aidlc/commands/plugin.py` — the generator (new).
- `src/flow_aidlc/cli.py` — registered the `plugin` subcommand.
- `plugin/**` — generated plugin tree (committed artifact).
- `.claude-plugin/marketplace.json` — repo-root marketplace (generated).
- `README.md` — added "Claude Code plugin" section.
- `plugin/README.md` — install + composition doc (generated).
