> Live version as of 2026-11-16, sanitised by scripts/sync.py; app names and ids are the example config's.

Review: PASS (with two things to confirm on the PR before merging: the Site check and a Weekly updates dispatch on the branch, see below)

## Blocking
None.

## Non-blocking
1. `~/Github/FieldApp/.claude/worktrees/fld-328/FieldSite/package-lock.json:2736`: astro 7.4.12 now requires Node `>=22.23.4` (7.3.8 required `>=22.12.0`). `FieldSite/.nvmrc` is `22`, and `site.yml` / `weekly-updates.yml` use setup-node without `check-latest`, so CI takes whatever 22.x the runner image has cached. 22.23.4 came out 2026-10-20 and 22.23.5 is in the setup-node manifest, so it should be fine, but the worker's build ran on local Node v24.11.0, not CI's Node 22. The Site check on the PR is the real proof; if it fails with an unsupported-Node error, the fix is `check-latest: true` or a higher `.nvmrc`.
2. `~/Github/FieldApp/.claude/worktrees/fld-328/FieldSite/package.json:7`: `engines.node` still says `>=22.12.0`, now below what astro accepts. Worth raising to `>=22.23.4` in this PR or a follow-up.
3. The PR does not exist yet (branch not pushed). Its body must name the three majors held back: typescript 7.0.2, @types/node 26.6.6, concurrently 10.0.7.
4. Scope beyond the card: `FieldTiles/package.json` and `FieldTiles/README.md` move `npx wrangler@4.154.0` to `4.163.0`. This is justified, since `scripts/package-audit.py:109-115` fails every PR's fast tier if the Tiles pin differs from the site's wrangler. Nobody ran Tiles `dev`/`deploy` with 4.163.0 (it needs a Cloudflare login).
5. FieldManager lint has 5 errors before and after per the hand-back, and lint is not in CI. That is a follow-up card, as the hand-back says.

## Done when
- **astro without the two advisories, npm audit clean, site builds and checks pass**: proven except the build, which I did not run.
  - The lockfile resolves astro 7.4.12 from registry.npmjs.org.
  - GitHub's advisory data gives the fixes as 7.4.5 for GHSA-mh32-jxcr-mh9f and 7.4.7 for GHSA-r3h5-4585-7x3w; 7.4.12 is past both.
  - I ran `npm audit --package-lock-only` in FieldSite and FieldManager: 0 vulnerabilities in each.
  - The build claim (7 pages) is the worker's, on Node 24; the Site workflow on the PR settles it.
- **Other patch/minor updates, no majors**: proven.
  - Every changed range in both `package.json` files stays within its major.
  - typescript stays `~6.0.2` (locked 6.0.3), @types/node stays on 24, concurrently stays `^9`.
  - The weekly script now lists only those three as newer.
- **Weekly updates passes on the branch**: proven locally, not yet on GitHub.
  - I ran `python3 scripts/package-audit.py --updates` at 2539ec73: 0 advisories for all 24 packages, both audits "nothing found", three major-version warnings only, no `::error` line.
  - The fast-tier `python3 scripts/package-audit.py` also passes ("all 24 listed ... at their locked versions").
  - The branch is not pushed, so the workflow itself has not run there; dispatch it on the branch after pushing.

## Other checks I ran
- **Diff scope**: 7 files, one commit, clean tree: the two `package.json` files, the two lockfiles, `packages.json`, and the two Tiles files. No workflow, script or source changes.
- **Lockfile consistency**: `npm ci --dry-run` succeeds in both projects with no out-of-sync error.
- **Supply chain**: all 349 (Site) and 214 (Manager) `resolved` URLs are registry.npmjs.org. No `hasInstallScript` entry was added or removed.
- **New transitive packages in Site**:
  - `@astrojs/runtime`, `@astrojs/vite-plugin-astro`, `mri` and `tinyps` are direct astro dependencies; `fnv1a-64` and `std-env` come in transitively.
  - `tinyps` (tinylibs) and `fnv1a-64` are both young, from 2026, but from known maintainers and without install scripts.
  - The rest are wasm and platform bindings.
- **Screenshots**: I viewed `home-before.png` and `home-after.png`, and `cmp` reports them byte-identical. They cover the home page only: dark theme, 1280 wide, first 2400 px.

## Not checked
- A real `npm ci`, `npm run build` for the site, and FieldManager `npm run build` / `npm run lint`: my role here is read-only and excludes running builds, so those rest on the hand-back and the PR's Site check. FieldManager has no CI job at all, so its build after react 19.3 / vite 8.3.8 is the worker's word only; running `npm ci` then `npm run build` in FieldManager would settle it.
- The hand-back's dist comparison (HTML byte-identical, CSS differing only by tailwind 4.3.5 output): not reproduced. The other six pages, mobile width and light mode were not pictured.
- `python3 -m unittest discover -s scripts`: the worker did not finish it and I did not run it. CI's Engine job covers it.
- Whether the `/api/subscribe` Pages function still works under wrangler 4.163.0 and the new workers-types: there is no typecheck script, so only the PR preview deploy shows it.