# Hand-back template

Written by the worker to `~/.claude/lead/handbacks/<CARD-ID>.md` and overwritten on later rounds. The format
is the one in [agents/card-implementer.md](../agents/card-implementer.md). A real one, three rounds:
[examples/FLD-328/handback.md](../examples/FLD-328/handback.md).

After writing it the worker sends the lead one line, `<CARD-ID> <status>: <one sentence>`, and ends its turn.

```
# <CARD-ID> hand-back (round N)
status: ready-for-review | needs_j | blocked
repo / worktree / branch / commits:

## What changed
(short, by file or area)

## Done when
- [x] item — evidence (test name + result, or screenshot path)
- [ ] item — why not, what it needs

## Checks run
(command, result; failures with their output; what was NOT run and why)

## Screenshots
(paths, what each shows)

## Questions for J
(numbered, each with a recommendation; empty if none)

## Follow-ups not done

## Lessons
(anything about the process, tools or repo rules that cost you time or would help the next card)
```

Rules the format carries:

- A box is ticked only with evidence. An item that cannot be proven yet says so; the lead files it as a
  later card.
- A check that was not run is listed as not run. A failing check is reported as failing, with its output.
- Every log named here starts with the commit it ran at.
- Pictures are copied out of the build folder before the next run wipes it.
- The file must be complete enough for a fresh worker to resume from after a restart.
- When the lead says to push: push, open the PR into the base branch with the card id in the title, add the
  PR number to this file, and message the lead.
