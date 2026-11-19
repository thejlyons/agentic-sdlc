---
name: lead-loop
description: How the lead session runs studio roadmap cards end to end - pick, spec, dispatch a background worker, review, merge, record status on the dashboard, ping J. Use when dispatching or collecting a card worker, changing any card's status, deciding what runs on the simulator lane, asking J something, or writing a retro entry.
---

> Live version as of 2026-11-18, sanitised by scripts/sync.py. App names (FieldApp, StudyApp), card ids (FLD-123), `$TOKENS` and the machine's numbers are example values: at run time the real ones come from `~/.claude/lead/config.json` (config/SCHEMA.md) and win wherever they differ.

# Lead loop

You are the lead for the studio: you triage, spec, dispatch, review and report. Workers build. J reads on a phone, checks in every few hours, and should meet only finished work and real decisions. The current goal is `goal` in the config. The example goal is "pre-license complete": every stage 0 and 1 card built in every app; stages 2, 3 and After 1.0 wait.

This skill adds the orchestration on top of `vault-sdlc` (card and PR rules), `apple-ci-standards` (CI tiers, the Mac), and a working-with-the-owner skill (asking and reporting). Where they disagree with this file on who records status or who reviews, this file is newer.

There is one lead. Only the lead writes card status, because subagents and workers cannot reach the dashboard database and two writers fight over card versions.

## Where a card lives

Check for `Roadmaps/<App>/_FROZEN.md` in `$VAULT`. That marker is the switch, so this keeps working as J migrates apps.

| | Marker present (apps with `roadmap: "dashboard"` in the config; example: FieldApp `fld`) | No marker (apps with `roadmap: "vault"`) |
|---|---|---|
| Read | `db_query` / `db_get` on artifact slug `$SLUG` | the card file in `Roadmaps/<App>/` |
| Write | `db_get` for the version, build the op with `python3 ~/.claude/lead/dashboard/roadmap_card.py op card.json --status … --pr … --needs-j … --note …`, send it with `db_write` (`ifVersion`; on 409 read again and resend) | pull, edit frontmatter and the notes paragraph, commit `<ID>: <what>`, `git push origin HEAD:main`; then `python3 ~/.claude/lead/dashboard/sync_vault.py` and publish `mirror.js` with the command it prints |

Details and the document shape: `~/.claude/lead/dashboard/ROADMAP-DB.md`. Vault field rules: the vault's `CLAUDE.md`. Never change how the dashboard counts, and never edit a frozen folder.

Queries return whole card bodies, so filter hard: by `status` in (`In progress`, `In review`, `Next`), by `needs_j`, or by `stage` + `priority` when choosing the next card. Do not list a whole collection.

## Status changes are part of the step, not a later chore

| Moment | Write |
|---|---|
| Worker launched | `In progress`, note: worker name, branch |
| PR opened | `In review`, `pr` |
| Squash-merged into `dev` | `Done` at once; tick "Done when" boxes; proof that must wait for the license becomes a new `2 Paid` card |
| Question for J | `needs_j: true`, the question and your recommendation at the top of the notes |
| J answered | `needs_j: false`, the decision and date in the notes |
| dev to main merged | `Released` for every Done card whose PR is in `main` |

Every `at` and `updated` you write is the real clock time (`date -u +%Y-%m-%dT%H:%M:%SZ`, run in the same turn right before the write; leads guessed times ahead of the clock on 2026-11-17 and twice on 2026-11-18), never a rounded or guessed one: the dashboard decides whether J has answered a question, and what happened "since the last check-in", by comparing these times. When you set `needs_j`, put the question itself, with your recommendation, as the first paragraph of the card's notes; the dashboard's "Needs you" box shows that paragraph and nothing else.

Make the write in the same turn as the event. If a write fails, retry it before anything else; a stale dashboard is the thing J notices first.

## Picking the next card

Order: finish `In review`, then `In progress`, then `Backlog` by priority (P0, P1, P2, P3), smaller first within a priority. Skip cards with `needs_j` and cards whose "Depends on" is not built. Only stages starting `0` or `1`.

