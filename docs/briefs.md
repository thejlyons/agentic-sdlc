# Briefs, hand-backs and what a round trip looks like

A brief is the ticket a worker gets. A hand-back is what it returns. This page walks through one real card,
sanitised: a dependency update for two security advisories. It is a small card, chosen because the whole
trail fits on a screen and still shows a failure the process did not prevent.

- Brief: [examples/FLD-328/brief.md](../examples/FLD-328/brief.md)
- Hand-back, three rounds: [examples/FLD-328/handback.md](../examples/FLD-328/handback.md)
- What the reviewer was given: [examples/FLD-328/review-request.md](../examples/FLD-328/review-request.md)
- The review: [examples/FLD-328/review.md](../examples/FLD-328/review.md)

Templates: [brief](../templates/brief.md), [hand-back](../templates/handback.md),
[review report](../templates/review-report.md).

## Anatomy of the brief

**Who and where.** The first paragraph names the agent role, the card, the lead session to message, and the
starting ref. Nothing is left to infer.

**The lane, stated as a constraint with its reason.**

> This card is SIM-FREE: never boot a simulator, never run xcodebuild; another worker (fld-224) holds the
> simulator lane. [...] Do not push or open a PR until the lead says so (a push starts CI on the shared Mac).

**The card in full, with the evidence that opened it.** The failing weekly check, the two advisory ids, the
current and available versions. The worker does not have to rediscover why the card exists.

**"Done when" boxes that can be checked.**

> - astro updated to a version without the two advisories; `npm audit` clean in FieldSite; the site builds
>   and its checks pass.
> - The other patch and minor updates taken where safe; NO major versions [...]
> - The Weekly updates check's script passes when run locally on the branch [...]

Each one names a command or an observable state. The second also says what is out of scope and what to do
with it (name the held-back majors in the PR text).

**How to work: method, not solution.** Read the advisories and the changelog. Build as CI does. Compare the
built pages before and after "so a silent rendering change is caught". The brief says what would count as
proof. It does not say what the worker will find.

**The hand-back contract.** Where the file goes, what it must list, and the standing habits: `git status`
before every commit, one git command per call, never wait by ending the turn.

## What came back

Round 1 of the hand-back ticks each "Done when" item with its evidence: `npm audit` before (1 moderate) and
after (0), page count, byte-identical HTML once a hashed CSS name is normalised, byte-identical screenshots.
It also reports what it did not do:

> NOT run: `python3 -m unittest discover -s scripts` in full. It ran over 2 minutes without finishing while
> fld-224 held the lane, so I stopped it rather than wait [...]

and one change outside the card, with the reason (an audit script fails unless a version pin in another
package matches). A reviewer can judge a stated deviation. It cannot judge a hidden one.

## What the reviewer was given, and found

The review request gives the card text, the worktree, the head commit and the base ref, and a list of things
to "check for yourself, not from the worker's claims". It points at the hand-back so the reviewer can verify
its claims. It does not argue that the change is right.

The review passed with no blocking items, and still found something the worker had not:

> astro 7.4.12 now requires Node `>=22.23.4` (7.3.8 required `>=22.12.0`). [...] the worker's build ran on
> local Node v24.11.0, not CI's Node 22. The Site check on the PR is the real proof

The reviewer also checked what a dependency update can hide: every resolved URL is the public registry, no
install script was added or removed, and the new transitive packages are named. Its "Not checked" section
lists what it could not verify read-only. Round 2 of the hand-back raises the Node floor and builds on that
exact Node version.

## What still broke

The first push failed in CI:

> Site workflow's `npm ci` failed on the PR (Missing @emnapi/core|runtime from lock file): my lockfiles were
> written by npm 11 (Node 24) and omit optional @emnapi entries that npm 10 (Node 22 on the runner) requires.

The worker's local `npm ci` had passed. The reviewer's `npm ci --dry-run` had passed. Both ran the local
npm. The reviewer's Node note pointed at the right risk (local toolchain differs from CI's) but named the
Node version, not the npm major. CI caught it; the fix was a lockfile regenerated with CI's npm major, and
the lead verified that commit as lockfile-only.

The lesson went into the retro log the same day ([RETRO.md](../RETRO.md), 2026-11-16): verify lockfiles with
the CI npm major before pushing. From red weekly check to merged card took about ninety minutes, while a
simulator worker on another card held the lane.

## What makes a brief good, in this system's experience

- It states constraints with reasons, so the worker can apply them to cases the brief did not foresee.
- "Done when" items are checkable by someone who was not there.
- It lists what earlier cards already prove, so the worker does not redo it.
- It separates the goal from guesses about the cause. A guessed cause stated as fact gets "confirmed".
- It says where findings go: repo text says what the change does; investigation figures go in the hand-back.
  One card spent five review rounds on sentences in comments that claimed more than the logs supported.
- It is complete enough to restart from. After a machine restart a worker resumed from its hand-back alone.
