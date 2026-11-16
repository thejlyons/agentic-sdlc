# Remove a worktree only after the worker's final hand-back

Date: 2026-11-02

Rule: A worker's worktree is removed only after its final hand-back is collected and nothing is left to do, never when its PR merges.

Incident: The lead force-removed a worktree right after the PR merged. The worker was still alive and had just started its next card in that worktree. Its edits and git metadata were lost and the card was restarted by a fresh worker.

Why: A merged PR does not mean the worker is finished; hand-backs can be interim.

How to apply: Before removing: the worker reports finished with no pending work, `git -C <worktree> status` is clean or accounted for, and no process is using the directory. Stop the worker first, then remove.