Bundle related small cards (same screen, pose or test area) into one worker session and one PR; J dropped "one card, one PR" on 2026-11-12 because each PR costs a cold boot, a build, a review and a CI slot. Every card ID goes in the PR title, the reviewer checks each card's "Done when" separately, and each card keeps its own status and history. Do not bundle unrelated areas or a risky change with safe ones.

App order on the simulator lane is `apps[].lane_priority` in the config (J, 2026-11-11; example: FieldApp until it has no stage 1 cards left, then StudyApp). Cards of a lower-priority app that need no simulator (core, web, content packs, CI scripts) run alongside the whole time. J's rollout rule still holds: port a pipeline lesson to the next app only after the source app is parked.

## The simulator lane

The build machine (`machine` in the config; the live one is a 16 GB Mac mini) crashed twice under parallel simulators. One lane: a single simulator worker OR a single CI run (a PR push counts, it boots a CI simulator). So:

- At most one lane-holding worker. Sim-free workers may run beside it, at most two, and hold their pushes.
- Before starting a lane worker, a push, or a full run: `~/.claude/lead/bin/macgate.sh` must exit 0 (load under 30, swap under 12 GB, nothing booted, no CI run active; the limits are `machine.gate`). To wait for it, run `~/.claude/lead/bin/waitgate.sh` in the background. Also read free disk (`df -g /System/Volumes/Data`): give the lane only with about 40 GB free (2026-11-17: a cold boot takes about 11 GB through swap and an iPad run fell from 36 to 22 GB, one above the stop line); get space first by having idle Rust worktrees `cargo clean`. Before spending a reviewer, check the hand-back's device table against the repo's CLAUDE.md row list, nightly device included (2026-11-17: an incomplete table cost a review round).
- One PR in CI at a time. Release the lane to the next worker only after that CI run ends.
- While a simulator job runs the stop rule is `~/.claude/lead/bin/macstop.sh` (J, 2026-11-11): a reading is bad when swap is over 13 GB and load is over 30 or free memory is under 15%, and the job stops only on two bad readings in a row about 2 minutes apart (J, 2026-11-12: a cold boot alone tripped the single-reading rule and cleared within a minute). Swap total alone misleads, because an erased simulator's first boot parks about 11 GB in swap. Readings in the first 5 minutes after a simulator boots are not counted (J, 2026-11-13: a cold boot alone tripped the two-readings rule); macstop reads the youngest launchd_sim's age itself. Simulators are erased at the end of a card, not between runs.
- J's standing offer: any rule set under older conditions can be renegotiated. When a rule costs work, bring him the readings and a proposed replacement instead of working around it or silently obeying it forever.
- A Vision Pro run is always alone. When J says he needs the Mac for something else, stop all simulator and build work until he says otherwise.

## Dispatch

1. Write the brief: the card text in full, the "Done when" list, which screens to capture and in which modes, lane holder or sim-free, the lead session's name for SendMessage, and anything J already decided (from the card notes and memory). State the goal and constraints; do not paste your guesses about the cause of a bug as fact.
2. Record `In progress`.
3. Launch from the app repo so the worker gets a worktree of that repo, off `dev`:

```sh
cd ~/Github/<repo> && git fetch -q origin && \
claude --bg --name <card-id> --worktree <card-id> \
  --agent card-implementer --model sonnet --advisor fable --permission-mode auto "$(cat <brief-file>)"
```

   If the launch prints "Workspace not trusted", J has not yet accepted that repo's trust prompt (he runs `claude` there once). Do not work around the prompt itself. Until then, create the worktree by hand and launch from the trusted lead workspace:

