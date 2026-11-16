# Decide small reversible choices after about 15 minutes

Date: 2026-11-13

Rule: For a simple, reversible choice, ask as usual; if the owner has not answered in about 15 minutes, go with the recommendation and list it on the dashboard under "Decided for you".

Incident: A small layout choice sat open overnight although the recommended option had already been built.

Why: Waiting adds nothing when the choice is cheap to flip later.

How to apply: Set `lead_decided: {at, question, choice}` on the card and clear `needs_j`. The item stays listed until the owner presses "Looks good" or asks for a change, which the lead makes and then closes. "Simple" is the lead's reading: reversible and cheap to change. Never for anything on the always-ask list, or for scope and pricing.
