# Rules

The durable rules of this process, one file each: a dated statement, the incident behind it, the reason,
and how to apply it. They are rewritten from the lead session's persistent memory, with app names and
personal details removed. Dates are when the owner set the rule.

Two uses:

- **Reading.** Each rule shows what broke before it existed. [docs/memory-and-rules.md](../docs/memory-and-rules.md)
  explains how a correction becomes a rule.
- **Starting memory.** A new account or machine has no memory. The bootstrap skill
  ([BOOTSTRAP.md](../BOOTSTRAP.md)) offers to load these files as the lead's starting memory, so the rules
  are not relearned from the same incidents. Read them first: several are tuned to one machine and one
  owner's preferences, and numbers such as 15 minutes or 21 GB are that owner's.

Rules found by the lead and the workers themselves, without the owner saying anything, are in the
[retro log](../RETRO.md) and are folded into the [skills](../skills/lead-loop/SKILL.md) and
[agents](../agents/card-implementer.md).

| Date | Rule |
|---|---|
| 2026-10-29 | [Validate UI yourself, in the simulator](validate-ui-yourself.md) |
| 2026-11-01 | [Watch CI and propose improvements](watch-ci-and-propose.md) |
| 2026-11-02 | [Remove a worktree only after the worker's final hand-back](remove-worktrees-after-final-handback.md) |
| 2026-11-03 | [Only erase frees simulator disk](erase-simulators-to-free-disk.md) |
| 2026-11-03 | [Merge without asking, after an independent review and green CI](merge-after-independent-review.md) |
| 2026-11-04 | [One simulator-using job at a time](one-simulator-lane.md) |
| 2026-11-06 | [A merged card is Done; proof that must wait becomes its own card](close-cards-on-merge.md) |
| 2026-11-07 | [Simulators and their tooling may be used freely; the memory rules stay](simulators-are-free-to-use.md) |
| 2026-11-08 | [Stop all machine-heavy work when the owner needs the machine](pause-when-owner-needs-machine.md) |
| 2026-11-10 | [Do known follow-ups now, not in a later phase](no-backlog-for-known-defects.md) |
| 2026-11-10 | [Start full proof runs yourself](start-proof-runs-yourself.md) |
| 2026-11-11 | [One lead, and only the lead writes card status](one-lead-one-writer.md) |
| 2026-11-11 | [A question parks one card, never the queue](questions-park-one-card.md) |
| 2026-11-11 | [A PR push is a lane use](pr-ci-shares-the-lane.md) |
| 2026-11-11 | [Renegotiate a costly rule with readings and one proposal](renegotiate-rules-with-readings.md) |
| 2026-11-11 | [Stop a simulator job on sustained pressure, not on one number](stop-rule-needs-sustained-pressure.md) |
| 2026-11-12 | [Bundle related small cards into one worker run and one PR](bundle-related-cards.md) |
| 2026-11-12 | [Dashboard order: questions, then percentages, then activity](dashboard-layout-order.md) |
| 2026-11-13 | [The priority app gets the lane first](one-app-owns-the-lane.md) |
| 2026-11-13 | [Decide small reversible choices after about 15 minutes](decide-small-choices-after-15-minutes.md) |
| 2026-11-14 | [Screen sessions on the build machine may run without asking](machine-screen-available.md) |
| 2026-11-14 | [Visual pitches need a craft brief and a render-critique-fix loop](visual-pitches-need-a-craft-brief.md) |
| 2026-11-15 | [Taste work is an iteration until the owner accepts it](iterations-until-owner-accepts.md) |

Format of each file:

```
# <title>
Date: <when the owner set it>
Rule: <one statement>
Incident: <what happened>
Why: <the reason>
How to apply: <what to do>
```

A rule can be renegotiated: see [renegotiate-rules-with-readings](renegotiate-rules-with-readings.md).
