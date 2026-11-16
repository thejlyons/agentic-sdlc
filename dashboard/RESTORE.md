# Restoring the dashboard from this repo

The dashboard is a private claude.ai artifact: one page (`site/`) plus a database of roadmap cards. This file is the procedure for standing it up again on a new account or machine, and for getting the cards back in. It is written for a Claude session with the claude-artifacts tools, with the owner at hand for the two steps only the owner can do.

What is in this folder:

| Path | What | From |
|---|---|---|
| `site/index.html`, `site/app.js`, `site/logic.js` | the page | live files, sanitised by `scripts/sync.py` |
| `ROADMAP-DB.md` | the data model, the counting rules, the lead's write path | live file, sanitised |
| `roadmap_card.py`, `sync_vault.py` | build `db_write` payloads; read a markdown vault | live files, sanitised |
| `tests/logic.test.js` | the counting rules' tests | live file, sanitised |
| `configure_apps.py` | rewrites a copy of the page and tools for your apps | written for this repo |
| `export_cards.py` | turns saved database reads into a backup | written for this repo |
| `seed/`, `example-vault/` | **example data for a made-up app** | written for this repo |
| `preview/` | open the page locally with an in-memory database | written for this repo |
| `tests/test_tools.py`, `tests/seed.test.js` | tests for the above | written for this repo |

**FieldApp, StudyApp, AppC to AppG, the `FLD-` cards, `OWNER` and `roadmap-vault` are examples.** The eight cards in `seed/fld_seed.js` and the four in `example-vault/` are invented (`seed/make_example.py` writes them). Your real apps come from `~/.claude/lead/config.json`, which bootstrap writes and which never belongs in this repo.

Where a step below comes from: steps marked **(live)** are how the live system does it (`ROADMAP-DB.md`). Steps marked **(tool guidance)** are taken from what the claude-artifacts server's `guide` and `describe_capabilities` tools said on 2026-11-16 (runtime contract 0.2.96). Read those tools again at restore time: the server's rules can change, and theirs win over this file.

## What cannot be restored from this repo

Read this first. The repo holds the page and the tools, not your data.

- **The old artifact's data**: every card, its comments, its history, `lead_decided`, the meta documents. They live only in the old artifact's database. A new artifact starts empty.
- **Card history from a markdown vault**, if the vault repo is gone: `roadmap_card.py import` rebuilds a card's status history from the vault's `git log`. Markdown files without their git history import with an empty history.
- **The lead's memory** and the hand-backs, briefs and attention log under `~/.claude/lead/`. `rules/` in this repo holds the durable rules in generic form; the memory itself is not here.
- **The old artifact's slug, URL and page version ids.** A restored dashboard has new ones; links to the old page stop working.
- **Pictures** that card bodies point at.

So export while you still have access. See the next section.

## Export while you still have access

Do this on the old account, on a schedule you choose and before any planned change of account or machine. Keep the result in a private place (a private repo or a disk). Never commit it to this repo: `export_cards.py` refuses an output folder inside it.

1. A Claude session with the claude-artifacts tools reads every collection and saves each result, unchanged, as a JSON file in a folder outside this repo, for example `~/roadmap-backup/raw/`:
   - `db_list slug=<artifact-slug> collection=<collection>` for each database app's collection (`apps[].collection` in the config), following any cursor until the list is complete; one file per page of results is fine.
   - `db_list slug=<artifact-slug> collection=meta`.
   - If `db_list` returns ids without the documents, `db_get` each one and save those results instead.
   Queries return whole card bodies, so large collections come back in pages. Do not summarise or re-type a result: save what the tool returned.
2. Convert and check:

   ```sh
   python3 dashboard/export_cards.py ~/roadmap-backup/raw/*.json --out ~/roadmap-backup/2026-11-16
   python3 dashboard/export_cards.py --verify ~/roadmap-backup/2026-11-16
   ```

   The first command writes `cards.json` (the full documents: this is the backup), `meta.json`, one markdown file per card under `Roadmaps/<App>/` and `index.md` with counts per app and status. The second re-reads the markdown and compares every field and body with `cards.json`.
