# One simulator-using job at a time

Date: 2026-11-04

Rule: At most one simulator-using worker runs at a time on the shared build machine. Read-only reviewers may run in parallel.

Incident: The machine (ten cores, 16 GB) crashed twice in one day while several simulator workers and CI jobs, each with booted simulators, ran together. Load averages sat between 150 and 700.

Why: A crash kills every worker mid-run, loses simulator state, makes UI tests flaky afterwards, and wastes more time than serial work would have.

How to apply: Before starting a worker or re-running CI, check that the 1-minute load is under about 30 and let post-crash system daemons settle. Do not push several branches at once. Prefer fewer, larger PRs and targeted checks. A visionOS simulator run is always alone.
