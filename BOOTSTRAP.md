# Restore from zero

This repo is also a restore kit. On a new machine, or a new Claude account, or after a long pause, it puts the lead loop back: the skills, the worker and reviewer agents, the two hooks, the machine-safety scripts, the dashboard's source and the rules. Then Claude asks you for what a public repo cannot hold (your apps, your build machine, your guardrails) and writes the answers to a private file on your machine.

What it restores is the process. It does not restore your data: see [What the repo cannot restore](#what-the-repo-cannot-restore).

## Before you start

| Need | For |
|---|---|
| Claude Code CLI, logged in | everything; `claude --bg`, `--worktree`, `--agent` and `--advisor` are used to launch workers |
| git, GitHub CLI (`gh`) logged in | worktrees, PRs, CI status, the machine gate |
| python3 (3.9 or newer, standard library only) | the installer, the hooks, the card tool |
| node 20 or newer | only to run the dashboard's tests |
| Xcode | only if your apps need simulators; the lane scripts read `xcrun simctl` |

## One sentence, or one command

Clone the repo, open Claude Code in it, and say:

> Bootstrap the SDLC from this repo.

Claude reads [`skills/bootstrap/SKILL.md`](skills/bootstrap/SKILL.md) and does the rest, asking as it goes. (On a first run the skill is not installed yet. If Claude does not find it by itself, say "read skills/bootstrap/SKILL.md and follow it".)

Or run the installer yourself and let Claude do only the interview:

```sh
python3 bootstrap/install.py --dry-run   # prints every action and the settings diff; writes nothing
python3 bootstrap/install.py             # installs; asks before it changes settings.json
```

## What gets installed where

| From the repo | To | Notes |
|---|---|---|
| `skills/lead-loop`, `back-to-work`, `bootstrap` | `~/.claude/skills/<name>/SKILL.md` | |
| `agents/card-implementer.md`, `card-reviewer.md` | `~/.claude/agents/` | user level, so every repo's worktree sees them |
| `hooks/guard.py`, `attention.py` | `~/.claude/hooks/` | |
| `scripts/macgate.sh`, `macstop.sh`, `waitgate.sh`, `waitci.sh` | `~/.claude/lead/bin/` | executable |
| `dashboard/` (not `out/`) | `~/.claude/lead/dashboard/` | card tool, page source, tests, seed, restore steps |
| `rules/` | `~/.claude/lead/rules/` | offered as starting memory, never loaded silently |
| (created) | `~/.claude/lead/briefs/`, `handbacks/`, `research/`, `queue.md`, `attention.jsonl` | only when missing; never emptied |
| your answers | `~/.claude/lead/config.json` | private; schema in [config/SCHEMA.md](config/SCHEMA.md) |
| (derived) | `~/.claude/lead/machine.env` | written from the config; the scripts read it |
| `hooks/settings.example.json` | merged into `~/.claude/settings.json` | see below |
| (record) | `~/.claude/lead/.install-manifest.json` | what was installed, with checksums |

Install is a plain copy. The files already name these places, so nothing is rewritten on the way.

**settings.json is merged, not replaced.** The installer adds two hook entries (PreToolUse on Bash runs `guard.py`; Notification runs `attention.py`), a list of allow rules and one ask rule, each only if missing. The allow rules are read-only git, gh and text commands, the gate and stop scripts, the card tool and the dashboard database tools, including `db_write`, which the lead uses to record card status. It prints the diff first, backs the old file up beside it, and does not write without your "y" or `--yes`. Auto-mode rules are not merged: a session cannot set its own, and [`hooks/settings.example.json`](hooks/settings.example.json) has wording to paste by hand.

**Your own files are kept.** If a destination file exists, differs from the repo's and was not put there by the installer, it is left and listed. `--force` replaces it and keeps a backup.

## The interview

The `bootstrap` skill asks in five short batches and proposes an answer wherever it can read one from the machine:

1. You and the lead: name, GitHub account, how you read reports, the lead's working folder.
2. Each app: name, card prefix, what it is, platforms, repo and local path, branches, where its roadmap lives (dashboard database or markdown vault), its place in the simulator lane, whether its PR CI boots a simulator here, its nightly window. Then the current goal in one sentence.
3. The build machine: RAM, cores, simulators, CI runners on it, and the gate and stop limits. The example numbers come from one 16 GB machine and are starting points to change with readings.
4. Guardrails: what always asks first, folders nothing may touch, the vault repo, how long a small reversible question waits before the lead decides.
5. Models: lead, implementer, advisor, reviewer. The reviewer is never the model that wrote the code.

The answers go to `~/.claude/lead/config.json` only. [`config/config.example.json`](config/config.example.json) shows the shape for a made-up studio; every value in it is an example. The skill ends by checking that the repo's `git status` is clean.

After the interview Claude proves the install (`install.py --check`, `guard.py --test`, one `macgate.sh` reading), offers the rules as starting memory, walks you through the dashboard ([dashboard/RESTORE.md](dashboard/RESTORE.md)) and runs a first `/back-to-work`.

## Later

```sh
python3 bootstrap/install.py --check       # exit 1 if anything installed differs from the repo
python3 bootstrap/install.py               # after `git pull`: update; unchanged files are reported as unchanged
python3 bootstrap/install.py --config FILE # validate FILE and install it as the private config
python3 bootstrap/install.py --uninstall   # remove what was installed and the settings entries
```

`--uninstall` removes only files that still match what was installed; a file you changed is left and listed. It keeps `config.json`, briefs, hand-backs, the queue and the attention log. `--uninstall --purge` removes those too. Both take `--dry-run`.

## What the repo cannot restore

| Lost with the old account or machine | How to keep it |
|---|---|
| The dashboard's cards, comments and status history (they live in the old artifact's database) | Export while you can still read it: [dashboard/RESTORE.md](dashboard/RESTORE.md) has the steps and the export script. Keep the export in a private backup, not here. |
| The lead's memory | The durable rules are in [`rules/`](rules/), sanitised. Anything else in memory is gone unless you copy the memory folder to a private backup. |
| Briefs, hand-backs, screenshots, session transcripts | Private files under `~/.claude/`. Back them up privately if you want them. |
| The private config | Back up `~/.claude/lead/config.json` privately. Without it, the interview takes ten minutes. |
| Your own skills the loop refers to (`vault-sdlc`, `apple-ci-standards`, a working-with-the-owner skill, and the design and UX skills) | They are yours and are not in this repo. The loop runs without them; agents load them only when present. |
| Claude Code login, Remote Control push, each app repo's workspace-trust prompt, auto-mode rules | You do these by hand, once. |
| App repos, their `CLAUDE.md`, CI workflows, self-hosted runners | They live in the app repos and on the machine. |

## What has been verified

[docs/restore-verification.md](docs/restore-verification.md) has the dated result of `bash bootstrap/restore_test.sh`, which installs into an empty temporary home folder and checks the files, the settings merge, the hooks against sample tool calls, the scripts, the card tool and the uninstall. CI runs the same test on every push. The same page lists what has not been tested: a new Claude account, the dashboard publish, memory loading, another machine's limits.
