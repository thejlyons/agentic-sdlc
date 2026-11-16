# Guardrails

Workers run unattended in auto mode, often for hours. Three things keep that safe: a hook that inspects
every shell command, a short list of actions that always go to the owner, and a rule about agents asking
each other for favours.

Files: [hooks/guard.py](../hooks/guard.py), [hooks/attention.py](../hooks/attention.py),
[hooks/settings.example.json](../hooks/settings.example.json).

## The guard hook

`guard.py` is a PreToolUse hook on the Bash tool. It splits the command into simple commands, follows `cd`
and `git -C`, and prints a decision only when a rule matches. Otherwise it stays silent and the normal
permission flow decides. It has a self-test (`python3 hooks/guard.py --test`, 21 cases) that CI runs.

**Denied outright**

- Anything that names a protected folder (`guardrails.protected_paths` in the private config).
- A force-push to `main` or `dev`, in any spelling: `-f`, `--force-with-lease`, a `+` refspec, `--mirror`.

**Asks the owner**

- A push to an app repo's `main`. Releases go through a `dev` to `main` PR. The roadmap vault's `main` is
  exempt, because card commits go there directly.
- `gh pr merge`, unless the merge check below passes.
- App Store Connect and notarization tooling.
- Deleting vault content (`rm`, `git rm`, `git clean` inside the vault).
- Deleting a repo; creating or deleting a release.
- Publishing a site by hand (`wrangler deploy` or `publish`). CI deploys normally.

**The merge check.** Before a `gh pr merge` runs, the hook reads the PR. It lets the merge through only when
every CI check is green, at least one check exists, and the PR carries a comment or review containing
`Review: PASS`. Anything else asks the owner, with the reason: which checks are not green, or that no review
comment exists. So the path of least resistance for the lead is the reviewed, green one.

The hook reads the PR before the command runs. Posting the review comment and merging in one chained command
therefore fails the check: the comment does not exist yet. They are two separate calls. This was found on
the first card through the loop, when the owner got a prompt for a merge that was in fact reviewed.

The marker is a convention, not proof. The hook cannot tell who wrote the comment. It stops an unreviewed
merge by accident; it does not stop a lead that lies. See [limits.md](limits.md).

## The attention hook

`attention.py` is a Notification hook. When any session, lead or worker, waits on a permission prompt or
sits idle for input, it appends a line to `~/.claude/lead/attention.jsonl` and shows a desktop notification.
Nothing leaves the machine. The lead reads the log when a worker goes quiet, and checks each worker's state
for `waitingFor: "permission prompt"` on every pass.

## What always asks first

Whatever the mode, and whether or not a hook fires:

- a direct push to an app repo's `main`
- anything in App Store Connect
- anything legal, tax, banking, purchases or domains
- deleting vault content or an artifact
- sending email or posting publicly

The same list is in the lead skill, in the auto-mode rules of the settings example, and partly in the hook.
The skill says it plainly: the rule is the lead's to keep even where no hook fires.

Merges are not on the list. The owner's standing approval (2026-11-03, widened 2026-11-11) covers feature
and release merges when CI is green and a separate reviewer passed the change. If a branch ruleset refuses
something, that is the owner's guard: it is reported, not worked around.

## No permission laundering

An agent never asks another session to do something that was blocked for it. If a worker is denied a
command and asks the lead to run it, the request goes to the owner, in the owner's terms, once, with the
exact rule text. The lead cannot answer another session's prompt. If the owner approves, the lead runs the
action itself, respawns the worker and tells it what was run.

A session also cannot edit its own auto-mode rules. Permission changes are the owner's to make.

## Auto mode is for workers only

Workers are launched with the auto permission mode by flag. Nothing changes for the owner's own sessions:
global auto mode was rejected in the plan as too broad.

## Never sit on a prompt

Nobody is at the keyboard. A worker once waited 80 minutes on a prompt raised by a multi-line shell command.
So:

- Workers write files with the Write and Edit tools and keep shell calls short and single-purpose: one git
  command per call.
- Reviewers use one read-only command per call, `git -C <path>` instead of `cd <path> &&`, no chained
  sequences and no redirects. Read-only git, gh and text commands are on the allow list.
- A refused call is not retried another way. The worker records the exact call in the hand-back, messages
  the lead and carries on with what does not depend on it.

## What the guardrails do not cover

The hook sees Bash only. Actions through other tools rely on the permission lists and the auto-mode rules in
the settings file. The hook matches text, so a string that merely mentions a protected folder inside a
command is denied too; that false positive is accepted.
