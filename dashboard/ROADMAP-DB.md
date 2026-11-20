> Live version as of 2026-11-20, sanitised by scripts/sync.py; app names and ids are the example config's.

# Roadmap cards in the artifact database (FieldApp, StudyApp, AppC, AppD)

The cards of these apps live in the database of the artifact **studio roadmap**:
$DASHBOARD_URL (slug `$SLUG`).

Page versions (2026-11-11): live `<page-version>` (the page described under "What the page shows");
roll back to `<page-version>` (AppC in the database, old layout); before that `<page-version>`.
The source before any of it is `~/.claude/lead/dashboard-backup/`. Tests:
`node --test ~/.claude/lead/dashboard/tests/logic.test.js`.

| App | Collection | Since | Vault snapshot (frozen, don't edit or read for status) |
|---|---|---|---|
| FieldApp | `fld/FLD-<n>` | 2026-11-05 | `Roadmaps/FieldApp/` at `97a0f33` |
| StudyApp | `stu/STU-<n>` | 2026-11-06 | `Roadmaps/StudyApp/` at `d953b33` |
| AppC | `apc/APC-<n>` | 2026-11-11 | `Roadmaps/AppC/` at `1146862` |
| AppD | `apd/APD-<n>` | 2026-11-20 | `Roadmaps/AppD/` at `372b06a` |

**Rule for the coordinator and every worker: FieldApp, StudyApp, AppC and AppD card
status, PR, notes and new cards are written to the database, never to the vault.** Each frozen folder
has a `_FROZEN.md`, and the vault's CLAUDE.md says the same. The other apps (AppF, AppG,
AppE) stay in the vault; the page shows them read-only from `mirror.js` (see `sync_vault.py`).

The database can only be written through the claude-artifacts MCP tools (`db_get`, `db_list`,
`db_query`, `db_write`) or by J on the page. There is no shell or HTTP path, so `roadmap_card.py`
only builds payloads; a Claude thread sends them. (`fld_card.py` still works: it is
`roadmap_card.py` with FieldApp as the default app.)

## Layout

| Path | What |
|---|---|
| `fld/<id>`, `stu/<id>`, `apc/<id>`, `apd/<id>` | One document per card (new cards: next free number of that prefix) |
| `meta/fld_import`, `meta/stu_import`, `meta/apc_import`, `meta/apd_import` | Written by the page when its import from the vault finished: `{done, at, written, total, vault_commit, …}` |
| `meta/lead_checkin` | `{at, by}`, written by the lead each time it reports to J |

The page itself (`site/`): `logic.js` `DB_APPS` lists the DB apps and their collections; `app.js`
subscribes to each, shows them as live tiles, lists them in "All cards" (app picker), and lets J
edit any of them the same way. Everything else comes from `mirror.js`, which `sync_vault.py`
builds without the DB apps (`sync_vault.DB_APPS`, same list).

Write access: owner and Editors only (`write: "admin"` on the whole database).

## What the page shows and where each number comes from

Top to bottom. Every rule is a pure function in `site/logic.js` with a test in `tests/logic.test.js`.

| Section | Reads | Rule |
|---|---|---|
| Top line | cards, `meta/lead_checkin` | "N cards need you": stage 0 and 1 cards with `needs_j: true`, not built, that J hasn't answered (`openAsks`). "N in flight": the In flight list. "lead checked in": `lead_checkin.at`. |
| Line under it | load state | Names any DB app still loading or unreadable; its cards are then missing from every list. |
| Needs you | `needs_j`, `body`, `comments` | One block per stage 0 or 1 ask, showing the first paragraph of the card's notes as the question. J's answer is appended to `comments` (`by: "J"`); the card then reads "answered" and stops counting until a newer `history` entry appears (`answerOf`). needs_j cards in stages 2, 3 and After 1.0 are folded below. |
| Since you last looked | `history`, `meta/lead_checkin`, this browser | Cards with a `history` entry after the start of the window, each once under its last move: Built (Done), Released, Went to review, Started, Queued next, Moved back, New cards, Notes added (`changesSince`). The window starts at this device's previous visit when that is older than the check-in, else at the check-in, else 24 h back (`sinceWindow`). Vault apps: cards built in the window only. |
| In flight | `status`, `history`, `comments`, `updated` | In progress and In review, newest change first. "Quiet": In review 24 h or In progress 72 h without a change; never for needs_j cards, cards past stage 1, or vault cards (`inFlight`). |
| Left before the license | `stage`, `status` | Unbuilt stage 0 and 1 cards per app, moving ones first (`preLicenseLeft`). Stages 0 and 1 together, unlike a tile, which counts the current phase. |
| Apps (tiles), charts | as before | `summarize`; unchanged since before 2026-11-11 and guarded by a test that runs the old `logic.js` beside the new one. |

What the lead must do for this to read right (nothing new to maintain, only how it is written):