3. Compare the counts in `index.md` with the dashboard's tiles. A collection that came back short is the usual failure.
4. Back up the rest of the private state the same day: `~/.claude/lead/` (config, briefs, hand-backs, queue), the lead's memory folder, and the markdown vault repo if you use one.

The markdown files hold the frontmatter fields and the body. Comments, history and `lead_decided` are only in `cards.json`. A single card: save its `db_get` result as `card.json` and run `python3 dashboard/roadmap_card.py to-md card.json`.

`export_cards.py` accepts: a list of `{path, version, data}`, an object with such a list under any key (`documents`, `docs`, ...), one `db_get` result, a bare list of card documents, and JSON Lines. The exact shape `db_list` returns was not checked against a real database for this repo (see "Not verified"), which is why the reader is tolerant.

## Restore

### 1. Configure the page for your apps

The page names its apps in a few constants. `configure_apps.py` writes a configured copy outside the repo from the private config:

```sh
python3 dashboard/configure_apps.py --dry-run
python3 dashboard/configure_apps.py            # writes ~/.claude/lead/dashboard/build/
```

It rewrites, and stops without writing anything if one is not found exactly once:

| File | Constant | From the config |
|---|---|---|
| `site/logic.js` | `APPS` | every app's `name`, in config order |
| `site/logic.js` | `DB_APPS` | apps with `"roadmap": "dashboard"`: `collection`, `prefix` |
| `site/logic.js` | `REPOS` | the repository name from `repo` |
| `site/logic.js` | `github.com/OWNER/` (twice, in `prLink`) | `owner.github` |
| `site/app.js` | `COLOR_ORDER` | every app's `name` (tile colours `--s1` to `--s7` in `index.html`; add more for an eighth app) |
| `sync_vault.py` | `DB_APPS`, `REPOS`, `github.com/OWNER/` (twice, in `pr_link`) | the same |

By hand, those are the edits. Two things it does not change: `short()` in `app.js` (optional short tile names) and the comments.

The tests are not copied. `tests/logic.test.js` pins the example names (`FieldApp`, `AppC`, `FLD-`, `APC-` ids appear in most of its tests, starting with "AppC is a database app with collection apc"), and `tests/seed.test.js` pins the example seed. Run the tests in the repo, on the example names, to check the counting rules; the configured copy differs only in the constants above.

### 2. Gather the page's files

The published page is these files, side by side:

| File | Needed | Notes |
|---|---|---|
| `index.html`, `app.js`, `logic.js` | yes | from the configured copy's `site/` |
| `mirror.js` | yes | `index.html` loads it with a script tag. Use `seed/mirror.js` (empty) when no app stays in a markdown vault; otherwise run `sync_vault.py` from the configured copy against the vault and use its `out/mirror.js`. |
| `<collection>_seed.js` | only to import through the page | one per database app, for example `fld_seed.js` setting `window.FLD_SEED`. There is no script tag for seeds: `app.js` loads `<collection>_seed.js` by name when it needs one. |

What the page does without a seed (read from `app.js`, and seen in the local preview): if `meta/<collection>_import` says `done`, nothing; the seed is never asked for. If it does not, the page tries to load the seed, fails, shows the app's database cards only, and on the owner's visit shows "The <App> import stopped (couldn't load <collection>_seed.js)" every time. So for each database app either publish a seed, or have the lead write `meta/<collection>_import` with `{"done": true, ...}` after importing by `db_write` (step 4b).

The page also loads `marked` and `DOMPurify` from cdnjs, which the artifact content policy allows **(tool guidance)**.

### 3. Publish a new private artifact with a database

Nothing in this repo publishes anything. A Claude session does this when the owner asks **(tool guidance, except where marked)**:

1. `guide` (topic `pages`) and `describe_capabilities` (capability `db`): read the current rules.
2. `publish_files` with no slug, a title, and the files from step 2 (`as` is the file name, `path` its absolute path; `index.html` is required). The result gives the new `slug`, `version` and `url`. A new artifact is visible to its owner only.
3. `read_declaration`, then `declare_capabilities` with the whole declaration: `db` and `user` (the page calls `claude.use("db")` and `claude.use("user")`). The order for a new page is publish, then declare.
4. Database rules. The live database lets signed-in viewers read and only the owner and Editors write (`write: "admin"`) **(live)**. As the guidance describes them, rules are per path with a `read` and a `write` level (`view` < `interact` < `admin` < `owner`), for example one rule per collection and one for `meta`:

   ```json
   {"db": {"rules": [
     {"path": "fld",  "read": "view", "write": "admin"},
     {"path": "meta", "read": "view", "write": "admin"}
   ]}, "user": {}}
   ```

   The exact rule the live artifact stores was not read for this repo; take the syntax from `describe_capabilities` on the day.
5. Record the new slug and URL in `~/.claude/lead/config.json` under `roadmap.dashboard` (`artifact_slug`, `url`). The skills and `sync_vault.py` read them from there.
6. The owner opens the page once. Sharing it with anyone else is the owner's choice, made on the page; no tool here changes who can see it.

### 4. Import the cards

Pick one path per app. Both write the same documents (`ROADMAP-DB.md`, "A card document").

**a. Through the page, from a seed (live).** Publish `<collection>_seed.js` with the page. When the owner opens the page, it copies every seed card the database does not hold yet, then writes `meta/<collection>_import` (`done`, `written`, `already`, `repaired`, `total`, `vault_commit`). It runs once per app, only for the owner, and picks up where it stopped if the page is closed. Use this for anything over a few dozen cards: the live system found that passing large batches through a tool call gets cut off.

**b. With `db_write`, from batches (live).** `roadmap_card.py import` writes `batch_NN.json` files, each `{"ops": [...]}` of `set` ops under 58 KB and 50 ops. A Claude session passes one file's `ops` to `db_write` at a time, then writes `meta/<collection>_import` itself (`{"done": true, "at": "<now>", "total": n}`), so the page does not look for a seed. `set` has no `ifVersion` and overwrites: use it only for cards the database does not hold.

Where the seed or the batches come from:

- **From an export** (`cards.json` from the section above). There is no script for this step yet. The documents in `cards.json` are already in database shape: a session builds `set` ops (`{"op": "set", "path": "<collection>/<id>", "data": <data>}`) in batches under 50 ops and about 58 KB, or writes a seed file as `window.<COLLECTION>_SEED = {"vault_commit": "", "made_at": "<now>", "cards": [<data>, ...]};`. This keeps comments and history.
- **From markdown files**: next section.
- **The example**: `seed/fld_seed.js`, to try the whole procedure before using real cards.

### 5. Migrating cards from markdown files

The layout the tools read **(live)**: one file per card at `Roadmaps/<App>/<ID> <title>.md`, fields in YAML frontmatter, the running notes as the first paragraph under the title, "Done when" as `- [ ]` lines. `example-vault/` is a small made-up one; `example-vault/_templates/Card.md` is the template. Field names and values are in `ROADMAP-DB.md`.

```sh
# a seed file for the page to import
python3 dashboard/roadmap_card.py seed --app FieldApp --vault <vault> --out <dir>/fld_seed.js
# or batches for db_write
python3 dashboard/roadmap_card.py import --app FieldApp --vault <vault> --out <dir>/fld_import
```

Use the configured copy's `roadmap_card.py` for a real app: `--app` only accepts the apps in `DB_APPS`.

Three things to know, all checked here:

- **The vault must be inside a git repository.** History comes from `git log -- Roadmaps`. Outside any git repository the command fails with a `CalledProcessError` from git (exit 128). A folder of markdown without history: run `git init`, `git add -A` and one commit in it first; each card then gets one history entry, the status it was committed with. `tests/test_tools.py` does exactly this with the example vault.
- **The vault should be the root of its repository.** Run against `dashboard/example-vault` in place, the command works but every history comes out empty and `vault_commit` is this repo's commit, because git reports paths from the repository root. Copy the vault out and make it its own repository to see history.
- Every imported card gets `updated_by: "import from vault"` and a `source` block with the frontmatter text and a body hash, so `roadmap_card.py to-md` returns the original file byte for byte until someone changes a field.

