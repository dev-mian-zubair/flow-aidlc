# Auto mode — final report

Emitted when the loop stops (queue empty | max_tasks | budget | .flow/STOP). List:

- **Merged:** ticket id, PR url, one-line summary — one row each.
- **Parked (flow-blocked):** ticket id, draft PR url, the blocking reason.
- **Skipped:** any ticket not reached (cap/kill-switch), so the human knows the tail.

End with the stop reason and the merged/parked counts.
