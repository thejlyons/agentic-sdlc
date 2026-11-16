# One lead, and only the lead writes card status

Date: 2026-11-11

Rule: There is one lead session. It is the only writer of card status on the dashboard. Workers report; the lead records.

Incident: Setting up the loop showed that background workers and subagents cannot reach the dashboard database, and that two coordinators writing the same card fight over its version.

Why: One writer means no version fights and one place where status can be wrong.

How to apply: Write status in the same turn as the event, with real clock times. A handover between lead sessions happens at a clean point (the old lead's last PR merged).
