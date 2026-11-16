# Independent review

Every card is reviewed by a separate agent before its PR is pushed or merged. The agent definition is
[agents/card-reviewer.md](../agents/card-reviewer.md). The owner does not test builds by hand, so this is the
last check before a change reads as "done".

## The protocol

- **Fresh context.** The reviewer starts with no history of the work.
- **Evidence in, reasoning out.** It gets the card text, the worktree path, the base ref and the screenshot
  paths. It is not given the implementer's explanation of why the change is right. An agent handed a
  conclusion tends to return it confirmed.
- **Read-only.** Its tools are Read, Grep, Glob and Bash; Edit, Write and NotebookEdit are disallowed. Bash
  is limited by instruction, not by the tool list: the agent file tells it to inspect only and never commit,
  build, run tests or boot a simulator. Once the lead let a reviewer run a build anyway, and it pulled in a
  1.3 GB toolchain. If it thinks a test needs running, it says which and why.
- **A different model from the one that wrote the code.** Sonnet-built cards are reviewed on Fable.
  Fable-built cards are reviewed on Opus.
- **The contract is the card.** For each "Done when" item the reviewer decides whether the evidence proves
  it. A test that would pass without the change proves nothing.
- **Blocking or not.** Blocking: wrong behaviour, an unproven "Done when" item, a broken or meaningless
  test, a visible defect in a picture, a repo rule broken. Style and ideas for later are non-blocking.
  Missing pictures are a `CHANGES` by themselves.
- **A fresh reviewer each round.** `CHANGES` items go to the worker verbatim. The next round starts a new
  reviewer.
- **Three-round check.** After three rounds the lead looks at the card itself: it is probably mis-specified
  or too big, and should be split. In practice this has been a prompt, not a hard stop: 8 of the 30 PRs in
  [data/merged-prs.tsv](../data/merged-prs.tsv) went to four, five or six rounds.
- **Lead acceptance is not a review.** Every commit after the last reviewer pass gets a fresh reviewer, or,
  for a named mechanical change (a comment, a time limit, a lockfile), a line-by-line lead check that is
  stated on the PR.
- **The verdict is posted.** The PR gets a comment starting `Review: PASS` with the reviewer model, the
  round count and the non-blocking notes. The [guard hook](guardrails.md) checks for it before a merge.

The report format is in [templates/review-report.md](../templates/review-report.md). A full real report is
[examples/FLD-328/review.md](../examples/FLD-328/review.md).

## How often it returns CHANGES

Between 2026-11-11 and 2026-11-16 the lead started 87 reviewer runs. 60 ended in `CHANGES` and 27 in
`PASS`. The count is of the reviewer agents' final verdicts in the lead session's transcripts; the rows are
in [data/reviewer-runs.tsv](../data/reviewer-runs.tsv). Rounds per PR and the other figures are derived in
the [README's numbers section](../README.md#numbers).

Read that ratio with care. It includes pre-run code reviews and narrow re-reviews of a single commit, and
late rounds on the same card. It does not say 69% of first attempts were wrong. It does say that a second
reader with no stake in the work usually finds something.

## What it caught

Each of these passed the implementer's own checks. Sanitised from the PR review comments and the
[retro log](../RETRO.md).

**Regenerated data that blanked 216 source links.** A content generator was re-run without its cache. It
fell back to an empty value and rewrote every source URL in one data file without its page. The card was
about a credit line; the data file was not in scope and no test looked at it. The reviewer diffed the file
against the base branch. Rule since: regenerated data is diffed line by line, and the generator now fails
without its cache.

**A 24 pt tap target.** A new disclosure header was tappable on an area about 24 pt high. The accessibility
audit measured the accessibility element, not the tappable header, so it passed. The reviewer read the
picture. The fix added its own 44 pt button and a UI test asserting the frame.

**A test that passed on the old layout.** A new settings test asserted something the old code already
satisfied. Rule since: every new test is shown failing on the old code, with the log.

**A rule that cut long two-word names.** A new text-fitting rule truncated long two-word names on every list
that shares the row. The sample name passed by luck. A UI test cannot see a cut label; only pictures with a
deliberately long name showed it.

**A CSS denylist filter that kept losing.** A sanitiser for card styles could be broken out of: a `url()`
copied verbatim closed the style tag, single-pass deletion rebuilt removed tokens, and `image-set()` strings
carried URLs past the list. Six rounds, three of them on a second model briefed to break the code instead of
checking a list. The filter became an allowlist. Nothing displayed that HTML yet, so nothing was exposed.

**A merge rule with two holes visible only from mid-sync states.** A sync rule for a counter passed its own
tests. A reviewer traced two cases: a device with a fast clock could raise the other device's count after
the two had settled, and a lone change was lost when the other device had only synced in between. Every
existing test settled first. The fixes came with failing tests that start from mid-sync states.

**A fix keyed on a fold state, proven in too few poses.** On a folding device, one bundle ran each fix in
one or two poses and changed a layout rule after those runs. Reviewers insisted on the repo's per-pose check
and largest-text pictures at the final rule; they found two real layout problems the default-size runs
missed. In a later card a fix tied to a fold state left another pose that shares the state without its only
Share control. Rule since: a fix keyed on a fold state is checked in every pose that shares that state, at
the final rule.

**A pixel test reading through translucent glass.** A test "proved" a background fix by sampling pixels
under a translucent control, so it measured the control's own shadow. It passed by accident. Rule since: a
pixel test logs the frames it samples and is shown failing on the old code with its readings.

## What it costs and what it misses

Rounds are expensive: several cards took four to six. Five of one card's six rounds were about sentences in
comments that claimed more than the logs supported. The reviewer cannot run anything, so a failure that only
shows on the CI runner gets through: see the lockfile failure in [briefs.md](briefs.md). More in
[limits.md](limits.md).
