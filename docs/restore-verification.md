# Restore verification

What has been tested about "restore from zero", and what has not. Dated; rerun and replace when the installer changes.

## 2026-11-16: `bash bootstrap/restore_test.sh`

Run on the live build machine (macOS 27.2, python 3.14 and the system python 3.9 for the installer alone, node 24), against the working tree as first committed on 2026-11-16 (rerun by the lead-side check after the last change that day: 54 passed). The test makes an empty temporary folder, sets `HOME` to it, and installs there. The real home folder is not touched.

Result: 54 checks passed, 0 failed, 0 skipped. The full output:

```
== 1. dry run writes nothing
ok    dry run exits 0
ok    home folder still empty after the dry run
ok    dry run lists the files and the settings diff
== 2. install without --yes and without a terminal leaves settings alone
ok    settings.json not written without consent
== 3. real install, twice
ok    install exits 0
ok    second install exits 0
ok    second install changes nothing
== 4. every file landed and equals the repo's
ok    34 installed files match the repo by checksum
ok    skill lead-loop installed
ok    skill back-to-work installed
ok    skill bootstrap installed
ok    agent card-implementer installed
ok    agent card-reviewer installed
ok    working folder briefs
ok    working folder handbacks
ok    working folder research
ok    file queue.md
ok    file attention.jsonl
ok    file config.json
ok    file machine.env
ok    file .install-manifest.json
ok    macgate.sh is executable
ok    macstop.sh is executable
ok    waitgate.sh is executable
ok    waitci.sh is executable
== 5. settings.json
ok    both hooks present exactly once after two installs; allow rules not doubled
ok    an existing settings.json keeps its own entries, gains ours, and is backed up
ok    the settings diff was printed
== 6. machine.env from the example config
ok    machine.env holds the config's limits and repos
ok    a broken config is refused
== 7. scripts parse
ok    bash -n macgate.sh
ok    bash -n macstop.sh
ok    bash -n waitgate.sh
ok    bash -n waitci.sh
ok    macstop.sh prints a reading on this Mac (11:55 load=5.56 swapMB=9004.81 memFree=46%)
== 8. guard hook
ok    guard.py --test (its own 21 cases)
ok    guard asks: git push origin main in an app folder
ok    guard denies: rm -rf under the protected path of the config
ok    guard stays silent: git status
ok    guard ignores tools other than Bash
== 9. attention hook
ok    a permission prompt is logged to attention.jsonl
ok    other notification types are not logged
ok    attention hook exits 0 when it cannot show a notification
== 10. dashboard tools
ok    roadmap_card.py builds a new-card op
ok    dashboard tests pass from the installed copy (23 passed, 5 skipped for want of private data)
== 11. check, an owner-edited file, uninstall
ok    install.py --check passes
ok    --check notices an edited file
ok    uninstall dry run removes nothing
ok    uninstall exits 0
ok    installed files are gone
ok    the edited file was left in place
ok    settings.json no longer has the hooks or the rules
ok    config, queue, attention log and working folders are kept
ok    --purge removes the private folder

restore test on Darwin: 54 passed, 0 failed, 0 skipped (python 3.14.4, node v24.11.0)
```

What that proves, in plain terms:

- **Dry run** prints the plan and the settings diff and writes nothing.
- **Consent**: without `--yes` and without a terminal, `settings.json` is not written.
- **Install** lands every skill, agent, hook, script, dashboard file and rule, byte-identical to the repo. A second run changes nothing.
- **Settings merge**: both hooks are present exactly once after two installs; an existing `settings.json` keeps its own keys, rules and hooks, gains ours, and is backed up; the diff is printed.
- **Config**: the example config validates and installs; `machine.env` carries its limits and repos; a broken config is refused.
- **Scripts** parse with `bash -n`; `macstop.sh` printed a real reading on this Mac.
- **Guard hook**, from the installed copy, with the installed example config: its own 21 self-test cases pass; a sample `git push origin main` tool call gets `ask`; `rm -rf` under the configured protected path gets `deny`; `git status` and a non-Bash tool get no output (the normal permission flow decides).
- **Attention hook** logs a permission-prompt notification to `attention.jsonl`, ignores other types, and exits 0 when no notifier exists.
- **Card tool** builds a new-card op; the dashboard's node tests pass from the installed copy (the ones that need the owner's private seed data skip).
- **Check and uninstall**: `--check` passes on a clean install and fails after a file is edited; uninstall removes what was installed, leaves the edited file, removes the hook entries and rules from `settings.json`, keeps the config, queue, attention log and working folders; `--purge` removes those.

## 2026-11-16: the same test in CI on ubuntu

The [check workflow](../.github/workflows/check.yml) ran the test on `ubuntu-latest` (python 3.11, node 20) on a push to the repo's private remote before publication: 53 passed, 0 failed, 1 skipped. The skip is the `macstop.sh` reading, which needs macOS counters.

## Not verified

Nothing below has been tried. Each is a real gap, not a formality.

- **A new Claude account.** The test cannot create one. Whether a fresh account's Claude Code picks up the installed skills and agents, and whether `claude --bg --agent card-implementer --advisor …` behaves the same there, is untested. The advisor flag was experimental when the loop was built.
- **The bootstrap skill as a conversation.** The installer it calls is tested; the interview, the config Claude writes from it and the memory offer have not been run end to end with a person.
- **Loading `rules/` as memory.** The skill describes it; no session has done it from this repo.
- **Publishing the dashboard.** `dashboard/RESTORE.md` describes publishing the page as a new private artifact and importing cards. That needs the artifact tools of a logged-in Claude session and was not done as part of this test.
- **The lane scripts on Linux.** `macgate.sh` and `macstop.sh` read macOS counters (`sysctl vm.swapusage`, `memory_pressure`, `xcrun simctl`), so on Linux they are parse-checked only and are not usable there.
- **Another machine's limits.** The gate and stop numbers are one 16 GB Mac mini's. On other hardware they are a starting point; nothing here shows they are right elsewhere.
- **`macgate.sh` against real repos.** The test only parses it. Run once by hand from the repo with no repo list, it printed a reading (`load=3.82 swapMB=8988.81 bootedSims=1 activeRuns=0`, exit 1 because a simulator was booted); the version in this repo, which reads its limits and repos from `machine.env`, has not yet replaced the live one, so its CI-run count against real repos is unproven.
- **Real repos.** Workspace trust, `gh` login, self-hosted runners, each app's `CLAUDE.md` and CI are outside this repo and outside the test.
- **`--force` and the interactive "y/N" prompt** are not covered by the test.
