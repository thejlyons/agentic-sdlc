# Do known follow-ups now, not in a later phase

Date: 2026-11-10

Rule: Follow-ups found by a review or a run are queued for the next worker in the current phase, not filed for after it.

Incident: The lead was pushing review follow-ups to a post-phase backlog while nothing was blocking the work from being done immediately.

Why: Idle agent time is free; a backlog of known defects is not.

How to apply: File the follow-up card in the same pass as the merge and put it in the current queue. Only proof that truly depends on a later stage is split off (see close-cards-on-merge). The lane limits still apply.
