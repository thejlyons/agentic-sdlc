#!/bin/bash
# Live version as of 2026-11-20, sanitised by scripts/sync.py; app, repo and machine values come from ~/.claude/lead/config.json.
# Limits and repos come from ~/.claude/lead/machine.env, which bootstrap writes from config.json (`machine`).
# The defaults below are the live machine's (a 16 GB Mac mini).
[ -f "${LEAD_DIR:-$HOME/.claude/lead}/machine.env" ] && . "${LEAD_DIR:-$HOME/.claude/lead}/machine.env"
: "${GATE_MAX_LOAD:=30}" "${GATE_MAX_SWAP_MB:=12288}"
# Mac gate: prints state; exit 0 only when swap < 12 GB, or < 13 GB when load < 5 (J, 2026-11-20: stale swap sat just over 12 GB after most jobs with the Mac idle and cost 3-10 min each time) (J raised it to 12 GB on 2026-11-14: stale swap sat at 11.3 GB with nothing booted and 79% memory free after a day of cold boots; before that 10 GB, raised from 8 GB on 2026-11-11; the 13 GB stop rule is unchanged; stale swap idles near 4.5 GB; real crashes were 14+ GB with several sims), load < 30, no CI simulator booted, no CI run in progress/queued
l=$(uptime | sed 's/.*load averages*: //' | awk '{print $1}' | tr -d ,)
sw=$(sysctl -n vm.swapusage | sed 's/.*used = \([0-9.]*\)M.*/\1/')
booted=$(xcrun simctl list devices booted | grep -c "Booted")
runs=0
for r in $GATE_REPOS; do
  n=$(gh run list -R "$r" --limit 6 --json status 2>/dev/null | grep -Ec '"status":"(in_progress|queued|waiting|pending)"')
  runs=$((runs + n))
done
echo "load=$l swapMB=$sw bootedSims=$booted activeRuns=$runs"
awk -v l="$l" -v s="$sw" -v b="$booted" -v r="$runs" -v ml="$GATE_MAX_LOAD" -v ms="$GATE_MAX_SWAP_MB" 'BEGIN{exit !(l<ml && (s<ms || (s<ms+1024 && l<5)) && b==0 && r==0)}'
