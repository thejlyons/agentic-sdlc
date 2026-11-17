---
name: back-to-work
description: J's resume ritual for the studio. Use when J says "back to work", "status", "where are we", "what needs me", or opens the workspace after time away. Produces the short status report from the dashboard, vault and GitHub, then dispatches the next roadmap cards.
---

> Live version as of 2026-11-16, sanitised by scripts/sync.py. App names (FieldApp, StudyApp), card ids (FLD-123), `$TOKENS` and the machine's numbers are example values: at run time the real ones come from `~/.claude/lead/config.json` (config/SCHEMA.md) and win wherever they differ.

# Back to work

J has been away for hours and is probably on a phone. He wants four things in one screen: what got done, what is in flight, what is blocked, what needs him. Then he wants the work to keep moving without further input. Load `lead-loop` for how cards are dispatched and recorded; this file is only the ritual.

Card state lives in the dashboard database, the vault, GitHub and the running sessions, so rebuild it from those every time. What they do not hold (work that is not a roadmap card, open questions with J, promises, the order of work) is in `~/.claude/lead/STATE.md`: read it FIRST in a fresh session, and trust the live sources over it where they disagree.

## When J should start a fresh session (J, 2026-11-16)

A long session re-reads its whole history on every turn, so the lead is replaced, not kept. The rule J follows: start a fresh session and say "back to work" (1) at the start of each day, (2) when a milestone closes and the next work is a different project or app, and (3) whenever the lead says "good moment for a fresh session" (it says so after the conversation has been summarised twice, or after about a day). There is ONE lead for the whole company (every app, the game, the public process repo): J wants a single place to talk to, so never split the lead by project; keep it cheap by keeping its history short, not by dividing it. Before any of these, the lead rewrites `STATE.md`; J loses nothing by switching. A fresh lead must recreate the overnight check cron (it is session-only).

## 1. Gather (run these together)

- **Since when**: `db_get` `meta/lead_checkin` on artifact `$SLUG` gives `at` from the last report. Missing: use 24 hours ago.
- **Database apps** (folders with `_FROZEN.md` in the vault's `Roadmaps/`): `db_query` each collection for `status in ["In progress","In review","Next"]`, and for `needs_j == true`. From the results, done since last time = cards whose `history` has a `Done` or `Released` entry after `at`; for those, also `db_query` `status == "Done"` ordered by `-updated` with a small limit.
- **Vault apps**: `git -C $VAULT pull -q --rebase origin main`, then `git log --since=<at> --format='%s'` for card commits, and `grep -l` for `status: "In progress"`, `status: "In review"` and `needs_j: true` under the non-frozen `Roadmaps/` folders (count `needs_j` only on cards that are not Done or Released).
- **GitHub**, for each app repo with work in flight: `gh pr list --json number,title,baseRefName,statusCheckRollup` and `gh run list --limit 5`.
- **Workers**: `claude agents --json --all`, new files in `~/.claude/lead/handbacks/`, and `~/.claude/lead/attention.jsonl`.
- **The Mac**: `~/.claude/lead/bin/macgate.sh`.

Check each in-flight card against reality: a card `In progress` with no live worker and no recent commit is stalled, not in flight. Say so.

## 2. Report

Under 15 lines, plain sentences, the thing J must act on first. Use these headings and drop any that are empty:

```
**Needs you** (n)   one line each: the decision, your recommendation, where the pictures are
**Done since <when>** (n)   card ids with five-word titles; group by app
**In flight**   card, who is on it, what it is waiting for
**Blocked / stalled**   card and the cause
**Next up**   what you are dispatching now
Pre-license left: <prefix> n, for each app in the config
```

Anything longer (a failure log, a set of screenshots, a comparison) goes in an artifact, linked in one line. Dashboard: $DASHBOARD_URL

## 3. Record the check-in

Write `meta/lead_checkin` with `{"at": "<now, ISO>", "by": "lead"}` (`set`; with `ifVersion` when it exists).

## 4. Keep moving

Without waiting for a reply: collect finished hand-backs, start reviews, merge what is green and reviewed, and dispatch the next cards within the lane rules in `lead-loop`. J's answers to "Needs you" items unpark those cards when they arrive; nothing else waits on them.

If J's message came with instructions ("back to work, and skip StudyApp today"), they override the default order for this session.
