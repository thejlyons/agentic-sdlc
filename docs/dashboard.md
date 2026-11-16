# The dashboard

The dashboard is a private web page with a small document database behind it. It is the roadmap: one
document per card, read by the owner on a phone and written by the lead session. This repo describes it and
includes its source; it has no screenshots, because the real page shows private roadmap cards.

- Data model and write rules: [dashboard/ROADMAP-DB.md](../dashboard/ROADMAP-DB.md)
- Page source: [dashboard/site/](../dashboard/site/index.html); every counting rule is a pure function in
  [dashboard/site/logic.js](../dashboard/site/logic.js) with a test in
  [dashboard/tests/logic.test.js](../dashboard/tests/logic.test.js)
- Card tool: [dashboard/roadmap_card.py](../dashboard/roadmap_card.py)
- Rebuilding it from this repo: [dashboard/RESTORE.md](../dashboard/RESTORE.md)

## Data model in brief

A card document carries `id`, `app`, `title`, `stage`, `area`, `type`, `size`, `priority`, `status`,
`needs_j`, `pr`, `created`, a markdown `body` (running notes first, then "Done when" checkboxes), a
`comments` array (the owner's answers), a `history` array (one entry per status change, with time, author
and a note) and `updated`. Statuses: Backlog, Next, In progress, In review, Done, Released. A
`meta/lead_checkin` document records when the lead last reported.

Cards began as markdown files in a vault repo. Apps were moved to the database one at a time; an app whose
vault folder holds a freeze marker is read and written in the database, the others are shown read-only from
a mirror file built by [dashboard/sync_vault.py](../dashboard/sync_vault.py).

## What the page shows, top to bottom

The order is the owner's (2026-11-12): open questions first, and only when there are any; then the per-app
percentage tiles; then "Since you last looked" and "In flight".

1. Top line: how many cards need the owner, how many are in flight, when the lead last checked in.
2. Needs you: one block per open question.
3. Decided for you: choices the lead made after waiting.
4. App tiles: percent built per app for its current phase.
5. Since you last looked, In flight, and what is left in the stages in scope.
6. All cards, with an editor for any card.

## The counting rules

These are fixed. Layout may change; a counting rule changes only with the owner's agreement, and a test runs
the previous `logic.js` beside the new one to prove no tile number moved.

- **Built** means `Done` or `Released`. Both count the same; the tile tracks building, not shipping. Done
  cards with a PR also show as a muted "need release" count until the next release PR merges.
- **Current phase** of an app is the lowest stage that still has unfinished cards. While that phase is stage
  0 or 1, the tile's big number is built cards over all cards in that phase; once an app is past stage 1, it
  is built cards over all stage 0 and 1 cards ("Before the license").
- **Needs you** counts cards in the early stages (0 and 1) with `needs_j: true`, not built, that the owner
  has not answered. Later-stage questions are folded below.
- **Answered** means a comment from the owner newer than the card's last history entry. The card stops
  counting until a newer history entry appears.
- **Since you last looked** lists each card once, under its last real move inside the window. The window
  starts at this device's previous visit when that is older than the lead's check-in, else at the check-in,
  else 24 hours back.
- **In flight** is In progress and In review, newest change first.
- **Quiet** marks a card In review for 24 hours or In progress for 72 hours without a change. Never for
  cards waiting on the owner, cards past stage 1, or cards mirrored from the vault.

## Questions, and "Decided for you"

To ask, the lead sets `needs_j: true`, puts the question with its recommendation as the first paragraph of
the card's notes, and adds a history entry in the same write. The page shows that paragraph and nothing
else, up to 600 characters. The owner answers on the page; the answer lands in `comments`. The lead then
clears `needs_j` and records the decision and date. An answered card leaves the owner's view once handled.

A question parks one card. The lead moves on to the next.

For simple, reversible choices (a small layout or wording call, which of two built options), the owner's
rule since 2026-11-13: if there is no answer in about 15 minutes, the lead goes with its recommendation. It
clears `needs_j` and sets `lead_decided: {at, question, choice}` on the card. The page lists these under
"Decided for you", each with a "Looks good" button that closes it. A reply instead asks for a change; the
lead makes it and then closes the item. This does not apply to anything on the always-ask list
([guardrails.md](guardrails.md)), or to scope and pricing.

## Rules for the writer

- **One writer.** Only the lead writes status. Workers and subagents cannot reach the database, and writes
  are last-writer-wins guarded only by a version check. On a version mismatch the lead reads again and
  resends.
- **Real clock times.** `history[].at`, `updated` and the check-in time are compared with each other and
  with the reader's clock. A rounded or future time shows as "just now" or hides an entry from the window.
- **One history entry per real step**, with a note the owner can read on its own.
- **Write in the same turn as the event.** A stale dashboard is the first thing the owner notices.

## Known limits

Arrays replace wholesale on update, so the writer must send the whole history back. A write call is capped
at about 64 KB; one bulk import by hand failed for that reason and was moved to the page itself. Pictures in
card bodies do not render. The old vault dashboard still counts the frozen folders, so its numbers for
migrated apps are stale.
