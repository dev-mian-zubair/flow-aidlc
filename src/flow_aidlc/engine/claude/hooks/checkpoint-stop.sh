#!/usr/bin/env bash
# checkpoint-stop.sh — Hook: Stop
#
# v1 REMINDER ONLY — this hook surfaces a pending checkpoint notice but does
# NOT hard-block or prevent the agent from advancing. Full enforcement is
# deferred to WS-8 pilot tuning. Do not rely on this as a hard gate.
#
# If the active worklog's progress.md contains a line matching
# "CHECKPOINT_PENDING: <stage>", prints a ⏸ reminder to stdout and exits 0.
# Fail-open: exits 0 under all conditions.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$SCRIPT_DIR/_lib.sh" || true

flow_read_input

# Auto mode bypass: /flow-auto runs without human checkpoints. If the repo is in
# an auto run (a .flow/STOP sentinel is the kill-switch, and FLOW_MODE=auto marks
# the session), do not print the checkpoint reminder.
if [ "${FLOW_MODE:-}" = "auto" ]; then
  exit 0
fi

worklog="$(flow_active_worklog)"
[ -z "$worklog" ] && exit 0

progress_file="$worklog/progress.md"
[ -f "$progress_file" ] || exit 0

# Look for CHECKPOINT_PENDING: <stage>
pending_line="$(grep -m1 '^CHECKPOINT_PENDING:' "$progress_file" 2>/dev/null || true)"
[ -z "$pending_line" ] && exit 0

stage="$(echo "$pending_line" | sed 's/^CHECKPOINT_PENDING:[[:space:]]*//')"

echo "⏸ Checkpoint pending at $stage — review the artifacts and run /flow-approve to continue."

exit 0
