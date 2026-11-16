# Limits and open problems

What this system does not do, has not proven, or gets wrong. Sources are the [retro log](../RETRO.md) and
the live files.

## The evidence is thin

- The numbers in the README cover about five days (reviews from late on 2026-11-11, merges from 2026-11-12
  to 2026-11-16), two apps, one owner, one machine.
- The apps are unreleased. There is no production traffic, no user reports, no incident data. "A bug that
  reaches the owner" is the only failure the system can currently observe.
- Cost is not measured: not tokens, not money, not the owner's minutes. Review rounds are known to be
  expensive only by count.
- No baseline. There is no comparison against the same cards done without the reviewer or without the lead.

## The machine is the bottleneck

- One 16 GB machine is both the simulator host and the CI runner. Only one card at a time can be proven on
  a simulator ([lane.md](lane.md)). Workers wait: one sat idle most of an afternoon behind a three-hour slot.
- The gate and stop thresholds are tuned to that machine by trial. They are not portable.
- There is no cross-app lock. The gate sees only CI runs that have started.
- A restart kills every worker and the context in it. This happened; work resumed from hand-back files, and
  files kept in `/tmp` were lost. Restartability depends on each hand-back being complete, which is checked
  by nobody until it is needed.

## Review is expensive and incomplete

- Several cards took four to six review rounds. One S-size bundle used five rounds and four lane slots.
- Five of one card's six rounds were about wording in comments, not behaviour.
- The reviewer is read-only by instruction. It does not run tests, so a claim that needs a run rests on the
  worker's logs or on CI. The lockfile failure in [briefs.md](briefs.md) passed both the worker and the reviewer.
- PR CI is the fast tier: it runs no UI tests. Local proof by the worker is the only UI proof before merge;
  the nightly full run finds what was missed a day later. Two nightlies went red on tests that had been
  proven on one device only.
- The reviewer and the implementer are different models from the same vendor. Shared blind spots are
  possible and untested.
- The `Review: PASS` comment the merge check looks for is a convention. The hook cannot verify who wrote it
  ([guardrails.md](guardrails.md)).
- Commits after the last reviewer pass are sometimes verified by the lead alone when they are small and
  mechanical. That is a judgement call, stated on the PR each time.

## Flaky tests are not solved

Some failures did not reproduce and remain open as cards: a UI test that stalled once in a 77-minute
suite (its result bundle was deleted by the rerun), a first-test-after-cold-boot failure, a timing test that
fails in the full plan and passes alone. The rule is to report red as red and never retry for a green; the
causes are still unknown.

## The lead is a single point

- One long-lived lead session holds the queue, the lane and the only write access to the dashboard. If it
  stops, nothing is dispatched and notifications do not reach the owner.
- The lead has made the errors it is meant to prevent: it nearly merged a card without a fresh review of the
  last commits, released the lane while the gate was closed, told a reviewer that CI covered something it
  did not, and let an answered question sit overnight.
- Context loss on restart applies to the lead too. The state is rebuilt from the dashboard, the vault,
  GitHub and the hand-back folder ([back-to-work](../skills/back-to-work/SKILL.md)); anything that lived
  only in the conversation is gone.

## Rules drift

- Rules live in memory, skills, agent files, briefs and scripts. Nothing checks that the copies agree.
- Some of the owner's skills are synced from elsewhere and cannot be edited locally, so lessons for them
  queue up as a diff for the owner.
- The retro log is written by the lead about its own work.

## The dashboard

- One writer, last-writer-wins, guarded by a version check only.
- It depends on a hosted artifact and its database. The repo can rebuild the page and the rules, not the
  data ([dashboard/RESTORE.md](../dashboard/RESTORE.md)).

## This repo

- The files here are sanitised copies. App names, ids, paths and machine numbers are example values.
- The restore kit has been tested in a temporary home directory, not on a new account or a new machine
  ([restore-verification.md](restore-verification.md)).
- The design process ([design-work.md](design-work.md)) rests on one prototype.
- Platform-specific: the skills assume Claude Code, git worktrees, the GitHub CLI and Apple's simulator
  tooling. The lane scripts are macOS-only.
