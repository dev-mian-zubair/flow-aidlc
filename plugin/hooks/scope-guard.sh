#!/usr/bin/env bash
# scope-guard.sh — Hook: PreToolUse (Write | Edit)
# Denies writes to .flow/** and docs/** when a Flow workstream is active.
# Fail-open: no active worklog → allow everything. Unknown paths → allow.
# Deny signal: JSON permissionDecision:"deny" printed to stdout, exit 0.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh" || true

flow_read_input

worklog="$(flow_active_worklog)"
# No active workstream → allow all writes
[ -z "$worklog" ] && exit 0

file_path="$(flow_field tool_input.file_path)"
# No path to check → allow
[ -z "$file_path" ] && exit 0

# Normalise: strip leading ./
norm_path="${file_path#./}"

# Check if the path falls under a denied prefix
deny_path() {
    local p="$1"
    case "$p" in
        .flow/*|.flow)    return 0 ;;
        docs/*|docs)      return 0 ;;
        *)                return 1 ;;
    esac
}

if deny_path "$norm_path"; then
    python3 -c "
import json, sys
msg = {
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': (
            'scope-guard: ' + sys.argv[1] +
            ' is outside this task\\'s scope (.flow/ and docs/ are not task output). '
            'Use the Flow\\'s own stages to change methodology/docs.'
        )
    }
}
print(json.dumps(msg))
" "$norm_path"
fi

exit 0
