# The private config

`~/.claude/lead/config.json` holds everything about one owner's setup that this repo must not hold: the real apps, the build machine, the guardrails, the model choices. The skills, agents, hooks and scripts in this repo are generic and read their specifics from it.

- It is written by the `bootstrap` skill after its interview, or by hand, and installed with `python3 bootstrap/install.py --config FILE`.
- It is private. It is never committed here; `.gitignore` lists `config.json` in case a copy lands in the checkout.
- [`config.example.json`](config.example.json) shows the shape for a made-up studio. **Every value in it is an example**: FieldApp, StudyApp, `OWNER`, `roadmap-vault`, `~/Protected`, and all numbers, which are the limits of the one 16 GB machine this process grew up on.
- `python3 bootstrap/install.py --validate FILE` checks a file against the rules marked "required" below.

## Who reads it

| Reader | Keys | How |
|---|---|---|
| `scripts/macgate.sh`, `macstop.sh`, `waitci.sh` | `machine.gate`, `machine.stop`, `apps[].repo` | through `~/.claude/lead/machine.env`, which the installer writes from the config (below) |
| `hooks/guard.py` | `guardrails.vault_repo`, `guardrails.protected_paths` | reads the JSON on every call; falls back to the example values when the file is missing |
| `dashboard/sync_vault.py`, `roadmap_card.py` | `roadmap.dashboard`, `roadmap.vault.path` | reads the JSON at start |
| Skills `lead-loop`, `back-to-work`, the two agents | everything else | the model reads the file. Where a skill names FieldApp, FLD-123, a `$TOKEN` or a number, the config's value wins |

Tokens used in the skills: `$SLUG` is `roadmap.dashboard.artifact_slug`, `$DASHBOARD_URL` is `roadmap.dashboard.url`, `$VAULT` is `roadmap.vault.path`, `$LEAD_WORKSPACE` is `lead.workspace`.

## Keys

### `version`
Number. The schema version; `1` today.

### `owner`
| Key | Required | Meaning |
|---|---|---|
| `name` | yes | How the lead refers to the owner in reports and cards. |
| `github` | no | GitHub account that owns the app repos. |
| `reads_on` | no | `"phone"` or `"desk"`. Reports are kept under 15 lines for a phone. |
| `check_in_hours` | no | How often the owner usually looks. Informs when a push is worth sending. |

### `lead`
| Key | Required | Meaning |
|---|---|---|
| `workspace` | yes | Folder the lead session runs from (`$LEAD_WORKSPACE`). Workers are launched from here when an app repo's trust prompt has not been accepted. |
| `dir` | no | Where briefs, hand-backs, the queue and the attention log live. The installer and scripts assume `~/.claude/lead`; change it only together with `LEAD_DIR` in the scripts' environment. |
| `session_name` | no | The lead session's name, which each brief gives the worker for its hand-back message. |

### `goal`
String. What "done for now" means across the apps, in one sentence. `lead-loop` uses it to decide which stages are in scope.

### `apps[]` (required, at least one)
| Key | Required | Meaning |
|---|---|---|
| `name` | yes | The app's name as cards and reports use it. |
| `prefix` | yes | Card id prefix, 2 to 6 capitals or digits, unique (`FLD` gives `FLD-123`). |
| `description` | no | One line. Goes into briefs and review requests so a fresh agent knows what the app is. |
| `platforms` | no | For example `["iOS", "iPadOS", "macOS"]`. Tells the lead which screens and devices a brief must ask for. |
| `repo` | yes | `owner/name` on GitHub. Used by `gh` and by the gate to count active CI runs. |
| `path` | yes | Local clone. Workers get a git worktree of it. |
| `base_branch`, `release_branch` | no | Feature PRs target the base branch (`dev`); releases merge base into release (`main`). The guard hook's rules are written for `dev` and `main`. |
| `roadmap` | yes | `"dashboard"`: cards are documents in the dashboard artifact's database. `"vault"`: cards are markdown files in the vault repo. |
| `collection` | when `roadmap` is `"dashboard"` | The database collection, lower case (`fld`). |
| `lane_priority` | no | Whole number, unique. `1` gets the simulator lane first; others fill its gaps. |
| `needs_simulator` | no | `false` for an app whose cards never boot a simulator: its workers are always "sim-free". |
| `ci.fast_tier_boots_simulator` | no | `true` when a PR push starts a CI run that boots a simulator on the build machine. Then a push counts as holding the lane. |
| `ci.nightly_window_local` | no | `"HH:MM-HH:MM"` local time. Workers stay off the simulator in this window. |
| `ci.runs_on_build_machine` | no | Default `true`. `false` leaves this repo out of `GATE_REPOS` (its CI runs elsewhere, so its runs do not close the gate). |

