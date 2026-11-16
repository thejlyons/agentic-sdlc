# Card template

A roadmap card. As a markdown file it has YAML frontmatter and a body; in the dashboard database the same
fields are a document ([dashboard/ROADMAP-DB.md](../dashboard/ROADMAP-DB.md)). Field names and values are
fixed, because the dashboard's counting rules read them ([docs/dashboard.md](../docs/dashboard.md)).

```markdown
---
id: "FLD-123"
app: "FieldApp"
title: "Plain words, what changes for the user or the build"
stage: "1 Free build"
area: "CI"
type: "Bug"
size: "S"
priority: "P2"
status: "Backlog"
needs_j: false
pr: ""
created: "2026-11-16"
tags: ["card"]
---

# Plain words, what changes for the user or the build

Running notes, short and dated. This first paragraph is what the dashboard shows under the card. When
`needs_j` is true it must be the question itself, with a recommendation.

What is wrong or wanted, with the evidence: the failing run, the picture, the versions.

Depends on: FLD-120

## Done when
- [ ] A checkable item: a command and its result, or an observable state
- [ ] Pictures in light, dark and the largest text size, for anything visible
```

| Field | Values |
|---|---|
| `id` | `<PREFIX>-<n>`; the next number is one more than the highest used for that prefix |
| `stage` | `0 Free build`, `1 Free build`, `1 Refactor`, `2 Paid`, `3 Release`, `After 1.0`. Stages 0 and 1 are the pre-license stages; the dashboard's current phase is the lowest stage with unfinished cards |
| `status` | `Backlog`, `Next`, `In progress`, `In review`, `Done` (merged into the base branch), `Released` (in the release branch) |
| `priority` | `P1`, `P2`, `P3` (the lead skill also orders a `P0` first) |
| `size` | `S`, `M`, `L`, `XL` |
| `needs_j` | boolean; true while something waits on the owner |
| `area`, `type` | free text kept consistent per app (for example `CI`, `Testing`, `Site`; `Bug`, `Feature`, `Chore`) |
| `pr` | a number, `#n`, a URL or `repo#n`; empty for none |

Rules:

- Only the lead changes `status`, `pr` and `needs_j`.
- In review when the PR opens; Done when it squash-merges; Released when the release PR containing it merges.
- A card whose proof must wait for something later is closed on merge, and the proof becomes a new card in
  the later stage.
- A card that runs past three review rounds is split.
