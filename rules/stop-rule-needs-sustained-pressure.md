# Stop a simulator job on sustained pressure, not on one number

Date: 2026-11-11, refined 2026-11-12 and 2026-11-13

Rule: A reading is bad when swap is over the limit and the machine is under real pressure (high load or low free memory). The job stops only on two bad readings in a row about two minutes apart, and readings in the first five minutes after a simulator boots are not counted.

Incident: Swap alone stopped runs that were healthy. Then a cold boot alone tripped the single-reading rule (load 119, swap 14.1 GB, 33% free) and cleared within a minute. Then a cold boot tripped the two-readings rule (load 116, then 33 and falling).

Why: A stop rule that fires on a normal cold boot wastes the run it was meant to protect.

How to apply: Use the stop script every two minutes during a simulator job and keep its lines for the hand-back. On a stop: end the job, shut the simulator down without erasing, report the readings and the test that was running. Stage cold starts so a boot spike never overlaps a test. The thresholds are per machine and live in the private config.