After the import, freeze the vault folder with a `_FROZEN.md` so nothing writes cards there again **(live)**; the lead-loop skill uses that marker to decide where a card lives.

### 6. Meta documents and the lead's write path

| Path | Written by | Content |
|---|---|---|
| `meta/<collection>_import` | the page after its import, or the lead after a `db_write` import | `{done, at, written, total, ...}`; `done: true` stops the page from asking for a seed |
| `meta/lead_checkin` | the lead, each time it reports to the owner | `{at, by}`; starts the page's "since you last looked" window |

How the lead reads and writes cards from here on (read, `roadmap_card.py op`, `db_write` with `ifVersion`, real clock times, the question as the first paragraph when `needs_j` is set) is in `ROADMAP-DB.md` under "Write path" and in `skills/lead-loop/SKILL.md`. Nothing about it changes with a restore except the slug.

### 7. Verify

In the repo, on the example data:

```sh
node --test dashboard/tests/logic.test.js dashboard/tests/seed.test.js
python3 -m unittest discover -s dashboard/tests -p 'test_*.py'
```

Preview the page locally before publishing (no artifact, in-memory database, nothing saved):

```sh
bash dashboard/preview/preview.sh                       # example page and example seed
bash dashboard/preview/preview.sh ~/.claude/lead/dashboard/build/site <folder with your seed and mirror.js>
```

With the example seed and the unconfigured example page, expect (the same numbers `tests/seed.test.js` asserts):

- top line: "1 card needs you · 2 in flight";
- Needs you: FLD-6, showing its question paragraph;
- Decided for you: FLD-7, "Newest first: the record just added stays in view.";
- FieldApp tile: "Phase 1 Free build", 40%, 2/5 built, 1 wait on the license, 1 in review, 1 in progress, 2 need release, 1 needs you this phase;
- left before the license: 4 of 7 built; FLD-4, FLD-5, FLD-6 left, in that order;
- StudyApp and AppC: a line saying their move could not be confirmed and an "import stopped (couldn't load apc_seed.js)" banner, because the example ships a seed for FieldApp only. A configured copy with one seed per database app does not show this.

On the real artifact, after the owner's first visit: `db_get` `meta/<collection>_import` shows `done: true` and `total` equal to your card count; `db_list` on each collection returns that many documents; each tile's numbers match `index.md` from your export; one test card moved with `roadmap_card.py op` and `db_write` shows its new status on the page without a reload.

## Not verified

Stated plainly, as of 2026-11-16:

- **Nothing was published.** No artifact was created, no capability declared and no database written for this repo. Steps 3 and 4 are assembled from the live system's notes and the server's guidance text; a first real restore should treat them as a checklist to confirm, starting with `publish_files`, `declare_capabilities` and one `db_write`.
- **The rule syntax** in step 3.4 is the guidance's example form, not a rule read back from the live artifact.
- **The shape of `db_list` / `db_query` results** was not captured from a real database; `export_cards.py` is tested on three plausible shapes built from the example seed.
- **Restoring from `cards.json`** (step 4, "From an export") has no script and no test.
- **A new Claude account** was not tested: whether the tools are present there, the plan's limits, and the page's behaviour for a second viewer.
- What was run: both test commands above pass (node: 28 tests, 23 pass, 5 skipped for want of the private seed files; python: 17 pass). The example page was loaded once in headless Chrome through `preview/` with the in-memory database: the page's own import wrote the eight cards and `meta/fld_import` (`done: true, written: 8, total: 8`), and the rendered text showed the numbers listed in step 7. The picture was not inspected for layout; only the text was read. The preview's database is a stand-in written for this repo, so it shows that the page's code runs, not that the real runtime behaves the same.
