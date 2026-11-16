# Validate UI yourself, in the simulator

Date: 2026-10-29

Rule: An agent checks UI behaviour itself (build, install, screenshot, UI test, accessibility audit) and reads the pictures. It does not ask the owner to check by hand.

Incident: While a local screen loop was being set up for one app, agents were still handing UI checks to the owner.

Why: The owner checking by hand is the bottleneck the screen loop exists to remove.

How to apply: Before asking the owner anything about UI, run the screen loop or a UI test and open the pictures. For a fix, prefer a separate validator that sees only the diff and the app's rules. Ask the owner only for taste calls and for things that need a new permission.
