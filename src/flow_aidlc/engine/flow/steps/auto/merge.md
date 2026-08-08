# Auto mode — open, poll CI, merge on green

Runs after `steps/ship/open-pr.md` opens the PR (auto mode only). TWO independent
gates must both be green to merge: (a) every in-session adversarial panel cleared,
and (b) the PR's required CI checks green.

1. **Open** the PR via the tracker/VCS adapter `OPEN_PR` (base = `execution.merge.target`
   or `config.vcs.base`), body includes `Fixes <id>`.
2. **Poll** the PR's required checks via the tracker/VCS MCP until they settle.
3. **Green →** merge (respect branch protection; never override it). The ticket
   auto-closes via `Fixes <id>`. Return success to the loop.
4. **Red →** pull the failing check output, run a fix-loop in the workspace, push,
   and re-poll. Bounded by `execution.review.max_rounds`.
5. **Still red / timeout →** do NOT merge. Convert to a draft PR, add the
   `flow-blocked` label + a comment with the failing checks, and return "parked"
   to the loop (`steps/auto/loop.md` step 6).

Branch protection is authoritative — if it blocks the merge, park (never bypass).
