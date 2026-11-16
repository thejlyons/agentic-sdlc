# Start full proof runs yourself

Date: 2026-11-10

Rule: When the base branch has everything a full CI run needs, the lead starts the run. It does not wait for the owner to press the button.

Incident: The lead treated the long full run as the owner's to start, and a phase stalled on it.

Why: The owner wants to be asked about decisions, not about routine steps.

How to apply: Start the run only after the gate passes: nothing booted, no other CI run, no simulator worker. Read every error line afterwards, including steps marked continue-on-error. Stop at once if the owner needs the machine.
