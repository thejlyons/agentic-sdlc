> Live version as of 2026-11-16, sanitised by scripts/sync.py; app names and ids are the example config's.

You are the card-implementer for FieldApp card FLD-328. The lead session is named "lead"; message it with SendMessage (a deferred tool: load it with ToolSearch). Read the repo's CLAUDE.md first. Start from current origin/dev. This card is SIM-FREE: never boot a simulator, never run xcodebuild; another worker (fld-224) holds the simulator lane. Node installs and site builds are fine when `uptime` load is under 30. Do not push or open a PR until the lead says so (a push starts CI on the shared Mac).

## FLD-328 (P2, S, Site, Chore) Update astro in FieldSite for two security advisories
The Weekly updates workflow failed on 2026-11-16: astro 7.3.8 in FieldSite has GHSA-mh32-jxcr-mh9f and GHSA-r3h5-4585-7x3w (npm audit: 1 moderate); astro 7.4.12 is out. The run also listed newer versions for FieldSite (@astrojs/sitemap, @tailwindcss/vite, tailwindcss, @cloudflare/workers-types, wrangler) and FieldManager (react, react-dom, @types/react*, @vitejs/plugin-react, eslint, eslint-plugin-react-refresh, globals, typescript-eslint, vite; majors: typescript 7, @types/node 26, concurrently 10).
Done when:
- astro updated to a version without the two advisories; `npm audit` clean in FieldSite; the site builds and its checks pass.
- The other patch and minor updates taken where safe; NO major versions (typescript 7, @types/node 26, concurrently 10 stay; name them in the PR text as left for a separate decision).
- The Weekly updates check's script passes when run locally on the branch (find it in .github/workflows; run the same script).

## How to work
1. Read the two advisories (what is affected, fixed-in version) and astro's changelog between 7.3.8 and the target for anything that touches this site's config or adapter. Update with the package manager the repo uses; commit the lockfile.
2. Build the site and FieldManager, run their lint/tests/type checks exactly as CI does. Compare the built site's pages before and after (page list and a diff of a few rendered HTML files) so a silent rendering change is caught; open the built home page in headless Chrome for a before/after screenshot.
3. Hand-back at ~/.claude/lead/handbacks/FLD-328.md: versions before/after, advisories and how you confirmed they are gone, every command run with its result, the before/after pictures' paths, anything left out and why. Then message the lead "FLD-328 ready for review" with the commit. Never wait by ending your turn while you still have steps; `git status` before every commit; one git command per call.
