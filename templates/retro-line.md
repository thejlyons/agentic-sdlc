# Retro line template

One line per card or incident, appended by the lead after the merge or the event. The log is
[RETRO.md](../RETRO.md).

```
| <YYYY-MM-DD> | <card ids and a few words, or the event> (PR #<n>) | <what worked> | <what broke> | <the lesson, as a rule someone can follow> |
```

How to write one:

- **Worked**: what you would do again, with the figure if there is one ("settled in 55 s").
- **Broke**: what went wrong, including the lead's own errors, stated as fact. Name the review round and what
  it found.
- **Lesson**: an instruction, not a feeling. "Run each new test on every device its job covers before
  hand-back", not "be more careful with devices".
- Take the worker's "Lessons" section into account.
- No investigation guesses. If the cause is unknown, say unknown and name the card that tracks it.

A real line:

```
| 2026-11-16 | FLD-328 astro advisories (PR #283) | A red weekly check became a filed, reviewed and merged card in ninety minutes with a sim-free worker; the reviewer checked advisories, registry sources and install scripts for itself | The first push failed npm ci on Linux: the lockfile was written on macOS with a newer npm and lacked optional entries | Verify lockfiles with the CI npm major (npx npm@10 ci) before pushing; a Node floor change needs a build on that Node |
```

About every ten cards, or at once when the same thing breaks twice, fold the durable lessons into the lead
skill, the agent files and the brief template, and note it in [CHANGELOG.md](../CHANGELOG.md).
