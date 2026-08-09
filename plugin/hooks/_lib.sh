#!/usr/bin/env bash
# _lib.sh — Shared helpers for Flow hooks.
# SOURCED ONLY — never exec'd directly (no shebang intended for execution).
# All functions are side-effect-free and never exit non-zero.

# ---------------------------------------------------------------------------
# flow_read_input
#   Reads all of stdin into the global variable FLOW_INPUT.
#   Must be called exactly once per hook, before any flow_field() calls.
# ---------------------------------------------------------------------------
flow_read_input() {
    FLOW_INPUT="$(cat)"
}

# ---------------------------------------------------------------------------
# flow_field <dotted.path>
#   Echoes the value of the given dotted key from $FLOW_INPUT (JSON).
#   Returns empty string on any error — never exits non-zero.
# ---------------------------------------------------------------------------
flow_field() {
    local path="$1"
    [ -z "${FLOW_INPUT:-}" ] && { echo ""; return 0; }
    FLOW_INPUT="$FLOW_INPUT" python3 -c '
import os, sys, json
try:
    data = json.loads(os.environ.get("FLOW_INPUT", ""))
    for p in sys.argv[1].split("."):
        data = data.get(p, "") if isinstance(data, dict) else ""
    sys.stdout.write("" if data is None else str(data))
except Exception:
    pass
' "$path" 2>/dev/null || echo ""
}

# ---------------------------------------------------------------------------
# flow_repo_root
#   Echoes the absolute path to the git repo root, or empty on failure.
# ---------------------------------------------------------------------------
flow_repo_root() {
    git rev-parse --show-toplevel 2>/dev/null || echo ""
}

# ---------------------------------------------------------------------------
# flow_active_worklog
#   Returns the absolute path to the active worklog directory, or empty.
#   Resolution order:
#     1. docs/flow/worklog/.active file exists → docs/flow/worklog/<its-contents>
#     2. Most-recently-modified docs/flow/worklog/*/progress.md parent dir
#     3. Empty → hooks should no-op
# ---------------------------------------------------------------------------
flow_active_worklog() {
    local root
    root="$(flow_repo_root)"
    [ -z "$root" ] && echo "" && return 0

    local active_ptr="$root/worklog/.active"

    # (1) explicit pointer
    if [ -f "$active_ptr" ]; then
        local slug
        slug="$(cat "$active_ptr" 2>/dev/null | tr -d '[:space:]')"
        if [ -n "$slug" ]; then
            local candidate="$root/worklog/$slug"
            if [ -d "$candidate" ]; then
                echo "$candidate"
                return 0
            fi
        fi
    fi

    # (2) most-recently-modified progress.md — worklog dir must exist first
    if [ -d "$root/worklog" ]; then
        local newest
        newest="$(find "$root/worklog" -maxdepth 2 -name "progress.md" 2>/dev/null \
            | xargs -r ls -t 2>/dev/null \
            | head -1)"
        if [ -n "$newest" ]; then
            echo "$(dirname "$newest")"
            return 0
        fi
    fi

    echo ""
    return 0
}

# ---------------------------------------------------------------------------
# flow_iso_now
#   Echoes the current UTC timestamp in ISO-8601 format.
# ---------------------------------------------------------------------------
flow_iso_now() {
    date -u +%Y-%m-%dT%H:%M:%SZ
}
