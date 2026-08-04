#!/usr/bin/env bash
# precompact-save.sh — Hook: PreCompact
# Appends a context-compaction boundary marker to <worklog>/journal.md so
# the resume trail notes where a context window was compacted.
# Fail-open: exits 0 under all conditions.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh" || true

flow_read_input

worklog="$(flow_active_worklog)"
[ -z "$worklog" ] && exit 0

journal="$worklog/journal.md"
iso="$(flow_iso_now)"

if [ ! -f "$journal" ]; then
    mkdir -p "$(dirname "$journal")"
    touch "$journal"
fi

{
    echo ""
    echo "## $iso — context compacted"
} >> "$journal"

exit 0
