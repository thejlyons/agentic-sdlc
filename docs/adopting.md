# Adopting pieces

The parts are separable. Listed from least to most commitment, with what to change. Names like FieldApp and
FLD-123, and every machine number, are example values.

## 1. The reviewer alone

Copy [agents/card-reviewer.md](../agents/card-reviewer.md) to `~/.claude/agents/`. It needs no other file.

Change: the first paragraph (who you are, what "done" means for you), the skill names in step 3 (they are
the owner's own; delete or replace them), and the device-specific items in step 5.

Keep: read-only tools; "you were deliberately not given the implementer's reasoning"; the verdict format;
the definition of blocking. When you call it, pass the ticket text, the diff location and the evidence. Do
not pass your summary of why the change is right. Use a different model from the one that wrote the code if
you have one. See [independent-review.md](independent-review.md).

## 2. Brief and hand-back templates

Copy [templates/brief.md](../templates/brief.md) and [templates/handback.md](../templates/handback.md). They
work with any agent that can read a file and write one.

The parts that paid for themselves: "Done when" boxes ticked only with evidence; a "Checks run" section that
must list what was not run; a "Lessons" section; one hand-back file per card, overwritten each round, so a
restarted worker or a new lead can resume from it. Worked example: [briefs.md](briefs.md).

## 3. The guard hook

Copy [hooks/guard.py](../hooks/guard.py) and the hook entries from
[hooks/settings.example.json](../hooks/settings.example.json). Run `python3 guard.py --test` after any edit.

Change: the branch names if yours are not `main` and `dev`; the vault exemption (drop it if you have no repo
that takes direct pushes to `main`); the review marker text; the protected folders and vault name, which are
read from `~/.claude/lead/config.json` and fall back to the example values.

The merge check needs the GitHub CLI and expects a PR comment starting `Review: PASS`. See
[guardrails.md](guardrails.md) for what the hook does not cover.

## 4. The lane scripts

Copy [scripts/macgate.sh](../scripts/macgate.sh), [macstop.sh](../scripts/macstop.sh),
[waitgate.sh](../scripts/waitgate.sh) and [waitci.sh](../scripts/waitci.sh). macOS only.

Change: every threshold. They are read from `~/.claude/lead/machine.env`; the defaults are for one 16 GB
machine. Measure yours first: swap after a cold simulator boot, load during a build, where it actually fell
over. Set `GATE_REPOS` to the repos whose CI runs on the same machine.

The idea transfers further than the scripts: decide what the scarce resource is, make one gate script that
exits 0 only when it is free, and make every agent run it. See [lane.md](lane.md).

## 5. The whole kit

[BOOTSTRAP.md](../BOOTSTRAP.md) installs the skills, agents, hooks and scripts, creates the working folders,
and interviews you for the private config: your apps, your machine, your guardrails, your model choices.
[config/SCHEMA.md](../config/SCHEMA.md) documents every field. The dashboard is rebuilt separately:
[dashboard/RESTORE.md](../dashboard/RESTORE.md).

Expect to rewrite, not just configure:

- The skills reference the owner's other process skills by name. Those are not in this repo.
- The lead skill assumes a roadmap of cards with stages and a dashboard database. With a different tracker,
  replace the "Where a card lives" and status sections and keep the rest.
- The implementer's verification section is written for Apple apps (simulators, text sizes, device poses).
  Keep its shape and substitute your platform's proof.
- [rules/](../rules/README.md) can be loaded as starting memory. Read them first; several are about one
  machine and one owner's preferences.

## What to adopt first

If only one thing: the separate, read-only reviewer that never sees the implementer's reasoning. It is one
file, and it is the part with the most evidence behind it here. Then hand-back files. The lane rules matter
only once you run more than one agent against one scarce machine.

## What not to copy

The numbers. The stage names. The assumption that one person answers every question within a few hours.
The claim to completeness: read [limits.md](limits.md) before relying on any of it.
