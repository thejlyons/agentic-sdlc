# The priority app gets the lane first

Date: 2026-11-13

Rule: While the priority app has cards left in the current phase, its workers get the simulator lane first. Other apps use the lane only in its gaps and hand it back as soon as a priority worker is ready.

Incident: The lane alternated between two apps. A whole-suite run for the second app, run twice, held the lane for 80 minutes while a bundle for the priority app waited, and the owner noticed before the lead acted.

Why: Finishing one app's phase matters more than even progress across apps.

How to apply: Keep a priority-app worker always queued so the lane has no idle gap. A worker for another app asks the lead before any simulator run longer than about 15 minutes, because it cannot read a hand-back request until its command ends. If a long run is in the way, the lead stops it. Sim-free work for other apps runs alongside as before. The order is `apps[].lane_priority` in the config.
