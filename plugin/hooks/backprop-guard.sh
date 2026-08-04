#!/usr/bin/env bash
# backprop-guard.sh — Hook: SubagentStop
#
# v1 REMINDER ONLY — this hook flags when code has been modified after the
# current slice's design document was last written, but does NOT block or
# revert anything. Full enforcement logic is deferred to WS-8 pilot tuning.
# Do not rely on this as a hard gate.
#
# If any tracked file under a workspace code dir (backend/, frontend/, infra/,
# dist/, scripts/, docker/) has an mtime newer than the current slice's
# build/<slice>/design.md, appends a backprop warning to <worklog>/journal.md.
# Fail-open: exits 0 under all conditions. Guards against missing slice/design.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh" || true

flow_read_input

worklog="$(flow_active_worklog)"
[ -z "$worklog" ] && exit 0

root="$(flow_repo_root)"
[ -z "$root" ] && exit 0

# Find the current slice: most-recently-modified build/<slice>/design.md
# Guard: build/ may not exist yet — find exits 1 on a missing dir.
design_file=""
if [ -d "$worklog/build" ]; then
    design_file="$(find "$worklog/build" -maxdepth 2 -name "design.md" 2>/dev/null \
        | xargs -r ls -t 2>/dev/null \
        | head -1 || true)"
fi
[ -z "$design_file" ] && exit 0
[ -f "$design_file" ] || exit 0

design_mtime="$(stat -c %Y "$design_file" 2>/dev/null || stat -f %m "$design_file" 2>/dev/null || true)"
[ -z "$design_mtime" ] && exit 0

# Check workspace code dirs for files newer than design.md
code_dirs=("backend" "frontend" "infra" "dist" "scripts" "docker")
newer_file=""
for dir in "${code_dirs[@]}"; do
    dir_path="$root/$dir"
    [ -d "$dir_path" ] || continue
    # Find any file with mtime strictly after design.md
    found="$(find "$dir_path" -type f -newer "$design_file" 2>/dev/null | head -1)"
    if [ -n "$found" ]; then
        newer_file="$found"
        break
    fi
done

[ -z "$newer_file" ] && exit 0

# Append warning to journal
journal="$worklog/journal.md"
iso="$(flow_iso_now)"
if [ ! -f "$journal" ]; then
    mkdir -p "$(dirname "$journal")"
    touch "$journal"
fi

{
    echo ""
    echo "## $iso — backprop check: code changed after slice design; confirm design reflects it."
} >> "$journal"

exit 0