### `roadmap`
| Key | Meaning |
|---|---|
| `dashboard.artifact_slug`, `dashboard.url` | The private dashboard artifact (`$SLUG`, `$DASHBOARD_URL`). Empty until you publish it: see [dashboard/RESTORE.md](../dashboard/RESTORE.md). |
| `vault.path`, `vault.repo` | The markdown vault's clone and GitHub repo (`$VAULT`), for apps with `roadmap: "vault"`. Leave out when every app is in the dashboard. |

### `machine`
The shared build machine. `name`, `ram_gb`, `cores` and `shared_with_ci_runners` are for the model's judgement and for reports. The numbers below drive the scripts.

| Key | Required | Example | Meaning |
|---|---|---|---|
| `gate.max_load` | yes | 30 | `macgate.sh` passes only when the 1-minute load is under this. |
| `gate.max_swap_mb` | yes | 12288 | ...and swap used is under this, nothing is booted and no CI run is active. |
| `stop.swap_mb` | yes | 13312 | `macstop.sh`: a reading is bad when swap is over this AND (load over `stop.load` OR free memory under `stop.min_free_pct`). Two bad readings in a row stop the job. |
| `stop.load` | yes | 30 | |
| `stop.min_free_pct` | yes | 15 | |
| `stop.grace_s` | yes | 300 | Readings this soon after a simulator boots are not counted. |
| `disk_floor_gb` | no | 21 | Workers stop a simulator job when free disk goes under this. |
| `max_sim_free_workers` | no | 2 | How many workers that need no simulator may run beside the lane holder. |

These are not recommendations for another machine. Each example number was set, and most were changed, after real readings on one 16 GB Mac mini (the history is in the comments of `scripts/macgate.sh` and `scripts/macstop.sh`, and in [CHANGELOG.md](../CHANGELOG.md)). Start from them, keep the readings, and change a number when it costs work.

### `guardrails`
| Key | Required | Meaning |
|---|---|---|
| `vault_repo` | yes | Name of the vault repo. `guard.py` lets card commits push to its `main` and asks before anything is deleted in it. Keep the example value if you have no vault. |
| `protected_paths` | yes | Folders no session may touch. `guard.py` denies any shell command that names `~/<last part>`; the agents are told the same. May be an empty list. |
| `always_ask` | yes | What needs the owner's yes every time, as plain sentences. The skills read it; `guard.py` enforces the parts a shell hook can see (push to `main`, merge without green CI and a review, store tooling, deleting vault content, releases, hand deploys). |
| `auto_decide_minutes` | no | How long a small, reversible question waits before the lead goes with its recommendation and lists it under "Decided for you". `0` turns that off. |

### `models`
| Key | Required | Meaning |
|---|---|---|
| `lead` | yes | The long-lived orchestrating session. |
| `implementer`, `advisor` | `implementer` yes | The worker's model and the stronger model it may consult (`claude --model … --advisor …`). |
| `implementer_ui` | no | Model for UI-heavy cards, run without an advisor. |
| `reviewer` | yes | The read-only reviewer's default. |
| `reviewer_when_implementer_is_fable` | yes | The reviewer used when the default reviewer's model wrote the code. The one fixed rule: the reviewer is never the model that wrote the code. |
| `scout` | no | Cheap model for read-only searches. |

## `machine.env`

Written by the installer next to the config, from the config; do not edit it. With the example config:

```sh
GATE_MAX_LOAD=30
GATE_MAX_SWAP_MB=12288
GATE_REPOS="OWNER/fieldapp OWNER/studyapp"   # every app unless ci.runs_on_build_machine is false
STOP_SWAP_MB=13312
STOP_LOAD=30
STOP_MIN_FREE_PCT=15
STOP_GRACE_S=300
CI_REPO="OWNER/fieldapp"                     # the lane_priority 1 app; waitci.sh's default repo
DISK_FLOOR_GB=21
```

Without this file the scripts use the example numbers and an empty repo list (the gate then cannot see CI runs).

## What is not configurable yet

- The dashboard page and `sync_vault.py` name their apps and the GitHub account `OWNER` in a few constants. They do not read this file at run time: `python3 dashboard/configure_apps.py` writes a copy for your apps from `apps` and `owner.github` when the dashboard is restored ([dashboard/RESTORE.md](../dashboard/RESTORE.md)).
- `guard.py` assumes the branch names `dev` and `main`.
- The skills are prose with example values inline. They tell the model that the config wins; nothing rewrites them per owner.
