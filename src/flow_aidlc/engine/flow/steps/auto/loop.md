# Auto mode — the autonomous loop

Drives one or many tickets through Scope→Shape→Build→Ship with NO human
checkpoints. Load per `/flow-auto`.

## Preconditions
- CI workflow present (green CI is the merge backstop) and tracker write scope.
- Read `config.yaml → execution` for: `label` (default flow-auto), `max_tasks`
  (default 5), `budget`, `review.max_rounds`, `merge.{gate,target}`.

## The loop
1. **Kill-switch check:** if `.flow/STOP` exists, stop — report and exit.
2. **Pull next task:** via the tracker adapter (`steps/shared/tracker.md`
   `DEDUP_SEARCH`/`GET_TICKET`), the highest-priority open ticket labeled
   `<execution.label>` (or the `<id>` argument). None → exit (queue empty).
3. **Run the playbook without stops:** execute Scope→Shape→Build→Ship. At every
   `checkpoint: yes` stage, run the stage-typed adversarial panel
   (`steps/auto/panel-review.md`) instead of stopping for `/flow-approve`.
4. **Ship + merge:** follow `steps/ship/open-pr.md` then `steps/auto/merge.md`
   (open the PR, poll checks, merge only on green CI).
5. **On success:** the ticket auto-closes via `Fixes #`; increment the merged
   count and the attempted count; go to 1.
6. **On a task that cannot settle** (panel non-converge at `review.max_rounds`,
   or CI red after fixes): PARK it — leave a draft PR, add the `flow-blocked`
   label + a comment on why, increment the attempted count, and continue to the
   next task (do not halt the run).
7. **Stop conditions:** queue empty | attempted count (merged + parked) == `max_tasks` | budget
   exhausted | `.flow/STOP` present. Then emit `steps/auto/report.md`.

## Guarantees
- Every gate that controlled mode runs still runs here.
- One stuck task never halts the run — it is parked and reported.