```sh
git -C ~/Github/<repo> worktree add .claude/worktrees/<card-id> -b <card-id>-<words> origin/dev
cd $LEAD_WORKSPACE && claude --bg --name <card-id> \
  --add-dir ~/Github/<repo>/.claude/worktrees/<card-id> \
  --agent card-implementer --model sonnet --advisor fable --permission-mode auto "$(cat <brief-file>)"
```

   In that case the brief must give the worktree path, tell the worker to `cd` there and to read the repo's `CLAUDE.md` itself (it is not auto-loaded).

   In every brief: J's skills are called with the prefix `anthropic-skills:` (for example `anthropic-skills:apple-ci-standards`), and `SendMessage` is a deferred tool the worker loads with ToolSearch.

   Models are `models` in the config; the live choice: UI-heavy cards (a new screen, a layout, a visual polish pass): `--model fable` and drop `--advisor`. Everything else: Sonnet with the Fable advisor. Use Haiku only for read-only scouting (`Agent` with `subagent_type: Explore`, `model: haiku`).
4. Subscribe once: `SendMessage` to the worker with `notify_when_idle: true`. Do not poll. `claude agents --json --all` shows state if you need it.

Repo names and local paths: `apps[].repo` and `apps[].path` in the config.

## Collect, review, merge

1. Read `~/.claude/lead/handbacks/<CARD-ID>.md`. Look at the screenshots yourself. Check its two required sections before spending a reviewer: "New tests failing on the old code" and the "Device table" (every device and pose CI runs the touched tests on, at the final commit). Missing or incomplete: send it straight back, no review round.
2. `needs_j` or `blocked`: park the card (below) and dispatch the next one.
3. `ready-for-review`: start the `card-reviewer` agent with the card text, worktree path, base ref (`origin/dev`) and screenshot paths. Do not pass the worker's summary of why it is right. A Sonnet-built card is reviewed on Fable (the agent's default); a Fable-built card is reviewed with `model: opus`, so the reviewer is never the model that wrote the code.
4. `CHANGES`: send the blocking items to the worker verbatim, wait for the next hand-back, review again with a fresh reviewer. Count the rounds (the hand-back's first line carries the number). Before a fourth round starts, write on the card, in its history note, either the split you made or why it continues as one card; six FieldApp PRs went to four or more rounds with no such stop, because nothing counted. Give the reviewer the hand-back's two evidence sections (failing-on-old-code table, device table) and nothing else from the hand-back.
   A commit made after a PASS: if it touches only tests, comments or docs, the lead may check it alone and quotes the diff summary in the `Review: PASS` comment; if it touches app code or CI scripts, it gets a fresh reviewer.
5. `PASS`: when the lane is free, tell the worker to push and open the PR. Record `In review`. Wait for fast CI. A red run is read line by line and fixed, never re-run for a green.
6. Green: post the reviewer's verdict on the PR as a comment that starts `Review: PASS` (reviewer model, round count, non-blocking notes). The guard hook lets `gh pr merge` through only when checks are green and that comment exists; otherwise it asks J. Post the comment and run the merge as two separate Bash calls: the hook reads the PR before the command runs, so a combined command has no comment yet and J gets a prompt (happened on STU-112). Squash-merge into `dev`, record `Done`, then triage the hand-back's follow-ups and the review's non-blocking list by the bar J set on 2026-11-16: a finding becomes a card in this phase only when a person would notice it in normal use or it breaks a test. A small cosmetic finding in a rare pose or size goes on the app's "later" list (one card per app titled "Later list", stage `After 1.0`, appended to, shown to J when the phase ends), never a blocking card. Small improvements are not deferred either way: workers make them inside the PR that already touches that area (card-implementer "leave the place better"), so expect and welcome an "Improvements beyond the card" section. A polish phase is one audit at the start and one closing check; the closing check may reopen only findings that pass the bar.
7. Stop the worker and remove its worktree only after its final hand-back is collected.
8. Add the retro line.

dev to main: open the release PR when an app's phase is finished or enough is ready, start the full run yourself once the gate passes, fix failures through feature PRs, review, then merge with a merge commit. J's standing approval covers this when CI is green and a separate reviewer passed it.

## What always asks J first

Direct push to an app repo's `main`; anything in App Store Connect; anything legal, tax, banking, purchases or domains; deleting vault content; deleting an artifact; sending email or posting publicly; and whatever `guardrails.always_ask` in the config adds. The guard hook and auto-mode rules enforce most of this, but the rule is yours to keep even where no hook fires. Never ask another session to do something that was blocked for you.

## Asking J

J's rule: a decision must not block everything. So a question parks one card, never the queue.

- Batch questions: one ask, numbered, each with a recommendation, answerable as "all yes".
- Visual choices are two or three real screenshots side by side in one gallery artifact, never descriptions.
- Record `needs_j` with the question on the card, send one `PushNotification` under 200 characters that leads with what J must decide, then go on to the next card. No second push for the same question.
- Simple, reversible choices (J, 2026-11-13): if J hasn't answered in about 15 minutes, go with the recommendation. Clear `needs_j`, set `lead_decided: {at, question, choice}` on the card, and carry on. The dashboard lists these under "Decided for you" above the app tiles until you set `lead_decided.closed: true` (after J says OK, or asks for a change and you've made it). Not for anything on the always-ask list, scope or pricing.
- Push also for: a block you cannot route around, a finished phase, a crash or stop-rule event. Not for routine progress.
- A worker stuck on a permission prompt shows in `claude agents --json --all` as `waitingFor: "permission prompt"`. Check that field on every pass; the session's `cwd` is where it was launched, not its worktree, so match by session id in the attention log. You cannot answer another session's prompt. If J approves the action, run it yourself, `claude respawn <id>` the worker (by id, not name), and tell it what you ran.
- `~/.claude/lead/attention.jsonl` lists sessions that sat waiting on a prompt (written by the Notification hook). Check it when a worker goes quiet.

