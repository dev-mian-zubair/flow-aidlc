# Code Graph Adapter

The single place that maps Flow's **universal code-graph operations** to the tools
of the configured graph backend. Steps and agents that need code *structure*
(callers, dependents, contracts, impact) use the universal operation names below
and look the mapping up here — **no step names a backend-specific command.**

The code graph is the source of truth for derivable **structure**; `knowledge/map/`
holds the **invariants** the graph cannot know. Flow reaches the graph only through
this adapter — the backend is swappable (Graphify by default).

## Select the backend

Read `config.yaml → graph.backend` (and `graph.output`, `graph.code_only`). Use the
mapping section for that backend. **An unmapped / NOT IMPLEMENTED backend is a hard
stop** — do not improvise graph commands. (`config-consistency` C6 enforces that
`graph.backend` is implemented here.)

**Implemented:** `graphify`.

## Universal operations (the contract callers use)

| Operation | Inputs | Returns | Purpose |
|---|---|---|---|
| `WHO_CALLS` | symbol | callers/dependents + `file:line` | the "who depends on this / don't-change list" |
| `NEIGHBORS` | symbol | connections + methods + `file:line` | a symbol's contract + immediate structure |
| `QUERY` | plain-language question | scoped subgraph + citations | structural question in NL |
| `PATH` | symbol A, symbol B | shortest path | how A and B are connected |
| `HUBS` | — | most-connected nodes | the architectural surface of a subsystem |
| `IMPACT_OF_DIFF` | changed files/symbols | affected nodes | blast radius of a change |
| `BUILD` | path | graph file | (re)build the graph, offline |
| `UPDATE` | path | graph file | incremental re-extract after a change |

Callers cite operations by name, e.g. *"resolve callers via `WHO_CALLS` (see
`steps/shared/graph.md`)"* — never the underlying command.

## Backend mappings

### graphify

Graph file = `config.graph.output` (default `graphify-out/graph.json`); every query
takes `--graph <that file>`. **Air-gap:** always pass `--code-only` on build/update
(local tree-sitter AST — no API key, no egress).

| Operation | graphify CLI | MCP tool (`config.graph.mcp`) — verified live |
|---|---|---|
| `WHO_CALLS(sym)` | `graphify affected "<sym>" --graph <g>` (reverse traversal → callers/dependents) | `get_neighbors(label)` → read the **incoming `<--`** edges (dependents); optional `relation_filter: calls`. No dedicated reverse tool — the direction is in the arrows. |
| `NEIGHBORS(sym)` | `graphify explain "<sym>" --graph <g>` | `get_neighbors(label)` (returns both `<--` and `-->` edges, arrow-marked) |
| `QUERY(q)` | `graphify query "<q>" --graph <g>` (BFS; `--budget N` caps tokens) | `query_graph(question, mode, depth, token_budget)` |
| `PATH(a, b)` | `graphify path "<a>" "<b>" --graph <g>` | `shortest_path` |
| `HUBS()` | `graphify god-nodes --graph <g>` | `god_nodes` (also `graph_stats`, `get_node`, `get_community`) |
| `IMPACT_OF_DIFF(paths)` | for each changed symbol → `graphify affected "<sym>"` — works on a **local, pre-PR** diff | ⚠ `get_pr_impact` needs an **existing GitHub PR number** (post-PR only). For a local branch diff (branch-hardening) use `get_neighbors` per changed symbol and read the `<--` edges. |
| `BUILD` | `config.graph.build` = `graphify extract . --code-only --no-cluster --force` — **one directed extract at the repo root**. Scope is `.graphifyignore`, not multiple roots. `--force` skips the incremental cache (a warm-cache build is not equivalent to a clean one, so dev must match CI's fresh-checkout build). | — (build is CLI, never MCP) |
| `UPDATE` | **Use `BUILD`**. `graphify update` clusters and produces a *different* topology than `extract --no-cluster`, so it must not refresh the committed graph. There is no fast incremental here. | — |

**Scope:** ONE directed extract at the repo root; the cut is `config.graph.ignore_file`
(when set, e.g. `.graphifyignore`), not multiple roots — `graphify extract` takes a
single path, and **a single _directed_ graph is required** so `WHO_CALLS` (`affected`)
does precise reverse traversal. (Merging per-root graphs yields `directed: false` and
turns "who depends on me" into "everything I touch" — so we do not merge.) A typical
`ignore_file` drops tests, tooling (`scripts/`, `infra/`, `docs/`), vendored/generated
trees, and dependency manifests; product code lives under `config.graph.focus`. If a
codebase spans multiple languages that only communicate over HTTP (e.g. a frontend
calling a backend API), those regions sit in the **same file but as unconnected
regions** — an HTTP boundary is not an AST edge — so cross-language call paths do not
connect; each region is complete for its own `map-existing`.

**Determinism / committed:** `--code-only --no-cluster` is **byte-identical across
runs**; `graphify-out/graph.json` is therefore **committed** (instant availability on
checkout) and CI verifies freshness by rebuild+diff. Everything else graphify writes
is git-ignored.

**MCP (agent-facing path):** the `graphify` server in your MCP config (`config.graph.mcp`)
runs `graphify-mcp <config.graph.output>` over stdio. Tools (verified live, v0.9.33):
`query_graph`, `get_node`, `get_neighbors`, `get_community`, `god_nodes`, `graph_stats`,
`shortest_path`, `list_prs`, `get_pr_impact`, `triage_prs`. Agents (e.g. `shape-map` via
`mcp__graphify`) use these rather than shelling out — **but note there is no reverse
`affected` tool**: resolve `WHO_CALLS` from `get_neighbors`' incoming (`<--`) edges, and
remember `get_pr_impact` is for an *existing GitHub PR*, not a local diff. **Needs the
`[mcp]` extra** (`uv tool install "graphifyy[mcp]==0.9.33" --force`); without it the
server errors and consumers degrade to the `Explore`/grep fallback.

**Freshness:** if your repo routes hooks through `core.hooksPath` (bypassing graphify's
own `hook install`), wire freshness through convention: (1) a `pre-push` staleness
warning; (2) a `graphify-out/graph.json` merge-driver to union-merge parallel branches;
(3) **CI as the authoritative gate** — rebuild with the canonical command and fail on any
diff. Rebuild locally with `flow refresh` (or the configured `graph.build`) after
changing product code.

**Preconditions:** `graphify` CLI installed (`uv tool install graphifyy==0.9.33`) or the
MCP running; the graph built for the repo; `code_only: true` for air-gapped deployments.

## Consumers (who calls these ops)

- **Shape / `map-existing`** — `WHO_CALLS` + `NEIGHBORS` for callers/dependents/
  don't-change + contracts (replaces grep). The primary consumer.
- **Scope / `clarify`** — `QUERY` / `HUBS` to identify the touched subsystems.
- **Ship / `branch-hardening`** — `IMPACT_OF_DIFF` for blast radius on the branch diff.
- **`curator`** — `HUBS` + `NEIGHBORS` to re-derive the *thinned* map's structure section.

## Rule

- Steps and agents invoke operations by **universal name** and cite this file —
  never a backend command directly. That keeps the methodology graph-tool-neutral.
- An unmapped or stubbed backend is a **hard stop**, not an improvisation.
- The graph carries **structure only**; invariants come from `knowledge/map/`.
- Adding a backend = filling in its `### <backend>` section here + granting its CLI/MCP
  to the graph-consuming agents. No caller-prose changes.
