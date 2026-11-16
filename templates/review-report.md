# Review report template

The reviewer replies with this and nothing else. The format is the one in
[agents/card-reviewer.md](../agents/card-reviewer.md). A real report:
[examples/FLD-328/review.md](../examples/FLD-328/review.md). The protocol:
[docs/independent-review.md](../docs/independent-review.md).

```
VERDICT: PASS | CHANGES
## Blocking
1. file:line — what is wrong, the concrete case that breaks, what would fix it
## Non-blocking
(nits and follow-up ideas; each one line)
## Done when
- item — proven | not proven (why)
## Not checked
(what you could not verify from the diff and pictures)
```

Blocking means: wrong behaviour, a "Done when" item not proven, a broken or meaningless test, a visible
defect in a screenshot, or a repo rule broken. PASS only when the Blocking list is empty. Missing pictures,
or a diff that does not match the card, is CHANGES with that as the blocking item.

## What the lead sends the reviewer

```
Review <App> card <ID> (read-only). Worktree: <path>, branch <branch>, head <commit>, base <ref>.
<Lane note: sim-free, do not boot a simulator or run builds.>

Card text:
"<the card and its Done when list, verbatim>"

Check for yourself, not from the worker's claims: <the specific things this change could get wrong>.
Screenshots: <paths>. The hand-back is at <path>; verify its Done-when claims.
```

Not included, on purpose: the worker's explanation of why the change is right.

## What the lead posts on the PR after PASS and green CI

```
Review: PASS. <N> rounds of separate read-only <model> review (fresh reviewer each round); the code was
written on <model>. Round <N> passed at <commit>. <Any commit after that: what it changes and that the lead
verified it line by line.>

Round 1 found: <blocking items, one line each>.
Not proven, accepted: <...>
Follow-ups filed: <card ids>
```

The comment must start with `Review: PASS`; the guard hook looks for that text before a merge. Post it and
run the merge as two separate calls.
