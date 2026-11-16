# Merge without asking, after an independent review and green CI

Date: 2026-11-03 (widened 2026-11-11)

Rule: A PR is merged without asking the owner when every CI check is green with none pending and a separate reviewer, not the author and not the lead's own opinion, found nothing blocking.

Incident: The lead had been asking before each release merge, which stalled work for hours. The owner replaced the question with a condition.

Why: The owner wants work to keep moving, and trusts the condition more than his own glance at a diff.

How to apply: Applies to feature PRs into the base branch (squash) and to release PRs (merge commit). Tell the owner afterwards. PR comments, PR creation and feature-branch pushes need no check-in either. If a branch ruleset refuses something, report it; do not work around it. Still ask for anything outward-facing or irreversible that is not a merge. The guard hook enforces the condition mechanically.