- **Real clock times.** `history[].at`, `updated` and `meta/lead_checkin.at` are compared with each
  other and with the reader's clock. Rounded or future times show as "just now" and can hide an
  entry from the window. Use the time of the write.
- **The question first.** When setting `needs_j: true`, put the question as the first paragraph of
  the card's notes (under the title, above everything else, 600 characters at most are shown), and
  add a `history` entry in the same write. J's answer arrives in `comments`; after acting on it,
  clear `needs_j` or add a `history` entry (a newer entry is what makes the card count again).
- **One history entry per real step**, with a note J can read on its own: the note of the newest
  entry is what the page prints under the card.
- **`meta/lead_checkin`** on every report to J, as before.
- Until an app's `meta/<col>_import` exists (or when `meta` can't be read) the page fills cards the
  database lacks from that app's seed file, so its tile is never a partial count.

## A card document

```json
{
  "id": "STU-54", "app": "StudyApp", "title": "…",
  "stage": "1 Free build", "area": "CI", "type": "Feature", "size": "M", "priority": "P1",
  "status": "In progress",          // Backlog | Next | In progress | In review | Done | Released
  "needs_j": false,                 // boolean
  "pr": "23",                       // as in the vault: a number, "#n", a URL, or "repo#n"; "" for none
  "created": "2026-10-28", "tags": ["card"], "notion": "https://…",   // notion only on migrated cards
  "body": "\n# Title\n\nRunning notes…\n\n## Done when\n- [ ] …\n",      // the full markdown after the frontmatter
  "comments": [{"at": "ISO", "by": "J", "text": "answer to the question…"}],
  "history":  [{"status": "In review", "at": "ISO", "by": "claude", "note": "PR #123 into dev"}],
  "updated": "ISO", "updated_by": "claude",
  "source": {"file": "Roadmaps/StudyApp/….md", "vault_commit": "d953b33",
             "frontmatter_raw": "…", "body_sha256": "…"}   // the vault snapshot it came from
}
```

- `history` holds status changes only, oldest first. The import filled it from the vault's git log
  (one entry per status change, the commit subject as `note`, `by: "vault"`); an entry with
  `imported: true` is a card that arrived already built from the Notion migration.
- `comments` are J's notes and answers from the page (and yours, if you need to leave one). The
  running notes stay the body's first paragraph, as in the vault.
- "Done when" checkboxes are `- [ ]` / `- [x]` lines in `body`; the page toggles them in place.
- Field names and values are the vault's (README.md) so the dashboard rules don't change.

## Write path for the coordinator and workers

Every op on an existing document needs `ifVersion`, and arrays (`history`, `comments`) replace
wholesale in an `update`, so always read first and send the whole array back with your entry added.
One `db_write` at a time; after a call with many ops wait 2 s; at most 50 ops per call.

1. Read: `db_get slug=$SLUG path=stu/STU-54` -> `version` and the data.
2. Write (example: STU-54 to In review with PR 80):

```json
db_write slug=$SLUG ops=[{
  "op": "update", "path": "stu/STU-54", "ifVersion": 1,
  "data": {
    "status": "In review", "pr": "80",
    "updated": "2026-11-06T18:10:00Z", "updated_by": "claude",
    "history": [ …every existing entry…,
      {"status": "In review", "at": "2026-11-06T18:10:00Z", "by": "claude", "note": "PR #80 into dev"} ]
  }
}]
```

   A `version_mismatch` (409) means someone (often J on the page) changed the card since your read:
   read again and resend. Nothing was written. (FieldApp: the same with `fld/FLD-<n>`.)
3. Running notes: change `body` (whole string) in the same `update`; keep it short and dated, as in
   the vault rules. Ticking a "Done when" item is a `body` change too.
