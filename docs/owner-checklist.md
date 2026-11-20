# The owner's checklist

Some work only the owner can do: register identifiers, create a store record, type a listing into a
third-party site, test on a real device, press Submit. Those steps interleave with the agents' work, and each
side blocks the other. A roadmap card is the wrong shape for them: the owner needs an ordered list he can
tick on a phone, and needs to see at a glance what he can do now and what is waiting on an agent.

So each app heading for a release gets a second, smaller page beside the [dashboard](dashboard.md): a launch
checklist. The owner asked for it to be kept as part of the process on 2026-11-20, after the first one had
carried an app from "no store record" to a first beta build in an evening.

## What it is

One private page per app with a small document database behind it, the same kind of page as the dashboard.
One document per step:

```json
{
  "n": 7,                         // order on the page; fractions insert a step between two others
  "phase": "2. Store listing",    // steps are grouped under phase headings, in order of first appearance
  "who": "you",                   // "you" (the owner) or "claude" (the lead and its workers)
  "title": "Version page: the listing text",
  "why": "One or two sentences: why the step exists and what to watch for.",
  "steps": ["Click-by-click lines, with `values to paste` marked as code."],
  "blockedBy": ["t03", "t05"],    // ids of steps that must be done first, on either side
  "status": "todo",               // todo | doing (agent steps only) | done
  "result": "Agent steps: what happened, in a sentence the owner can read alone.",
  "note": "Owner steps: free text the owner types on the page for the lead."
}
```

The page shows a progress bar, then one box lifted to the top: **Your next step** (the first open owner step
with nothing blocking it) or, when there is none, **Waiting on Claude** with the agent step that unblocks
him. Below that, every step in order. An owner step has a tick box and a note field; a blocked step is
greyed and names what it waits for; an agent step shows "Claude is on it" or its result.

## Rules for the lead

- **Blocking goes both ways and is explicit.** Every step lists what it waits for. The owner never has to
  work out whether he can start something.
- **Unblock early.** If part of a blocked step can be done now (the listing text before the screenshots
  exist), split it into its own step instead of leaving the whole thing locked.
- **Paste-ready values.** A short field value goes in the step itself, marked as code. A long text is a file
  path the owner can open and copy whole. Nothing is retyped from memory.
- **Third-party steps are checked first.** Field names and menu paths for a site the lead cannot see are
  checked against that site's current help pages on the day, and the step says which parts could not be
  verified. A walkthrough written from memory once named boxes that no longer existed, and the owner pasted
  text into the wrong one.
- **Decisions are steps with a recommendation.** "Which countries: I recommend X because Y; write what you
  picked in the note."
- **The lead reads the notes.** A tick or a note is the owner's reply. At each check-in the lead reads the
  open checklists, acts on new notes, marks its own steps `doing` and `done`, and writes the `result`.
- **Agent steps mirror cards.** The work itself is still a roadmap card with a review; the checklist step
  names the card and carries only the outcome.
- **One writer per side.** The page writes `status`, `doneAt` and `note` for owner steps; the lead writes
  everything else.

## When to make one

When an app enters a phase with more than three or four owner-only steps: account and identifier setup, a
first beta, a store submission, a launch. Not for ordinary building, where the owner's part is answering
questions on the dashboard.
