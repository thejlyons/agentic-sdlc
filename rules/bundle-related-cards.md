# Bundle related small cards into one worker run and one PR

Date: 2026-11-12

Rule: "One card, one PR" is not a rule. Cards that touch the same screen, device pose or test area are built by one worker and merged as one PR.

Incident: About twenty small cards remained in one phase. As twenty PRs each would cost a cold simulator boot, a build, a review and a CI slot: several nights. As seven or eight bundles, far less.

Why: The per-PR overhead on a single build machine is larger than the cards.

How to apply: Put every card id in the PR title. The reviewer checks each card's "Done when" separately. Each card keeps its own status and history. Do not bundle unrelated areas or a risky change with safe ones. On multi-item bundles, get a code review before the first lane slot.