4. Done when the PR into dev squash-merges; Released when the dev -> main PR containing it merges
   (same rules as the vault's CLAUDE.md). Several cards at once: one `db_write` with up to 50 ops,
   each with its own `ifVersion` (read them with `db_list collection=stu` or `db_query`).
5. New card: `db_write` op `set` (no ifVersion) at `stu/STU-<next>` with the shape above,
   `history: [{"status": "Backlog", "at": …, "by": "claude", "note": "filed: why"}]`,
   `comments: []`, `source: {}`. Next number: one more than the highest id in `db_list collection=stu`
   (StudyApp: 114 is next as of the move). `roadmap_card.py new` prints that op.

`roadmap_card.py` builds the same payloads, so you don't hand-assemble the history array:

```sh
# save db_get's version and data as {"version": n, "data": {...}} in card.json, then:
python3 ~/.claude/lead/dashboard/roadmap_card.py op card.json --status "In review" --pr 80 --note "PR #80 into dev"
python3 ~/.claude/lead/dashboard/roadmap_card.py op card.json --comment "Asked J about the sort order" --by claude
python3 ~/.claude/lead/dashboard/roadmap_card.py new --app StudyApp --id STU-114 --title "…" --stage "1 Free build" --note "why"
python3 ~/.claude/lead/dashboard/roadmap_card.py to-md card.json > STU-54.md   # back to vault markdown
```

Read-only questions (what's in review, what needs J):
`db_query slug=… collection=stu where=[{"field":"status","op":"==","value":"In review"}]`.

## The imports

- FieldApp (2026-11-05): FLD-234 written by a thread with `db_write`; the other 235 imported by the
  page on J's first visit from its file `fld_seed.js` (vault `97a0f33`); `meta/fld_import` done.
  FLD-237 was filed in the vault after the freeze and moved to the database by the coordinator.
- StudyApp (2026-11-06, vault `d953b33`, 113 cards): STU-1..STU-55 written by threads with `db_write`
  (`out/stu_import/batch_01-02.json`; read back: all 55 present, status and pr equal to the vault).
  Passing the rest by hand failed (a 55 KB tool call got cut off), so STU-56..STU-113 are imported
  by the page from `stu_seed.js` the next time J opens it; it then writes `meta/stu_import`
  (`written`, `already`, `repaired`). The same run compares every card still `updated_by: "import from
  vault"` with the seed and rewrites any that differ, so a slip in the hand-copied 55 is repaired.
- Until `meta/stu_import` exists, a worker that finds a StudyApp card missing (`exists: false`) writes it
  first: `python3 roadmap_card.py import --app StudyApp` makes `out/stu_import/batch_NN.json`; send that
  one card's `set` op as it is (no ifVersion), then make your change on top. Don't hand-copy a whole batch.
- AppC (2026-11-11, vault `1146862`, 235 cards): the 26 cards that were not built (APC-45, 50-54,
  56-59, 62-64, 68, 76-78, 80-82, 86, 88, 170, 179, 233, 235) written by a thread with `db_write` in
  three calls of 13 to 18 KB (`out/apc_import/open_1..3.json`; read back: all 26 present, status and pr
  equal to the vault). The 209 built cards are imported by the page from `apc_seed.js` the next time J
  opens it; it then writes `meta/apc_import`. Until that document exists:
  - the page shows every AppC card the database doesn't hold yet from the seed (`fillFromSeed`
    in `logic.js`), so the tile's numbers are the vault's from the first moment, not a partial count;
  - a worker that finds an AppC card missing (`exists: false`) writes it first from
    `out/apc_import/batch_NN.json` (that one card's `set` op as it is), then makes its change on top.
  Next new id: `APC-236`.
- AppD (2026-11-20, vault `372b06a`, 323 cards, APD-1..APD-323): all imported by the page
  from `apd_seed.js` (`roadmap_card.py seed --app "AppD"`) the next time the owner opens
  it; it then writes `meta/apd_import`. Until then the page fills from the seed exactly as for AppC (tile numbers equal the old mirror's, guarded by tests, which keep the old rows in
  `tests/apd_mirror_before.json`). Cards in flight at the move (APD-321 In progress, APD-323 Backlog with
  needs_j) are in the seed as the vault had them; a status changed in the vault after `372b06a` must
  be re-applied in the database. A worker that finds a card missing before the import is done writes
  it from `roadmap_card.py import --app "AppD"`. Next new id: `APD-324`.
- Moving another app later: add it to `DB_APPS` in `sync_vault.py` and `site/logic.js`, run
  `roadmap_card.py seed --app <App>`, publish the seed and the page, re-run `sync_vault.py` and
  publish `mirror.js`, freeze its vault folder with a `_FROZEN.md`, and update this file.

## Keeping the mirrored apps right

The page knows the vault only as of the last `sync_vault.py` run. Re-run it and publish `mirror.js`
after vault commits that change mirrored cards (the command it prints). Its output lists, per app,
both numbers Obsidian's Dashboard shows: the per-app block ("Phase X" while the phase is stage 0 or 1,
else "Before the license" over all stage 0 and 1 cards), which is the tile's big number on the page,
and the top summary tile (the current phase's x/y), which the page lists under it once the phase
is past the license.

## What could lose information versus the markdown

- Nothing at import: every card's frontmatter (raw text kept in `source.frontmatter_raw`) and body
  round-trip byte for byte (`roadmap_card.py to-md`).
- Images: bodies keep their paths, but the page can't show vault pictures.
- A document is capped at 256 KB (the largest card is ~15 KB) and a `db_write` call at about 64 KB.
- Wikilinks (`[[STU-12]]`) show as text on the page, not links.
- Two writers, one card: writes are last-writer-wins, guarded only by `ifVersion` on the tool side.
- Obsidian's Dashboard still counts the frozen folders, so its FieldApp, StudyApp, AppC and
  AppD numbers are the snapshot's, not live.
