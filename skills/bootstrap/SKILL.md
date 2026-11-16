---
name: bootstrap
description: Set up or restore the lead loop on a machine from the agentic-sdlc repo - install the skills, agents, hooks and machine scripts, interview the owner for the real apps, the build machine, the guardrails and the models, and write those answers to a private config. Use when the owner says "bootstrap the SDLC from this repo", "restore from zero", "set this machine up", or after a new machine, a new Claude account or a long pause.
---

# Bootstrap

The repo holds the process: skills, agents, hooks, machine scripts, the dashboard's source, the rules. It does not hold the owner's apps, machine, accounts or history. Your job is to install the first and ask for the second. Everything the owner tells you goes into `~/.claude/lead/config.json` and nowhere else. Never write an answer into the repo: it is public.

Work from the repo's folder (the one that holds `bootstrap/install.py`). Call it `<repo>` below. Run each step yourself and show the owner the output that matters. Keep shell commands short and single-purpose.

## 1. Look before you write

1. `python3 <repo>/bootstrap/install.py --dry-run`. It prints every file it would copy, every folder it would make and the exact diff it would apply to `~/.claude/settings.json`. It writes nothing.
2. Show the owner the settings diff and the list of anything marked `kept` (a file that already exists and differs from the repo's: it is theirs). Say in one line what the two hooks do: `guard.py` asks or denies before risky shell commands; `attention.py` logs when a session sits on a prompt.
3. If `~/.claude/lead/config.json` already exists, this is an update, not a first install. Read it, skip the questions it already answers, and ask only about what is missing or what the owner wants to change.

## 2. Install

`python3 <repo>/bootstrap/install.py --yes` once the owner has seen the diff and said yes. Without `--yes` and without a terminal the installer leaves `settings.json` alone and says so; do not work around that.

The installer is safe to run again: unchanged files are reported as unchanged. It does not replace a file the owner changed unless you pass `--force`, and you pass `--force` only when the owner asks, per file, after seeing what differs.

## 3. Interview

Ask in small batches, one topic at a time, each question with a proposed answer where you can make one. The owner should be able to reply "yes to all" to a batch. Use `<repo>/config/SCHEMA.md` for the meaning of every key and `<repo>/config/config.example.json` for the shape. The example's values (FieldApp, StudyApp, OWNER, `~/Protected`, the 16 GB machine's numbers) are examples: none of them may survive into the real config unless the owner confirms it.

**Batch 1, the owner and the lead.** Name to use; GitHub account; where they read reports (phone or desk) and how often they check in; the folder the lead session runs from (`lead.workspace`).

**Batch 2, the apps, one at a time.** Name; card prefix (2 to 6 capitals); one line of what it is; platforms; GitHub repo (`owner/name`) and the local path of its clone; base and release branches; whether its cards live in the dashboard database or as markdown files in a vault; its place in the simulator lane order; whether its PR CI boots a simulator on this machine; its nightly CI window in local time. Check what you can instead of asking: `git -C <path> remote get-url origin`, `git -C <path> branch -r`, `ls <path>/.github/workflows`. Then ask for the goal in one sentence (`goal`): what "done for now" means across the apps.

**Batch 3, the build machine.** Read it first: `sysctl -n hw.memsize`, `sysctl -n hw.ncpu`, `xcrun simctl list devices` when Xcode is present, `gh api repos/<owner>/<repo>/actions/runners` when the owner says CI runs on this machine. Then propose gate and stop numbers scaled from the example (which is a 16 GB, ten-core machine: start gate at load 30 and swap 12 GB, stop at swap 13 GB with load over 30 or free memory under 15%). Say plainly that these are starting points. The live numbers were each changed after real readings, and the rule is to bring readings and a proposed replacement when a limit costs work, not to work around it. If the apps need no simulator, say that the lane rules then matter little and keep the defaults.

**Batch 4, guardrails.** What always asks first (start from the example list and let the owner add or cut); folders no session may ever touch (`guardrails.protected_paths`); the vault repo's name if there is one; how many minutes a small reversible question waits before the lead goes with its own recommendation (the example is 15; 0 turns that off).

