#!/usr/bin/env bash
# session-start.sh — Hook: SessionStart
# Surfaces the active workstream slug, next unchecked stage from progress.md,
# and a count of STALE knowledge docs.
# Fail-open: exits 0 under all conditions.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh" || true

flow_read_input

worklog="$(flow_active_worklog)"

if [ -z "$worklog" ]; then
    echo "No active Flow workstream."
    exit 0
fi

slug="$(basename "$worklog")"

# First unchecked stage from progress.md
progress_file="$worklog/progress.md"
next_stage=""
if [ -f "$progress_file" ]; then
    next_stage="$(grep -m1 '^\- \[ \]' "$progress_file" 2>/dev/null | sed 's/^- \[ \] *//' || true)"
fi

# Count STALE docs: files under docs/flow/knowledge/map/ with frontmatter status: STALE
root="$(flow_repo_root)"
stale_count=0
if [ -n "$root" ] && [ -d "$root/knowledge/map" ]; then
    stale_count="$(grep -rl '^status: STALE' "$root/knowledge/map/" 2>/dev/null | wc -l | tr -d ' ')" || stale_count=0
fi

echo "=== Flow: Active Workstream ==="
echo "Workstream : $slug"
if [ -n "$next_stage" ]; then
    echo "Next stage : $next_stage"
else
    echo "Next stage : (all stages complete or progress.md not found)"
fi
echo "Stale docs : $stale_count"

exit 0
