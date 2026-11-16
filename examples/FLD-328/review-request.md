> Live version as of 2026-11-16, sanitised by scripts/sync.py; app names and ids are the example config's.

Review FieldApp card FLD-328 (read-only). Worktree: ~/Github/FieldApp/.claude/worktrees/fld-328, branch fld-328-site-deps-audit, head 2539ec73, base origin/dev. This card is sim-free: do NOT boot a simulator or run xcodebuild (another worker holds the simulator lane). Node commands are fine if `uptime` load is under 30.

Card text:
"Update astro in FieldSite for two security advisories. 2026-11-16: The Weekly updates workflow failed: astro 7.3.8 in FieldSite has GHSA-mh32-jxcr-mh9f and GHSA-r3h5-4585-7x3w (npm audit: 1 moderate). astro 7.4.12 is out.
Done when:
- astro updated in FieldSite to a version without the two advisories; npm audit clean there; the site builds and its checks pass.
- The other small patch and minor updates the run listed for FieldSite and FieldManager taken where they are safe (no major versions: typescript 7, @types/node 26, concurrently 10 stay as they are and are named in the PR).
- The Weekly updates check passes when run on the branch."

Check for yourself, not from the worker's claims: `git diff origin/dev...HEAD --stat` and the diff (package.json and lockfiles only? anything else changed?); that no major version moved; that the lockfile is consistent with package.json (a clean install with the repo's package manager in frozen/ci mode works); `npm audit` in FieldSite; the site build and FieldManager's build/lint/type checks as CI runs them (see .github/workflows); the weekly updates script from the workflow run locally; whether the resolved astro version actually contains the fixes for both GHSA ids (check the advisories' fixed-in versions); any new transitive dependency that looks odd (new postinstall scripts, a changed registry, a package that was not there before with few downloads). The hand-back is at ~/.claude/lead/handbacks/FLD-328.md; verify its Done-when claims and its before/after rendering comparison.

Report: "Review: PASS" or "Review: CHANGES" first, blocking items with file and line, then non-blocking notes. Short.