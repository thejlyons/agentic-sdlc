# A merged card is Done; proof that must wait becomes its own card

Date: 2026-11-06

Rule: When a card's PR merges, the card is closed. If part of its proof depends on something that comes later, that proof is filed as a separate card in the later stage.

Incident: Merged cards sat in review waiting for a real-world run that could not happen yet. The board understated what was finished and a phase could never reach 100%.

Why: The dashboard should show what is actually built, and a phase must be finishable.

How to apply: On merge set Done and tick the boxes. For proof that must wait, file a follow-up in the matching later stage with the exact "first real run must show" checklist.
