# Watch CI and propose improvements

Date: 2026-11-01

Rule: Whenever you look at a CI run, note its duration and failures, and propose a card when a job gets slow or the same test fails twice.

Incident: The CI fix-and-fail loop had become the owner's largest time sink, and nobody raised slow or flaky jobs until he noticed them.

Why: The process should improve itself instead of waiting for the owner to notice.

How to apply: Thresholds used so far: a UI suite well over about 25 minutes, a fast tier over about 10 minutes on a free runner, or one test failing twice. Say so and file a card with the readings.
