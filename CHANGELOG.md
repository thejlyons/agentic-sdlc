# Changelog of the process

Dated changes to how the work is run: a rule, a script, a hook, a tool. Reconstructed from the
[retro log](RETRO.md), the lead-loop plan, the dates in the lead's memory and the comments in the scripts.
Newest first. Entries before 2026-11-11 predate the lead loop and come from memory dates only.

## 2026-11-20
- The owner's launch checklist is part of the process: one small page per app for the steps only the owner can do, in order, each naming what it waits for on either side, with paste-ready values and a note field the lead reads ([docs/owner-checklist.md](docs/owner-checklist.md)). The owner: "super useful".
- A fourth app's cards moved from the vault to the dashboard's database, by the page's own import on the owner's next visit; a test pins its tile numbers to what the mirror showed before ([dashboard/ROADMAP-DB.md](dashboard/ROADMAP-DB.md)).
- The dashboard shows a row of pinned pages under its title, read from a `meta/links` document the lead writes, so the checklists are one tap away ([dashboard/site/app.js](dashboard/site/app.js)).
- The memory gate lets a job start with swap up to 13 GB when the machine is otherwise idle (load under 5): stale swap just over the 12 GB line was costing 3 to 10 minutes after most jobs ([scripts/macgate.sh](scripts/macgate.sh)).
- Nightly runs are paused during a heavy build phase: they were green every night and took the whole night's simulator lane.
- The lead never puts store-tooling words in a shell command, even inside a search pattern: the guard hook matches the words and asks the owner ([hooks/guard.py](hooks/guard.py)).

## 2026-11-18
- Public copy (store listings, About pages, shop text) states only what the repo, the card or the owner's own words show; a loose phrase in a brief is never turned into a history or a claim. An invented origin story reached a paste-ready folder before review caught it (APC-252, [agents/card-implementer.md](agents/card-implementer.md)).
- A transient state (a spinner, progress, a toast) gets a test-only delay or hold so a UI test can assert it and a picture can show it; "if it shows, take a picture" is not evidence. A review blocked on a spinner nobody had seen (APC-253, [agents/card-implementer.md](agents/card-implementer.md)).
- Every timestamp the lead writes comes from the clock read in the same turn, right before the write; guessed times ahead of the clock recurred three times in two days ([skills/lead-loop/SKILL.md](skills/lead-loop/SKILL.md)).

## 2026-11-17
- After a fix round a worker re-reads every comment, header and doc sentence in the files it touched against the final behaviour and deletes what no longer holds; a measured figure is named for what it measures; a check that parses a log fails when a passing test yields nothing to parse. Two review rounds on one card went to stale sentences (FLD-334, [agents/card-implementer.md](agents/card-implementer.md)).
- Disk is read before the lane is given and before each cold boot: a first boot of an erased simulator takes about 11 GB through swap, and one long run fell from 36 to 22 GB, one above the stop line. The lane is given with about 40 GB free; Rust worktrees are cleaned at hand-back ([skills/lead-loop/SKILL.md](skills/lead-loop/SKILL.md), [agents/card-implementer.md](agents/card-implementer.md)).
- The hand-back's device table has a fixed list of rows kept in the app repo's own instructions, the nightly's device included, and the lead checks the table against it before spending a reviewer. An incomplete table cost a review round (FLD-329).
- A local whole-plan run counts as evidence only if it is the run CI makes: a local script's extra host let three tests change the device's pose mid-plan and 19 later tests failed, which CI never sees (FLD-329).

## 2026-11-16
- In-depth retro of FieldApp's stage 1 (102 PRs in two weeks, [RETRO.md](RETRO.md)). Five mistakes had recurred after their rule was written, because the lessons sat in the retro log, this changelog and a brief attachment, none of which a worker reads. Changes: the hand-back now has two required sections (each new test failing on the old code; a table of every device CI runs the touched tests on, at the final commit), the reviewer checks them before anything else and returns a hand-back that lacks them, review rounds are counted with a written split-or-continue decision before a fourth, the refused shell forms are listed for workers, and lessons are folded into the agent files at every merge instead of about every ten cards ([agents/card-implementer.md](agents/card-implementer.md), [agents/card-reviewer.md](agents/card-reviewer.md), [skills/lead-loop/SKILL.md](skills/lead-loop/SKILL.md)).
- Correction to the 2026-11-12 entry on commits after a review pass: in practice ten PRs merged with a later test-only or comment-only commit that the lead checked alone. The rule now says that: such a commit may be checked by the lead with the diff quoted on the PR; a commit touching app code or CI scripts gets a fresh reviewer.
- The owner's two answers to the retro. A bar for findings: one becomes a card only when a person would notice it in normal use or it breaks a test; small cosmetic ones go on a per-app "later" list that never blocks. And "leave the place better than you found it": a worker fixes small things in the area it is already building and proving, in the same PR, listed under "Improvements beyond the card"; settled logic, rules, formats and decisions are off limits ([agents/card-implementer.md](agents/card-implementer.md), [agents/card-reviewer.md](agents/card-reviewer.md)).
- Guard hook: pushes to this repo's `main` no longer ask the owner (it has no `dev` branch; the sync scan gates each push). Force-pushes are still denied ([hooks/guard.py](hooks/guard.py)).
- The lead's handover note carries an "owed to the owner" list, read at every check-in, after one request went undelivered for four days.
- This repo: first sync of the live files ([scripts/sync.py](scripts/sync.py)), and the restore kit ([BOOTSTRAP.md](BOOTSTRAP.md)).
- Lockfiles are verified with the CI's npm major before a push. A lockfile written by a newer local npm failed `npm ci` on the Linux runner (FLD-328).
- Each new test runs on every device its CI job covers before hand-back. A nightly went red on a test run only on one device (FLD-325).