**Batch 5, models.** Which model the lead runs on, which model builds, which advises, which reviews. Keep the one rule that is not a preference: the reviewer is never the model that wrote the code.

Write the answers as one JSON file outside the repo (for example `~/.claude/lead/config.draft.json`, with the Write tool), then:

1. `python3 <repo>/bootstrap/install.py --validate ~/.claude/lead/config.draft.json` and fix what it names.
2. Show the owner the whole file once. It is theirs to correct.
3. `python3 <repo>/bootstrap/install.py --config ~/.claude/lead/config.draft.json --yes`. This installs it as `~/.claude/lead/config.json` and writes `~/.claude/lead/machine.env` from it, which the gate and stop scripts read.
4. `git -C <repo> status --short` must print nothing. If it prints anything you wrote, move it out of the repo.

## 4. Prove the install

Run these and report each result in a line:

- `python3 <repo>/bootstrap/install.py --check` exits 0.
- `python3 ~/.claude/hooks/guard.py --test` passes all its cases.
- `~/.claude/lead/bin/macgate.sh` prints a reading (`load=… swapMB=… bootedSims=… activeRuns=…`). A non-zero exit only means the machine is busy now. An error from `gh` means the CLI is not logged in or a repo name in the config is wrong.
- `claude agents --json --all` runs (the CLI is on the PATH and logged in).

## 5. Starting rules

`~/.claude/lead/rules/` holds the durable rules as dated statements, each with the incident that produced it. They are what the last lead learned the hard way. Offer them: list the titles, and ask whether to load all, some or none as starting memory. For each one the owner picks, save one memory in the lead workspace's memory with the rule, its reason and its date, marked as carried over from the repo rather than learned here. Do not load any silently, and do not load a rule that contradicts an answer the owner just gave; point out the conflict instead. Rules about a simulator lane are of no use to an owner whose apps need none.

## 6. The dashboard

The roadmap dashboard is a private artifact with a database. It cannot be installed by a script: you publish it. Follow `<repo>/dashboard/RESTORE.md` (also at `~/.claude/lead/dashboard/RESTORE.md`): publish the page, record the new artifact's slug and URL in the config (`roadmap.dashboard`), then import cards from an export or from markdown files. If the owner has no cards yet, the seed there gives a few example cards to see the page working; say they are examples and remove them before real work.

## 7. Say what was not restored

Tell the owner plainly, in one list, what the repo could not bring back and what each needs:

- The old dashboard's cards, comments and history: only from an export made while the old account could still be read (`dashboard/RESTORE.md` says how). Without one, cards start again from the app repos' issues, PR titles or the owner's notes.
- The old lead's memory and session transcripts: gone with the old account or machine, except for the rules in `rules/`.
- Briefs and hand-backs of past cards: private files that were never in the repo.
- The Claude Code login and, if used, the Remote Control push setting: the owner does these.
- Each app repo's workspace-trust prompt: the owner runs `claude` once in each repo. Until then a background worker cannot start there; `lead-loop` gives the fallback.
- Auto-mode rules: a session cannot edit its own. `<repo>/hooks/settings.example.json` has wording the owner can paste.
- The owner's own skills that the lead loop refers to (`vault-sdlc`, `apple-ci-standards`, a working-with-the-owner skill, `app-ux-standards`, `app-design-taste`, `xcode-device-hub-ci`): they are not in this repo. Without them the loop still runs; the agents load them only when they exist.
- Each app repo's own `CLAUDE.md`, CI and scripts: they live in the app repos.

## 8. First run

Finish with `/back-to-work`. With an empty dashboard its report is short; that is correct. From here `lead-loop` is the skill that runs the work.

## Later

- The repo changed: `git -C <repo> pull`, then steps 1 and 2. Your own edits to installed files are kept and listed.
- The apps, machine or guardrails changed: edit `~/.claude/lead/config.json`, then run the installer again so `machine.env` follows.
- Removing it: `python3 <repo>/bootstrap/install.py --uninstall` removes what was installed and the settings entries, and keeps the config, briefs, hand-backs, queue and attention log. `--purge` removes those too; only on the owner's explicit word.
