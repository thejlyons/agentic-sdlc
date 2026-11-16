# Screen sessions on the build machine may run without asking

Date: 2026-11-14

Rule: UI tests and picture sessions that take the build machine's screen and keyboard may run without asking first, one at a time and never beside a simulator run.

Incident: Asking before each short desktop-app picture session held up proof that only that session could give.

Why: The machine is there for this work; asking each time bought nothing.

How to apply: Same lane rules: gate first, stop-rule readings during. Build the desktop target before asking for the session. Stop when the owner needs the machine. The lead does not script GUI apps on the runner itself: a system dialog it raised once failed a CI trial.
