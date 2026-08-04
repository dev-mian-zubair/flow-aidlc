#!/usr/bin/env bash
# prompt-journal.sh — Hook: UserPromptSubmit
# Appends the raw user prompt to <worklog>/journal.md.
# Fail-open: never blocks a prompt; exits 0 under all conditions.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh" || true

flow_read_input

worklog="$(flow_active_worklog)"
[ -z "$worklog" ] && exit 0

prompt="$(flow_field prompt)"
[ -z "$prompt" ] && exit 0

journal="$worklog/journal.md"
iso="$(flow_iso_now)"

# Create journal if it doesn't exist
if [ ! -f "$journal" ]; then
    mkdir -p "$(dirname "$journal")"
    touch "$journal"
fi

# Append entry — never overwrites existing content
{
    echo ""
    echo "## $iso — user"
    echo "$prompt"
} >> "$journal"

exit 0
