# A PR push is a lane use

Date: 2026-11-11

Rule: The lane holds one simulator worker or one CI run. A PR push counts, because fast CI boots a simulator on the same machine. Sim-free workers commit locally and hold their pushes.

Incident: A sim-free worker pushed while a simulator worker's run was going. Its CI job booted a second simulator. Swap reached 16 GB, load 260 to 320, the stop rule fired and the run was lost.

Why: The build machine is one shared lane for dev simulators and self-hosted CI.

How to apply: Open one PR at a time and wait for its CI to finish before the next simulator worker starts. Check for queued and in-progress runs before starting a worker: the gate counts active runs, but a push can start one right after it passes. The lead waits for the gate to pass before releasing the lane, whatever the active run is.
