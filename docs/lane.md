# The simulator lane and machine safety

Throughput in this system is set by the build machine, not by the models. The live machine is one Mac mini
with 16 GB of memory and ten cores. It runs the workers' simulators and it is also the self-hosted CI
runner. Models can write code for several cards at once; the machine can prove one of them at a time.

The rules below exist because the machine crashed twice on 2026-11-04 with several simulator workers and CI
jobs running together (load averages of 150 to 700). A crash kills every worker mid-run and costs more time
than serial work would have.

## One lane

One lane holds either a single simulator worker or a single CI run. A PR push counts as a CI run, because
fast CI boots a CI simulator on the same machine. So:

- At most one lane-holding worker. Up to two sim-free workers (core, web, scripts, content) may run beside
  it. They commit locally and hold their pushes until the lead says the lane is free.
- One PR in CI at a time. The lane goes to the next worker only after that CI run ends.
- Nightly CI windows are fixed. Workers are off the simulator, with it erased, before a window starts and
  until the run has appeared and finished. See [examples/lane-rules.md](../examples/lane-rules.md), the
  shared rules handed to workers during one busy week.

The incident behind "a push counts": on 2026-11-11 a sim-free worker pushed while a simulator worker's run
was going. Its CI job booted a second simulator. Swap reached 16 GB, load 260 to 320, and the run was lost.

## The start gate

[scripts/macgate.sh](../scripts/macgate.sh) prints the machine's state and exits 0 only when load is under
30, swap is under 12 GB, no simulator is booted and none of the six most recent CI runs of each listed repo
is in progress or queued.
[scripts/waitgate.sh](../scripts/waitgate.sh) polls it. The lead runs the gate before starting a lane
worker, before allowing a push, and before a full run.

The swap limit was 8 GB, then 10 GB (2026-11-11), then 12 GB (2026-11-14). The last change came with a
reading: 11.3 GB of stale swap with nothing booted and 79% of memory free after a day of cold boots.

## The stop rule, and how it changed three times

[scripts/macstop.sh](../scripts/macstop.sh) is run every two minutes during a simulator job. Its history is
in its own comments:

| Date | Rule | The reading that forced the change |
|---|---|---|
| before 2026-11-11 | Stop at 13 GB of swap; erase the simulator after every use | An erased simulator's first boot alone parks about 11.6 GB in swap, so the two rules together guaranteed a stop. Five runs of one card were stopped before any completed, four of them this way. |
| 2026-11-11 | A reading is bad when swap is over 13 GB and the machine is under real pressure (load over 30, or free memory under 15%). Erase at the end of a card. | Swap total alone misleads. A warm boot sat at 7.9 GB against 11.6 GB cold. |
| 2026-11-12 | Stop only on two bad readings in a row, 90 seconds to 10 minutes apart | A cold boot alone tripped the rule (load 119, swap 14.1 GB, 33% free) and a minute later the machine was at 7.4 GB swap and 76% free. |
| 2026-11-13 | Readings in the first 5 minutes after a simulator boots are not counted | A cold boot alone tripped the two-readings rule (load 116, then 33 and falling). The script reads the youngest simulator process's age itself. |

Each change was proposed to the owner with the readings and one replacement rule. That is itself a rule:
see [rules/renegotiate-rules-with-readings.md](../rules/renegotiate-rules-with-readings.md).

These numbers are tuned to one machine. On another machine they are starting values to measure against, not
facts. They are read from the private config ([config/SCHEMA.md](../config/SCHEMA.md), `machine.gate` and
`machine.stop`).

## Staged cold start

A freshly erased simulator's first boot costs about 11 GB of swap on this machine, and a full compile on top
of it pushes load past 100. Workers stage a cold start:

1. Boot the simulator alone. Wait for load under 15.
2. `xcodebuild build-for-testing -jobs 4` with the test script's own flags and DerivedData path.
3. Wait for load under 15 again. A whole suite's first test failed at load 123 when this step was skipped.
4. Run the tests.

Between runs the simulator stays booted or shut down, not erased. A long suite is split into class groups.
The simulator is erased once, at the end of the card. Before cold-booting a second simulator the first is
erased, because a shut-down simulator keeps about 6 GB in swap. Simulators are shut down by UDID, never
"all": a worker once shut down every simulator instead of its own.

## Disk

Swap lives on the data volume. A long suite took free disk from 35 GB to 20 GB. Workers read free disk with
every stop-rule reading and stop under 21 GB. A failed run's result bundle is copied out before any rerun,
because the next run deletes it.

## Waiting

A worker waits inside commands, in poll loops of at most three minutes, never by ending its turn. An idle
session is not woken when load drops (one sat idle for 90 minutes), and a long loop hides the lead's
messages (a 20-minute loop hid a lane release for 30 minutes). Sim-free workers read `uptime` before a
heavy compile and wait when load is over 30: load reached 315 when a cold boot and two workers' builds
landed together.

## When the owner needs the machine

When the owner says he needs the machine, all simulator, build and UI-test work stops at once and resumes
only on his word. Board work, review and reading continue.

## What is not solved

There is no lock across apps: the gate sees only CI runs that have already started, so a push that lands
right after the gate passes can still collide. A machine restart still kills every worker
([limits.md](limits.md)).
