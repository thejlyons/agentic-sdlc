# Stop all machine-heavy work when the owner needs the machine

Date: 2026-11-08

Rule: When the owner says he needs the build machine, all simulator, build and UI-test work stops at once and resumes only when he says so.

Incident: The build machine is also the owner's own computer. Simulators and builds take the memory he needs.

Why: It is his machine, and a running simulator makes it unusable for anything else.

How to apply: The moment he says it: message every worker to stop simulators, builds and UI tests, commit work in progress, shut down and erase its simulators, and wait for the lead's go without polling the gate. Do only board, review, reading and cleanup work meanwhile. Do not resume on a guess.
