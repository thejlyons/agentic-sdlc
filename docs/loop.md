# The loop in detail

One long-lived lead session runs every roadmap card through the same steps. The live instructions are
[skills/lead-loop/SKILL.md](../skills/lead-loop/SKILL.md); this page explains them.

```
card -> brief -> worker in a worktree -> proof -> independent review -> PR and CI
     -> squash-merge -> dashboard status -> retro line -> rules
```

## 1. Pick

Order: finish `In review`, then `In progress`, then `Backlog` by priority, smaller cards first within a
priority. Skip cards waiting on the owner (`needs_j`) and cards whose dependency is not built. Only the
stages in scope for the current goal are eligible.

Related small cards (same screen, same device pose, same test area) are bundled into one worker session and
one PR. The owner dropped "one card, one PR" on 2026-11-12: on the shared build machine each PR costs a cold
simulator boot, a build, a review and a CI slot. Every card id goes in the PR title, the reviewer checks each
card's "Done when" separately, and each card keeps its own status and history. Unrelated areas are not
bundled, and a risky change is not bundled with safe ones.

## 2. Brief

The lead writes a brief: the card text in full, the "Done when" list, which screens to capture and in which
modes, whether the worker holds the simulator lane or is sim-free, the lead session's name, and what the
owner already decided. The brief states the goal and constraints. It does not state the lead's guess about a
bug's cause as fact. See [briefs.md](briefs.md) and [templates/brief.md](../templates/brief.md).

## 3. Worker in a worktree

The lead launches a background session with the
[card-implementer](../agents/card-implementer.md) agent in its own git worktree, branched off `origin/dev`.
The default is Sonnet with a stronger model as advisor; UI-heavy cards run on the stronger model directly.
The lead subscribes once to be told when the worker goes idle. It does not poll.

The worker never edits cards, never merges, and does not push until the lead says so, because a push starts
CI and CI boots a simulator on the same machine ([lane.md](lane.md)).

## 4. Proof

The worker builds, runs the tests that cover the change, adds tests for new behaviour, and for anything
visible captures the screens in light, dark and the largest text size, then opens the pictures and reads
them. Rules that came from incidents:

- Every test log starts with the commit it ran at.
- Each new test is shown failing on the old code.
- Pictures are copied out of the build folder right after the run, because test scripts wipe it.
- Regenerated data files are diffed line by line against the base branch.
- A check that was not run is reported as not run.

The worker writes a hand-back file ([templates/handback.md](../templates/handback.md)) and sends the lead a
one-line message. Each "Done when" box is ticked only with evidence: a test name and result, or a picture.

## 5. Independent review

The lead reads the hand-back and the pictures, then starts a
[card-reviewer](../agents/card-reviewer.md): read-only tools, fresh context, given the card, the worktree,
the base ref and the pictures. It is never given the worker's explanation of why the change is right, and it
is never the model that wrote the code. `CHANGES` goes back to the worker verbatim; the next round gets a
fresh reviewer. After three rounds the lead looks at the card itself, though 8 of 30 PRs still went to four
or more rounds. See [independent-review.md](independent-review.md).

## 6. PR, CI, merge

On `PASS`, and when the lane is free, the worker pushes and opens the PR into `dev`. Fast CI runs. A red run
is read line by line and fixed; it is not re-run to get a green. When CI is green the lead posts the
reviewer's verdict on the PR as a comment starting `Review: PASS`, then squash-merges. The
[guard hook](guardrails.md) lets the merge through only when checks are green and that comment exists.

Releases are a separate `dev` to `main` PR that runs the full suite and merges with a merge commit.

## 7. Dashboard status

Only the lead writes card status. Two reasons, both found on the first day: background workers and
subagents cannot reach the dashboard database, and two writers fight over card versions. Status is written
in the same turn as the event:

| Moment | Write |
|---|---|
| Worker launched | `In progress`, note: worker name, branch |
| PR opened | `In review`, PR number |
| Squash-merged into `dev` | `Done` at once; tick "Done when"; proof that must wait becomes a new card in a later stage |
| Question for the owner | `needs_j: true`, the question and a recommendation at the top of the notes |
| Owner answered | `needs_j: false`, the decision and date in the notes |
| `dev` to `main` merged | `Released` for every Done card whose PR is in `main` |

Timestamps are the real clock time of the write. The dashboard compares them to decide what changed since
the last check-in ([dashboard.md](dashboard.md)).

## 8. Retro and rules

After each card and each incident the lead appends one dated line to the retro log
([RETRO.md](../RETRO.md)): what worked, what broke, the lesson. About every ten cards, or at once when the
same thing breaks twice, durable lessons are folded into the skill, the agent files and the brief template
([memory-and-rules.md](memory-and-rules.md)). Follow-ups from the hand-back and the reviewer's non-blocking
list are filed as cards in the same pass.

## What "done" means

A card is Done when its PR is squash-merged into `dev` after: the worker's build, tests and pictures; a PASS
from a separate reviewer on the final commits (or a lead check of a named, mechanical last commit, stated on
the PR); and green CI. Done is an engineering state. Taste work has a different end state
([design-work.md](design-work.md)).

## What the owner is asked

Irreversible actions and taste decisions only. A question parks one card, never the queue: the lead records
it, sends one notification, and dispatches the next card. Visual choices arrive as two or three real
screenshots. Simple reversible choices are decided by the lead after about 15 minutes and listed on the
dashboard under "Decided for you" until the owner accepts or asks for a change.
