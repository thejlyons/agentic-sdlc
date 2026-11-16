# Only erase frees simulator disk

Date: 2026-11-03

Rule: Shutting a simulator down does not free its disk or its swap; only erasing does. CI erases its simulators at the end of every job. A worker erases its dev simulator at the end of its card.

Incident: The shared build machine kept failing the free-disk gate. 41 simulators held 14.7 GB; five of them held almost all of it, and each had only cost disk after it had run. A shut-down simulator also keeps about 6 GB in swap.

Why: Disk and swap are on the same volume, and the machine has little of either.

How to apply: CI: shut down and erase at job end. Workers: keep the simulator booted or shut down between runs of one card, erase once when the card's simulator work is finished, and erase the first simulator before cold-booting a second. Delete simulators of parked apps. The free-disk gate is 20 GB for CI and 21 GB for workers.
