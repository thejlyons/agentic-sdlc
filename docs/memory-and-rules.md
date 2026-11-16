# Memory and rules

The process is mostly rules, and almost every rule has an incident behind it. This page says how a
correction from the owner becomes something the next session still follows, and gives examples. The rules
themselves, one file each, are in [rules/](../rules/README.md).

## The path from a correction to a durable rule

1. **The owner says it**, usually in one sentence, usually right after something went wrong.
2. **A dated memory entry.** The lead writes it to its persistent memory the same turn: the rule, the date,
   the incident, why it matters, and how to apply it. Where the lead is interpreting ("simple" means
   reversible and cheap to change), the entry says that the reading is the lead's, not the owner's words.
3. **Folded into the working files.** Memory reaches only the lead. Workers and reviewers start with no
   memory, so a rule that binds them has to be in the [agent files](../agents/card-implementer.md), the
   [lead skill](../skills/lead-loop/SKILL.md), or the brief. About every ten cards, or at once when the same
   thing breaks twice, the lead folds retro lessons in. [CHANGELOG.md](../CHANGELOG.md) records when.
4. **Sometimes a script or a hook.** A rule that a tired or freshly restarted agent could miss gets
   mechanised: the lane rules became [macgate.sh](../scripts/macgate.sh) and
   [macstop.sh](../scripts/macstop.sh); "merge only after review and green CI" became a check in
   [guard.py](../hooks/guard.py).

The retro log ([RETRO.md](../RETRO.md)) is the other input. It records lessons the lead and workers found
themselves, one line per card or incident.

## Rules can be renegotiated, with readings

The owner's standing offer (2026-11-11): any rule set under older conditions can be changed, just ask. The
discipline that goes with it: when a rule costs real work, keep obeying it, and bring the readings and one
proposed replacement in the same message. Do not work around it. Do not wait for the fourth wasted run to
raise it. The stop rule changed three times in three days this way ([lane.md](lane.md)).

## Incident to rule: examples

| Incident | Rule | File |
|---|---|---|
| The build machine crashed twice in one day with several simulator workers and CI jobs running (load 150 to 700). | One simulator-using job at a time. Check load before starting anything. | [one-simulator-lane](../rules/one-simulator-lane.md) |
| A "sim-free" worker pushed a branch; its CI job booted a simulator beside a running simulator worker. Swap 16 GB, load 260 to 320, run lost. | A PR push counts as a lane use. Sim-free workers hold pushes. One PR in CI at a time. | [pr-ci-shares-the-lane](../rules/pr-ci-shares-the-lane.md) |
| The lead removed a worker's worktree right after its PR merged. The worker was alive and had started its next card there; the work was lost. | Remove a worktree only after the worker's final hand-back, never on merge. | [remove-worktrees-after-final-handback](../rules/remove-worktrees-after-final-handback.md) |
| The lead obeyed "stop at 13 GB swap" through four wasted runs, though an erased simulator's first boot alone parks about 11.6 GB. | Bring readings and a replacement at the first wasted run. | [renegotiate-rules-with-readings](../rules/renegotiate-rules-with-readings.md) |
| The disk gate kept failing. 41 simulators held 14.7 GB; shutting them down freed nothing. | Only erase frees simulator disk. CI erases at the end of every job; workers erase at the end of a card. | [erase-simulators-to-free-disk](../rules/erase-simulators-to-free-disk.md) |
| A small layout choice sat open overnight although the recommended option was already built. | For simple reversible choices, decide after about 15 minutes and list it under "Decided for you". | [decide-small-choices-after-15-minutes](../rules/decide-small-choices-after-15-minutes.md) |
| About twenty small cards as twenty PRs would each cost a cold boot, a build, a review and a CI slot. | Bundle related small cards into one worker run and one PR. | [bundle-related-cards](../rules/bundle-related-cards.md) |
| Merged cards sat "In review" waiting for proof that could only come much later. The board hid real progress. | A merged card is Done. Proof that must wait becomes its own card in the later stage. | [close-cards-on-merge](../rules/close-cards-on-merge.md) |
| A long suite for a lower-priority app held the lane 80 minutes while the priority app's bundle waited. The owner noticed before the lead did. | The priority app gets the lane first; others ask before any run over about 15 minutes. | [one-app-owns-the-lane](../rules/one-app-owns-the-lane.md) |
| A first round of quick vector mockups read as machine-made. | Visual pitches get a craft brief, parallel illustrators and a render-critique-fix loop. | [visual-pitches-need-a-craft-brief](../rules/visual-pitches-need-a-craft-brief.md) |

## Lessons the owner did not have to state

Many rules came from the retro log without the owner saying anything. A few, with the line that produced
them:

- Copy pictures out of the build folder after every run (test scripts wipe it; a reviewer got none).
- Investigation figures stay in the hand-back, never in repo comments (five review rounds on one card).
- Security filters are allowlists from the start (a denylist lost six times).
- Run each new test on every device its CI job covers before hand-back (two red nightlies).
- Keep anything worth keeping outside `/tmp`; hand-backs must be complete enough to restart a worker from
  (a machine restart killed every worker).

## Limits of this mechanism

Memory is per account and per workspace. A new account starts empty; that is why [rules/](../rules/README.md)
exists and why [BOOTSTRAP.md](../BOOTSTRAP.md) offers to load it. Skills that are synced from elsewhere
cannot be edited locally, so lessons that belong in them wait for the owner as a batched diff. Nothing
checks that a rule in memory and the same rule in a skill still agree.