## 2026-11-15
- Taste work is "an iteration" until the owner accepts it; per-element status has two end states ([docs/design-work.md](docs/design-work.md)).
- After a machine restart killed every worker: hand-backs must be complete enough to restart a worker from; nothing worth keeping goes in `/tmp`; the lead does not script GUI apps on the runner machine (FLD-326, FLD-323).
- New UI tests run once on the device each CI tier uses before merge.

## 2026-11-14
- Start gate raised from 10 to 12 GB of swap: stale swap sat at 11.3 GB with nothing booted and 79% of memory free ([scripts/macgate.sh](scripts/macgate.sh)).
- Shared lane rules file for briefs; code is reviewed before a worker's first lane slot on multi-item cards ([examples/lane-rules.md](examples/lane-rules.md)).
- Screen sessions on the build machine may run without asking, one at a time, never beside a simulator run.
- Workers shut simulators down by UDID only, never all at once.
- Visual pitches use an anti-slop brief, parallel illustrator agents and a render-critique-fix loop.

## 2026-11-13
- Stop rule, third version: readings in the first 5 minutes after a simulator boots are not counted. A cold boot alone tripped the two-readings rule ([scripts/macstop.sh](scripts/macstop.sh)).
- Small reversible choices are decided by the lead after about 15 minutes and listed under "Decided for you" on the dashboard.
- The priority app owns the lane; other apps ask before any simulator run over about 15 minutes. A whole suite had held the lane 80 minutes.
- Investigation figures and suspected causes stay in the hand-back, not in code comments or commit messages. Such sentences caused five of six review rounds on FLD-311.
- Security filters are allowlists from the start; reviewers on security cards try to break the code (STU-121).
- Answered questions are checked on every lead pass.

## 2026-11-12
- "One card, one PR" dropped: related small cards are bundled into one worker run and one PR; each card keeps its own "Done when" check and status.
- Stop rule, second version: stop only on two bad readings in a row about 2 minutes apart.
- Lead acceptance is not a review: every commit after the last reviewer pass gets a fresh reviewer before merge (STU-73).
- Reviewers use one read-only command per shell call; read-only git, gh and text commands went on the allow list.
- Workers read free disk with every stop-rule reading and stop under 21 GB. A long suite took it from 35 to 20 GB through swap.
- Dashboard order: open questions, then per-app tiles, then activity.

## 2026-11-11
- Lead loop set up: the [lead-loop](skills/lead-loop/SKILL.md) and [back-to-work](skills/back-to-work/SKILL.md) skills, the [implementer](agents/card-implementer.md) and [reviewer](agents/card-reviewer.md) agents, the [guard hook](hooks/guard.py) with a 21-case self-test, the [attention hook](hooks/attention.py). One lead, the only writer of card status.
- First card through the loop (STU-112): three review rounds, each finding what the worker's checks missed.
- A PR push counts as the lane: a simulator-free worker's push started CI during another worker's run (swap 16 GB, load 260 to 320). Workers hold pushes.
- Stop rule, first rework: swap over 13 GB and (load over 30 or free memory under 15%), instead of swap alone. Simulators are erased at the end of a card, not between runs. Start gate raised from 8 to 10 GB.
- Any rule can be renegotiated: bring readings and one proposed replacement.
- Merges and PR comments need no check-in once a separate reviewer passed and CI is green; the guard hook enforces the "Review: PASS" comment.
- Dashboard: "Needs you", "Since you last looked" and "In flight" views, with a test that pins the old counts.
- Folded into the skills: copy pictures out of `build/` after each run; diff regenerated data line by line; stage cold starts.

## Before the lead loop
- 2026-11-10: follow-up cards are done in the current phase, not pushed to a backlog; the lead starts full proof runs itself.
- 2026-11-08: all simulator and build work stops when the owner needs the machine, until he says otherwise.
- 2026-11-07: older restrictions on using other simulators lifted; the memory gate stays.
- 2026-11-06: a merged card is Done; proof that must wait becomes a separate card in a later stage.
- 2026-11-05 and 11-06: roadmap cards for two apps moved from markdown files to the dashboard's database ([dashboard/ROADMAP-DB.md](dashboard/ROADMAP-DB.md)); a third followed on 11-11.
- 2026-11-04: the build machine crashed twice under parallel simulator workers and CI. One simulator worker at a time; check load before starting.
- 2026-11-03: PRs merge without asking when CI is green and a separate thread reviewed. CI simulators are erased at the end of every job; the free-disk gate went from 25 to 20 GB.
- 2026-11-02: a worktree is removed only after the worker's final hand-back. One was removed at merge while its worker was still using it.
- 2026-11-01: the lead watches CI duration and failures and proposes cards.
- 2026-10-29: agents validate UI themselves in the simulator and read the screenshots; the owner does not test by hand.
- 2026-10-20: feature PRs target `dev` with a fast CI tier; a `dev` to `main` PR runs the full suite.