## Retro

After each card and each incident, append one dated line to `Process/Retro.md` in the vault (commit and push like a card edit): card, what worked, what broke, the lesson. Take the worker's "Lessons" section into account. Fold at every merge, not later (2026-11-16 retro: folding "about every ten cards" happened once in forty cards, and five mistakes recurred because their lesson sat in this log, the changelog or a brief attachment, none of which a worker reads): a lesson that should change what a worker or reviewer does goes into `~/.claude/agents/card-implementer.md` or `card-reviewer.md` or this skill in the same turn, as a required hand-back field or a reviewer check where possible, not as one more sentence. End each retro line with `folded: <file>` or `folded: no rule needed`. Rules for one repo go in that repo's `CLAUDE.md`. Do not keep rules in brief attachments. Lessons that belong in a synced skill (`vault-sdlc`, `apple-ci-standards`, `app-ux-standards`, a working-with-the-owner skill, …) cannot be edited locally because claude.ai overwrites them; collect those as a diff and give it to J in one batch.

## Lessons folded in

- 2026-11-11 (STU-112): test scripts wipe `build/screenshots` on every run, so pictures are copied to `~/.claude/lead/handbacks/<CARD>-shots/` after each run. Regenerated data files are diffed line by line against `origin/dev` (a missing cache silently blanked 216 source links; the reviewer caught it, the worker's tests did not).
- 2026-11-11 (STU-112): four stopped runs came from cold-booting an erased simulator while compiling. Stage cold starts (boot, settle, `build-for-testing -jobs 4`, test), keep the simulator warm between runs, group long suites.

## Handover note (STATE.md)

Rewrite `~/.claude/lead/STATE.md` at every milestone (a card merged, a design delivered, a decision from J) and when J says he is starting a fresh session: order of work, what is in flight that is not a card, what is waiting on J, and an "Owed to J" list (everything J asked for that is not delivered, with the date he asked; read it at every check-in and say what is on it; a request of his sat four days in 2026-11 because no list held it). Under about 80 lines; delete what is finished. Tell J "good moment for a fresh session" when a milestone closes, after the conversation has been summarised twice, or after about a day. Reason: every turn of a long session re-reads its history, so an old lead woken many times a day is the main usage cost.
